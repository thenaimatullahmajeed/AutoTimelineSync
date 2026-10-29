"""Six measured, scalable caption styles used by the shared Qt compositor."""
from __future__ import annotations
import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen

PROFILES={
    'Hormozi Style':dict(font='Montserrat',size=86,weight=QFont.ExtraBold,accent='#FFE600',stroke=7,shadow=.35,animation='POP',caps=True),
    'MrBeast / Viral Pop':dict(font='Luckiest Guy',size=88,weight=QFont.Bold,accent='#FF2D2D',stroke=9,shadow=.65,animation='BOUNCE',caps=True),
    'Karaoke Highlight':dict(font='Poppins',size=78,weight=QFont.Black,accent='#8A2BE2',stroke=0,shadow=.25,animation='NONE',caps=False),
    'Neon Glow':dict(font='Bebas Neue',size=86,weight=QFont.Bold,accent='#00F0FF',stroke=0,shadow=0,animation='FADE_SCALE',caps=True),
    'Minimal Cinematic':dict(font='Inter',size=60,weight=QFont.DemiBold,accent='#FFFFFF',stroke=0,shadow=.5,animation='FADE_UP',caps=False),
    'Highlighter Box':dict(font='Montserrat',size=78,weight=QFont.Bold,accent='#FFE600',stroke=0,shadow=.15,animation='POP',caps=False),
}
NEW_CAPTION_PRESETS=tuple(PROFILES)

def render_caption(image,caption,frame,fps,preset,settings,active,emphasized=(),cache=None):
    profile=PROFILES[preset];w,h=image.width(),image.height()
    portrait=h>w
    scale=min(w/1080,h/1920) if portrait else min(w/1920,h/1080)
    scale=max(.06,scale)
    font=QFont(settings.caption_font if settings.caption_font not in {'Arial','Segoe UI'} else profile['font'])
    from .fonts import resolve_font_family
    font.setFamily(resolve_font_family(font.family()))
    font.setWeight(profile['weight'])
    tokens=caption.text.split()
    if profile['caps']:tokens=[token.upper() for token in tokens]
    if not tokens:return
    available=w*(1-2*max(90/1080,settings.caption_safe_margin/100))
    size=max(12*scale,profile['size']*scale*settings.caption_size/100)
    key=(tuple(tokens),w,h,size,settings.caption_font,preset,settings.caption_max_lines)
    cached=cache.get(key) if cache is not None else None
    if cached is None:
        best=None
        for _ in range(32):
            font.setPixelSize(max(1,round(size)));metrics=QFontMetricsF(font)
            widths=[metrics.horizontalAdvance(token) for token in tokens];gap=metrics.horizontalAdvance(' ')
            if settings.caption_max_lines==2 and len(tokens)>1:
                split=min(range(1,len(tokens)),key=lambda i:max(sum(widths[:i])+gap*(i-1),sum(widths[i:])+gap*(len(tokens)-i-1)))
                lines=[list(range(split)),list(range(split,len(tokens)))]
                if sum(widths)+gap*(len(tokens)-1)<=available:lines=[list(range(len(tokens)))]
            else:lines=[list(range(len(tokens)))]
            longest=max(sum(widths[i] for i in line)+gap*(len(line)-1) for line in lines)
            if longest<=available or size<=10*scale:break
            size*=.92
        items=[];line_h=metrics.height()*1.12
        for row,line in enumerate(lines):
            line_w=sum(widths[i] for i in line)+gap*(len(line)-1)
            x=(w-line_w)/2
            for i in line:
                path=QPainterPath();path.addText(QPointF(x,row*line_h+metrics.ascent()),font,tokens[i])
                items.append((i,path,QRectF(x,row*line_h,widths[i],metrics.height())))
                x+=widths[i]+gap
        text_h=line_h*len(lines)
        cached=(items,text_h,size)
        if cache is not None:
            cache[key]=cached
            while len(cache)>96:cache.popitem(last=False)
    items,text_h,size=cached
    # Creator presets default to 63%: above the platform controls.
    if settings.caption_position=='Custom':center=h*settings.caption_custom_y/100
    elif settings.caption_position=='Top':center=h*.23
    elif settings.caption_position=='Center':center=h*.5
    else:center=h*(.63 if portrait else .78)
    y=max(h*.08,min(center-text_h/2,h*.80-text_h if portrait else h*.92-text_h))
    age=(frame-caption.start_frame)/fps
    active_age=next(((frame-start)/fps for i,(start,end,text) in enumerate(caption.words) if i==active),age)
    animation=profile['animation']
    t=max(0,min(1,active_age/.12))
    factor=1;opacity=1;dy=0;rotation=0
    if animation in {'POP','BOUNCE'} and t<1:
        factor=(.8+.3*(t/.55)) if t<.55 else (1.1-.1*((t-.55)/.45))
        if animation=='BOUNCE':rotation=3*math.sin(t*math.pi*2)*(1-t)
    elif animation in {'FADE_UP','FADE_SCALE'}:
        fade=max(0,min(1,age/.2));opacity=fade
        if animation=='FADE_UP':dy=(1-fade)*14*scale
        else:factor=.96+.04*fade
    accent=QColor(settings.caption_highlight_color or profile['accent'])
    white=QColor(settings.caption_text_color)
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);p.setRenderHint(QPainter.TextAntialiasing)
    p.setOpacity(opacity);p.translate(w/2,y+text_h/2+dy);p.rotate(rotation);p.scale(factor,factor);p.translate(-w/2,-text_h/2)
    pad=10*scale
    if preset=='Highlighter Box':
        bounds=QRectF()
        for i,path,rect in items:bounds=bounds.united(rect)
        p.setPen(Qt.NoPen);p.setBrush(QColor('#FFFFFF'));p.drawRoundedRect(bounds.adjusted(-pad,-pad,pad,pad),8*scale,8*scale)
    for i,path,rect in items:
        selected=(i==active)
        emphasis=(i in emphasized)
        if preset=='Karaoke Highlight' and selected:
            p.setPen(Qt.NoPen);p.setBrush(accent);p.drawRoundedRect(rect.adjusted(-pad/2,-pad/3,pad/2,pad/3),7*scale,7*scale)
        if preset=='Highlighter Box' and selected:
            p.setPen(Qt.NoPen);p.setBrush(accent);p.drawRoundedRect(rect.adjusted(-pad/2,-pad/3,pad/2,pad/3),6*scale,6*scale)
        if preset=='Neon Glow':
            for width,alpha in ((32,12),(24,20),(16,34),(8,65)):
                glow=QColor(accent);glow.setAlpha(alpha)
                p.setBrush(Qt.NoBrush);p.setPen(QPen(glow,width*scale,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path)
        shadow=profile['shadow'] if settings.caption_shadow_on else 0
        if shadow:
            p.save();p.translate(3*scale,4*scale);p.setBrush(QColor(0,0,0,min(255,round(255*shadow*settings.caption_shadow/40))))
            p.setPen(QPen(QColor(0,0,0,round(80*shadow)),6*scale,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawPath(path);p.restore()
        if preset=='Highlighter Box':fill=QColor('#080808')
        elif preset=='Karaoke Highlight':fill=white if selected else QColor(255,255,255,102)
        elif preset in {'Neon Glow','Minimal Cinematic'}:fill=white
        else:fill=accent if selected or emphasis else white
        stroke=profile['stroke']*scale*(settings.caption_outline/60) if settings.caption_outline_on else 0
        p.setPen(QPen(QColor('#000000'),stroke*2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin) if stroke else Qt.NoPen)
        p.setBrush(fill);p.drawPath(path)
        if stroke:p.fillPath(path,fill)
    p.end()
