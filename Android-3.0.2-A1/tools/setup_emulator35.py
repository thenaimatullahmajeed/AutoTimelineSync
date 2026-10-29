from pathlib import Path
import urllib.request,xml.etree.ElementTree as ET,hashlib,zipfile,os
ROOT=Path(__file__).resolve().parents[1];SDK=Path.home()/'AppData/Local/Android/Sdk'
xml=urllib.request.urlopen('https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml',timeout=90).read()
root=ET.fromstring(xml)
package=next(e for e in root.iter() if e.tag.endswith('remotePackage') and e.get('path')=='system-images;android-35;default;x86_64')
values={e.tag.split('}')[-1]:e.text for e in package.iter() if e.tag.split('}')[-1] in {'size','checksum','url'}}
print('Official Android 15 test image:',values['url'],values['size'],flush=True)
destination=SDK/'system-images/android-35/default/x86_64'
if not (destination/'system.img').exists():
    archive=ROOT/'build/system-image35.zip';url='https://dl.google.com/android/repository/sys-img/android/'+values['url']
    with urllib.request.urlopen(url,timeout=90) as source,archive.open('wb') as out:
        total=0;next_report=64*1024*1024
        while True:
            chunk=source.read(1024*1024)
            if not chunk:break
            out.write(chunk);total+=len(chunk)
            if total>=next_report:print(total//1024//1024,'MiB',flush=True);next_report+=64*1024*1024
    if archive.stat().st_size!=int(values['size']) or hashlib.file_digest(archive.open('rb'),'sha1').hexdigest()!=values['checksum']:raise RuntimeError('Official image checksum mismatch')
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            bits=Path(item.filename).parts
            if '..' in bits:raise RuntimeError('Unsafe archive member')
            relative=Path(*bits[1:]);target=destination/relative
            if item.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(item) as src,target.open('wb') as dst:
                    import shutil;shutil.copyfileobj(src,dst)
    archive.unlink()
avd=Path.home()/'.android/avd/ATS_Test35.avd';avd.mkdir(parents=True,exist_ok=True)
(avd.parent/'ATS_Test35.ini').write_text(f'avd.ini.encoding=UTF-8\npath={avd}\ntarget=android-35\n',encoding='utf8')
(avd/'config.ini').write_text(f'avd.ini.encoding=UTF-8\nAvdId=ATS_Test35\navd.ini.displayname=ATS Android 15 verification\nabi.type=x86_64\nhw.cpu.arch=x86_64\nhw.cpu.ncore=4\nhw.ramSize=3072\nhw.lcd.width=1080\nhw.lcd.height=1920\nhw.lcd.density=420\nhw.keyboard=yes\nhw.gpu.enabled=yes\nhw.gpu.mode=swiftshader_indirect\nhw.audioInput=no\nhw.audioOutput=no\nimage.sysdir.1={destination}\nPlayStore.enabled=false\ndisk.dataPartition.size=4G\ntag.id=default\ntag.display=Default\nshowDeviceFrame=no\nfastboot.forceColdBoot=yes\n',encoding='utf8')
print('ATS_Test35 ready',flush=True)
