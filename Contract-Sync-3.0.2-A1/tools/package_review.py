"""Deliver the review artifacts only; do not install or replace the app."""
import sys,json,shutil,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT
destination=Path('C:/Users/naima/Downloads/ATS-SYNC-3.0.2-A1-REVIEW')
archive_path=destination.parent/(destination.name+'.zip')
assert destination.parent.resolve()==Path('C:/Users/naima/Downloads').resolve()
if destination.exists() or archive_path.exists():raise FileExistsError('Review delivery already exists; never overwrite it silently.')
destination.mkdir()
files=[]
for source in ROOT.rglob('*'):
    relative=source.relative_to(ROOT)
    if any(part.startswith('pytest-') or part=='__pycache__' for part in relative.parts):continue
    if not source.is_file():continue
    target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);files.append(str(relative))
# Rebase the new copy of the test project, preserving the original reference.
p=destination/'Evidence/Acceptance/project.ats3'
d=json.loads(p.read_text(encoding='utf-8'));d['image_folder']=str(p.parent/'images')
p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
with zipfile.ZipFile(archive_path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in destination.rglob('*'):
        if p.is_file():archive.write(p,Path(destination.name)/p.relative_to(destination))
with zipfile.ZipFile(archive_path) as archive:assert archive.testzip() is None
print(json.dumps({'folder':str(destination),'zip':str(archive_path),'file_count':len(files),'zip_megabytes':round(archive_path.stat().st_size/1024**2,2)},indent=2))
