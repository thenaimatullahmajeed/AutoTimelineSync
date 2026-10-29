"""Build in a new directory; never replace the original core or delivered EXE."""
import os,sys,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'ats_windows_3_0_2'
CORE=BASE/'core'
WORK=ROOT/'Packaging'
STAGE=WORK/'stage'
STAGE.mkdir(parents=True,exist_ok=True)
shutil.copytree(CORE/'ats_studio',STAGE/'ats_studio',dirs_exist_ok=True)
shutil.copytree(ROOT/'overlay/ats_studio',STAGE/'ats_studio',dirs_exist_ok=True)
for filename in ['bootstrap.py','launch_portable.py']:shutil.copy2(ROOT/filename,STAGE/filename)
command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--name','AutoTimelineSync',
 '--icon',str(CORE/'assets/icons/AutoTimelineSync.ico'),'--paths',str(STAGE),'--distpath',str(WORK/'dist'),
 '--workpath',str(WORK/'build'),'--specpath',str(WORK),
 '--add-data',str(CORE/'assets')+os.pathsep+'assets','--add-data',str(CORE/'presets')+os.pathsep+'presets']
modules=[m['module'] for m in json.loads((BASE/'RECOVERED_BASELINE.json').read_text())]
modules+=['ats_studio.sync_core','ats_studio.sync_diagnostics','ats_studio.sync_modes','ats_studio.sync_ui','ats_studio.portable_smoke']
for module in sorted(set(modules)):command+=['--hidden-import',module]
command+=[str(STAGE/'launch_portable.py')]
subprocess.run(command,check=True,cwd=WORK)
target=WORK/'dist/AutoTimelineSync'
for folder in ['runtime','licenses','Examples']:shutil.copytree(CORE/folder,target/folder,dirs_exist_ok=True)
for filename in ['capabilities.json','USER_GUIDE.md']:shutil.copy2(CORE/filename,target/filename)
for filename in ['ATS_CAPABILITIES.json','ATS_JSON_AUTHORING_GUIDE.md']:shutil.copy2(ROOT/filename,target/filename)
print('BUILT',target,flush=True)
