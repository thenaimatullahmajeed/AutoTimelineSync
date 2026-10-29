"""Locate the requested package without silently repairing/replacing any input."""
import sys,json,zipfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,application,install
application();install()
from ats_studio.sync_modes import FANCY,classify_counts
from ats_studio.sync_diagnostics import validate_all,copy_message
folder=Path('C:/Users/naima/Downloads/autodownload')
records=[];found=[]
def examine(origin,blob):
    try:d=json.loads(blob.decode('utf-8-sig'))
    except (UnicodeError,ValueError):return
    if not isinstance(d,dict) or len(d.get('scenes',[]))!=34:return
    types=[s.get('transition_config',{}).get('type',s.get('transition')) for s in d['scenes'][1:]]
    counts={'scenes':34,'words':len(d.get('words',[])),'captions':len(d.get('captions',[])),
            'noncuts':sum(x not in ['HARD_CUT','NONE'] for x in types),'fancy':sum(x in FANCY for x in types),
            'date_cards':sum(m.get('type')=='DATE_CARD' for m in d.get('moments',[])),
            'authored_sound_cues':sum(len(s.get('sfx',[]))+(s.get('transition_config',{}).get('sfx','NONE')!='NONE') for s in d['scenes'])}
    records.append({'origin':origin,'sha256':hashlib.sha256(blob).hexdigest(),**counts})
    if (counts['words'],counts['captions'],counts['noncuts'],counts['fancy'],counts['date_cards'],counts['authored_sound_cues'])==(256,65,22,8,3,6):found.append((origin,blob,d))
for p in folder.rglob('*ATS*.json'):
    if p.is_file() and p.stat().st_size<52_428_800:examine(str(p),p.read_bytes())
for p in folder.glob('*.zip'):
    try:
        with zipfile.ZipFile(p) as z:
            for entry in z.infolist():
                if 'ATS' in entry.filename.upper() and entry.filename.lower().endswith('.json') and entry.file_size<52_428_800:
                    examine(str(p)+' :: '+entry.filename,z.read(entry))
    except (OSError,zipfile.BadZipFile):pass
if found:
    # Equal duplicates are fine; divergent matches require explicit selection.
    unique={hashlib.sha256(b).hexdigest() for _,b,_ in found}
    if len(unique)==1:
        origin,blob,d=found[0];(ROOT/'Inputs/FINAL_RICH_03_ATS_PACKAGE_V2.json').write_bytes(blob)
        chosen=origin;content=blob.decode('utf-8-sig');matches=True
    else:chosen=None;content=None;matches=False
else:
    chosen=str(folder/'03_ATS_PACKAGE_V2.json');content=Path(chosen).read_text(encoding='utf-8-sig');matches=False
result=validate_all(content) if content is not None else {'valid':False,'diagnostics':[]}
(ROOT/'Evidence/acceptance-input.json').write_text(json.dumps({'matches_requested_final':matches,'selected':chosen,'candidates':records,'diagnostics':result,'render_status':'PENDING' if matches else 'NOT RUN: final RICH package not found; found old package is not substituted'},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'Evidence/acceptance-copy-errors.txt').write_text(copy_message(result),encoding='utf-8')
print(json.dumps({'matches_requested_final':matches,'selected':chosen,'candidates':records},ensure_ascii=False,indent=2))
print(copy_message(result))
