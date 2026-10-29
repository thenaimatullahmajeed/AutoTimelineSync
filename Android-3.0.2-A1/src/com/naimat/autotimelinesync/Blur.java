package com.naimat.autotimelinesync;
import android.graphics.Bitmap;
/** Two separable box passes with linear-time sliding sums; cached per asset by the compositor. */
public final class Blur {
 public static Bitmap apply(Bitmap image,int radius){int w=image.getWidth(),h=image.getHeight();int[]a=new int[w*h],b=new int[w*h];image.getPixels(a,0,w,0,0,w,h);for(int pass=0;pass<2;pass++){axis(a,b,w,h,radius,true);axis(b,a,w,h,radius,false);}Bitmap result=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);result.setPixels(a,0,w,0,0,w,h);return result;}
 static void axis(int[]src,int[]dst,int w,int h,int radius,boolean horizontal){int count=2*radius+1,lines=horizontal?h:w,len=horizontal?w:h;for(int line=0;line<lines;line++){long r=0,g=0,b=0,alpha=0;for(int n=-radius;n<=radius;n++){int p=pixel(src,line,Math.max(0,Math.min(len-1,n)),w,h,horizontal);alpha+=(p>>>24);r+=(p>>>16)&255;g+=(p>>>8)&255;b+=p&255;}for(int x=0;x<len;x++){int at=horizontal?line*w+x:x*w+line;dst[at]=((int)(alpha/count)<<24)|((int)(r/count)<<16)|((int)(g/count)<<8)|(int)(b/count);int remove=pixel(src,line,Math.max(0,x-radius),w,h,horizontal),add=pixel(src,line,Math.min(len-1,x+radius+1),w,h,horizontal);alpha+=(add>>>24)-(remove>>>24);r+=((add>>>16)&255)-((remove>>>16)&255);g+=((add>>>8)&255)-((remove>>>8)&255);b+=(add&255)-(remove&255);}}}
 static int pixel(int[]a,int line,int x,int w,int h,boolean horizontal){return a[horizontal?line*w+x:x*w+line];}
}
