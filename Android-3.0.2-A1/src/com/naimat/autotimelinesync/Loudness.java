package com.naimat.autotimelinesync;
import java.util.*;
/** Stereo K weighting and BS.1770 absolute/relative gated integrated loudness at 48 kHz. */
public final class Loudness {
 static final class Filter{double b0,b1,b2,a1,a2,z1,z2;Filter(double x,double y,double z,double a,double b){b0=x;b1=y;b2=z;a1=a;a2=b;}double run(double x){double y=b0*x+z1;z1=b1*x-a1*y+z2;z2=b2*x-a2*y;return y;}}
 final Filter[] shelf={new Filter(1.53512485958697,-2.69169618940638,1.19839281085285,-1.69065929318241,.73248077421585),new Filter(1.53512485958697,-2.69169618940638,1.19839281085285,-1.69065929318241,.73248077421585)};
 final Filter[] pass={new Filter(1,-2,1,-1.99004745483398,.99007225036621),new Filter(1,-2,1,-1.99004745483398,.99007225036621)};
 final List<Double> blocks=new ArrayList<>();final double[] hops=new double[4];long frames;double energy,total;
 public void add(double l,double r){double a=pass[0].run(shelf[0].run(l)),b=pass[1].run(shelf[1].run(r));energy+=a*a+b*b;total+=a*a+b*b;frames++;if(frames%4800==0){int ix=(int)((frames/4800-1)%4);hops[ix]=energy/4800;energy=0;if(frames>=19200)blocks.add((hops[0]+hops[1]+hops[2]+hops[3])/4);}}
 public double integrated(){if(blocks.isEmpty())return -.691+10*Math.log10(Math.max(1e-12,total/Math.max(1,frames)));double sum=0;int count=0;for(double b:blocks)if(-.691+10*Math.log10(Math.max(1e-12,b))>-70){sum+=b;count++;}if(count==0)return -120;double threshold=-.691+10*Math.log10(sum/count)-10;sum=0;count=0;for(double b:blocks)if(-.691+10*Math.log10(Math.max(1e-12,b))>Math.max(-70,threshold)){sum+=b;count++;}return count==0?-120:-.691+10*Math.log10(sum/count);}
}
