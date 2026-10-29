"""Deterministic procedural audio beds, cues, ducking and PCM mix for Pro mode."""

from __future__ import annotations

from array import array
from dataclasses import dataclass, replace
import hashlib
import math
from pathlib import Path
import random
import struct
import subprocess
import time
import wave
from typing import Callable

from .media import bundled_binary
from .pro_spec import RenderSpec, _seeded_unit
from .schema import PackageError


SAMPLE_RATE = 48000


@dataclass(frozen=True)
class Cue:
    id: str
    time_ms: int
    variant: int
    gain_db: float
    pitch_cents: float
    scene_id: str
    event_id: str = ""
    event_frame: int | None = None
    tag: str = ""
    feature: str = "onset"
    lead_ms: float = 0
    event_time_ms: float = 0


def _cue_id(transition: str, motion: str) -> str:
    if transition in {"INK_WIPE", "BRUSH_WIPE", "PAPER_TEAR"}:
        return "PAPER_SLIDE"
    if transition in {"FILM_BURN", "LIGHT_LEAK_FLASH"}:
        return "IMPACT_SOFT"
    if transition in {"WHIP_PAN", "QUICK_PUSH", "SLIDE_SHADOW"}:
        return "WHOOSH_FAST"
    if motion == "TINY_PUNCH_IN":
        return "IMPACT_LOW"
    if transition in {"CROSSFADE", "GENTLE_DISSOLVE", "DISSOLVE_BLUR"}:
        return "SWIPE_SOFT"
    return "FILM_CLICK"


def choose_cues(spec: RenderSpec, density: float, enabled: bool = True) -> tuple[Cue, ...]:
    if not enabled:
        return ()
    if spec.package.schema_version=='ATS_PACKAGE_V3':
        from .event_audio import choose_event_cues
        return choose_event_cues(spec,spec.package.pro.get('audio',{}).get('sfx',{}))[0]
    explicit=[]
    for i,item in enumerate(spec.package.pro.get("scenes",[])):
        cues=list(item.get("sfx",[]))
        transition_sfx=item.get("transition_config",{}).get("sfx")
        if transition_sfx and transition_sfx!="NONE":
            cues.append({"id":transition_sfx,"offset_ms":0})
        for cue in cues:
            offset=cue.get("offset_ms",0)
            cue_ms=max(0,round(spec.scenes[i].first_frame/spec.package.fps*1000+offset))
            if any(abs(c.time_ms-cue_ms)<350 for c in explicit):
                raise PackageError(f"$.scenes[{i}].sfx: cue is within 350 ms of another explicit cue")
            explicit.append(Cue(cue["id"],cue_ms,1 if cue.get("variant","AUTO")=="AUTO" else cue["variant"],
                                cue.get("gain_db",-22),cue.get("pitch_cents",0),spec.scenes[i].id))
    if spec.package.pro.get("product_version")==3:
        return tuple(c for c in explicit if c.scene_id!=spec.scenes[0].id)
    scenes=spec.scenes
    choices=[]
    for i in range(1,len(scenes)):
        scene=scenes[i]
        prior=spec.package.scenes[i-1]
        priority=(3 if scene.motion=="TINY_PUNCH_IN" else 2 if prior.voice_text.rstrip().endswith((".","!","?"))
                  else 1 if scene.transition_applied not in {"HARD_CUT","NONE"} else 0)
        choices.append((-priority,_seeded_unit(spec.seed,f"cueorder:{i}"),i))
    choices.sort()
    target=round(len(choices)*max(0,min(1,density)))
    selected=list(explicit)
    if (density>0 and spec.auto_direct and not spec.strict_json and
        spec.package.pro.get("auto_direct",{}).get("pattern_interrupt",True)):
        for scene in scenes:
            if scene.frames <= round(3.5*spec.package.fps):
                continue
            if len(selected)>=target:
                break
            midpoint=round((scene.first_frame+scene.frames//2)/spec.package.fps*1000)
            if any(abs(c.time_ms-midpoint)<350 for c in selected):
                continue
            selected.append(Cue("TICK_SOFT",midpoint,1,-28,0,scene.id))
    automatic_target=max(0,target-len(selected))
    automatic=0
    for _priority,_random,i in choices:
        if automatic>=automatic_target:break
        scene=scenes[i]
        cue_id=_cue_id(scene.transition_applied,scene.motion)
        boundary_ms=round(scene.first_frame/spec.package.fps*1000)
        lead=90 if cue_id in {"SWIPE_SOFT","WHOOSH_FAST","PAPER_SLIDE"} else 0
        cue_ms=max(0,boundary_ms-lead)
        if any(abs(c.time_ms-cue_ms)<350 for c in selected):continue
        variant=1+int(_seeded_unit(spec.seed,f"cuevariant:{i}")*4)
        pitch=(_seeded_unit(spec.seed,f"cuepitch:{i}")*2-1)*40
        jitter=(_seeded_unit(spec.seed,f"cuegain:{i}")*2-1)
        selected.append(Cue(cue_id,cue_ms,variant,(-19 if cue_id.startswith("IMPACT") else -24)+jitter,pitch,scene.id))
        automatic+=1
    return tuple(sorted(selected,key=lambda c:c.time_ms))


def _run_decode(command: list[str], cancelled=None):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    started=time.monotonic()
    try:
        while True:
            if time.monotonic()-started>180:raise PackageError("Audio processing timed out after 180 seconds.")
            if cancelled and cancelled():
                from .renderer import RenderCancelled
                raise RenderCancelled()
            try:
                stdout, stderr = process.communicate(timeout=.1)
                return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            except subprocess.TimeoutExpired:
                continue
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def _decode_narration(path: Path, frames: int, cancelled=None) -> array:
    command=[str(bundled_binary("ffmpeg")),"-hide_banner","-loglevel","error","-nostdin",
             "-i",str(path),"-vn","-ac","1","-ar",str(SAMPLE_RATE),"-f","f32le","pipe:1"]
    done=_run_decode(command,cancelled)
    if done.returncode:
        raise PackageError(f"Cannot decode narration: {done.stderr[-1000:].decode(errors='replace')}")
    samples=array("f")
    samples.frombytes(done.stdout[:len(done.stdout)//4*4])
    if len(samples)<frames:samples.extend(array("f",[0.0])*(frames-len(samples)))
    return samples[:frames]


def _decode_user_music(path: Path, frames: int, cancelled=None) -> array:
    command=[str(bundled_binary("ffmpeg")),"-hide_banner","-loglevel","error","-nostdin","-i",str(path),"-vn","-ac","1","-ar",str(SAMPLE_RATE),"-f","f32le","pipe:1"]
    done=_run_decode(command,cancelled)
    if done.returncode:raise PackageError("Selected music file could not be decoded.")
    import numpy as np
    from .music import loop_pcm
    source=np.frombuffer(done.stdout,dtype="<f4")
    if not len(source):raise PackageError("Selected music file has no audio samples.")
    return loop_pcm(source,frames,SAMPLE_RATE)

from .music import loop_seams


def _procedural_cue(cue: Cue, seed: int) -> array:
    seconds={"IMPACT_LOW":.58,"IMPACT_SOFT":.46,"RISER_SHORT":.70,"WHOOSH_FAST":.45,
             "WHOOSH_SOFT":.55,"SWIPE_SOFT":.36,"PAPER_SLIDE":.40,"BRUSH_SCRATCH":.50,
             "PAGE_TURN":.62}.get(cue.id,.20)
    count=round(seconds*SAMPLE_RATE)
    rng=random.Random((seed, cue.id, cue.variant).__repr__())
    out=array("f",[0.0])*count
    low=0.0
    frequency=(50 if cue.id.startswith("IMPACT") else 200)*(2**(cue.pitch_cents/1200))
    for i in range(count):
        t=i/SAMPLE_RATE
        phase=i/max(1,count-1)
        noise=rng.random()*2-1
        low=.94*low+.06*noise
        if cue.id.startswith("IMPACT") or cue.id in {"STAMP_THUD","FILM_CLICK"}:
            value=(math.sin(2*math.pi*frequency*t)*.72+low*.28)*math.exp(-11*phase)
        elif cue.id.startswith("WHOOSH") or cue.id in {"SWIPE_SOFT","PAPER_SLIDE","PAGE_TURN","BRUSH_SCRATCH","RISER_SHORT"}:
            envelope=math.sin(math.pi*phase)**1.4
            value=(low*.65+noise*.18)*envelope
        else:
            value=(low*.35+noise*.30)*math.exp(-20*phase)
        fade=min(1,i/120,(count-i-1)/120)
        out[i]=value*max(0,fade)
    return out


def _write_wav(path: Path, samples: array) -> None:
    pcm=array("h",(int(max(-1,min(1,s))*32767) for s in samples))
    with wave.open(str(path),"wb") as file:
        file.setnchannels(1);file.setsampwidth(2);file.setframerate(SAMPLE_RATE)
        file.writeframes(pcm.tobytes())


def _speech_activity(samples: array) -> list[float]:
    block=round(SAMPLE_RATE*.02)
    result=[]
    for i in range(0,len(samples),block):
        part=samples[i:i+block]
        rms=math.sqrt(sum(value*value for value in part)/max(1,len(part)))
        result.append(min(1,max(0,(rms-.004)/.018)))
    smoothed=[];level=0.0
    for value in result:
        coeff=.75 if value>level else .10
        level+=coeff*(value-level)
        smoothed.append(level)
    return smoothed


def build_audio_mix(spec: RenderSpec, narration_path: Path, settings, work: Path,
                    debug_stems: bool = False, cancelled: Callable[[],bool] | None = None
                    ) -> tuple[Path,tuple[Cue,...],dict,dict[str,Path]]:
    import numpy as np
    from .fast_audio import (cached_wave, procedural_bed, activity, write_pcm,
                             check_cancel, feature_times)
    from .audio_packs import installed_user_assets
    started=time.monotonic();timings={};cache_hits=0;cache_misses=0
    def checkpoint(name, mark):
        timings[name]=round(time.monotonic()-mark,4);check_cancel(cancelled)
    mark=time.monotonic();user_assets,pack_warnings=installed_user_assets()
    frames=round(spec.package.total_frames/spec.package.fps*SAMPLE_RATE)
    narration=np.asarray(_decode_narration(narration_path,frames,cancelled),dtype=np.float32)
    narration*=getattr(settings,'voice_volume',1.0)
    checkpoint('decode_narration_s',mark)
    sfx=np.zeros(frames,dtype=np.float32);music=np.zeros_like(sfx);ambience=np.zeros_like(sfx)
    audio=spec.package.pro.get('audio',{});options=audio.get('sfx',{})
    if spec.package.schema_version=='ATS_PACKAGE_V3':
        from .fast_audio import event_feature_times
        feature_times=event_feature_times
        options={'intensity':settings.sfx_intensity,'max_per_second':settings.sfx_max_per_second,**options}
    auto_sfx=spec.package.pro.get('auto_direct',{}).get('sfx',True)
    density=options.get('density',settings.sfx_density if spec.auto_direct and auto_sfx else 0)
    cues=choose_cues(spec,density,spec.package.pro.get('direction',{}).get('sfx_enabled',True) and options.get('enabled',True))
    if spec.package.schema_version=='ATS_PACKAGE_V3':
        from .event_audio import choose_event_cues
        cues=choose_event_cues(spec,options)[0]
    effective=[];cue_sources=[]
    mark=time.monotonic()
    from .event_audio import library
    local_library=library() if spec.package.schema_version=='ATS_PACKAGE_V3' else {}
    for cue in cues:
        check_cancel(cancelled);asset=user_assets.get(('sfx',cue.id));source_file='PROCEDURAL'
        if cue.tag in local_library and local_library[cue.tag]:
            path=local_library[cue.tag][(cue.variant-1)%len(local_library[cue.tag])];source_file=str(path)
            from .media import probe_audio
            source=np.asarray(_decode_narration(path,round(min(30,probe_audio(path)[0])*SAMPLE_RATE),cancelled),dtype=np.float32)
        elif asset:
            path=asset['files'][(cue.variant-1)%len(asset['files'])];source_file=str(path)
            source=np.asarray(_decode_narration(path,round(asset['duration_s']*SAMPLE_RATE),cancelled),dtype=np.float32)
        else:
            count=round({'IMPACT_LOW':.58,'IMPACT_SOFT':.46,'RISER_SHORT':.70,'WHOOSH_FAST':.45,'WHOOSH_SOFT':.55,'SWIPE_SOFT':.36,'PAPER_SLIDE':.40,'BRUSH_SCRATCH':.50,'PAGE_TURN':.62}.get(cue.id,.20)*SAMPLE_RATE)
            source,hit=cached_wave('cue',[cue.id,cue.variant,cue.pitch_cents],count,spec.seed,lambda:_procedural_cue(cue,spec.seed),cancelled)
            cache_hits+=hit;cache_misses+=not hit
        features=feature_times(source)
        target_ms=cue.event_time_ms-cue.lead_ms
        clip_ms=cue.time_ms
        if cue.event_id:
            feature_ms=features.get(cue.feature+'_ms')
            clip_ms=target_ms-(feature_ms or 0)
        start=round(clip_ms/1000*SAMPLE_RATE)
        trimmed=max(0,-start)
        if trimmed:source=source[trimmed:];start=0;clip_ms=0
        local=narration[max(0,start-SAMPLE_RATE//4):min(frames,start+SAMPLE_RATE//4)]
        rms=float(np.sqrt(np.mean(local.astype(np.float64)**2))) if len(local) else 0
        peak=float(np.max(np.abs(source))) if len(source) else 1
        margin=(8 if cue.id.startswith('IMPACT') else 10) if cue.event_id else (10 if cue.id.startswith('IMPACT') else 16)
        safe=max(.002,rms)*10**(-margin/20)/max(.001,peak)
        if rms<.004:safe=max(safe,10**((-28 if cue.event_id else -38)/20)/max(.001,peak))
        gain=min(10**((cue.gain_db+options.get('gain_db',0))/20),safe)
        effective.append(replace(cue,time_ms=clip_ms,gain_db=round(20*math.log10(max(1e-7,gain)),2)))
        count=min(len(source),max(0,frames-start))
        if count:sfx[start:start+count]+=source[:count]*gain
        cue_sources.append({'cue':replace(cue,time_ms=clip_ms),'start':start,'count':count,'features':feature_times(source),'file':source_file,'trimmed_head_samples':trimmed,'target_ms':target_ms})
    checkpoint('sfx_s',mark)
    mark=time.monotonic();music_options=audio.get('music',{})
    music_id=music_options.get('track_id',spec.style.get('music','NONE') if settings.music_track=='STYLE_DEFAULT' else settings.music_track)
    source=None
    product=getattr(settings,'product_version',0)==3
    if product:music_id='NONE'
    if settings.music_path and (product or 'track_id' not in music_options):
        source=np.asarray(_decode_user_music(Path(settings.music_path),frames,cancelled),dtype=np.float32);music_id='USER_FILE'
    else:
        asset=user_assets.get(('music',music_id))
        if asset:source=np.asarray(_decode_user_music(asset['files'][0],frames,cancelled),dtype=np.float32)
    positions=np.arange(frames,dtype=np.float32)
    if music_id!='NONE':
        if source is None:
            source,hit=cached_wave('music',music_id,frames,0,lambda:procedural_bed('music',music_id,frames,0,cancelled),cancelled)
            cache_hits+=hit;cache_misses+=not hit
        gain=settings.music_volume if product else 10**(music_options.get('gain_db',-24)/20)*settings.music_volume
        duck=10**((settings.music_duck_db if product else music_options.get('duck_db',-9))/20)
        fi=max(1,round((.5 if product else music_options.get('fade_in_s',1))*SAMPLE_RATE));fo=max(1,round((1.5 if product else music_options.get('fade_out_s',3))*SAMPLE_RATE))
        envelope=np.clip(np.minimum(positions/fi,(frames-positions-1)/fo),0,1)
        music=source*gain*(1-activity(narration)*(1-duck))*envelope
    checkpoint('music_s',mark)
    mark=time.monotonic();amb_options=audio.get('ambience',{})
    amb_id=amb_options.get('bed_id',spec.style.get('ambience','NONE') if settings.ambience=='STYLE_DEFAULT' else settings.ambience)
    if product:amb_id='NONE'
    if amb_id!='NONE':
        asset=user_assets.get(('ambience',amb_id))
        if asset:source=np.asarray(_decode_user_music(asset['files'][0],frames,cancelled),dtype=np.float32)
        else:
            source,hit=cached_wave('ambience',amb_id,frames,spec.seed,lambda:procedural_bed('ambience',amb_id,frames,spec.seed,cancelled),cancelled)
            cache_hits+=hit;cache_misses+=not hit
        ambience=source*10**(amb_options.get('gain_db',-34)/20)*np.clip(np.minimum(positions/SAMPLE_RATE,(frames-positions-1)/(2*SAMPLE_RATE)),0,1)
    checkpoint('ambience_s',mark)
    mark=time.monotonic();mixed=narration+sfx+music+ambience
    raw_peak=float(np.max(np.abs(mixed))) if len(mixed) else 0
    headroom=min(1.,.98/max(1e-9,raw_peak))
    for stem in [narration,sfx,music,ambience]:stem*=headroom
    mixed*=headroom;mix_path=work/'pro-mix.wav';write_pcm(mix_path,mixed)
    checkpoint('mix_write_s',mark)
    mark=time.monotonic();table=[]
    # Verify the quantised final stem samples, not only source timing assumptions.
    final_sfx=(np.clip(sfx,-1,1)*32767).astype(np.int16).astype(np.float32)/32767
    for entry in cue_sources:
        cue=entry['cue'];start=entry['start'];count=entry['count']
        measured=feature_times(final_sfx[start:start+count]);expected=entry['features']['onset_ms']
        onset=measured['onset_ms'];offset=None if onset is None or expected is None else onset-expected
        overlap=any(other is not entry and other['start']<start+count and other['start']+other['count']>start for other in cue_sources)
        row={'scene_id':cue.scene_id,'cue_id':cue.id,'file':entry['file'],'clip_start_ms':cue.time_ms,'source_onset_ms':expected,'measured_stem_onset_ms':None if onset is None else cue.time_ms+onset,'placement_offset_ms':offset,'detector_resolution_ms':5,'measurement_stage':'quantised pre-master SFX stem; onset attribution is not separated from final AAC','overlapping_cue':overlap,'alignment_basis':'V1/V2 clip placement'}
        if cue.event_id:
            mf=measured.get(cue.feature+'_ms');sf=entry['features'].get(cue.feature+'_ms')
            row.update(event_id=cue.event_id,event_frame=cue.event_frame,event_time_ms=cue.event_time_ms,tag=cue.tag,feature=cue.feature,lead_ms=cue.lead_ms,trimmed_head_samples=entry['trimmed_head_samples'],source_feature_ms=sf,measured_feature_time_ms=None if mf is None else cue.time_ms+mf,alignment_basis='V3 event feature -> PCM sample',feature_offset_ms=None if mf is None else cue.time_ms+mf-entry['target_ms'])
        table.append(row)
    checkpoint('sfx_verify_s',mark)
    offsets=[abs(t['placement_offset_ms']) for t in table if t['placement_offset_ms'] is not None and not t['overlapping_cue']]
    stems={};mark=time.monotonic()
    if debug_stems:
        for name,data in [('narration',narration),('sfx',sfx),('music',music),('ambience',ambience)]:
            path=work/(name+'.wav');write_pcm(path,data);stems[name]=path
    checkpoint('stems_write_s',mark)
    timings['total_s']=round(time.monotonic()-started,4)
    metadata={'music_id':music_id,'ambience_id':amb_id,'density_requested':density,'density_actual':len(cues)/max(1,len(spec.scenes)-1),'mix_sample_peak':round(float(np.max(np.abs(mixed))),6),'raw_mix_sample_peak':round(raw_peak,6),'headroom_gain_db':round(20*math.log10(headroom),4),'sample_rate':SAMPLE_RATE,'pack_warnings':pack_warnings,'substage_timings':timings,'procedural_cache':{'hits':cache_hits,'misses':cache_misses,'limit_mb':128},'sfx_cue_table':table,'sfx_placement_verification':{'max_offset_ms':max(offsets,default=None),'mean_offset_ms':sum(offsets)/len(offsets) if offsets else None,'measured_cues':len(offsets),'event_bound':False},'procedural_limits':['PAGE_TURN and BRUSH_SCRATCH are stylised noise textures; replace with licensed user-pack recordings for realism.']}
    if spec.package.schema_version=='ATS_PACKAGE_V3':
        from .event_audio import choose_event_cues
        metadata['dropped_events']=choose_event_cues(spec,options)[1]
        metadata['sfx_placement_verification']['event_bound']=True
        metadata['sfx_cues_per_second']=len(cues)/spec.package.audio_duration
        metadata['sfx_feature_alignment_scope']='Quantised pre-master stem; overlapping clips are flagged, no isolated-feature certification on the final AAC mix.'
    return mix_path,tuple(effective),metadata,stems


def master_filter(options: dict, settings, before: dict) -> str | None:
    """Shared preview/export mastering; LIMIT_ONLY preserves relative dynamics."""
    mode=options.get("mode",settings.master_mode)
    target=float(options.get("target_lufs",-14))
    ceiling_db=float(options.get("true_peak_db",-1))
    if mode=="OFF":return None
    if mode=="LIMIT_ONLY":
        correction=target-before["integrated_lufs"] if before["integrated_lufs"] is not None else 0
        ceiling=10**((ceiling_db-.7)/20)
        return f"volume={correction:.3f}dB,alimiter=limit={ceiling:.6f}:level=false:attack=5:release=50"
    return f"loudnorm=I={target}:TP={ceiling_db-.7}:LRA=11"


def master_preview_audio(mix: Path, spec, settings, work: Path, cancelled=None) -> Path:
    from .pro_renderer import _measure_audio
    before=_measure_audio(mix,cancelled)
    options=spec.package.pro.get("audio",{}).get("master",{})
    audio_filter=master_filter(options,settings,before)
    if audio_filter is None:return mix
    encoded=work/"preview-master.m4a"
    base_filter=audio_filter;post_gain=0.;iterations=0
    mode=options.get("mode",settings.master_mode);target=float(options.get("target_lufs",-14));peak=float(options.get("true_peak_db",-1))
    while True:
        command=[str(bundled_binary("ffmpeg")),"-hide_banner","-loglevel","error","-nostdin","-i",str(mix),"-af",audio_filter,"-c:a","aac","-b:a","192k","-ac","2","-ar","48000","-y",str(encoded)]
        done=_run_decode(command,cancelled)
        if done.returncode:raise PackageError("Cannot prepare mastered preview audio.")
        after=_measure_audio(encoded,cancelled);iterations+=1
        if iterations>=3 or mode=="OFF" or not ((after["true_peak_dbtp"] is not None and after["true_peak_dbtp"]>peak+.05) or (after["integrated_lufs"] is not None and abs(after["integrated_lufs"]-target)>1)):break
        loud=(target-after["integrated_lufs"]) if after["integrated_lufs"] is not None else 0
        head=(peak-after["true_peak_dbtp"]-.3) if after["true_peak_dbtp"] is not None else 0
        post_gain+=min(loud,head) if loud>0 else loud
        audio_filter=f"{base_filter},volume={post_gain:.2f}dB"
    return encoded
