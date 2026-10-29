"""Grounded live Android UI smoke, independent of programmatic view callbacks."""
from pathlib import Path
import subprocess,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
ADB=Path.home()/'AppData/Local/Android/Sdk/platform-tools/adb.exe';SERIAL='emulator-5556'
OUT=ROOT/'Verification/UI-release-smoke';OUT.mkdir(parents=True,exist_ok=True)
def adb(*args):return subprocess.check_output([str(ADB),'-s',SERIAL,*args])
def state():
    adb('shell','uiautomator','dump','/sdcard/ats-ui-release.xml')
    data=adb('shell','cat','/sdcard/ats-ui-release.xml')
    return ET.fromstring(data)
def tap(label):
    nodes=list(state().iter('node'))
    matches=[n for n in nodes if (n.get('text') or n.get('content-desc') or '').lower()==label.lower()]
    assert matches,('Missing live control',label)
    n=matches[0];x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
    assert x2>x1 and y2>y1
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2))
def shot(name):
    current=state()
    assert not any("isn't responding" in n.get('text','') for n in current.iter('node')),'Platform ANR overlay obstructs smoke'
    (OUT/(name+'.xml')).write_bytes(ET.tostring(current))
    (OUT/(name+'.png')).write_bytes(adb('exec-out','screencap','-p'))
adb('shell','am','start','-n','com.naimat.autotimelinesync/.MainActivity')
shot('01-editor')
tap('⋮');shot('02-menu')
tap('Main Master Prompt V5.2.5');shot('03-master-prompt')
tap('Copy');shot('04-after-copy')
tap('⋮');tap('Utilization report');shot('05-utilization')
tap('Close');shot('06-timeline')
(OUT/'result.json').write_text(json.dumps({'ok':True,'actual_menu_taps':True,'prompt_copy_button_tapped':True,'no_anr_overlay_in_smoke':True,'text_integrity_evidence':'API35-Sync/clipboard-roundtrip.json'},indent=2),encoding='utf-8')
print('Live UI smoke PASS')
