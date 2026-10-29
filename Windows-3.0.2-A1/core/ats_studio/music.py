"""Equal-power loop schedule used by audio mix and timeline seam markers."""
import numpy as np

def seam_samples(length,rate=48000):return min(round(.8*rate),max(0,length//2))

def loop_pcm(source,frames,rate=48000):
    source=np.asarray(source,dtype=np.float32)
    if not len(source):raise ValueError('Music has no samples.')
    n=len(source)
    if frames<=n:return source[:frames].copy()
    seam=seam_samples(n,rate);step=max(1,n-seam)
    positions=np.arange(frames,dtype=np.int64);phase=positions%step;cycled=positions>=step
    out=source[phase].copy()
    if seam:
        mask=cycled & (phase<seam);t=(phase[mask]+.5)/seam*np.pi/2
        out[mask]=source[phase[mask]]*np.sin(t)+source[step+phase[mask]]*np.cos(t)
    return out

def loop_seams(clip_seconds,total_seconds,rate=48000):
    if total_seconds<=clip_seconds:return []
    n=max(1,round(clip_seconds*rate));step=(n-seam_samples(n,rate))/rate
    # Timeline can't display more than 1000 meaningful seam marks.
    return [i*step for i in range(1,min(1001,int(total_seconds/step)+1)) if i*step<total_seconds]
