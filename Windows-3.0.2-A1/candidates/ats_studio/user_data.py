"""One local user-data root; imports previous presets without removing originals."""
import os, shutil, json, hashlib
from pathlib import Path

def user_data_root():
    return Path(os.environ.get('APPDATA',str(Path.home()/'AppData'/'Roaming')))/'Naimat'/'AutoTimelineSync'

def migrate_presets():
    root=user_data_root();old=root.parent.parent/'AutoTimelineSync'/'presets';new=root/'presets'
    tracker=new/'.legacy-migration.json'
    try:records=json.loads(tracker.read_text(encoding='utf-8'))
    except (OSError,ValueError):records={}
    changed=False
    if old.is_dir():
        for src in old.rglob('*.json'):
            relative=src.relative_to(old);dest=new/relative;key=relative.as_posix()
            digest=hashlib.sha256(src.read_bytes()).hexdigest()
            untouched=dest.is_file() and records.get(key)==hashlib.sha256(dest.read_bytes()).hexdigest()
            if not dest.exists() or untouched and records.get(key)!=digest:
                dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
                records[key]=digest;changed=True
    if changed:tracker.write_text(json.dumps(records,sort_keys=True),encoding='utf-8')
    return new
