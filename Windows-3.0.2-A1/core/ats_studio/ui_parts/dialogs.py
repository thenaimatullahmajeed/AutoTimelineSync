"""Transactional launch/import and focused export dialogs."""
from pathlib import Path
import json
import time
from dataclasses import replace
from datetime import datetime,date
from PySide6.QtCore import QThread, Signal, QTimer, Qt, QPropertyAnimation, QEasingCurve,QSize,QPoint
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLineEdit,QPlainTextEdit,QLabel,
    QFileDialog,QDialogButtonBox,QProgressBar,QMessageBox,QApplication,QPushButton,QSizePolicy,QGraphicsDropShadowEffect)
from PySide6.QtGui import QColor
from ..product import Project, FORMATS, StageETA
from ..pro_spec import build_spec
from .common import Dialog,button,label,scroll,ClickCombo,human_time,reduced_motion,text_label,IconTile,ghost,Segmented,svg_icon
from .workers import ExportWorker

class ImportWorker(QThread):
    ready=Signal(object,object);failed=Signal(str)
    def __init__(self,project,parent=None):super().__init__(parent);self.project=project
    def run(self):
        try:
            p=self.project.validate();spec=build_spec(p.effective_package(),p.images,p.settings())
            from ..pro_audio import choose_cues
            choose_cues(spec,0,p.package.pro.get('direction',{}).get('sfx_enabled',True))
            if not self.isInterruptionRequested():self.ready.emit(p,spec)
        except Exception as exc:
            if not self.isInterruptionRequested():self.failed.emit(str(exc))

class AssetRow(QWidget):
    def __init__(self,key,title,callback,paste=None):
        super().__init__();self.key=key;self.setObjectName('rowCard');self.setFixedHeight(70);self.setAttribute(Qt.WA_StyledBackground,True)
        h=QHBoxLayout(self);h.setContentsMargins(17,13,17,13);h.setSpacing(14)
        h.addWidget(IconTile({'narration':'audio','image_folder':'images','script':'json','music':'music'}[key]))
        v=QVBoxLayout();v.setAlignment(Qt.AlignVCenter);v.setSpacing(2);v.setContentsMargins(0,0,0,0);t=QHBoxLayout();t.setSpacing(10);t.addWidget(text_label(title,15,700,height=18))
        if key=='music':
            optional=text_label('Optional',11,700,'#8B93A1',20);optional.setObjectName('chip');optional.setStyleSheet('background:transparent;color:#8B93A1;border:1px solid #2A303A;border-radius:10px;padding:2px 9px;font-size:11px;font-weight:700;');t.addWidget(optional)
        t.addStretch();v.addLayout(t)
        self.detail=text_label({'narration':'Choose a file...','image_folder':'Choose a folder...','script':'Choose a file or paste...','music':'Choose a file...'}[key],13,400,'#8B93A1',16);self.detail.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);v.addWidget(self.detail);h.addLayout(v,1)
        self.ready=text_label('✓  Ready',13,700,'#2DD4BF');self.ready.hide();h.addWidget(self.ready)
        self.choose=button('Choose',callback);self.choose.setStyleSheet('font-size:14px;padding:0 18px;');h.addWidget(self.choose)
        self.paste=button('Paste',paste) if paste else None
        if self.paste:self.paste.setStyleSheet('font-size:14px;padding:0 18px;');h.addWidget(self.paste)
    def present(self,detail,filled=False):
        self.detail.setText(detail);self.detail.setToolTip(detail);self.ready.setVisible(filled);self.choose.setText('Replace' if filled else 'Choose')
        self.choose.setProperty('ghost',filled);self.choose.setStyleSheet('background:transparent;color:#8B93A1;font-size:13px;padding:0 8px;' if filled else 'background:#232830;color:#E8EAED;font-size:14px;padding:0 18px;')
        if self.paste:self.paste.setVisible(not filled)

class LaunchDialog(Dialog):
    def __init__(self,parent=None,current=None,recents=()):
        super().__init__(parent);self.setObjectName('launchDialog');self.setWindowTitle('New project · Auto Timeline Sync 3.0');self.resize(960,570)
        self.setMinimumSize(600,420);self.result_project=None;self.spec=None;self.worker=None;self.revision=0;self.validated_revision=-1;self.error=''
        root=QHBoxLayout(self);root.setContentsMargins(1,1,1,1);root.setSpacing(0)
        self.sidebar=QWidget();self.sidebar.setObjectName('launchSidebar');self.sidebar.setFixedWidth(240);r=QVBoxLayout(self.sidebar);r.setContentsMargins(16,24,16,24);r.setSpacing(6)
        brand=QWidget();b=QHBoxLayout(brand);b.setContentsMargins(12,0,12,16);b.setSpacing(10);b.addWidget(IconTile('logo',28,28,False));name=text_label('Auto Timeline\nSync',16,700);b.addWidget(name,1);r.addWidget(brand)
        recent_header=text_label('RECENT',12,700,'#8B93A1');recent_header.setContentsMargins(12,0,12,6);r.addWidget(recent_header)
        for path in recents[:5]:
            entry=QPushButton();entry.setFixedHeight(52);entry.setToolTip(path);entry.clicked.connect(lambda checked=False,path=path:self.open_project(path));entry.setStyleSheet('QPushButton{'+('background:#1A1F27;border:0;border-radius:10px;padding:0;' if path==recents[0] else 'background:transparent;border:0;padding:0;')+'min-height:52px;max-height:52px;}')
            e=QVBoxLayout(entry);e.setContentsMargins(12,10,12,10);e.setSpacing(2);recent_title=Path(path).stem;recent_detail=''
            try:
                saved=json.loads(Path(path).read_text(encoding='utf-8'));recent_title=saved.get('name',recent_title);duration=json.loads(saved.get('script','{}')).get('audio_duration',0)
                modified=datetime.fromtimestamp(Path(path).stat().st_mtime).date();days=(date.today()-modified).days;recent_detail='Today' if days==0 else 'Yesterday' if days==1 else modified.strftime('%b %d').replace(' 0',' ')
                if duration and path==recents[0]:recent_detail+=' · '+human_time(duration)
            except (OSError,ValueError,TypeError):pass
            e.addWidget(text_label(recent_title,14,700 if path==recents[0] else 500,height=16))
            e.addWidget(text_label(recent_detail,12,400,'#8B93A1',14));r.addWidget(entry)
        r.addStretch();open_button=ghost('Open project...',self.open_project,14,12);open_button.setStyleSheet('background:transparent;color:#8B93A1;text-align:left;font-size:14px;padding:0 12px;');r.addWidget(open_button);root.addWidget(self.sidebar)
        body=QWidget();v=QVBoxLayout(body);v.setContentsMargins(32,28,32,28);v.setSpacing(12)
        header=QHBoxLayout();header.addWidget(text_label('New project',24,800,height=29));header.addStretch();self.format_chip=text_label('',11,700,'#C9CFD8');self.format_chip.setObjectName('chip');self.format_chip.setStyleSheet('background:transparent;color:#C9CFD8;border:1px solid #2A303A;border-radius:10px;padding:2px 9px;font-size:11px;font-weight:700;');self.format_chip.hide();header.addWidget(self.format_chip);v.addLayout(header)
        self.format_chip.setFixedHeight(20)
        self.name=QLineEdit(current.name if current else 'Untitled project');self.name.setPlaceholderText('Project name');self.name.setFixedHeight(44);self.name.setStyleSheet('font-size:14px;min-height:42px;max-height:42px;');v.addWidget(self.name)
        self.fields={}
        self.rows={}
        for key,title in [('narration','Narration audio'),('image_folder','Numbered images'),('script','Script JSON'),('music','Background music')]:
            edit=QLineEdit(self);edit.setReadOnly(True);edit.hide();self.fields[key]=edit
            row=AssetRow(key,title,lambda checked=False,key=key:self.choose(key),self.paste_json if key=='script' else None);self.rows[key]=row;v.addWidget(row)
        self.script_text=current.script if current else '';self.source_name='Pasted JSON' if self.script_text else ''
        self.summary=text_label('Choose narration, numbered images and a script. Music is optional.',14,400,'#8B93A1',17);v.addWidget(self.summary)
        self.copy=button('Copy for ChatGPT',self.copy_error);self.copy.hide();v.addWidget(self.copy)
        footer=QWidget();actions=QHBoxLayout(footer);actions.setContentsMargins(0,6,0,0);actions.setSpacing(12);actions.addStretch();actions.addWidget(ghost('Cancel',self.reject));self.create=button('Create Timeline',self.accept_project,True);self.create.setFixedHeight(52);self.create.setStyleSheet('font-size:16px;min-height:52px;max-height:52px;padding:0 40px;');self.create.setEnabled(False);actions.addWidget(self.create);v.addWidget(footer)
        root.addWidget(scroll(body),1)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(250);self.timer.timeout.connect(self.validate_async)
        if current:
            for key in ('narration','image_folder','music'):self.fields[key].setText(getattr(current,key))
            self.fields['script'].setText(self.source_name)
        for edit in self.fields.values():edit.textChanged.connect(self.changed)
        self.name.textChanged.connect(self.changed)
        if current:self.changed()

    def set_field(self,key,value):self.fields[key].setText(value)
    def choose(self,key):
        if key=='image_folder':path=QFileDialog.getExistingDirectory(self,'Numbered images')
        else:
            filters='JSON (*.json)' if key=='script' else 'Audio (*.mp3 *.wav *.m4a *.flac)'
            path,_=QFileDialog.getOpenFileName(self,'Choose '+key,'',filters)
        if not path:return
        if key=='script':
            try:self.script_text=Path(path).read_text(encoding='utf-8');self.source_name=path
            except Exception as exc:self.show_error(str(exc));return
            self.script_name()
        self.set_field(key,path)

    def paste_json(self):
        dialog=Dialog(self);dialog.setWindowTitle('Paste script JSON');dialog.resize(640,400);layout=QVBoxLayout(dialog)
        text=QPlainTextEdit(self.script_text or QApplication.clipboard().text());layout.addWidget(text)
        box=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);box.accepted.connect(dialog.accept);box.rejected.connect(dialog.reject);layout.addWidget(box)
        if dialog.exec()==Dialog.Accepted:
            self.script_text=text.toPlainText();self.source_name='Pasted JSON';self.fields['script'].setText(self.source_name);self.changed()
            self.script_name()

    def script_name(self):
        if self.name.text()=='Untitled project':
            try:self.name.setText(json.loads(self.script_text).get('project_title','Untitled project'))
            except (ValueError,AttributeError):pass

    def changed(self):
        self.revision+=1;self.create.setEnabled(False);self.copy.hide();self.format_chip.hide();self.present_rows();self.timer.start()

    def present_rows(self,project=None):
        for key,row in self.rows.items():
            path=self.fields[key].text()
            if not path:
                row.present({'narration':'Choose a file...','image_folder':'Choose a folder...','script':'Choose a file or paste...','music':'Choose a file...'}[key],False)
                continue
            detail=Path(path).name;filled=bool(path)
            if project:
                p=project.package
                if key=='narration':detail=f'{Path(path).name} · {human_time(p.audio_duration)} · {Path(path).stat().st_size/1024**2:.1f} MB'
                elif key=='image_folder':ids=list(project.images);detail=f'{len(ids)} images · {ids[0]} to {ids[-1]}'
                elif key=='script':detail=f'{p.schema_version} · {len(p.scenes)} scenes · {len(p.captions)} captions'
                elif key=='music' and Path(path).is_file():
                    from ..media import probe_audio
                    from ..music import loop_seams
                    duration=probe_audio(Path(path))[0];loops=1+len(loop_seams(duration,p.audio_duration));detail=f'{Path(path).name} · {human_time(duration)} · repeats {loops}x to fit {human_time(p.audio_duration)}'
            row.present(detail,filled)

    def validate_async(self):
        if self.worker and self.worker.isRunning():self.worker.requestInterruption();return
        if not self.script_text or not self.fields['narration'].text() or not self.fields['image_folder'].text():return
        project=Project(self.name.text().strip() or 'Untitled project',self.fields['narration'].text(),self.fields['image_folder'].text(),self.script_text,self.fields['music'].text())
        revision=self.revision;self.summary.setText('Checking files and preparing your timeline…')
        self.worker=ImportWorker(project,self);worker=self.worker
        worker.ready.connect(lambda p,s:self.validated(revision,p,s));worker.failed.connect(self.show_error)
        worker.finished.connect(lambda:self.worker_finished(worker,revision));worker.start()

    def worker_finished(self,worker,revision):
        if self.worker is worker:self.worker=None
        worker.deleteLater()
        if revision!=self.revision and self.isVisible():self.timer.start()

    def validated(self,revision,project,spec):
        if revision!=self.revision:return
        self.result_project,self.spec=project,spec;self.validated_revision=revision
        self.summary.setWordWrap(False);self.summary.setFixedHeight(17)
        p=project.package;self.summary.setText(f'✓  All files match: {len(p.scenes)} scenes, {len(project.images)} images, audio {human_time(p.audio_duration)}');self.summary.setStyleSheet('background:transparent;color:#2DD4BF;font-size:13px;font-weight:500;')
        self.present_rows(project);self.format_chip.setText(f'Format: {FORMATS[project.orientation][0]} {project.orientation.title()} - from script');self.format_chip.show()
        self.create.setEnabled(True);self.copy.hide()

    def show_error(self,message):
        self.error=f'ATS 3.0 import error\nJSON: {self.source_name or "not selected"}\n{message}\nExpected: one ATS_PACKAGE_V2 object matching the final narration and numbered images. Fix the identified path; return the complete corrected package.'
        self.summary.setText(message);self.summary.setWordWrap(True);self.summary.setMaximumHeight(100);self.summary.setMinimumHeight(18);self.summary.setStyleSheet('color:#FF6B6B;background:transparent;');self.copy.show();self.create.setEnabled(False)

    def copy_error(self):QApplication.clipboard().setText(self.error)
    def accept_project(self):
        if self.validated_revision==self.revision and self.result_project:self.accept()

    def open_project(self,path=None):
        if isinstance(path,bool) or not path:path,_=QFileDialog.getOpenFileName(self,'Open ATS 3 project','','ATS project (*.ats3)')
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding='utf-8'))
            if data.get('project_format')!=2:raise ValueError('Expected an ATS 3.0 project (project_format 2).')
            project=Project.load(path)
            self.result_project=project;self.spec=build_spec(project.effective_package(),project.images,project.settings());self.accept()
        except Exception as exc:self.show_error(str(exc))

    def done(self,result):
        self.timer.stop()
        if self.worker and self.worker.isRunning():self.worker.requestInterruption();self.worker.wait()
        super().done(result)

class ExportDialog(Dialog):
    def __init__(self,project,parent=None):
        super().__init__(parent);self.project=project;self.worker=None;self.started=0;self.eta=StageETA();self.result=None
        self.setWindowFlag(Qt.FramelessWindowHint,True);self.setAttribute(Qt.WA_TranslucentBackground,True)
        self.setObjectName('exportDialog');self.setWindowTitle('Export video');self.resize(640,748);self.setMinimumSize(520,480)
        box=QWidget();v=QVBoxLayout(box);v.setContentsMargins(33,29,33,29);v.setSpacing(14)
        header=QHBoxLayout();header.addWidget(text_label('Export video',22,800));header.addStretch();close=ghost('',self.reject,13,0);close.setFixedSize(44,44);close.setIcon(svg_icon('close'));close.setIconSize(QSize(20,20));header.addWidget(close);v.addLayout(header);p=project.package
        self.project_card=QWidget();self.project_card.setObjectName('rowCard');self.project_card.setFixedHeight(84);card=QHBoxLayout(self.project_card);card.setContentsMargins(17,13,17,13);card.setSpacing(14)
        thumb=QLabel();thumb.setFixedSize(34,58);thumb.setStyleSheet('background:qlineargradient(x1:0,y1:0,x2:0.3,y2:1,stop:0 #3b5a4a,stop:1 #0d1217);border:2px solid #232830;border-radius:6px;');card.addWidget(thumb)
        detail=QVBoxLayout();detail.setAlignment(Qt.AlignVCenter);detail.setSpacing(2);detail.addWidget(text_label(project.name,15,700,height=18));detail.addWidget(text_label(f'{FORMATS[project.overrides.get("orientation",project.orientation)][0]} · {p.fps} fps · {human_time(p.audio_duration)} · MP4 (H.264 + AAC)',13,400,'#8B93A1',16));card.addLayout(detail,1);v.addWidget(self.project_card)
        sizes=FORMATS[project.overrides.get('orientation',project.orientation)][1]
        self.tier=Segmented([f'{name} {w}×{h}' for name,(w,h) in zip(['HD','Full HD','4K'],sizes)]);self.tier.setCurrentIndex(1)
        self.quality=Segmented(['Fast','Higher quality'])
        self.framing=Segmented(['Fill frame (crop)','Fit entire image']);self.framing.setCurrentIndex(0 if project.overrides.get('framing','FILL')=='FILL' else 1)
        for title,w in [('RESOLUTION',self.tier),('QUALITY',self.quality),('FRAMING',self.framing)]:v.addWidget(text_label(title,12,700,'#8B93A1',14));v.addWidget(w)
        v.addWidget(text_label('SAVE TO',12,700,'#8B93A1',14))
        safe=''.join(c for c in project.name if c not in '<>:"/\\|?*').strip() or 'ATS video'
        self.path=QLineEdit(str(Path.home()/'Videos'/(safe+'.mp4')));self.path.setFixedHeight(44);self.path.setStyleSheet('min-height:0;');row=QHBoxLayout();row.setSpacing(10);row.addWidget(self.path);row.addWidget(button('Browse',self.browse));v.addLayout(row)
        v.addWidget(text_label('Preview is close to the final video, but not pixel-identical.',12,400,'#8B93A1',14))
        self.progress=QProgressBar();self.progress.setRange(0,1000);self.progress.setTextVisible(False);self.progress.hide();v.addWidget(self.progress)
        self.status=label('',True);self.status.hide();v.addWidget(self.status)
        footer=QWidget();actions=QHBoxLayout(footer);actions.setContentsMargins(0,6,0,0);actions.setSpacing(12);actions.addStretch();self.cancel=ghost('Cancel',self.cancel_export);actions.addWidget(self.cancel);self.export=button('Export MP4',self.start_export,True);self.export.setFixedHeight(52);self.export.setStyleSheet('font-size:16px;padding:0 36px;');actions.addWidget(self.export);v.addWidget(footer)
        self.surface=QWidget();self.surface.setObjectName('exportSurface');self.surface.setStyleSheet('QWidget#exportSurface{background:#101318;border:1px solid #232830;border-radius:20px;}')
        shadow=QGraphicsDropShadowEffect(self.surface);shadow.setBlurRadius(80);shadow.setOffset(0,30);shadow.setColor(QColor(0,0,0,153));self.surface.setGraphicsEffect(shadow)
        panel=QVBoxLayout(self.surface);panel.setContentsMargins(0,0,0,0);panel.addWidget(scroll(box))
        root=QVBoxLayout(self);root.setContentsMargins(40,10,40,70);root.addWidget(self.surface);self.clock=QTimer(self);self.clock.setInterval(1000);self.clock.timeout.connect(self.tick)
        self.stage='';self.percent=0.;self.detail='';self.remaining=None

    def showEvent(self,event):
        super().showEvent(event)
        if self.parentWidget():self.move(self.parentWidget().frameGeometry().center()-QPoint(self.width()//2,self.height()//2-30))

    def browse(self):
        path,_=QFileDialog.getSaveFileName(self,'Save video',self.path.text(),'MP4 (*.mp4)')
        if path:self.path.setText(path)

    def start_export(self):
        if self.worker:return
        self.status.show()
        target=Path(self.path.text())
        if target.exists():self.status.setText('That file already exists. Choose another filename.');return
        target.parent.mkdir(parents=True,exist_ok=True)
        settings=self.project.settings(tier=self.tier.currentIndex(),quality='STANDARD' if self.quality.currentIndex()==0 else 'MAX',framing='FILL' if self.framing.currentIndex()==0 else 'FIT')
        settings=replace(settings,encoder='Auto')
        self._voice_muted=settings.voice_volume<=0
        self.worker=ExportWorker(self.project.effective_package(),self.project.images,Path(self.project.narration),target,settings)
        self.worker.progress_changed.connect(self.update_progress);self.worker.completed.connect(self.completed);self.worker.failed.connect(self.failed);self.worker.stopped.connect(lambda:self.failed('Export cancelled.'))
        self.worker.finished.connect(self.worker_finished)
        for w in (self.tier,self.quality,self.framing,self.path,self.export):w.setEnabled(False)
        self.eta=StageETA();self.percent=0;self.stage='Preparing';self.remaining=None
        self.progress.show();self.started=time.monotonic();self.clock.start();self.worker.start()

    def update_progress(self,stage,percent,detail):
        self.stage,self.percent,self.detail=stage,percent,detail;self.remaining=self.eta.update(percent,time.monotonic())
        old=getattr(self,'_progress_anim',None)
        if old:old.stop()
        if reduced_motion():self.progress.setValue(round(percent*10))
        else:
            a=QPropertyAnimation(self.progress,b'value',self);a.setDuration(160);a.setStartValue(self.progress.value());a.setEndValue(round(percent*10));a.setEasingCurve(QEasingCurve.OutCubic);self._progress_anim=a;a.start()
        self.tick()

    def tick(self):
        elapsed=human_time(time.monotonic()-self.started);eta=human_time(self.remaining) if self.remaining is not None else 'Calculating…'
        self.status.setWordWrap(True)
        self.status.setText(f'{self.stage or "Preparing"} · {self.percent:.0f}%\nElapsed {elapsed} · Stage remaining {eta}' + (f'\n{self.detail}' if self.detail else ''))
        if getattr(self,'_voice_muted',False):self.status.setText(self.status.text()+'\nVoice is muted (0%). Close to change Sound settings.')

    def completed(self,result):self.result=result;self.progress.setValue(1000);self.clock.stop();self.status.setText('Export complete. Video and report saved.');self.cancel.setText('Done')
    def failed(self,message):self.clock.stop();self.status.setText(message);self.cancel.setText('Close');self.cancel.setEnabled(True)
    def worker_finished(self):
        worker=self.worker;self.worker=None;worker.deleteLater()
        self.cancel.setEnabled(True)
        if self.result:self.export.setText('Open video');self.export.setEnabled(True);self.export.clicked.disconnect();self.export.clicked.connect(self.open_result)
        else:
            for w in (self.tier,self.quality,self.framing,self.path,self.export):w.setEnabled(True)
    def open_result(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.path.text()))
    def cancel_export(self):
        if self.worker:self.worker.cancel_event.set();self.cancel.setEnabled(False);self.status.setText('Cancelling…')
        else:self.reject()
    def reject(self):
        if self.worker:self.cancel_export()
        else:super().reject()
