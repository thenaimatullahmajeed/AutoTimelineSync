"""Native-size Pro frames, balanced workers and one audio encode before muxing.

The installed compositor/spec/mixer remain the authority for rendered content.
This module replaces export orchestration, not the schema or effect definitions.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
import hashlib, json, math, os, queue, re, shutil, subprocess, threading, time, uuid
from .media import bundled_binary, preflight_pro_media
from .renderer import RenderCancelled, _probe_video
from .schema import PackageError
from .pro_spec import build_spec
from .pro_audio import build_audio_mix
from .pro_compositor import ProCompositor

FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)

class Stop:
    def __init__(self,external):self.external=external;self.local=threading.Event()
    def is_set(self):return self.external.is_set() or self.local.is_set()
    def set(self):self.local.set()

def run_process(command,cancel,progress=None,duration=1.,timeout=180):
    """Drain both pipes continuously; no stderr pipe deadlock at finalization."""
    process=subprocess.Popen([str(x) for x in command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,creationflags=FLAGS)
    lines=queue.Queue();errors=[];start=time.monotonic();last_output=start
    def read_output():
        for line in iter(process.stdout.readline,b''):lines.put(line.decode('utf8','replace').strip())
    def read_error():
        for line in iter(process.stderr.readline,b''):
            errors.append(line.decode('utf8','replace'))
            if len(errors)>300:del errors[:100]
    a=threading.Thread(target=read_output,daemon=True);b=threading.Thread(target=read_error,daemon=True);a.start();b.start()
    try:
        while process.poll() is None or not lines.empty():
            if cancel.is_set():process.kill();raise RenderCancelled()
            try:
                line=lines.get(timeout=.1);last_output=time.monotonic()
                if progress and line.startswith('out_time_us='):
                    try:progress(min(1.,max(0.,int(line.split('=',1)[1])/1e6/max(.001,duration))))
                    except ValueError:pass
            except queue.Empty:pass
            if time.monotonic()-start>timeout:
                process.kill();raise PackageError('Audio/mux process timed out; no final output was published.')
        a.join(2);b.join(2);message=''.join(errors)
        if process.returncode:raise PackageError('FFmpeg failed: '+message[-2400:])
        return message
    finally:
        if process.poll() is None:process.kill()
        process.wait();a.join(2);b.join(2)
        process.stdout.close();process.stderr.close()

def measure(path,cancel):
    text=run_process([bundled_binary('ffmpeg'),'-hide_banner','-nostdin','-i',path,'-vn',
        '-af','ebur128=peak=true','-f','null','NUL'],cancel,timeout=180)
    summary=text.rsplit('Summary:',1)[-1]
    def number(pattern):
        match=re.search(pattern,summary)
        if not match:return None
        value=float(match.group(1));return value if math.isfinite(value) else None
    return dict(integrated_lufs=number(r'\bI:\s*([-\d.]+)\s*LUFS'),
        lra_lu=number(r'\bLRA:\s*([-\d.]+)\s*LU'),
        true_peak_dbtp=number(r'True peak:\s*\n\s*Peak:\s*([-\d.]+)\s*dBFS'))

def audio_encode(mix,output,spec,settings,cancel,announce):
    options=spec.package.pro.get('audio',{}).get('master',{})
    mode=options.get('mode',settings.master_mode);target=float(options.get('target_lufs',-14));ceiling=float(options.get('true_peak_db',-1))
    announce('Checking audio',3,'Measuring the narration/music mix')
    before=measure(mix,cancel);silent=(before['integrated_lufs'] is None or before['integrated_lufs']<=-69)
    notices=[]
    if silent:
        notices.append('Audio mix is silent. Check Sound > Voice/Music if silence was not intended.')
        if mode=='LOUDNORM':raise PackageError('LOUDNORM cannot normalize silence. Sound > Voice is muted or the input has no audible audio. Restore Voice above 0% and retry.')
    base=None
    if mode=='LOUDNORM':
        announce('Preparing loudness',4,'Measuring normalization parameters before rendering video')
        text=run_process([bundled_binary('ffmpeg'),'-hide_banner','-nostdin','-i',mix,'-vn','-af',
            f'loudnorm=I={target}:TP={ceiling-.7}:LRA=11:print_format=json','-f','null','NUL'],cancel)
        objects=re.findall(r'\{[^{}]*"input_i"[^{}]*\}',text,re.S)
        if not objects:raise PackageError('Loudness analysis returned no parameters.')
        stats=json.loads(objects[-1])
        base=(f'loudnorm=I={target}:TP={ceiling-.7}:LRA=11:linear=true:'
            f'measured_I={stats["input_i"]}:measured_TP={stats["input_tp"]}:'
            f'measured_LRA={stats["input_lra"]}:measured_thresh={stats["input_thresh"]}:offset={stats["target_offset"]}')
    elif mode=='LIMIT_ONLY':
        # Peak limiting must not impose a target LUFS or amplify intentionally quiet audio.
        base=f'alimiter=limit={10**((ceiling-.7)/20):.8f}:level=false'
    elif mode!='OFF':raise PackageError('Unsupported mastering mode: '+str(mode))
    gain=0.;after=None
    for attempt in range(1,4):
        announce('Encoding audio',5,'Encoding AAC once before video; peak correction uses audio only')
        command=[bundled_binary('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-i',mix,'-vn']
        filt=base
        if gain:filt=(filt+',' if filt else '')+f'volume={gain:.4f}dB'
        if filt:command+=['-af',filt]
        command+=['-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-progress','pipe:1','-stats_period','0.25','-y',output]
        run_process(command,cancel,lambda fraction:announce('Encoding audio',5+fraction*3,'AAC audio'),spec.package.total_frames/spec.package.fps)
        after=measure(output,cancel)
        peak=after['true_peak_dbtp'];lufs=after['integrated_lufs']
        peak_bad=mode!='OFF' and peak is not None and peak>ceiling+.1
        loudness_bad=mode=='LOUDNORM' and lufs is not None and abs(lufs-target)>1.
        if not peak_bad and not loudness_bad:break
        if attempt==3:raise PackageError(f'Audio mastering verification failed before video rendering: {lufs} LUFS, {peak} dBTP.')
        correction=(target-lufs) if loudness_bad else 0.
        headroom=(ceiling-peak-.3) if peak is not None else 0.
        gain+=min(correction,headroom) if correction>0 else min(correction,headroom)
    return before,after,attempt,notices

def encode_chunk(index,start,end,spec,images,settings,work,cancel,on_frames,cache_limit,encoder):
    target=work/f'chunk-{index:04d}.mp4';hardware=encoder!='libx264'
    width,height=settings.width,settings.height
    command=[bundled_binary('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin',
        '-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate',str(spec.package.fps),'-i','pipe:0','-an',
        '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p','-c:v',encoder]
    fast=settings.quality_tier!='MAX'
    if hardware:
        if encoder=='h264_amf':command+=['-quality','speed' if fast else 'quality']
        elif encoder=='h264_nvenc':command+=['-preset','p1' if fast else 'p5','-cq','20' if fast else '17']
        elif encoder=='h264_qsv':command+=['-preset','veryfast' if fast else 'medium','-global_quality','20' if fast else '17']
    else:
        command+=['-preset','ultrafast' if fast else 'medium','-crf','20' if fast else '17',
            '-threads',str(max(1,(os.cpu_count() or 2)//max(1,settings.workers))),
            '-x264-params','colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off']
    command+=['-g',str(spec.package.fps*2),'-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709',
        '-color_trc','bt709','-color_range','tv','-frames:v',str(end-start),'-progress','pipe:1','-stats_period','0.25','-y',target]
    process=subprocess.Popen([str(x) for x in command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=FLAGS)
    errors=[];thread_errors=[];started=time.monotonic();last_activity=[started];finished=threading.Event();timed_out=threading.Event()
    def output():
        for line in iter(process.stdout.readline,b''):
            last_activity[0]=time.monotonic()
            if line.startswith(b'frame='):
                try:on_frames(index,min(end-start,int(line.split(b'=',1)[1])),end-start)
                except ValueError:pass
                except Exception as exc:thread_errors.append(exc);process.kill();return
    def error():
        for line in iter(process.stderr.readline,b''):
            errors.append(line.decode('utf8','replace'))
            if len(errors)>100:del errors[:50]
    def watchdog():
        while not finished.wait(.1):
            if cancel.is_set():process.kill();return
            if time.monotonic()-last_activity[0]>60:
                timed_out.set();process.kill();return
    threads=[threading.Thread(target=f,daemon=True) for f in (output,error,watchdog)]
    for thread in threads:thread.start()
    try:
        compositor=ProCompositor(spec,images,settings,width=width,height=height,cache_limit_bytes=cache_limit)
        for frame in range(start,end):
            if cancel.is_set():raise RenderCancelled()
            image=compositor.render_frame(frame)
            if image.bytesPerLine()!=width*3:raise PackageError('Raw frame row stride is not RGB24-packed.')
            process.stdin.write(image.constBits());last_activity[0]=time.monotonic()
        process.stdin.close();process.wait(timeout=60)
        for thread in threads[:2]:thread.join(3)
        if cancel.is_set():raise RenderCancelled()
        if thread_errors:raise thread_errors[0]
        if timed_out.is_set():raise PackageError('Encoder stalled for 60 seconds; stopped without publishing an incomplete MP4.')
        if process.returncode:raise PackageError(f'Encoder {encoder} failed: '+''.join(errors)[-2000:])
        on_frames(index,end-start,end-start)
        return target,time.monotonic()-started
    except BrokenPipeError as exc:
        if cancel.is_set():raise RenderCancelled() from exc
        raise PackageError(f'Encoder {encoder} closed its input: '+''.join(errors)[-2000:]) from exc
    finally:
        finished.set()
        if process.poll() is None:process.kill()
        process.wait()
        for thread in threads:thread.join(3)
        for pipe in (process.stdin,process.stdout,process.stderr):
            if pipe and not pipe.closed:pipe.close()

def export_pro_video(package,images,audio_path,output_path,settings,cancel,progress):
    from . import __version__
    from .hardware import machine_resources
    from .fonts import register_bundled_fonts
    from . import pro_renderer as baseline
    output_path=Path(output_path)
    if output_path.exists():raise PackageError(f'Output already exists: {output_path}')
    if settings.width%4 or settings.height%2 or min(settings.width,settings.height)<240:raise PackageError('Unsupported output dimensions.')
    output_path.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output_path.parent).free<256*1024**2:raise PackageError('Less than 256 MB of free space is available for export.')
    register_bundled_fonts();spec=build_spec(package,images,settings)
    warnings=preflight_pro_media(package,images,settings.width,settings.height,settings.framing)
    started=time.monotonic();log_path=output_path.with_name(output_path.name+'.log');report_path=output_path.with_name(output_path.name+'.report.json')
    log_path.write_text(f'ATS {__version__} Pro export\nOutput: {output_path}\nSettings: '+json.dumps(asdict(settings),ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
    last=[0.,'',0.];message_lock=threading.Lock()
    def announce(stage,percent,detail):
        with message_lock:
            percent=max(last[2],min(100.,percent));progress(stage,percent,detail)
            now=time.monotonic()
            if stage!=last[1] or now-last[0]>=5:
                with log_path.open('a',encoding='utf8') as log:log.write(f'{time.strftime("%Y-%m-%dT%H:%M:%S")} {percent:.2f}% {stage}: {detail}\n')
                last[:]=[now,stage,percent]
            else:last[2]=percent
    work=output_path.parent/f'.{output_path.stem}.ats-work-{uuid.uuid4().hex[:10]}';work.mkdir()
    (work/'.ats-temporary-session.json').write_text(json.dumps(dict(ats_temp=1,created=time.time())))
    times={};peak_cache=0;master_iterations=0;caption_samples=[]
    try:
        announce('Preparing audio',0,'Checking the mix before rendering video')
        caption_active=package.captions_enabled and settings.caption_preset!='Off'
        if caption_active and package.captions:
            ratio=settings.width/settings.height
            sample_height=360;sample_width=max(4,int(sample_height*ratio)//4*4)
            checker=ProCompositor(spec,images,settings,width=sample_width,height=sample_height,cache_limit_bytes=64*1024**2)
            from .schema import frame_at
            for caption in (package.captions[0],package.captions[len(package.captions)//2],package.captions[-1]):
                frame=min(package.total_frames-1,frame_at((caption.start+caption.end)/2,package.fps))
                if frame in caption_samples:continue
                checker.captions_visible=False;a=checker.render_frame(frame)
                checker.captions_visible=True;b=checker.render_frame(frame)
                if a==b:raise PackageError(f'Caption pixel check failed at frame {frame}.')
                caption_samples.append(frame)
        stage=time.monotonic()
        mix,cues,audio_meta,stems=build_audio_mix(spec,Path(audio_path),settings,work,settings.debug_stems,cancelled=cancel.is_set)
        audio_file=work/'mastered.m4a'
        before,after,master_iterations,audio_warnings=audio_encode(mix,audio_file,spec,settings,cancel,announce)
        warnings+=audio_warnings;times['audio_s']=round(time.monotonic()-stage,3)
        if cancel.is_set():raise RenderCancelled()
        announce('Checking encoder',9,'Checking local hardware support; CPU fallback is automatic')
        encoder=(baseline._hardware_encoder() or 'libx264') if settings.encoder=='Auto' else 'libx264'
        if settings.encoder=='Auto' and encoder=='libx264':warnings.append('Hardware encoding unavailable; using CPU x264.')
        workers=max(1,min(settings.workers,machine_resources()['physical_cores'],max(1,package.total_frames//max(1,package.fps))))
        groups_count=min(workers*2,max(workers,math.ceil(package.total_frames/max(1,package.fps*6))))
        groups=[(i*package.total_frames//groups_count,(i+1)*package.total_frames//groups_count) for i in range(groups_count)]
        cache_per_worker=max(64*1024**2,min(256*1024**2,machine_resources()['available_ram_bytes']//max(4,workers*4)))
        counts=[0]*len(groups);count_lock=threading.Lock();render_started=time.monotonic()
        def frames(index,n,total):
            nonlocal peak_cache
            with count_lock:
                counts[index-1]=max(counts[index-1],n);complete=sum(counts);elapsed=max(.001,time.monotonic()-render_started)
                announce('Rendering video',10+complete/package.total_frames*80,
                    f'{complete:,}/{package.total_frames:,} encoded frames · {complete/elapsed:.1f} fps · {encoder}')
                size=sum(p.stat().st_size for p in work.iterdir() if p.is_file());peak_cache=max(peak_cache,size)
                if size>settings.max_cache_gb*1024**3:raise PackageError('Export cache limit exceeded.')
        def video_attempt(chosen):
            token=Stop(cancel);chunks=[None]*len(groups);timings=[]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                jobs={pool.submit(encode_chunk,i,a,b,spec,images,settings,work,token,frames,cache_per_worker,chosen):i
                    for i,(a,b) in enumerate(groups,1)}
                try:
                    for future in as_completed(jobs):
                        index=jobs[future];path,elapsed=future.result();chunks[index-1]=path;timings.append(dict(chunk=index,seconds=round(elapsed,3)))
                except Exception:token.set();raise
            return chunks,timings
        try:chunks,chunk_times=video_attempt(encoder)
        except PackageError:
            if encoder=='libx264' or cancel.is_set():raise
            warnings.append(f'{encoder} failed; all chunks were retried with CPU x264.')
            encoder='libx264';announce('Retrying encoder',last[2],'Retrying complete video with CPU x264')
            for path in work.glob('chunk-*.mp4'):path.unlink()
            chunks,chunk_times=video_attempt(encoder)
        times['video_s']=round(time.monotonic()-render_started,3);times['chunks_s']=chunk_times
        if cancel.is_set():raise RenderCancelled()
        manifest=work/'chunks.ffconcat';baseline._concat_manifest(manifest,chunks);partial=work/'final.mp4'
        stage=time.monotonic();announce('Finalizing MP4',91,'Copying encoded video and AAC; no repeated audio encoding')
        def mux_progress(fraction):
            nonlocal peak_cache
            size=sum(p.stat().st_size for p in work.iterdir() if p.is_file());peak_cache=max(peak_cache,size)
            if size>settings.max_cache_gb*1024**3:raise PackageError('Export cache limit exceeded while writing the final MP4.')
            announce('Finalizing MP4',91+fraction*6,'Writing final MP4')
        run_process([bundled_binary('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-f','concat','-safe','0','-i',manifest,
            '-i',audio_file,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-t',f'{package.total_frames/package.fps:.8f}',
            '-movflags','+faststart','-progress','pipe:1','-stats_period','0.25','-y',partial],cancel,
            mux_progress,package.total_frames/package.fps)
        times['mux_s']=round(time.monotonic()-stage,3);announce('Verifying MP4',98,'Checking frame count, dimensions and tracks')
        facts=_probe_video(partial,package,settings);video=next(s for s in facts['streams'] if s['codec_type']=='video');audio=next(s for s in facts['streams'] if s['codec_type']=='audio')
        if cancel.is_set():raise RenderCancelled()
        os.replace(partial,output_path)
        if stems:
            for name,path in stems.items():shutil.copy2(path,output_path.with_name(output_path.stem+f'.{name}.wav'))
        times['total_s']=round(time.monotonic()-started,3)
        report=dict(tool_version=__version__,render_backend='Pro Qt CPU compositor',
            package_sha256=hashlib.sha256(package.source_json.encode()).hexdigest(),settings=asdict(settings),encoder=encoder,
            encoder_requested=settings.encoder,workers_actual=workers,stage_timings=times,peak_cache_gb=peak_cache/1024**3,
            audio_stats=dict(before_aac=before,after_aac=after,master_iterations=master_iterations,**audio_meta),
            warnings=warnings+list(spec.warnings),seed=spec.seed,
            quality_tier=settings.quality_tier,
            scenes=[dict(id=s.id,motion=s.motion,motion_params=s.motion_config,ease=s.motion_config.get('ease'),
                focus_source=s.focus_source,focus=dict(x=s.focus_x,y=s.focus_y),transition_requested=s.transition_requested,
                transition_applied=s.transition_applied,transition_frames=s.transition_frames,look=s.look,look_intensity=s.look_intensity,
                sfx_cues=[asdict(c) for c in cues if c.scene_id==s.id],overlays=[o.get('id') for o in spec.overlays]) for s in spec.scenes],
            captions=dict(requested=package.captions_enabled,active=caption_active,package_intervals=len(package.captions),
                chunks_rendered=len(spec.captions),pixel_verified=bool(caption_samples),pixel_sample_frames=caption_samples,
                verification_scope='Uncompressed shared-compositor caption samples; output compression is not pixel-identical.',chunks=[asdict(c) for c in spec.captions]),
            auto_direct=dict(enabled=spec.auto_direct,strict_json=spec.strict_json,changes=spec.changes),
            visual_director=spec.changes.get('visual_director',{}),
            final_file=dict(path=str(output_path),bytes=output_path.stat().st_size,duration_s=float(facts['format']['duration']),
                width=video['width'],height=video['height'],fps=video['r_frame_rate'],frames=int(video['nb_frames']),audio_codec=audio['codec_name'],sample_rate=audio.get('sample_rate')))
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        announce('Complete',100,f'Saved {output_path.name}')
        return dict(elapsed_seconds=time.monotonic()-started,peak_cache_gb=peak_cache/1024**3,output_gb=output_path.stat().st_size/1024**3,report_path=str(report_path),log_path=str(log_path))
    except Exception as exc:
        with log_path.open('a',encoding='utf8') as log:log.write(f'FAILED: {type(exc).__name__}: {exc}\n')
        raise
    finally:
        if work.parent.resolve()!=output_path.parent.resolve() or not work.name.startswith('.'+output_path.stem+'.ats-work-'):
            raise RuntimeError('Unexpected export cleanup path')
        shutil.rmtree(work,ignore_errors=True)

def master_preview_audio(mix,spec,settings,work,cancelled=None):
    """Preview shares the same AAC mastering path, including silent LIMIT_ONLY."""
    class Token:
        def is_set(self):return bool(cancelled and cancelled())
    token=Token();audio=Path(work)/'preview-mastered.m4a';target=Path(work)/'preview-mastered.wav'
    audio_encode(Path(mix),audio,spec,settings,token,lambda *args:None)
    run_process([bundled_binary('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-i',audio,
        '-vn','-c:a','pcm_s16le','-ar','48000','-ac','2','-t',f'{spec.package.total_frames/spec.package.fps:.8f}','-y',target],token)
    return target
