import sys,json,copy,hashlib,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,CORE,application,install
app=application();install()
from ats_studio.product import parse_script,script_settings
from ats_studio.pro_spec import build_spec
from ats_studio.pro_compositor import ProCompositor,MOTION_PATHS
from ats_studio.caption_presets import PROFILES
from PySide6.QtGui import QFont,QFontMetricsF
base=json.loads((CORE/'Examples/ATS3_vertical.json').read_text())
image=ROOT.parent/'ats_contract_audit_3_0_2/Golden/minimal/images/001.png'
def build(d):
    p=parse_script(json.dumps(d,ensure_ascii=False));s=script_settings(p,'VERTICAL');images={x.image_id:image for x in p.scenes}
    return p,s,images,build_spec(p,images,s)
result={'motions':{},'styles':{},'energy':{},'motion_paths':{k:list(v) for k,v in MOTION_PATHS.items()}}
for motion in ['IMPACT_PUNCH_IN','SLOW_PULL_OUT','STATIC_HOLD','SUBTLE_PARALLAX']:
    d=copy.deepcopy(base);d['scenes'][0]['motion']=motion
    p,s,ims,spec=build(d);plan=spec.scenes[0]
    result['motions'][motion]={'resolved':plan.motion,'path':list(MOTION_PATHS[plan.motion]),'warnings':list(spec.warnings)}
for file in (CORE/'presets/styles').glob('*.json'):
    d=copy.deepcopy(base);d['style']={'preset':file.stem};p,s,ims,spec=build(d)
    result['styles'][file.stem]={'stored':json.loads(file.read_text()),'active_style':spec.style,'first_scene_look':spec.scenes[0].look,'first_scene_intensity':spec.scenes[0].look_intensity,'caption_preset':s.caption_preset}
for energy in ['SUBTLE','BALANCED','HIGH_ENERGY']:
    d=copy.deepcopy(base);d['direction']['energy']=energy
    p,s,ims,spec=build(d)
    from dataclasses import replace
    s=replace(s,width=180,height=320)
    compositor=ProCompositor(spec,ims,s)
    frames=[0,15,120,125,200]
    pixels={}
    for f in frames:
        rendered=compositor.render_frame(f)
        pixels[str(f)]=hashlib.sha256(bytes(rendered.bits())).hexdigest()
    result['energy'][energy]={'decisions':[(x.motion,x.transition_applied,x.transition_frames,x.direction,x.focus_x,x.focus_y,x.look,x.look_intensity) for x in spec.scenes],'pixels':pixels}
result['energy_explicit_pixels_identical']=len({json.dumps(x,sort_keys=True) for x in result['energy'].values()})==1
# Advisory nominal fit: repeated widest tested standalone Devanagari letter,
# Hormozi/Poppins ExtraBold; reserve stroke plus peak pop scale. Not codepoints.
letters='अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'
rows=[]
for ratio,(w,h) in {'9:16':(1080,1920),'16:9':(1920,1080),'1:1':(1080,1080),'4:5':(1080,1350)}.items():
    for size in [100,120,140]:
        scale=min(w/1080,h/1920) if h>w else min(w/1920,h/1080)
        font=QFont('Poppins');font.setWeight(QFont.ExtraBold);font.setPixelSize(round(86*scale*size/100))
        fm=QFontMetricsF(font);widest=max(letters,key=fm.horizontalAdvance);advance=fm.horizontalAdvance(widest)
        nominal=w*(1-2*90/1080);safe=nominal/1.1-28*scale
        count=max(1,math.floor(safe/advance))
        rows.append({'ratio':ratio,'resolution':[w,h],'size_percent':size,'font_pixel_size':font.pixelSize(),'conservative_standalone_letter_count':count,'widest_test_letter':widest,'glyph_advance_px':advance,'safe_line_px':safe})
result['caption_fit']={'status':'ADVISORY, not a hard maximum or a guarantee','preset':'Hormozi Style','font':'Poppins ExtraBold','specimen':letters,'method':'Repeated widest tested independent letter; reserve peak 1.1 pop scale and stroke; two lines configured. Spaces and joined/combined graphemes have different widths. Creator auto-shrink can fit longer strings.','rows':rows}
(ROOT/'Evidence/semantics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'motions':result['motions'],'energy_explicit_pixels_identical':result['energy_explicit_pixels_identical'],'fit_rows':rows},ensure_ascii=False,indent=2))
