"""Frame-accurate Pro export through the shared Qt compositor and local FFmpeg."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import ctypes
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid

from . import __version__
from .media import bundled_binary, preflight_pro_media
from .pro_audio import build_audio_mix
from .pro_compositor import ProCompositor
from .pro_spec import build_spec
from .renderer import (RenderCancelled, RenderSettings, _cleanup_stale_work,
                       _concat_manifest, _probe_video, _working_set_bytes)
from .schema import Package, PackageError

_ACTIVE_ENCODERS: dict[int, subprocess.Popen] = {}
_ENCODER_LOCK = threading.Lock()

def _measure_audio(path: Path) -> dict:
    done=subprocess.run([str(bundled_binary("ffmpeg")),"-hide_banner","-nostdin","-i",str(path),
        "-vn","-af","ebur128=peak=true","-f","null","NUL"],capture_output=True,text=True,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),timeout=120)
    text=done.stderr.rsplit("Summary:",1)[-1]
    def pick(pattern: str) -> float | None:
        found=re.search(pattern,text)
        return float(found.group(1)) if found else None
    return {"integrated_lufs":pick(r"\bI:\s*([-\d.]+)\s*LUFS"),
            "lra_lu":pick(r"\bLRA:\s*([-\d.]+)\s*LU"),
            "true_peak_dbtp":pick(r"True peak:\s*\n\s*Peak:\s*([-\d.]+)\s*dBFS")}


@lru_cache(maxsize=1)
def _hardware_encoder() -> str | None:
    for name in ("h264_amf","h264_nvenc","h264_qsv"):
        command=[str(bundled_binary("ffmpeg")),"-hide_banner","-loglevel","error",
                 "-f","lavfi","-i","color=c=black:s=240x426:r=30:d=0.2",
                 "-frames:v","3","-c:v",name,"-f","null","NUL"]
        try:
            done=subprocess.run(command,capture_output=True,timeout=15,
                                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if done.returncode==0:return name
        except (OSError,subprocess.TimeoutExpired):
            continue
    return None


def _encode_chunk(index: int, start: int, end: int, spec, images, settings: RenderSettings,
                  work: Path, cancel: threading.Event, on_frames, cache_limit: int,
                  encoder: str) -> tuple[Path,float,int,str]:
    target=work/f"chunk-{index:04d}.mp4"
    preset={"DRAFT":"ultrafast","STANDARD":"veryfast","MAX":"medium"}[settings.quality_tier]
    crf={"DRAFT":21,"STANDARD":18,"MAX":17}[settings.quality_tier]
    hardware=encoder!="libx264"
    pixel="nv12" if hardware else "yuv420p"
    render_w=(settings.width//2)//2*2 if settings.quality_tier=="DRAFT" else settings.width
    render_h=(settings.height//2)//2*2 if settings.quality_tier=="DRAFT" else settings.height
    scaler=(f"scale={settings.width}:{settings.height}:flags=fast_bilinear:" if
            settings.quality_tier=="DRAFT" else "scale=")
    if settings.quality_tier=="DRAFT":
        video_filter=scaler+f"in_range=pc:out_range=tv:out_color_matrix=bt709,format={pixel}"
    else:
        video_filter=f"scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format={pixel}"
    command=[str(bundled_binary("ffmpeg")),"-hide_banner","-loglevel","error","-nostdin",
             "-f","rawvideo","-pixel_format","rgb24","-video_size",f"{render_w}x{render_h}",
             "-framerate",str(spec.package.fps),"-i","pipe:0","-an",
             "-vf",video_filter,
             "-c:v",encoder]
    if hardware:
        if encoder=="h264_amf":command.extend(["-quality","balanced"])
    else:
        command.extend(["-x264-params","colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off",
                        "-preset",preset,"-crf",str(crf),"-threads",
                        str(max(1,os.cpu_count()//max(1,settings.workers)))])
    command += ["-g",str(spec.package.fps*2),
             "-pix_fmt",pixel,"-colorspace","bt709","-color_primaries","bt709",
             "-color_trc","bt709","-color_range","tv","-r",str(spec.package.fps),
             "-frames:v",str(end-start),"-y",str(target)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    with _ENCODER_LOCK:
        _ACTIVE_ENCODERS[id(process)] = process
    errors=[]
    def drain() -> None:
        if process.stderr:
            errors.append(process.stderr.read()[-3000:].decode(errors="replace"))
    reader=threading.Thread(target=drain,daemon=True);reader.start()
    started=time.monotonic()
    peak=0
    try:
        compositor=ProCompositor(spec,images,settings,width=render_w,height=render_h,
                                 cache_limit_bytes=cache_limit)
        assert process.stdin
        for frame in range(start,end):
            if cancel.is_set():
                raise RenderCancelled()
            image=compositor.render_frame(frame)
            if image.bytesPerLine()!=render_w*3:
                raise PackageError("Raw frame row stride is not RGB24-packed.")
            process.stdin.write(image.constBits())
            if (frame-start)%10==0 or frame==end-1:
                on_frames(index,frame-start+1,end-start)
                if target.exists() and target.stat().st_size>settings.max_cache_gb*1024**3:
                    raise PackageError("Pro chunk exceeded the selected cache limit.")
                if shutil.disk_usage(work).free<64*1024**2:
                    raise PackageError("Export stopped: less than 64 MB of free disk space remains.")
                if os.name=="nt":
                    with _ENCODER_LOCK:
                        child_ram=sum(_working_set_bytes(int(p._handle)) for p in _ACTIVE_ENCODERS.values()
                                      if p.poll() is None)
                    peak=max(peak,child_ram+
                             _working_set_bytes(int(ctypes.windll.kernel32.GetCurrentProcess())))
        process.stdin.close()
        code=process.wait(timeout=180)
        reader.join(timeout=3)
        if code:
            raise PackageError(f"Pro chunk {index} encoder failed: {''.join(errors)[-2000:]}")
        if not target.exists() or not target.stat().st_size:
            raise PackageError(f"Pro chunk {index} produced no video.")
        return target,time.monotonic()-started,peak,encoder
    except Exception:
        if process.poll() is None:
            process.kill()
        raise
    finally:
        with _ENCODER_LOCK:
            _ACTIVE_ENCODERS.pop(id(process),None)
        if process.stdin and not process.stdin.closed:process.stdin.close()
        if process.stderr:process.stderr.close()


def _mux(chunks: list[Path], audio: Path, output: Path, package: Package,
         filter_audio: str | None, cancel: threading.Event) -> None:
    manifest=output.parent/"chunks.ffconcat"
    _concat_manifest(manifest,chunks)
    command=[str(bundled_binary("ffmpeg")),"-hide_banner","-loglevel","error","-nostdin",
             "-f","concat","-safe","0","-i",str(manifest),"-i",str(audio),
             "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
             "-ar","48000","-ac","2"]
    command.extend(["-bsf:v","h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0"])
    if filter_audio:command.extend(["-af",filter_audio])
    command.extend(["-t",f"{package.total_frames/package.fps:.6f}","-movflags","+faststart","-y",str(output)])
    command[-2:-2] = ["-colorspace","bt709","-color_primaries","bt709",
                       "-color_trc","bt709","-color_range","tv"]
    process=subprocess.Popen(command,cwd=output.parent,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    while process.poll() is None:
        if cancel.is_set():
            process.kill();raise RenderCancelled()
        time.sleep(.1)
    message=process.stderr.read().decode(errors="replace") if process.stderr else ""
    if process.stderr:process.stderr.close()
    if process.returncode:
        raise PackageError(f"Pro audio mux failed: {message[-2000:]}")


def export_pro_video(package: Package, images: dict[str, Path], audio_path: Path,
                     output_path: Path, settings: RenderSettings,
                     cancel: threading.Event, progress) -> dict:
    if output_path.exists():raise PackageError(f"Output already exists: {output_path}")
    if settings.quality_tier not in {"DRAFT","STANDARD","MAX"}:
        raise PackageError("Unknown Pro quality tier.")
    if settings.width%2 or settings.height%2 or min(settings.width,settings.height)<240:
        raise PackageError("Output dimensions must be even and at least 240 pixels.")
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.instance() is None:
        ProCompositor._app = QGuiApplication([])
    if not 1<=settings.workers<=8:raise PackageError("Workers must be between 1 and 8.")
    output_path.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output_path.parent).free<256*1024**2:
        raise PackageError("Less than 256 MB of free space is available for export.")
    spec=build_spec(package,images,settings)
    preflight_warnings=preflight_pro_media(package,images,settings.width,
                                          settings.height,settings.framing)
    log_path=output_path.with_name(output_path.name+".log")
    report_path=output_path.with_name(output_path.name+".report.json")
    log_path.write_text(f"ATS {__version__} Pro export\nOutput: {output_path}\n"
        f"Settings: {json.dumps(asdict(settings),ensure_ascii=False,sort_keys=True)}\n",encoding="utf-8")
    last_log=[0.0,""]
    def announce(stage: str,percent: float,detail: str) -> None:
        progress(stage,percent,detail)
        now=time.monotonic()
        if stage!=last_log[1] or now-last_log[0]>=5:
            with log_path.open("a",encoding="utf-8") as handle:
                handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {percent:.2f}% {stage}: {detail}\n")
            last_log[:]=[now,stage]
    _cleanup_stale_work(output_path.parent)
    token=uuid.uuid4().hex[:10]
    work=output_path.parent/f".{output_path.stem}.ats-work-{token}"
    work.mkdir()
    (work/".ats-temporary-session.json").write_text(json.dumps({"ats_temp":1,"created":time.time()}),encoding="utf-8")
    partial=work/"final.mp4"
    started=time.monotonic();peak_ram=0;peak_cache=0
    times={"chunks_s":[]}
    try:
        groups=[]
        for i in range(0,len(spec.scenes),settings.chunk_scenes):
            part=spec.scenes[i:i+settings.chunk_scenes]
            groups.append((part[0].first_frame,part[-1].end_frame))
        completed=[0]*len(groups);lock=threading.Lock()
        cache_per_worker=max(128*1024**2,1536*1024**2//settings.workers)
        def on_frames(index: int,done: int,total: int) -> None:
            nonlocal peak_cache
            with lock:
                completed[index-1]=done
                complete=sum(completed)
                if complete==package.total_frames or complete%25<10:
                    announce("Rendering video",complete/package.total_frames*90,
                             f"{complete:,}/{package.total_frames:,} frames · {len(groups)} chunks")
                cache=sum(p.stat().st_size for p in work.glob("chunk-*.mp4"))
                peak_cache=max(peak_cache,cache)
                if cache>settings.max_cache_gb*1024**3:
                    cancel.set();raise PackageError("Pro cache exceeded the selected limit.")
        chunks=[None]*len(groups)
        requested_encoder=settings.encoder
        encoder_choice=(_hardware_encoder() or "libx264") if requested_encoder=="Auto" else "libx264"
        encoder_used=set()
        encoder_warnings=[]
        if requested_encoder=="Auto" and encoder_choice=="libx264":
            encoder_warnings.append("Hardware encoder probe failed; CPU x264 was selected.")
        announce("Rendering video",0,f"{len(groups)} chunks; {settings.workers} worker(s)")
        with ThreadPoolExecutor(max_workers=min(settings.workers,len(groups))) as executor:
            futures={executor.submit(_encode_chunk,i,start,end,spec,images,settings,work,cancel,on_frames,cache_per_worker,encoder_choice):i
                     for i,(start,end) in enumerate(groups,1)}
            for future in as_completed(futures):
                i=futures[future]
                try:
                    path,elapsed,ram,used=future.result()
                except PackageError:
                    if encoder_choice=="libx264":raise
                    start,end=groups[i-1]
                    target=work/f"chunk-{i:04d}.mp4"
                    if target.exists():target.unlink()
                    encoder_warnings.append(f"Chunk {i}: {encoder_choice} failed; retried with CPU x264.")
                    path,elapsed,ram,used=_encode_chunk(i,start,end,spec,images,settings,work,cancel,
                                                          on_frames,cache_per_worker,"libx264")
                encoder_used.add(used)
                chunks[i-1]=path;times["chunks_s"].append({"chunk":i,"seconds":round(elapsed,3)})
                peak_ram=max(peak_ram,ram)
        if cancel.is_set():raise RenderCancelled()
        audio_started=time.monotonic()
        announce("Mixing audio",91,"Building procedural cues, beds and narration mix")
        mix,cues,audio_meta,stems=build_audio_mix(spec,audio_path,settings,work,settings.debug_stems)
        times["audio_mix_s"]=round(time.monotonic()-audio_started,3)
        before=_measure_audio(mix)
        audio_options=package.pro.get("audio",{}).get("master",{})
        mode=audio_options.get("mode",settings.master_mode)
        target=float(audio_options.get("target_lufs",-14))
        peak_limit=float(audio_options.get("true_peak_db",-1))
        base_filter=None if mode=="OFF" else f"loudnorm=I={target}:TP={peak_limit-0.7}:LRA=11"
        filter_audio=base_filter
        mux_started=time.monotonic()
        announce("Finalizing MP4",96,"Muxing video and measured audio")
        _mux(chunks,mix,partial,package,filter_audio,cancel)
        after=_measure_audio(partial)
        iterations=1
        post_gain=0.0
        while mode!="OFF" and iterations<3 and (
            after["true_peak_dbtp"] is not None and after["true_peak_dbtp"]>peak_limit+.05 or
            after["integrated_lufs"] is not None and abs(after["integrated_lufs"]-target)>1):
            if cancel.is_set():raise RenderCancelled()
            loudness_correction=(target-after["integrated_lufs"]) if after["integrated_lufs"] is not None else 0
            headroom=(peak_limit-after["true_peak_dbtp"]-.3) if after["true_peak_dbtp"] is not None else 0
            correction=min(loudness_correction,headroom) if loudness_correction>0 else loudness_correction
            post_gain+=correction
            filter_audio=f"{base_filter},volume={post_gain:.2f}dB"
            _mux(chunks,mix,partial,package,filter_audio,cancel)
            after=_measure_audio(partial);iterations+=1
        times["mux_master_s"]=round(time.monotonic()-mux_started,3)
        announce("Verifying",99,"Checking encoded frame count and colour tags")
        verify_started=time.monotonic()
        facts=_probe_video(partial,package,settings)
        times["verify_s"]=round(time.monotonic()-verify_started,3)
        if after["true_peak_dbtp"] is not None and after["true_peak_dbtp"]>peak_limit+.1 and mode!="OFF":
            raise PackageError(f"Final AAC true peak {after['true_peak_dbtp']} dBTP exceeds {peak_limit} dBTP.")
        video=next(s for s in facts["streams"] if s["codec_type"]=="video")
        audio=next(s for s in facts["streams"] if s["codec_type"]=="audio")
        if (video.get("color_space")!="bt709" or video.get("color_range")!="tv" or
            video.get("color_primaries")!="bt709" or video.get("color_transfer")!="bt709"):
            raise PackageError("Final video lacks BT.709 limited-range tags.")
        os.replace(partial,output_path)
        if stems:
            for name,path in stems.items():
                shutil.copy2(path,output_path.with_name(output_path.stem+f".{name}.wav"))
        report={
            "tool_version":__version__,"render_backend":"Pro Qt CPU compositor",
            "package_sha256":hashlib.sha256(package.source_json.encode()).hexdigest(),
            "seed":spec.seed,"settings":asdict(settings),"quality_tier":settings.quality_tier,
            "encoder":" + ".join(sorted(encoder_used)),"encoder_requested":requested_encoder,
            "stage_timings":times,"peak_ram_mb":round(peak_ram/1024**2,1),
            "peak_cache_gb":peak_cache/1024**3,
            "scenes":[{"id":s.id,"motion":s.motion,"motion_params":s.motion_config,
                       "ease":s.motion_config.get("ease"),"focus_source":s.focus_source,
                       "focus":{"x":s.focus_x,"y":s.focus_y},
                       "transition_requested":s.transition_requested,
                       "transition_applied":s.transition_applied,"transition_frames":s.transition_frames,
                       "look":s.look,"look_intensity":s.look_intensity,
                       "sfx_cues":[asdict(c) for c in cues if c.scene_id==s.id],
                       "overlays":[o.get("id") for o in spec.overlays]} for s in spec.scenes],
            "captions":{"requested":package.captions_enabled,"active":package.captions_enabled and settings.caption_preset!="Off",
                        "package_intervals":len(package.captions),"chunks_rendered":len(spec.captions),
                        "pixel_verified":False},
            "audio_stats":{"before_aac":before,"after_aac":after,"master_iterations":iterations,**audio_meta},
            "auto_direct":{"enabled":spec.auto_direct,"strict_json":spec.strict_json,"changes":spec.changes},
            "visual_director":spec.changes.get('visual_director',{}),
            "warnings":preflight_warnings+list(spec.warnings)+encoder_warnings,
            "final_file":{"path":str(output_path),"bytes":output_path.stat().st_size,
                          "duration_s":float(facts["format"]["duration"]),"width":video["width"],
                          "height":video["height"],"fps":video.get("r_frame_rate"),
                          "frames":int(video["nb_frames"]),"color_range":video.get("color_range"),
                          "color_space":video.get("color_space"),"color_primaries":video.get("color_primaries"),
                          "color_transfer":video.get("color_transfer"),
                          "audio_codec":audio.get("codec_name"),"sample_rate":audio.get("sample_rate")},
        }
        from .capabilities import current_capabilities
        report["capabilities"]=current_capabilities()
        times["total_s"]=round(time.monotonic()-started,3)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        announce("Complete",100,f"Saved {output_path.name}")
        return {"elapsed_seconds":time.monotonic()-started,"peak_cache_gb":peak_cache/1024**3,
                "output_gb":output_path.stat().st_size/1024**3,"report_path":str(report_path),
                "log_path":str(log_path)}
    except Exception as exc:
        with log_path.open("a",encoding="utf-8") as handle:
            handle.write(f"FAILED: {type(exc).__name__}: {exc}\n")
        raise
    finally:
        shutil.rmtree(work,ignore_errors=True)
