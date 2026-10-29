"""Focused 3.0.2 fixes over the verified installed 3.0.1 product baseline."""
from collections import OrderedDict
from pathlib import Path
import threading
from PySide6.QtCore import QThread, Signal, Qt, QSize, QRectF
from PySide6.QtGui import QImage, QImageReader, QPainter, QPainterPath, QColor, QPen, QKeySequence, QAction

_applied=False

class ThumbnailWorker(QThread):
    ready=Signal(int,str,object)
    def __init__(self):
        super().__init__();self.condition=threading.Condition();self.jobs=[];self.generation=0;self.stopping=False
    def configure(self,images):
        with self.condition:
            self.generation+=1;self.jobs=list(images.items());self.condition.notify_all();return self.generation
    def run(self):
        while True:
            with self.condition:
                while not self.jobs and not self.stopping:self.condition.wait()
                if self.stopping:return
                ident,path=self.jobs.pop(0);generation=self.generation
            reader=QImageReader(str(path));reader.setAutoTransform(True);size=reader.size()
            if size.isValid():reader.setScaledSize(size.scaled(256,144,Qt.KeepAspectRatio))
            image=reader.read()
            if not image.isNull():image=image.scaled(256,144,Qt.KeepAspectRatio,Qt.SmoothTransformation)
            self.ready.emit(generation,ident,image)
    def stop(self):
        from shiboken6 import isValid
        if not isValid(self):return
        with self.condition:self.stopping=True;self.jobs.clear();self.condition.notify_all()
        self.wait()

def apply():
    global _applied
    if _applied:return
    _applied=True
    from .ui_parts import dialogs, views
    from .ui_parts.common import ClickCombo
    from .product import FORMATS
    from .ui import MainWindow

    original_row=dialogs.AssetRow.present
    original_row_init=dialogs.AssetRow.__init__
    def row_init(self,*args,**kwargs):
        original_row_init(self,*args,**kwargs);self.detail.setFixedHeight(20);self.detail.setAlignment(Qt.AlignVCenter)
    dialogs.AssetRow.__init__=row_init
    def present(self,detail,filled=False):
        original_row(self,detail,filled)
        if self.paste:
            self.paste.setVisible(True);self.paste.setText('Repaste' if filled else 'Paste')
            self.paste.setToolTip('Paste or replace the complete script JSON at any time.')
    dialogs.AssetRow.present=present

    original_launch=dialogs.LaunchDialog.__init__
    def launch_init(self,parent=None,current=None,recents=()):
        original_launch(self,parent,current,recents)
        self.setWindowTitle('New project · Auto Timeline Sync 3.0.2')
        self.format_choice=ClickCombo(self);self.format_choice.setObjectName('canvasFormat')
        self.format_choice.addItem('Format: From script (Auto)',None)
        for key,(ratio,_) in FORMATS.items():
            self.format_choice.addItem(f'{ratio} {key.title()}',key)
        self.format_choice.setToolTip('Defaults to the script. An override changes only this project canvas; Fill/Fit controls cropping.')
        self.format_choice.setFixedWidth(258);self.format_choice.setFixedHeight(36)
        header=self.format_chip.parentWidget().layout().itemAt(0).layout()
        header.addWidget(self.format_choice);self.format_chip.hide()
        if current and current.overrides.get('orientation'):
            self.format_choice.setCurrentIndex(self.format_choice.findData(current.overrides['orientation']))
        self.format_choice.currentIndexChanged.connect(self.changed)
    dialogs.LaunchDialog.__init__=launch_init

    original_worker=dialogs.ImportWorker.__init__
    def import_init(self,project,parent=None):
        chooser=getattr(parent,'format_choice',None)
        if chooser and chooser.currentData():project.overrides['orientation']=chooser.currentData()
        original_worker(self,project,parent)
    dialogs.ImportWorker.__init__=import_init

    original_validated=dialogs.LaunchDialog.validated
    def validated(self,revision,project,spec):
        original_validated(self,revision,project,spec)
        if revision!=self.revision:return
        chooser=getattr(self,'format_choice',None)
        if chooser:
            chooser.setItemText(0,f'Format: {FORMATS[project.orientation][0]} · From script')
            self.format_chip.hide()
    dialogs.LaunchDialog.validated=validated

    def reconfigure(self):
        if self.spec:
            rect=self.frame_rect();dpr=max(1.,float(self.devicePixelRatioF()))
            # Render at physical display pixels; never enlarge a tiny logical-pixel frame.
            scale=min(dpr,1920/max(1.,rect.width(),rect.height()))
            width=max(2,round(rect.width()*scale));height=max(2,round(rect.height()*scale))
            self.generation=self.worker.configure(self.spec,self.images,self.settings,width,height,
                round(self.position*self.spec.package.fps),self.captions_visible)
    views.PreviewView.reconfigure=reconfigure
    original_preview_paint=views.PreviewView.paintEvent
    def preview_paint(self,event):
        # Baseline frame, circle interaction and safe zones are retained. Match the
        # image's physical sampling size so its own drawImage does not pixelate it.
        original_preview_paint(self,event)
        if self.image.isNull():return
        painter=QPainter(self);painter.setRenderHint(QPainter.SmoothPixmapTransform,True)
        rect=self.frame_rect();clip=QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()).adjusted(5,5,-5,-5) if self.device_frame else rect,
            15 if self.device_frame else 12,15 if self.device_frame else 12)
        painter.setClipPath(clip);painter.drawImage(rect,self.image)
        if self.safe_zones:
            painter.setPen(QPen(QColor(255,255,255,150),1,Qt.DashLine))
            painter.drawRect(QRectF(rect.x()+rect.width()*.083,rect.y()+rect.height()*.1,
                rect.width()*.834,rect.height()*.7))
        painter.end()
    views.PreviewView.paintEvent=preview_paint

    original_canvas=views.TimelineCanvas.__init__
    def canvas_init(self):
        original_canvas(self);self.thumbnails=OrderedDict();self.thumb_generation=0
        self.thumb_worker=ThumbnailWorker();self.thumb_worker.ready.connect(lambda g,i,image:thumb_ready(self,g,i,image));self.thumb_worker.start()
        worker=self.thumb_worker;self.destroyed.connect(lambda:worker.stop())
    def thumb_ready(canvas,generation,ident,image):
        if generation==canvas.thumb_generation and not image.isNull():
            canvas.thumbnails[ident]=image
            while len(canvas.thumbnails)>4096:canvas.thumbnails.popitem(last=False)
            canvas.update()
    views.TimelineCanvas.__init__=canvas_init
    original_project=views.TimelineView.set_project
    def set_project(self,project):
        original_project(self,project);self.canvas.thumbnails.clear()
        self.canvas.thumb_generation=self.canvas.thumb_worker.configure(project.images)
    views.TimelineView.set_project=set_project
    original_canvas_paint=views.TimelineCanvas.paintEvent
    def canvas_paint(self,event):
        original_canvas_paint(self,event)
        if not self.project:return
        painter=QPainter(self);painter.setRenderHint(QPainter.SmoothPixmapTransform,True)
        y,height=self.row_positions()[0];pkg=self.project.package
        scale=self.width()/max(.001,pkg.total_frames/pkg.fps)
        for scene in pkg.scenes:
            image=self.thumbnails.get(scene.image_id)
            if image is None:continue
            left=scene.first_frame/pkg.fps*scale;width=max(1,scene.frame_count/pkg.fps*scale-2)
            dest=QRectF(left,y,width,height);source=QRectF(image.rect())
            painter.save();clip=QPainterPath();clip.addRoundedRect(dest,3,3);painter.setClipPath(clip)
            tile_width=max(8.,height*image.width()/max(1,image.height()))
            tile_left=left
            while tile_left<left+width:
                painter.drawImage(QRectF(tile_left,y,tile_width,height),image,source);tile_left+=tile_width
            painter.restore()
        painter.setPen(QPen(QColor('#FFFFFF'),1));x=self.position*scale;painter.drawLine(x,0,x,self.height());painter.end()
    views.TimelineCanvas.paintEvent=canvas_paint

    original_window=MainWindow.__init__
    def window_init(self,*args,**kwargs):
        original_window(self,*args,**kwargs)
        for action in self.findChildren(QAction):
            if action.text().startswith('Import'):
                action.setShortcuts([QKeySequence('Ctrl+I'),QKeySequence('Ctrl+N')]);break
    MainWindow.__init__=window_init
    original_mix_finished=MainWindow.mix_finished
    def mix_finished(self,worker):
        if self.closing or not self.work.is_dir():
            if self.mix_worker is worker:self.mix_worker=None
            worker.deleteLater();return
        original_mix_finished(self,worker)
    MainWindow.mix_finished=mix_finished
    original_close=MainWindow.closeEvent
    def close(self,event):
        original_close(self,event)
        if event.isAccepted():self.timeline.canvas.thumb_worker.stop()
    MainWindow.closeEvent=close

    from . import pro_renderer
    from .fast_export import export_pro_video
    pro_renderer.export_pro_video=export_pro_video
    from . import pro_audio
    from .fast_export import master_preview_audio
    pro_audio.master_preview_audio=master_preview_audio
