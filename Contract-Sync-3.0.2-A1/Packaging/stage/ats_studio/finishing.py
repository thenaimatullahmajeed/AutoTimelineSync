"""Deterministic finishing of footage; captions and moments stay crisp."""
import numpy as np
from functools import lru_cache

@lru_cache(maxsize=4)
def radial_mask(width,height):
    x=np.linspace(-1,1,width,dtype=np.float32);y=np.linspace(-1,1,height,dtype=np.float32)
    return np.clip((x[None,:]**2+y[:,None]**2-.2)/1.8,0,1)

def finish(image,settings,seed,frame):
    grain=getattr(settings,'finish_grain',0);vignette=getattr(settings,'finish_vignette',0);contrast=getattr(settings,'finish_contrast',0)
    if not (grain or vignette or contrast):return
    # Detach before exposing writable pixels; input image is RGB888 in this compositor.
    bits=image.bits();width,height=image.width(),image.height()
    data=np.frombuffer(bits,dtype=np.uint8).reshape(height,image.bytesPerLine())[:,:width*3].reshape(height,width,3)
    rgb=data.astype(np.float32)
    if contrast:rgb=(rgb-127.5)*(1+.35*contrast)+127.5
    if vignette:rgb*=1-radial_mask(width,height)[:,:,None]*(.7*vignette)
    if grain:
        # Coordinate-normalized hash gives repeatable texture in preview and export.
        x=(np.arange(width,dtype=np.uint32)*2048//width)[None,:];y=(np.arange(height,dtype=np.uint32)*2048//height)[:,None]
        noise=x*np.uint32(374761393)+y*np.uint32(668265263)+np.uint32((seed+frame*69069)&0xFFFFFFFF)
        noise=(noise^(noise>>np.uint32(13)))*np.uint32(1274126177);noise^=noise>>np.uint32(16)
        rgb+=(((noise & 255).astype(np.float32)/255-.5)*24*grain)[:,:,None]
    data[:]=np.clip(rgb,0,255).astype(np.uint8)
