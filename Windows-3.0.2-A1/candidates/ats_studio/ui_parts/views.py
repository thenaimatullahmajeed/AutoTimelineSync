"""One Pro preview path and a view/seek-only timeline."""
import math
from pathlib import Path
from PySide6.QtCore import Signal, Qt, QRectF, QTimer
from PySide6.QtGui import QPainter,QColor,QPen,QImage,QFont,QPainterPath,QImageReader
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout
from ..moments import validate_moments,destination
from .workers import ProPreviewWorker
from .common import ClickSlider,label,human_time,pixel_font,text_label

class PreviewView(QWidget):
    moment_changed=Signal(str,object);failed=Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent);self.setMinimumSize(160,100);self.image=QImage();self.spec=None;self.settings=None;self.images={};self.position=0;self.safe_zones=False;self.captions_visible=True;self.generation=0;self.drag=None;self.device_frame=True
        self.worker=ProPreviewWorker();self.worker.frame_ready.connect(self.frame_ready);self.worker.start();self.resize_timer=QTimer(self);self.resize_timer.setSingleShot(True);self.resize_timer.setInterval(120);self.resize_timer.timeout.connect(self.reconfigure)
        self.setToolTip('Alt+drag moves a script circle; Alt+Shift+drag sets its source-image box.')
    def configure_pro(self,spec,images,settings):self.spec,self.images,self.settings=spec,images,settings;self.reconfigure()
    def reconfigure(self):
        if self.spec:
            rect=self.frame_rect();w=max(1,round(rect.width()));h=max(1,round(rect.height()))
            self.generation=self.worker.configure(self.spec,self.images,self.settings,w,h,round(self.position*self.spec.package.fps),self.captions_visible)
    def resizeEvent(self,event):super().resizeEvent(event);self.resize_timer.start()
    def set_position(self,seconds):
        self.position=seconds
        if self.spec:self.worker.request(round(seconds*self.spec.package.fps))
    def frame_ready(self,generation,frame,image):
        if generation==self.generation:
            if image.isNull():self.failed.emit('Preview frame could not be rendered.')
            else:self.image=image
            self.update()
    def frame_rect(self):
        if self.device_frame:return QRectF(self.rect()).adjusted(5,5,-5,-5)
        ratio=self.settings.width/self.settings.height if self.settings else 9/16
        padding=10 if self.device_frame else 24
        w=min(max(1,self.width()-padding),max(1,self.height()-padding)*ratio);h=w/ratio
        return QRectF((self.width()-w)/2,(self.height()-h)/2,w,h)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);rect=self.frame_rect()
        if self.device_frame:
            p.setPen(QPen(QColor('#232830'),5));p.setBrush(QColor('#0E1013'));p.drawRoundedRect(QRectF(self.rect()).adjusted(2.5,2.5,-2.5,-2.5),17.5,17.5)
        if self.image.isNull():
            p.setFont(pixel_font(13,400));p.setPen(QColor('#8B93A1'));p.drawText(QRectF(self.rect()).adjusted(24,24,-24,-24),Qt.AlignCenter|Qt.TextWordWrap,'Create a timeline to preview');p.end();return
        path=QPainterPath();path.addRoundedRect(QRectF(self.rect()).adjusted(5,5,-5,-5) if self.device_frame else rect,15 if self.device_frame else 12,15 if self.device_frame else 12);p.setClipPath(path);p.drawImage(rect,self.image)
        if self.safe_zones:
            safe=QRectF(rect.x()+rect.width()*.083,rect.y()+rect.height()*.1,rect.width()*.834,rect.height()*.7)
            p.setPen(QPen(QColor(255,255,255,150),1,Qt.DashLine));p.drawRect(safe)
        p.end()
    def source_point(self,point):
        if not self.spec:return None
        frame=round(self.position*self.spec.package.fps);plan=next((s for s in self.spec.scenes if s.first_frame<=frame<s.end_frame),None)
        if not plan:return None
        from ..pro_compositor import ProCompositor
        comp=ProCompositor(self.spec,self.images,self.settings,cache_limit_bytes=64*1024**2);image=comp._image(plan.image_id)
        crop=comp._motion(plan,frame,image);dest=destination(crop,self.settings.width,self.settings.height,self.settings);rect=self.frame_rect()
        x=(point.x()-rect.x())/rect.width()*self.settings.width;y=(point.y()-rect.y())/rect.height()*self.settings.height
        return plan,((crop.x()+(x-dest.x())/dest.width()*crop.width())/image.width(),(crop.y()+(y-dest.y())/dest.height()*crop.height())/image.height())
    def mousePressEvent(self,event):
        if event.modifiers() & Qt.AltModifier:
            result=self.source_point(event.position())
            if result:
                plan,point=result;moments,_=validate_moments(self.spec.package);frame=round(self.position*self.spec.package.fps)
                m=next((m for m in moments if m['type']=='CIRCLE' and m['scene_id']==plan.id and m['first_frame']<=frame<m['end_frame']),None)
                if m:
                    box=self.spec.package.pro.get('moment_overrides',{}).get(m['id'],m['box']);self.drag=(m['id'],point,box,bool(event.modifiers() & Qt.ShiftModifier))
                    event.accept();return
        super().mousePressEvent(event)
    def mouseReleaseEvent(self,event):
        if self.drag:
            result=self.source_point(event.position());ident,start,box,resize=self.drag;self.drag=None
            if result:
                _,end=result
                if resize:x,y=min(start[0],end[0]),min(start[1],end[1]);w,h=abs(end[0]-start[0]),abs(end[1]-start[1])
                else:x,y=box[0]+end[0]-start[0],box[1]+end[1]-start[1];w,h=box[2:]
                if w>=.03 and h>=.03 and w*h<=.2 and x>=0 and y>=0 and x+w<=1 and y+h<=1:self.moment_changed.emit(ident,[x,y,w,h])
            return
        super().mouseReleaseEvent(event)
    def shutdown(self):self.resize_timer.stop();self.worker.stop()

class TimelineCanvas(QWidget):
    seek_requested=Signal(float)
    def __init__(self):super().__init__();self.project=None;self.position=0;self.waveforms={};self.seams=[];self.setMinimumHeight(142)
    def mousePressEvent(self,event):
        if self.project:self.seek_requested.emit(max(0,min(1,event.position().x()/max(1,self.width())))*self.project.package.audio_duration)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        if not self.project:p.setPen(QColor('#8190A2'));p.drawText(self.rect(),Qt.AlignCenter,'Your timeline appears here');p.end();return
        pkg=self.project.package;duration=pkg.total_frames/pkg.fps;scale=self.width()/max(.001,duration);rows=[(25,24),(53,10),(70,16),(92,18),(118,18)]
        p.setPen(QColor('#8190A2'));font=QFont('Inter',9);p.setFont(font)
        for i in range(8):
            x=i*self.width()/7;p.drawText(QRectF(min(x,self.width()-40),0,44,20),Qt.AlignLeft,human_time(duration*i/7))
        for index,scene in enumerate(pkg.scenes):
            x=scene.first_frame/pkg.fps*scale;w=scene.frame_count/pkg.fps*scale-1;p.setPen(Qt.NoPen);p.setBrush(QColor(['#3A5550','#364453','#494457'][index%3]));p.drawRoundedRect(QRectF(x,25,max(1,w),24),3,3)
        p.setBrush(QColor('#6555A6'))
        for c in pkg.captions:p.drawRoundedRect(QRectF(c.start*scale,53,max(1,(c.end-c.start)*scale-1),10),3,3)
        moments=getattr(self,'moments',validate_moments(pkg)[0])
        for m in moments:
            x=m['first_frame']/pkg.fps*scale;p.setPen(QColor('#D4D8E0'));p.setBrush(QColor('#DAAF24') if m['type']=='DATE_CARD' else QColor('#FF3434'));p.drawEllipse(x,72,7,7)
        for key,y,color in [('voice',92,'#91A4B9'),('music',118,'#736DBB')]:
            values=self.waveforms.get(key,[]);p.setPen(QPen(QColor(color),2))
            if values:
                for i,value in enumerate(values):x=i/max(1,len(values)-1)*self.width();p.drawLine(x,y+9-value*8,x,y+9+value*8)
            else:p.drawLine(0,y+9,self.width(),y+9)
        p.setPen(QPen(QColor('#7B85A0'),1,Qt.DashLine))
        for seam in self.seams:p.drawLine(seam*scale,117,seam*scale,137)
        x=self.position*scale;p.setPen(QPen(QColor('#FFFFFF'),1));p.drawLine(x,20,x,self.height());p.end()

class TimelineView(QWidget):
    seek_requested=Signal(float);gain_changed=Signal(str,float)
    def __init__(self,parent=None):
        super().__init__(parent);root=QVBoxLayout(self);root.setContentsMargins(24,8,24,8);root.setSpacing(4)
        self.summary=label('Timeline',True);root.addWidget(self.summary);row=QHBoxLayout();row.setSpacing(16);headers=QWidget();headers.setFixedWidth(128);g=QGridLayout(headers);g.setContentsMargins(0,0,0,0);g.setVerticalSpacing(5)
        for i,title in enumerate(['Images','Captions','Moments']):g.addWidget(label(title,True),i,0,1,2)
        self.gains={};self.values={}
        for i,(title,key) in enumerate([('Voice','voice_volume'),('Music','music_volume')],3):
            titlelabel=label(title,True);g.addWidget(titlelabel,i,0);value=label('100%',True);self.values[key]=value;g.addWidget(value,i,1)
            slider=ClickSlider();slider.setRange(0,100);slider.setFixedWidth(76);slider.valueChanged.connect(lambda value,key=key:self.gain_changed.emit(key,value/100));self.gains[key]=slider;g.addWidget(slider,i+2,0,1,2)
        # Align headers and separate sliders from canvas lanes with explicit positions.
        for w in headers.findChildren(QWidget):w.setMinimumHeight(0)
        self.canvas=TimelineCanvas();self.canvas.seek_requested.connect(self.seek_requested.emit);row.addWidget(headers);row.addWidget(self.canvas,1);root.addLayout(row)
    def set_project(self,project):
        self.canvas.project=project;self.canvas.waveforms={};self.canvas.seams=[]
        self.summary.setText(f'Timeline  ·  {len(project.package.scenes)} scenes  ·  {human_time(project.package.audio_duration)}' + ('  ·  Music repeats automatically' if project.music else ''));self.canvas.update()
    def set_settings(self,settings):
        for key,s in self.gains.items():s.blockSignals(True);value=round(getattr(settings,key)*100);s.setValue(value);s.blockSignals(False);self.values[key].setText(f'{value}%')
    def set_position(self,seconds):self.canvas.position=seconds;self.canvas.update()
