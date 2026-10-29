"""Soft-failing script moments and shared source-image geometry."""
from __future__ import annotations
import math
from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from .schema import frame_at

def validate_moments(package):
    words={w.index:w for w in package.words}; scenes={s.id:s for s in package.scenes}
    valid=[]; notices=[]; ids=set()
    values=package.pro.get('moments',[])
    if not isinstance(values,list):return [],['$.moments skipped: expected an array.']
    for i,item in enumerate(values):
        path=f'$.moments[{i}]'
        try:
            if not isinstance(item,dict):raise ValueError('expected an object')
            ident=item.get('id',str(i)); kind=item.get('type')
            if not isinstance(ident,str) or ident in ids:raise ValueError('id must be unique text')
            ids.add(ident)
            start=item.get('word_start_index'); end=item.get('word_end_index')
            if isinstance(start,bool) or isinstance(end,bool) or start not in words or end not in words or end<start:
                raise ValueError('word indices must reference an ordered range in words')
            first=frame_at(words[start].start,package.fps);last=frame_at(words[end].end,package.fps)
            if last<=first:raise ValueError('word timing must span at least one frame')
            if kind=='DATE_CARD':
                if item.keys()-{'id','type','text','word_start_index','word_end_index','dim'}:raise ValueError('unknown DATE_CARD field')
                if not isinstance(item.get('text'),str) or not 1<=len(item['text'])<=80:raise ValueError('text must be 1–80 characters')
                dim=item.get('dim',.65)
                if isinstance(dim,bool) or not isinstance(dim,(int,float)) or not math.isfinite(dim) or not 0<=dim<=.8:raise ValueError('dim must be 0–0.8')
            elif kind=='CIRCLE':
                if item.keys()-{'id','type','scene_id','box','word_start_index','word_end_index'}:raise ValueError('unknown CIRCLE field')
                scene=scenes.get(item.get('scene_id')); box=item.get('box')
                if not scene:raise ValueError('scene_id must exist')
                if not isinstance(box,list) or len(box)!=4 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in box):raise ValueError('box must be [x,y,width,height] in source-image coordinates')
                x,y,w,h=box
                if x<0 or y<0 or w<.03 or h<.03 or x+w>1 or y+h>1 or w*h>.2:raise ValueError('box must fit source image, each side ≥0.03, area ≤0.20')
                if first<scene.first_frame or last>scene.end_frame:raise ValueError('word range must be inside the referenced scene')
            else:raise ValueError('type must be DATE_CARD or CIRCLE')
            valid.append({**item,'id':ident,'first_frame':first,'end_frame':last})
        except (ValueError,TypeError,KeyError) as exc:notices.append(f'{path} skipped: {exc}.')
    return valid,notices

def destination(crop: QRectF,width: int,height: int,settings) -> QRectF:
    if settings.aspect_policy in {'FIT','BLUR_FILL'} or settings.aspect_policy is None and settings.framing=='Fit Entire Image':
        scale=min(width/crop.width(),height/crop.height())
        return QRectF((width-crop.width()*scale)/2,(height-crop.height()*scale)/2,crop.width()*scale,crop.height()*scale)
    return QRectF(0,0,width,height)

def map_box(box,image,crop,dest):
    x,y,w,h=box
    source=QRectF(x*image.width(),y*image.height(),w*image.width(),h*image.height())
    return QRectF(dest.x()+(source.x()-crop.x())*dest.width()/crop.width(),
                  dest.y()+(source.y()-crop.y())*dest.height()/crop.height(),
                  source.width()*dest.width()/crop.width(),source.height()*dest.height()/crop.height())

def circle_visible(moment,compositor,plan):
    image=compositor._image(plan.image_id);x,y,w,h=moment['box']
    box=QRectF(x*image.width(),y*image.height(),w*image.width(),h*image.height())
    # Check every frame because easing and focus clamping may peak between endpoints.
    return all(compositor._motion(plan,f,image).contains(box) for f in range(moment['first_frame'],moment['end_frame']))

def draw_circle(image,moment,frame,fps):
    x,y,w,h=moment['box']; rect=QRectF(x*image.width(),y*image.height(),w*image.width(),h*image.height())
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor('#FF3434'),max(2,image.width()*.004),Qt.SolidLine,Qt.RoundCap));p.setBrush(Qt.NoBrush)
    progress=min(1,(frame-moment['first_frame']+1)/max(1,round(.4*fps)))
    path=QPainterPath();path.arcMoveTo(rect,90);path.arcTo(rect,90,-360*progress);p.drawPath(path);p.end()

def draw_date(image,moment,frame,fps):
    fade=max(1,round(.15*fps));alpha=min(1,(frame-moment['first_frame']+1)/fade,(moment['end_frame']-frame)/fade)
    p=QPainter(image);p.setRenderHint(QPainter.TextAntialiasing);p.setOpacity(alpha)
    p.fillRect(image.rect(),QColor(0,0,0,round(255*moment.get('dim',.65))))
    font=QFont('Inter');font.setBold(True);font.setPixelSize(max(12,round(min(image.width()*.13,image.height()*.085))))
    p.setFont(font);p.setPen(QColor('#FFFFFF'))
    rect=QRectF(image.width()*.08,image.height()*.22,image.width()*.84,image.height()*.48)
    from PySide6.QtGui import QFontMetricsF
    while font.pixelSize()>12 and (QFontMetricsF(font).boundingRect(rect,Qt.AlignCenter|Qt.TextWordWrap,moment['text']).height()>rect.height()):
        font.setPixelSize(font.pixelSize()-2)
    p.setFont(font);p.drawText(rect,Qt.AlignCenter|Qt.TextWordWrap,moment['text']);p.end()
