"""Rebuild the portable app with all data/runtime files and the recovered baseline."""
from pathlib import Path
import os,subprocess,shutil,json
ROOT=Path(__file__).resolve().parent;CORE=ROOT/'core'
command=[os.sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed',
    '--name','AutoTimelineSync','--icon',str(CORE/'assets/icons/AutoTimelineSync.ico'),
    '--paths',str(CORE),'--distpath',str(ROOT/'dist'),'--workpath',str(ROOT/'build'),
    '--specpath',str(ROOT),
    '--add-data',str(CORE/'assets')+os.pathsep+'assets',
    '--add-data',str(CORE/'presets')+os.pathsep+'presets']
for module in json.loads((ROOT/'RECOVERED_BASELINE.json').read_text()):
    command+=['--hidden-import',module['module']]
command+=[str(CORE/'launch.py')]
subprocess.run(command,check=True,cwd=ROOT)
target=ROOT/'dist/AutoTimelineSync'
for folder in ('runtime','licenses','Examples'):
    shutil.copytree(CORE/folder,target/folder,dirs_exist_ok=True)
for name in ('capabilities.json','ATS_JSON_AUTHORING_GUIDE.md','USER_GUIDE.md'):
    shutil.copy2(CORE/name,target/name)
print('BUILT',target)
