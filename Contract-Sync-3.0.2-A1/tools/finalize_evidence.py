"""Finalize measured/exported evidence after the extracted frames were viewed."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT
out=ROOT/'Evidence/Acceptance'
result=json.loads((out/'result.json').read_text(encoding='utf-8'))
report=json.loads((out/'RICH-Hindi-Acceptance.mp4.report.json').read_text(encoding='utf-8'))
energy=json.loads((out/'energy-comparison.json').read_text(encoding='utf-8'))
before=float(np.asarray(Image.open(out/'frames/ending-before.png').convert('RGB')).mean())
after=float(np.asarray(Image.open(out/'frames/ending-final.png').convert('RGB')).mean())
result.update(visual_review={'viewed_scene_frames':['002','005','011','013','016','020','022','028','034'],
    'viewed_transition_frames':['002','005','011','013','016','020','022','028','034'],
    'viewed_dates':['1840','1879','1930'],'viewed_ending':True,
    'captions_canvas_fit':'PASS for every one of the supplied 65 captions, including measured peak pop allowance',
    'date_card_legibility':'FAIL: all three centered date cards overlap centered Hindi captions; 1879 is heavily obscured',
    'transitions':'PASS: blending/flash/slide/fade/iris effects visible on extracted frames',
    'ending':'PASS: strong fade into near black; final frame retains a small residual image'},
    ending_pixel_means={'before_fade':before,'final_frame':after},
    energy_check={'seeds':{k:v['seed'] for k,v in energy.items()},
        'all_decisions_identical':len({json.dumps(v['decisions'],sort_keys=True) for v in energy.values()})==1,
        'sampled_pixels_identical':len({json.dumps(v['pixels'],sort_keys=True) for v in energy.values()})==1,
        'scope':'Three energies on exact final package; five sampled frames at reduced test resolution, not three extra full exports'},
    audio_stats=report.get('audio_stats'),export_warnings=report.get('warnings',[]),
    contract_scope='D1-D5 review candidate only; installed Windows app unchanged')
assert after<before*.1
actual_sha=hashlib.sha256(Path('C:/Users/naima/Downloads/AutoTimelineSync-3.0.2-WINDOWS-FINAL/AutoTimelineSync/AutoTimelineSync.exe').read_bytes()).hexdigest()
assert actual_sha=='dcd94fd3694065470336bcb2e07efaee6ceb28a426277e3a74bf7b3f35bc901b'
result['installed_exe_unchanged']=True
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('ENERGY',result['energy_check'])
print('AUDIO',result['audio_stats'])
print('WARNINGS',result['export_warnings'])
print('FADE',result['ending_pixel_means'])
