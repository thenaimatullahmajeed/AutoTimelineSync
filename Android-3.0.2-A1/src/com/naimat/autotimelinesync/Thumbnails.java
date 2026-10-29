package com.naimat.autotimelinesync;
import android.graphics.*;import android.net.Uri;import android.os.Handler;import android.util.LruCache;import java.util.*;import java.util.concurrent.*;
/** Bounded background thumbnails; full-sized export images use their own cache. */
public final class Thumbnails {
 private final LruCache<String,Bitmap> cache=new LruCache<String,Bitmap>(4*1024*1024){protected int sizeOf(String k,Bitmap b){return b.getAllocationByteCount();}};
 private final Set<String> pending=Collections.synchronizedSet(new HashSet<>());
 private final ExecutorService executor=Executors.newSingleThreadExecutor(r->{Thread t=new Thread(r,"ATS thumbnails");t.setPriority(Thread.MIN_PRIORITY);return t;});
 private final Handler ui;private volatile boolean closed;
 public Thumbnails(Handler handler){ui=handler;}
 public Bitmap get(MediaFiles media,String id,Runnable changed){Uri uri=media.images.get(id);if(uri==null||closed)return null;String key=uri.toString();Bitmap b=cache.get(key);if(b!=null)return b;
  if(pending.add(key))executor.execute(()->{try{Bitmap source=media.image(id,192);float scale=Math.min(1,192f/Math.max(source.getWidth(),source.getHeight()));Bitmap thumb=Bitmap.createScaledBitmap(source,Math.max(1,Math.round(source.getWidth()*scale)),Math.max(1,Math.round(source.getHeight()*scale)),true);if(!closed){cache.put(key,thumb);ui.post(changed);}}catch(Exception ignored){}finally{pending.remove(key);}});return null;
 }
 public void close(){closed=true;executor.shutdownNow();cache.evictAll();pending.clear();}
}
