"""Render one authoring alternative without editing supplied JSON or renderer."""
import sys,json
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,application,install
application();install()
from ats_studio.product import Project
from ats_studio.pro_spec import build_spec
from ats_studio.pro_compositor import ProCompositor
out=ROOT/'Evidence/Acceptance'
d=json.loads((out/'project.ats3').read_text(encoding='utf-8'))
p=Project(d['name'],d['narration'],d['image_folder'],d['script'],d['music']).validate()
settings=replace(p.settings(tier=1),caption_position='Bottom')
spec=build_spec(p.effective_package(),p.images,settings)
moment=next(m for m in spec.changes['moments'] if m['type']=='DATE_CARD' and m['text']=='1879')
frame=(moment['first_frame']+moment['end_frame'])//2
image=ProCompositor(spec,p.images,settings).render_frame(frame)
assert image.save(str(out/'workaround-bottom-date-1879.png'))
print('Rendered Bottom-position comparison; original Center JSON and export retained')
