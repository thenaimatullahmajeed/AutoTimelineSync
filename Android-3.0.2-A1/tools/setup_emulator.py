"""Install one official Android SDK test image, checksum verified; no user media touched."""
import hashlib,os,urllib.request,zipfile,shutil
from pathlib import Path
root=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk'
dest=root/'system-images/android-30/default/x86_64'
if not (dest/'system.img').exists():
    cache=Path(__file__).resolve().parents[1]/'build/system-image.zip'
    cache.parent.mkdir(parents=True,exist_ok=True)
    url='https://dl.google.com/android/repository/sys-img/android/x86_64-30_r11.zip'
    h=hashlib.sha1();total=0;report=0
    with urllib.request.urlopen(url,timeout=60) as src,cache.open('wb') as out:
        while chunk:=src.read(1024*1024):
            out.write(chunk);h.update(chunk);total+=len(chunk)
            if total-report>=64*1024*1024:
                print(f'Official Android test image: {total//1048576} MiB',flush=True);report=total
    assert total==676379777 and h.hexdigest()=='5e4de3946d46f88856c35efcc4d797b381456347','SDK image checksum mismatch'
    with zipfile.ZipFile(cache) as z:
        for info in z.infolist():
            if info.is_dir():continue
            parts=Path(info.filename).parts
            if parts[0]=='x86_64':parts=parts[1:]
            target=dest.joinpath(*parts).resolve()
            assert target.is_relative_to(dest.resolve())
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src,target.open('wb') as out:shutil.copyfileobj(src,out)
    cache.unlink()
avd=Path.home()/'.android/avd/ATS_Test.avd';avd.mkdir(parents=True,exist_ok=True)
(avd.parent/'ATS_Test.ini').write_text(f'avd.ini.encoding=UTF-8\npath={avd}\ntarget=android-30\n',encoding='utf-8')
(avd/'config.ini').write_text('''AvdId=ATS_Test
avd.ini.encoding=UTF-8
abi.type=x86_64
hw.cpu.arch=x86_64
hw.cpu.ncore=4
hw.ramSize=3072
hw.lcd.width=1080
hw.lcd.height=1920
hw.lcd.density=420
hw.gpu.enabled=yes
hw.gpu.mode=swiftshader_indirect
hw.keyboard=yes
hw.audioInput=no
disk.dataPartition.size=4G
showDeviceFrame=no
fastboot.forceColdBoot=yes
image.sysdir.1=system-images/android-30/default/x86_64/
tag.id=default
tag.display=Default
''',encoding='utf-8')
print('ATS_Test Android emulator ready',flush=True)
