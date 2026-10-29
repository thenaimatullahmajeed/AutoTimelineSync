"""Vectorised PCM mixing and a bounded, versioned procedural waveform cache."""
from pathlib import Path
from array import array
import hashlib, json, math, os, random, tempfile, time, wave
import numpy as np
from .user_data import user_data_root

CACHE_VERSION='r2m0-wave-1'
CACHE_LIMIT=128*1024**2

def check_cancel(cancelled):
    if cancelled and cancelled():
        from .renderer import RenderCancelled
        raise RenderCancelled()

def cached_wave(kind, identity, frames, seed, factory, cancelled=None):
    root=user_data_root()/'cache'/'procedural_audio';root.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps([CACHE_VERSION,kind,identity,frames,seed],sort_keys=True).encode()).hexdigest()
    path=root/(key+'.npy');check_cancel(cancelled)
    if path.is_file():
        try:
            value=np.load(path,allow_pickle=False)
            if value.shape==(frames,) and value.dtype==np.float32 and np.isfinite(value).all():
                os.utime(path,None);return value,True
        except (OSError,ValueError,EOFError):pass
    value=np.asarray(factory(),dtype=np.float32);check_cancel(cancelled)
    if value.shape!=(frames,) or not np.isfinite(value).all():raise ValueError('Invalid procedural waveform')
    if value.nbytes<=CACHE_LIMIT:
        fd,tmp=tempfile.mkstemp(dir=root,suffix='.tmp')
        try:
            with os.fdopen(fd,'wb') as handle:np.save(handle,value,allow_pickle=False)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        files=[]
        for file in root.glob('*.npy'):
            try:files.append((file.stat().st_mtime,file.stat().st_size,file))
            except FileNotFoundError:continue
        used=0
        for _,size,file in sorted(files,reverse=True):
            used+=size
            if used>CACHE_LIMIT and file.resolve().is_relative_to(root.resolve()):file.unlink(missing_ok=True)
    return value,False

def low_filter(noise, coefficient, cancelled=None):
    out=np.empty(len(noise),dtype=np.float32);previous=0.
    for start in range(0,len(noise),1024):
        check_cancel(cancelled);part=noise[start:start+1024]
        powers=coefficient**np.arange(1,len(part)+1,dtype=np.float64)
        values=powers*(previous+np.cumsum((1-coefficient)*part/powers))
        out[start:start+len(part)]=values;previous=float(values[-1])
    return out

def procedural_bed(kind, name, frames, seed, cancelled=None):
    if kind=='music':
        tones={'DARK_DRONE_A':(55,82.4),'DARK_DRONE_B':(49,73.4),'TENSION_PULSE_A':(65.4,98),'WARM_PAD_A':(110,164.8),'FINANCE_PULSE_A':(130.8,196),'TECH_AMBIENT_A':(82.4,123.5)}
        a,b=tones.get(name,(0,0));t=(np.arange(frames,dtype=np.float64)+1)/48000
        result=np.sin(2*np.pi*a*t)*.65+np.sin(2*np.pi*b*t)*.30
        if 'PULSE' in name:result*=.65+.35*np.sin(2*np.pi*.7*(t-1/48000))
        return result.astype(np.float32)
    rng=random.Random(seed+741+sum(ord(c) for c in name))
    noise=np.fromiter((rng.random()*2-1 for _ in range(frames)),dtype=np.float64,count=frames)
    coeff={'WIND_SOFT':.995,'CITY_NIGHT_SOFT':.990,'CROWD_MURMUR':.975,'CANDLE_ROOM':.999}.get(name,.998)
    return low_filter(noise,coeff,cancelled)

def activity(samples):
    block=960;count=math.ceil(len(samples)/block)
    padded=np.pad(samples,(0,count*block-len(samples)))
    square=padded.reshape(count,block).astype(np.float64)
    lengths=np.full(count,block);lengths[-1]=len(samples)-(count-1)*block
    levels=np.clip((np.sqrt(np.sum(square*square,axis=1)/lengths)-.004)/.018,0,1)
    smoothed=np.empty(count,dtype=np.float32);level=0.
    for i,value in enumerate(levels):
        level+=(.75 if value>level else .10)*(value-level);smoothed[i]=level
    return np.repeat(smoothed,block)[:len(samples)]

def write_pcm(path,samples):
    pcm=(np.clip(samples,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as handle:
        handle.setnchannels(1);handle.setsampwidth(2);handle.setframerate(48000);handle.writeframes(pcm.tobytes())

def feature_times(samples):
    """Five-ms RMS transient detector; reports resolution rather than false precision."""
    samples=np.asarray(samples,dtype=np.float32);block=240
    if not len(samples):return {'onset_ms':None,'peak_ms':None,'end_ms':None}
    pad=np.pad(samples,(0,(-len(samples))%block)).reshape(-1,block)
    env=np.sqrt(np.mean(pad.astype(np.float64)**2,axis=1));peak=int(np.argmax(env))
    if env[peak]<.00001:return {'onset_ms':None,'peak_ms':None,'end_ms':None}
    first=np.flatnonzero(env[:peak+1]>=max(.01,env[peak]*.35))
    first=int(first[0]) if len(first) else peak
    while first>0 and env[first-1]>=env[peak]*.1:first-=1
    tail=np.flatnonzero(env[peak:]<.01)
    end=peak+int(tail[0]) if len(tail) else len(env)-1
    return {'onset_ms':first*5.,'peak_ms':peak*5.,'end_ms':end*5.}


def event_feature_times(samples):
    """Amplitude-invariant V3 transient detector; V1/V2 keep their original checks."""
    samples=np.asarray(samples,dtype=np.float32)
    peak=float(np.max(np.abs(samples))) if len(samples) else 0
    if peak<1e-7:return {'onset_ms':None,'peak_ms':None,'end_ms':None}
    return feature_times(samples/peak)
