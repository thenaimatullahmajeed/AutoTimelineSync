from pathlib import Path
import os,subprocess,zipfile,json,wave,math,struct,shutil
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
SDK=Path(os.environ.get('ANDROID_SDK_ROOT',Path.home()/'AppData/Local/Android/Sdk'))
JAVA=Path(os.environ.get('JAVA_HOME',Path.home()/'.jdks/jbr-17.0.14'))
BT=SDK/'build-tools/35.0.0'; ANDROID=SDK/'platforms/android-35/android.jar'
env=os.environ.copy();env['JAVA_HOME']=str(JAVA);env['PATH']=str(JAVA/'bin')+os.pathsep+env['PATH']
DESKTOP=Path('D:/My Created Software/Final AutoTimelineSync-3.0.1-FINAL-PORTABLE/AutoTimelineSync')
def run(args):
    p=subprocess.run([str(x) for x in args],env=env,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.stdout.strip(): print(p.stdout.strip(),flush=True)
    if p.returncode: raise RuntimeError(f'Build step failed ({p.returncode}): {args[0]}')
def assets():
    dest=ROOT/'assets';dest.mkdir(exist_ok=True)
    for name,source in [('fonts',DESKTOP/'_internal/assets/fonts'),('looks',DESKTOP/'_internal/presets/looks'),('styles',DESKTOP/'_internal/presets/styles'),('licenses',DESKTOP/'licenses')]:
        if source.exists():shutil.copytree(source,dest/name,dirs_exist_ok=True)
    for name in ['capabilities.json','CHATGPT_AUTHORING_GUIDE.md']:
        f=DESKTOP/name
        if f.exists():shutil.copy2(f,dest/name)
    verified=ROOT.parent/'ats_sync_3_0_2_A1'
    for name in ['ATS_CAPABILITIES.json','ATS_JSON_AUTHORING_GUIDE.md']:
        if (verified/name).exists():shutil.copy2(verified/name,dest/name)
    if (dest/'ATS_CAPABILITIES.json').exists():shutil.copy2(dest/'ATS_CAPABILITIES.json',dest/'capabilities.json')
    if (dest/'ATS_JSON_AUTHORING_GUIDE.md').exists():shutil.copy2(dest/'ATS_JSON_AUTHORING_GUIDE.md',dest/'CHATGPT_AUTHORING_GUIDE.md')
    catalog={f.stem:json.loads(f.read_text(encoding='utf-8-sig')) for f in (dest/'styles').glob('*.json')}
    literal=json.dumps(json.dumps(catalog,separators=(',',':')))
    (ROOT/'src/com/naimat/autotimelinesync/PresetCatalog.java').write_text('package com.naimat.autotimelinesync;import org.json.*;public final class PresetCatalog {static JSONObject catalog;public static JSONObject style(String name){try{if(catalog==null)catalog=new JSONObject('+literal+');JSONObject s=catalog.optJSONObject(name);return s==null?new JSONObject():s;}catch(Exception e){return new JSONObject();}}}',encoding='utf8')
    icon=ROOT/'res/drawable';icon.mkdir(exist_ok=True)
    original_icon=ROOT.parent/'assets/icons/AutoTimelineSync_Icon_512.png'
    if original_icon.exists():
        im=Image.open(original_icon).convert('RGBA');im.resize((192,192)).save(icon/'icon.png')
    elif not (icon/'icon.png').exists():raise RuntimeError('Bundled app icon is missing')
    demo=dest/'demo';demo.mkdir(exist_ok=True)
    for i in range(1,5):
        im=Image.new('RGB',(720,1280),(14+i*4,25+i*5,37+i*3));d=ImageDraw.Draw(im)
        for y in range(1280):d.line((0,y,720,y),fill=(int(18+(1-y/1280)*25),int(28+(1-y/1280)*30),int(40+(1-y/1280)*20)))
        if i==1:
            d.rectangle((60,320,660,850),fill='#17232e',outline='#536573',width=6);d.polygon([(140,480),(580,480),(520,700),(200,700)],fill='#e5d0a5');d.line((140,480,360,600,580,480),fill='#94775e',width=5)
        elif i==2:
            for x in range(70,720,120):d.rectangle((x,280,x+60,950),fill='#314554');d.ellipse((277,472,437,632),fill='#e8cd83',outline='#ffe793',width=8)
        elif i==3:
            d.rectangle((120,260,600,920),fill='#c1bba6');d.rectangle((155,310,565,720),fill='#304753');d.ellipse((285,460,435,610),fill='#dcb564');d.line((190,810,525,810),fill='#807b69',width=8)
        else:
            d.polygon([(180,950),(250,500),(350,460),(470,530),(550,950)],fill='#05080b');d.ellipse((260,280,470,510),fill='#05080b');d.rectangle((20,1060,700,1080),fill='#87c73c')
        d.text((40,60),f'ATS OFFLINE DEMO  /  SCENE {i:03}',fill='#c7d5df');im.save(demo/f'{i:03}.png')
    for name,seconds,music in [('narration.wav',8,False),('music.wav',2,True)]:
        with wave.open(str(demo/name),'wb') as w:
            w.setparams((2,2,48000,0,'NONE','not compressed'));block=bytearray()
            for n in range(seconds*48000):
                t=n/48000;en=.08 if music else (.14 if int(t*2)%2==0 else .012);v=en*(math.sin(t*2*math.pi*(164 if music else 330))+ .35*math.sin(t*2*math.pi*(246 if music else 495)));s=int(v*20000);block.extend(struct.pack('<hh',s,s))
                if len(block)>=16384:w.writeframesraw(block);block.clear()
            if block:w.writeframesraw(block)
    phrases=['In 1947 a letter arrived.','The guard held a coin.','A photograph revealed the secret.','Someone waited behind the door.'];words=[];captions=[];scenes=[];ix=1
    for i,phrase in enumerate(phrases):
        first=ix;tokens=phrase.split()
        for k,word in enumerate(tokens):words.append(dict(index=ix,start=round(i*2+k*1.8/len(tokens),5),end=round(i*2+(k+1)*1.8/len(tokens),5),text=word));ix+=1
        captions.append(dict(id=f'{i+1:03}',start=i*2,end=(i+1)*2,text=phrase,word_start_index=first,word_end_index=ix-1))
        scenes.append(dict(id=f'{i+1:03}',image_id=f'{i+1:03}',start=i*2,end=(i+1)*2,voice_text=phrase,motion=['SLOW_PUSH_IN','PAN_RIGHT','STATIC','SLOW_ZOOM_OUT'][i],transition=['HARD_CUT','CROSSFADE','PAPER_TEAR','FADE_THROUGH_BLACK'][i]))
    package=dict(schema='ATS_PACKAGE_V2',project_title='Offline demo — test tones',audio_duration=8,fps=30,format=dict(orientation='VERTICAL',aspect_ratio='9:16'),scenes=scenes,words=words,captions=captions,caption_style=dict(enabled=True,highlight_current_word=True,preset='Documentary Highlight'),direction=dict(energy='BALANCED',finish=dict(grain=.06,vignette=.12,contrast=.08),voice_level=1,music_level=.18,duck_db=-12,sfx_enabled=True,transition_frequency=.15),style=dict(look='CLEAN',look_intensity=1,seed=48127),moments=[dict(id='year',type='DATE_CARD',text='1947',word_start_index=2,word_end_index=2,dim=.6),dict(id='coin',type='CIRCLE',scene_id='002',box=[.39,.37,.22,.13],word_start_index=7,word_end_index=10)],ending=dict(mode='FADE_OUT',frames=12))
    (demo/'demo.json').write_text(json.dumps(package,separators=(',',':')),encoding='utf8')
def build(test=False):
    build=ROOT/'build';build.mkdir(exist_ok=True);classes=build/('test-classes' if test else 'classes');classes.mkdir(exist_ok=True);gen=build/'generated';gen.mkdir(exist_ok=True)
    name='AutoTimelineSync-tests' if test else 'AutoTimelineSync-3.0.2-A1-ANDROID'
    unsigned=build/(name+'-unsigned.apk');aligned=build/(name+'-aligned.apk');out=ROOT/(name+'.apk')
    manifest=ROOT/('tests/AndroidManifest.xml' if test else 'AndroidManifest.xml')
    args=[BT/'aapt.exe','package','-f','-M',manifest,'-I',ANDROID,'-F',unsigned]
    if not test: args+=['-S',ROOT/'res','-A',ROOT/'assets','-J',gen]
    run(args)
    sources=list((ROOT/('tests/src' if test else 'src')).rglob('*.java'))+(list(gen.rglob('*.java')) if not test else [])
    run([JAVA/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-classpath',str(ANDROID)+(os.pathsep+str(build/'classes') if test else ''),'-d',classes,*sources])
    jar=build/(name+'.jar');run([JAVA/'bin/jar.exe','cf',jar,'-C',classes,'.'])
    dex=build/('test-dex' if test else 'dex');dex.mkdir(exist_ok=True)
    args=[JAVA/'bin/java.exe','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',ANDROID,'--output',dex,jar]
    if test:args+=['--classpath',build/'AutoTimelineSync-3.0.2-A1-ANDROID.jar']
    run(args)
    with zipfile.ZipFile(unsigned,'a') as z:
        for f in dex.glob('*.dex'):z.write(f,f.name)
    run([BT/'zipalign.exe','-f','4',unsigned,aligned])
    keydir=Path.home()/'.codex/signing/ats-android';keydir.mkdir(parents=True,exist_ok=True);key=keydir/'ats-release.jks';passwordfile=keydir/'signing-password.txt'
    if not passwordfile.exists():
        import secrets;passwordfile.write_text(secrets.token_urlsafe(32),encoding='utf8')
    password=passwordfile.read_text().strip()
    if not key.exists():run([JAVA/'bin/keytool.exe','-genkeypair','-keystore',key,'-alias','ats','-keyalg','RSA','-keysize','3072','-validity','10000','-storepass',password,'-keypass',password,'-dname','CN=Naimat, OU=Auto Timeline Sync, O=Naimat'])
    run([JAVA/'bin/java.exe','-jar',BT/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','ats','--ks-pass','file:'+str(passwordfile),'--out',out,aligned])
    run([JAVA/'bin/java.exe','-jar',BT/'lib/apksigner.jar','verify','--verbose',out]);print('APK:',out,flush=True)
if __name__=='__main__':
    import sys
    if '--tests' not in sys.argv:
        assets()
        run([os.sys.executable,ROOT/'tools/sync_assets.py'])
    build('--tests' in sys.argv)
