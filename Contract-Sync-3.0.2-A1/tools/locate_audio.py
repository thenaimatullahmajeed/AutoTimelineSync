import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,application
application()
from ats_studio.media import probe_audio
candidates=set()
for directory in [Path('C:/Users/naima/OneDrive/Desktop'),Path('C:/Users/naima/Downloads')]:
    for p in directory.glob('*.ats3'):
        try:
            data=json.loads(p.read_text(encoding='utf-8'))
            if 'Hedge' in str(data.get('name')) or 'Hedge' in p.name or 'चीन' in str(data.get('narration')):candidates.add(Path(data['narration']))
        except (KeyError,ValueError,OSError):pass
    for p in directory.glob('*'):
        if p.is_file() and p.suffix.lower() in {'.mp3','.wav','.m4a'} and ('चीन' in p.name or 'hedge' in p.name.lower()):candidates.add(p)
records=[]
for p in sorted(candidates):
    if not p.is_file():continue
    try:records.append({'path':str(p),'probe':probe_audio(p)})
    except Exception as exc:records.append({'path':str(p),'error':str(exc)})
(ROOT/'Evidence/audio-location.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False,indent=2))
