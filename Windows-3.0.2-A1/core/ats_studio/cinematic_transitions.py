"""Frame-local Qt transitions: no external clips, extra duration, or Remotion."""
import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QLinearGradient, QRadialGradient

KINDS=frozenset({'BURN_LIGHT','TORN_CENTER_SPLIT','ZOOM_BLUR','FILM_FLASH',
    'LIGHT_LEAK','SMOKE_DISSOLVE','IRIS_REVEAL','INK_SPREAD','GLITCH_TRANSITION'})

def noise(seed,index):
    from .visual_director import unit
    return unit(seed,str(index))*2-1

def draw_transition(outgoing,incoming,kind,t,seed,settings):
    if t<=0:return outgoing.copy()
    if t>=1:return incoming.copy()
    w,h=incoming.width(),incoming.height()
    full=QRectF(0,0,w,h)
    out=QImage(w,h,QImage.Format_RGB888)
    out.fill(Qt.black)
    p=QPainter(out);p.setRenderHint(QPainter.Antialiasing);p.setRenderHint(QPainter.SmoothPixmapTransform)
    if kind=='TORN_CENTER_SPLIT':
        p.drawImage(full,incoming)
        # Two masks partition the SAME outgoing frame. Incoming fills every gap.
        rough=settings.torn_edge_intensity*w*.024
        left=QPainterPath();left.moveTo(-w,0)
        for i in range(33):
            y=h*i/32;edge=w/2+noise(seed,i)*rough
            left.lineTo(edge,y)
        left.lineTo(-w,h);left.closeSubpath()
        right=QPainterPath();right.addRect(full);right=right.subtracted(left)
        shift=(w/2+rough+2)*t
        for mask,offset in ((left,-shift),(right,shift)):
            p.save();p.translate(offset,0);p.setClipPath(mask)
            p.drawImage(full,outgoing);p.restore()
        if rough:
            p.setOpacity(.18*math.sin(math.pi*t));p.setPen(QColor('#F8E9D5'))
            for sign in (-1,1):
                for i in range(32):
                    p.drawLine(QPointF(w/2+noise(seed,i)*rough+sign*shift,h*i/32),
                               QPointF(w/2+noise(seed,i+1)*rough+sign*shift,h*(i+1)/32))
    elif kind in {'IRIS_REVEAL','INK_SPREAD','SMOKE_DISSOLVE','BURN_LIGHT'}:
        p.drawImage(full,outgoing)
        clip=QPainterPath()
        if kind=='IRIS_REVEAL':
            radius=math.hypot(w,h)*.501*t
            clip.addEllipse(QPointF(w*.5,h*.5),radius,radius)
        elif kind=='BURN_LIGHT':
            radius=math.hypot(w,h)*1.05*t
            clip.addEllipse(QPointF(w*.16,h*.48),radius,radius)
        else:
            # Deterministic organic reveal; overlapping circles grow without seams.
            for i in range(12):
                cx=(noise(seed,100+i)+1)*w/2;cy=(noise(seed,200+i)+1)*h/2
                radius=math.hypot(w,h)*t*(.5+(noise(seed,300+i)+1)*.16)
                clip.addEllipse(QPointF(cx,cy),radius,radius)
        p.setClipPath(clip);p.drawImage(full,incoming);p.setClipping(False)
        if kind=='BURN_LIGHT':
            radius=max(1,math.hypot(w,h)*1.05*t)
            gradient=QRadialGradient(QPointF(w*.16,h*.48),radius)
            alpha=round(220*settings.burn_intensity*math.sin(math.pi*t))
            gradient.setColorAt(0,QColor(255,100,12,0))
            gradient.setColorAt(.68,QColor(255,100,12,0))
            gradient.setColorAt(.82,QColor(255,111,15,alpha))
            gradient.setColorAt(.93,QColor(255,229,137,min(255,round(alpha*1.2))))
            gradient.setColorAt(1,QColor(255,123,30,0))
            p.fillRect(full,QBrush(gradient))
        elif kind=='SMOKE_DISSOLVE':
            p.setOpacity(.2*math.sin(math.pi*t))
            fog=incoming.scaled(max(2,w//15),max(2,h//15),Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
            p.drawImage(full,fog)
    elif kind=='ZOOM_BLUR':
        strength=math.sin(math.pi*t)
        for image,opacity,zoom in ((outgoing,1-t,1+.28*t),(incoming,t,1+.18*(1-t))):
            p.setOpacity(opacity)
            for i in range(4):
                z=zoom+strength*.018*i
                p.drawImage(QRectF((1-z)*w/2,(1-z)*h/2,w*z,h*z),image)
        p.setOpacity(1)
    elif kind=='GLITCH_TRANSITION':
        p.drawImage(full,outgoing);p.setOpacity(t);p.drawImage(full,incoming);p.setOpacity(1)
        amount=math.sin(math.pi*t)
        for i in range(10):
            y=h*i/10;sh=h/10
            shift=noise(seed,500+i+int(t*8))*w*.045*amount
            source=incoming if i%2 else outgoing
            p.drawImage(QRectF(shift,y,w,sh),source,QRectF(0,y,w,sh))
        p.fillRect(full,QColor(20,225,255,round(18*amount)))
    else:
        p.drawImage(full,outgoing);p.setOpacity(t);p.drawImage(full,incoming);p.setOpacity(1)
        if kind=='FILM_FLASH':
            flash=max(0,1-abs(t-.5)*3)
            p.fillRect(full,QColor(255,248,226,round(235*flash)))
        elif kind=='LIGHT_LEAK':
            gradient=QLinearGradient(w*(t-.2),0,w*(t+.25),h)
            alpha=round(155*settings.burn_intensity*math.sin(math.pi*t))
            gradient.setColorAt(0,QColor(255,90,10,0));gradient.setColorAt(.5,QColor(255,187,69,alpha));gradient.setColorAt(1,QColor(255,255,167,0))
            p.fillRect(full,QBrush(gradient))
    p.end()
    return out
