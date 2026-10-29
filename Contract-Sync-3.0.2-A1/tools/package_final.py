"""Deliver one standalone portable folder and its matching review/evidence files."""
import sys,json,shutil,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=Path('C:/Users/naima/Downloads/AutoTimelineSync-3.0.2-A1-FINAL-PORTABLE')
archive=target.parent/(target.name+'.zip')
assert target.parent.resolve()==Path('C:/Users/naima/Downloads').resolve()
if target.exists() or archive.exists():raise FileExistsError('Final delivery already exists; do not overwrite it silently.')
proof=json.loads((ROOT/'Evidence/release-verification.json').read_text())
assert proof['packaged_sync']==proof['packaged_import_export']=='PASS'
target.mkdir()
shutil.copytree(ROOT/'Packaging/dist/AutoTimelineSync',target/'AutoTimelineSync')
sync=target/'SyncPackage';sync.mkdir()
for source in ROOT.rglob('*'):
    rel=source.relative_to(ROOT)
    if any(part in ['Packaging','__pycache__','.pytest_cache'] or part.startswith('pytest-') for part in rel.parts):continue
    if not source.is_file():continue
    p=sync/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,p)
for filename in ['03_ATS_PACKAGE_V2_BOTTOM.json','CODEX_TO_CHATGPT_SYNC.md','SYNC_CHECKLIST.md']:
    shutil.copy2(ROOT/filename,target/filename)
# Resource documents beside the EXE must match the delivered live contract.
for filename in ['ATS_CAPABILITIES.json','ATS_JSON_AUTHORING_GUIDE.md']:
    shutil.copy2(ROOT/filename,target/'AutoTimelineSync'/filename)
# Make the copied acceptance project self contained; exact original script stays intact.
p=sync/'Evidence/Acceptance/project.ats3';d=json.loads(p.read_text(encoding='utf-8'))
source_audio=Path(d['narration']);narration=p.parent/'narration-original.mp3';shutil.copy2(source_audio,narration)
d['narration']=str(narration);d['image_folder']=str(p.parent/'images')
p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
exe=target/'AutoTimelineSync/AutoTimelineSync.exe'
assert hashlib.sha256(exe.read_bytes()).hexdigest()==proof['new_exe_sha256']
(target/'START_HERE.txt').write_text('Auto Timeline Sync by Naimat 3.0.2-A1\nContract: ATS_SYNC_2026-10-B\n\n1. Extract the entire ZIP to a folder.\n2. Open AutoTimelineSync/AutoTimelineSync.exe.\n3. Keep _internal, runtime and the other application folders together. No Python installation or login is needed.\n\nThe new build adds Validate all, Copy errors for ChatGPT, utilization/Copy utilization, early seed validation and warning-only RTL/font diagnostics.\n\nFor the supplied Hindi sample, use 03_ATS_PACKAGE_V2_BOTTOM.json to keep captions separate from centered date cards. Original JSON is in SyncPackage/Inputs.\n\nFor the master-prompt chat, send CODEX_TO_CHATGPT_SYNC.md together with the contract and guide in SyncPackage.\n\nExact test results and limitations: SYNC_CHECKLIST.md.\n',encoding='utf-8')
(target/'Run Auto Timeline Sync.cmd').write_text('@echo off\r\nstart "" "%~dp0AutoTimelineSync\\AutoTimelineSync.exe"\r\n',encoding='utf-8')
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in target.rglob('*'):
        if p.is_file():z.write(p,Path(target.name)/p.relative_to(target))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
result={'folder':str(target),'zip':str(archive),'exe':str(exe),'archive_mib':round(archive.stat().st_size/1024**2,2),'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'file_count':sum(p.is_file() for p in target.rglob('*'))}
(ROOT/'Evidence/delivery.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
