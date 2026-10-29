"""Measure the actual creator geometry for all 65 supplied Hindi captions."""
import sys,json
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,application,install
application();install()
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage
from ats_studio.product import Project
from ats_studio.pro_spec import build_spec
from ats_studio.caption_presets import render_caption,PROFILES
saved=json.loads((ROOT/'Evidence/Acceptance/project.ats3').read_text(encoding='utf-8'))
p=Project(saved['name'],saved['narration'],saved['image_folder'],saved['script'],saved['music']).validate()
settings=p.settings(tier=1);spec=build_spec(p.effective_package(),p.images,settings)
rows=[]
for ordinal,caption in enumerate(spec.captions,1):
    cache={};image=QImage(settings.width,settings.height,QImage.Format_RGB888);image.fill(0)
    render_caption(image,caption,caption.start_frame+8,spec.package.fps,settings.caption_preset,settings,0,(),cache)
    items,text_height,actual_size=next(iter(cache.values()))
    bounds=QRectF()
    for _,path,rect in items:bounds=bounds.united(path.boundingRect()).united(rect)
    # Source render transforms around the text center. Reserve the max pop
    # factor 1.1 and a conservative 18 px allowance for stroke/shadow.
    center_x=settings.width/2;center_y=settings.height/2
    left=center_x+(bounds.left()-center_x)*1.1-18
    right=center_x+(bounds.right()-center_x)*1.1+18
    top=center_y+(bounds.top()-text_height/2)*1.1-18
    bottom=center_y+(bounds.bottom()-text_height/2)*1.1+18
    fit=left>=0 and top>=0 and right<=settings.width and bottom<=settings.height
    rows.append({'id':f'{ordinal:03d}','text':caption.text,'fit_in_canvas':fit,'bounds_at_peak_pop':[left,top,right,bottom],
                 'requested_size_percent':settings.caption_size,'resolved_font_pixel_size':actual_size,'configured_position':settings.caption_position})
result={'method':'Actual render_caption cached path/line geometry, maximum pop scale 1.1, 18 px stroke/shadow allowance. Full HD canvas. Covers the supplied text only, not universal glyph/layout certification.',
        'font':settings.caption_font,'preset':settings.caption_preset,'resolution':[settings.width,settings.height],
        'caption_count':len(rows),'all_fit':all(x['fit_in_canvas'] for x in rows),'captions':rows}
(ROOT/'Evidence/Acceptance/caption-fit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('CAPTION FIT',len(rows),result['all_fit'])
for x in rows:
    if not x['fit_in_canvas']:print(x)
assert result['all_fit']
