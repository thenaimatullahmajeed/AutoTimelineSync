"""Run actual installed APK instrumentation and collect its evidence."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(__file__).resolve().parents[1]
ADB=Path.home()/'AppData/Local/Android/Sdk/platform-tools/adb.exe'
serial=sys.argv[1] if len(sys.argv)>1 else 'emulator-5554'
if serial.startswith('emulator-'):
 for args in [('svc','power','stayon','true'),('input','keyevent','KEYCODE_WAKEUP'),('wm','dismiss-keyguard')]:
  subprocess.run([str(ADB),'-s',serial,'shell',*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
api=subprocess.check_output([str(ADB),'-s',serial,'shell','getprop','ro.build.version.sdk'],text=True).strip()
output=ROOT/'Verification'/('API'+api+('-Sync' if '--sync-only' in sys.argv else ''));output.mkdir(parents=True,exist_ok=True)
with (output/'instrumentation.log').open('w',encoding='utf-8') as log:
 p=subprocess.Popen([str(ADB),'-s',serial,'shell','am','instrument','-w',*(['-e','sync_only','true'] if '--sync-only' in sys.argv else []),'com.naimat.autotimelinesync.tests/com.naimat.autotimelinesync.tests.TestRunner'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
 for line in p.stdout:
  log.write(line);log.flush()
  if (': PASS' in line or ': FAIL' in line) or 'Rendering MP4' in line or 'INSTRUMENTATION_FAILED' in line:print(line.strip(),flush=True)
 p.wait()
 if p.returncode:raise RuntimeError('Instrumentation command failed')
subprocess.run([str(ADB),'-s',serial,'pull','/sdcard/Android/data/com.naimat.autotimelinesync/files/verification/.',str(output)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
result=json.loads((output/'results.json').read_text(encoding='utf-8'))
print('RESULT',json.dumps({'api':api,'count':result['count'],'failures':result['failures']}),flush=True)
if result['failures']:sys.exit(1)
