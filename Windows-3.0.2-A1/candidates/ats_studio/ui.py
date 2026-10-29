"""ATS 3 editor coordinator: one import flow and one Pro preview path."""
from __future__ import annotations
import tempfile,shutil
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QSettings,QUrl,QEvent
from PySide6.QtGui import QAction,QIcon,QDesktopServices
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFileDialog,QPlainTextEdit,QDialog,QSplitter
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from . import __version__
from .assets import icon_path
from .product import Project,FORMATS
from .pro_spec import build_spec
from .ui_parts.common import STYLE,Dialog,button,label,ClickSlider,ClickCombo,human_time,fade_window,dark_titlebar
from .ui_parts.dialogs import LaunchDialog,ExportDialog
from .ui_parts.inspector import Inspector
from .ui_parts.views import PreviewView,TimelineView
from .ui_parts.audio_workers import MixWorker,WaveWorker

class MainWindow(QMainWindow):
    def __init__(self,show_launch=True):
        super().__init__();self.setWindowTitle(f'Auto Timeline Sync by Naimat · {__version__}');self.setWindowIcon(QIcon(str(icon_path())))
        self.resize(1280,800);self.setMinimumSize(760,520);self.setStyleSheet(STYLE)
        self.store=QSettings('Naimat','AutoTimelineSync3');self.project=None;self.spec=None;self.export_dialog=None;self.fullscreen=None;self.mix_worker=None;self.wave_worker=None;self.mix_pending=None;self.mix_generation=0;self.project_generation=0;self.closing=False
        self.work=Path(tempfile.mkdtemp(prefix='ats3-preview-'));self.player=QMediaPlayer(self);self.audio_output=QAudioOutput(self);self.player.setAudioOutput(self.audio_output);self.audio_output.setVolume(1)
        root=QWidget();self.setCentralWidget(root);v=QVBoxLayout(root);v.setContentsMargins(0,0,0,0);v.setSpacing(0)
        self.create_menus();top=QHBoxLayout();top.setContentsMargins(24,8,24,12);top.setSpacing(16)
        self.title=label('Auto Timeline Sync',heading=True);top.addWidget(self.title,1);self.format_chip=label('',True);top.addWidget(self.format_chip)
        self.status=button('No project',self.show_notices);top.addWidget(self.status);self.export_button=button('Export  ›',self.open_export,True);self.export_button.setEnabled(False);top.addWidget(self.export_button);v.addLayout(top)
        self.editor_split=QSplitter(Qt.Horizontal);previewbody=QWidget();p=QVBoxLayout(previewbody);p.setContentsMargins(16,0,16,8);p.setSpacing(8)
        self.preview=PreviewView();self.preview.failed.connect(self.preview_failed);self.preview.moment_changed.connect(self.moment_override);p.addWidget(self.preview,1)
        controls=QHBoxLayout();self.play=button('▶',self.toggle_play);controls.addWidget(self.play);self.seek=ClickSlider();self.seek.setRange(0,10000);self.seek.sliderMoved.connect(self.slider_seek);controls.addWidget(self.seek,1)
        self.time_label=label('00:00 / 00:00',True);controls.addWidget(self.time_label);controls.addWidget(button('⛶',self.open_fullscreen));p.addLayout(controls)
        self.editor_split.addWidget(previewbody);self.inspector=Inspector();self.inspector.changed.connect(self.override);self.inspector.reset_requested.connect(self.reset_overrides);self.editor_split.addWidget(self.inspector);self.editor_split.setStretchFactor(0,1);v.addWidget(self.editor_split,1)
        self.timeline=TimelineView();self.timeline.seek_requested.connect(self.seek_seconds);self.timeline.gain_changed.connect(self.override);v.addWidget(self.timeline)
        self.player.positionChanged.connect(self.position_changed);self.player.playbackStateChanged.connect(lambda state:self.play.setText('Ⅱ' if state==QMediaPlayer.PlayingState else '▶'))
        self.player.errorOccurred.connect(lambda error,text:self.preview_failed('Audio preview: '+text))
        self.mix_debounce=QTimer(self);self.mix_debounce.setSingleShot(True);self.mix_debounce.setInterval(350);self.mix_debounce.timeout.connect(self.request_mix)
        self.autosave=QTimer(self);self.autosave.setInterval(60000);self.autosave.timeout.connect(self.autosave_project);self.autosave.start();self.inspector.setEnabled(False)
        if show_launch:QTimer.singleShot(250,self.import_project)

    def action(self,menu,text,slot,shortcut=None,checkable=False):
        a=QAction(text,self);a.setCheckable(checkable)
        if shortcut:a.setShortcut(shortcut)
        a.triggered.connect(slot);menu.addAction(a);return a
    def create_menus(self):
        m=self.menuBar().addMenu('File');self.action(m,'Import…',self.import_project,'Ctrl+N');self.action(m,'Open project…',self.open_project,'Ctrl+O');self.action(m,'Save project',self.save_project,'Ctrl+S');self.action(m,'Save project as…',lambda:self.save_project(True),'Ctrl+Shift+S');m.addSeparator();self.action(m,'Export…',self.open_export,'Ctrl+E');self.action(m,'Exit',self.close)
        m=self.menuBar().addMenu('Edit');self.action(m,'Reset overrides to script',self.reset_overrides);self.action(m,'Settings…',self.settings_dialog)
        m=self.menuBar().addMenu('View');self.action(m,'Fullscreen preview',self.open_fullscreen,'F11');self.safe_action=self.action(m,'Preview safe zones',self.set_safe_zones,checkable=True);self.cc_action=self.action(m,'Preview captions',self.set_cc,checkable=True);self.cc_action.setChecked(True)
        m=self.menuBar().addMenu('Help');self.action(m,'Explain Package',self.explain_package);self.action(m,'Run Linter',self.run_linter);self.action(m,'JSON authoring guide',self.open_guide);self.action(m,'About',lambda:self.message('Auto Timeline Sync',f'Auto Timeline Sync by Naimat\nVersion {__version__}\nLocal Pro video editor.'))
    def showEvent(self,event):super().showEvent(event);dark_titlebar(self);fade_window(self)
    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type()==QEvent.WindowStateChange and event.oldState() & Qt.WindowMinimized and not self.isMinimized():fade_window(self,180)
    def recents(self):
        values=self.store.value('recent',[]);return values if isinstance(values,list) else [values] if values else []
    def remember(self,path):self.store.setValue('recent',[path]+[x for x in self.recents() if x!=path][:7])
    def import_project(self):
        if self.export_dialog and self.export_dialog.worker:return
        self.player.pause();d=LaunchDialog(self,self.project,self.recents());d.setStyleSheet(STYLE)
        if d.exec()==QDialog.Accepted:self.apply_project(d.result_project,d.spec)
        d.deleteLater()
    def apply_project(self,project,spec=None):
        self.player.stop();self.project=project;self.project_generation+=1;self.spec=spec or build_spec(project.effective_package(),project.images,project.settings(framing=project.overrides.get('framing','FILL')))
        self.title.setText(project.name);self.export_button.setEnabled(True);self.inspector.setEnabled(True);self.timeline.set_project(project);self.refresh_settings(False);self.seek_seconds(0);self.mix_debounce.start()
        if project.saved_path:self.remember(project.saved_path)
        if self.wave_worker and self.wave_worker.isRunning():self.wave_worker.requestInterruption();self.wave_worker.wait()
        self.wave_worker=WaveWorker(self.project_generation,project);self.wave_worker.ready.connect(self.wave_ready);self.wave_worker.start()
    def refresh_settings(self,rebuild=True):
        if not self.project:return
        s=self.project.settings(framing=self.project.overrides.get('framing','FILL'))
        if rebuild:self.spec=build_spec(self.project.effective_package(),self.project.images,s)
        self.inspector.set_settings(s,self.project.overrides);self.timeline.set_settings(s);self.preview.configure_pro(self.spec,self.project.images,s)
        if self.fullscreen:self.fullscreen.preview.configure_pro(self.spec,self.project.images,s)
        origin='override' if 'orientation' in self.project.overrides else 'from script' if 'format' in self.project.package.pro else 'from images'
        orientation=self.project.overrides.get('orientation',self.project.orientation);self.format_chip.setText(f'Format: {FORMATS[orientation][0]} {orientation.title()} · {origin}')
        notices=self.project.notices+[('warning',w) for w in self.spec.warnings]+[('info',w) for w in self.spec.changes.get('moment_notices',[])]
        self.notices=list(dict.fromkeys(notices));count=sum(level=='warning' for level,_ in self.notices);self.status.setText('Ready'+(f' · {count} notice' + ('s' if count!=1 else '') if count else ''));self.timeline.canvas.update()
        self.timeline.canvas.moments=self.spec.changes.get('moments',[])
    def override(self,key,value):
        if not self.project:return
        self.project.overrides[key]=value
        try:
            self.refresh_settings()
            if key in {'voice_volume','music_volume','energy'}:self.mix_debounce.start()
        except Exception as exc:self.message('Could not apply setting',str(exc))
    def reset_overrides(self):
        if self.project:self.project.overrides={};self.project.moment_overrides={};self.refresh_settings();self.mix_debounce.start()
    def moment_override(self,ident,box):
        if self.project:self.project.moment_overrides[ident]=box;self.refresh_settings()
    def request_mix(self):
        if not self.project or self.closing:return
        self.mix_generation+=1;self.mix_pending=(self.mix_generation,self.spec,self.project.narration,self.project.settings(framing=self.project.overrides.get('framing','FILL')))
        if self.mix_worker:self.mix_worker.requestInterruption();return
        self.start_mix()
    def start_mix(self):
        if not self.mix_pending or self.closing:return
        generation,spec,audio,s=self.mix_pending;self.mix_pending=None;work=self.work/str(generation);work.mkdir()
        worker=MixWorker(generation,spec,audio,s,work);self.mix_worker=worker;worker.ready.connect(self.mix_ready);worker.failed.connect(self.preview_failed);worker.finished.connect(lambda:self.mix_finished(worker));worker.start()
    def mix_ready(self,generation,path):
        if generation!=self.mix_generation or self.closing:return
        position=self.player.position();playing=self.player.playbackState()==QMediaPlayer.PlayingState;self.player.setSource(QUrl.fromLocalFile(path));self.player.setPosition(position)
        if playing:self.player.play()
    def mix_finished(self,worker):
        if self.mix_worker is worker:self.mix_worker=None
        worker.deleteLater()
        if self.mix_pending:self.start_mix()
        active=Path(self.player.source().toLocalFile()).parent
        for d in self.work.iterdir():
            if d.is_dir() and d!=active and d.name!=str(self.mix_generation):shutil.rmtree(d,ignore_errors=True)
    def wave_ready(self,generation,values,seams):
        if generation==self.project_generation:self.timeline.canvas.waveforms=values;self.timeline.canvas.seams=seams;self.timeline.canvas.update()
    def toggle_play(self):
        if not self.project:return
        if self.player.source().isEmpty():self.preview_failed('Preparing mixed audio preview. Playback will be available shortly.');return
        if self.player.playbackState()==QMediaPlayer.PlayingState:self.player.pause()
        else:self.player.play()
    def slider_seek(self,value):
        if self.project:self.seek_seconds(value/10000*self.project.package.audio_duration)
    def seek_seconds(self,seconds):self.player.setPosition(round(seconds*1000));self.position_changed(round(seconds*1000))
    def position_changed(self,ms):
        if not self.project:return
        seconds=min(ms/1000,self.project.package.audio_duration);self.preview.set_position(seconds);self.timeline.set_position(seconds)
        if self.fullscreen:self.fullscreen.preview.set_position(seconds)
        if not self.seek.isSliderDown():self.seek.setValue(round(seconds/self.project.package.audio_duration*10000))
        self.time_label.setText(f'{human_time(seconds)} / {human_time(self.project.package.audio_duration)}')
    def set_safe_zones(self,checked):
        self.preview.safe_zones=checked;self.preview.update()
        if self.fullscreen:self.fullscreen.preview.safe_zones=checked;self.fullscreen.preview.update()
    def set_cc(self,checked):
        self.preview.captions_visible=checked;self.preview.reconfigure()
        if self.fullscreen:self.fullscreen.preview.captions_visible=checked;self.fullscreen.preview.reconfigure()
    def open_fullscreen(self):
        if not self.project or self.fullscreen:return
        d=Dialog(self);d.setWindowTitle('Fullscreen preview · Esc to close');d.setStyleSheet(STYLE);v=QVBoxLayout(d);d.preview=PreviewView();d.preview.safe_zones=self.preview.safe_zones;d.preview.captions_visible=self.preview.captions_visible
        d.preview.configure_pro(self.spec,self.project.images,self.project.settings(framing=self.project.overrides.get('framing','FILL')));d.preview.set_position(self.player.position()/1000);v.addWidget(d.preview)
        row=QHBoxLayout();row.addWidget(button('Play / Pause',self.toggle_play));row.addWidget(button('Close',d.reject));v.addLayout(row);self.fullscreen=d;d.showFullScreen();d.finished.connect(lambda:self.close_fullscreen(d))
    def close_fullscreen(self,d):d.preview.shutdown();self.fullscreen=None;d.deleteLater()
    def open_export(self):
        if not self.project:return
        if self.export_dialog:self.export_dialog.raise_();return
        self.player.pause();d=ExportDialog(self.project,self);d.setStyleSheet(STYLE);self.export_dialog=d;d.finished.connect(lambda:self.export_closed(d));d.open()
    def export_closed(self,d):self.export_dialog=None;d.deleteLater()
    def open_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Open ATS 3 project','','ATS project (*.ats3)')
        if path:
            try:self.apply_project(Project.load(path));self.remember(path)
            except Exception as exc:self.message('Cannot open project',str(exc))
    def save_project(self,as_new=False):
        if not self.project:return
        path=self.project.saved_path
        if as_new or not path:path,_=QFileDialog.getSaveFileName(self,'Save project',self.project.name+'.ats3','ATS project (*.ats3)')
        if path:
            try:self.project.save(path);self.remember(path)
            except Exception as exc:self.message('Cannot save project',str(exc))
    def autosave_project(self):
        if self.project:
            try:
                if self.project.saved_path:self.project.save(self.project.saved_path)
                else:
                    saved=self.project.saved_path;folder=Path.home()/'AppData'/'Local'/'AutoTimelineSync3';folder.mkdir(parents=True,exist_ok=True);self.project.save(str(folder/'recovery.ats3'));self.project.saved_path=saved
            except OSError:pass
    def settings_dialog(self):
        d=Dialog(self);d.setWindowTitle('Settings');v=QVBoxLayout(d);v.addWidget(label('Advanced format override',heading=True));v.addWidget(label('Changing format can crop images and move captions or circle markers. Reset to script restores its format.',True));combo=ClickCombo();combo.addItem('From script / images');combo.addItems(list(FORMATS));v.addWidget(combo)
        if self.project:combo.setCurrentText(self.project.overrides.get('orientation','From script / images'))
        def apply():
            if self.project:
                if combo.currentIndex()==0:self.project.overrides.pop('orientation',None)
                else:self.project.overrides['orientation']=combo.currentText()
                self.refresh_settings()
            d.accept()
        v.addWidget(button('Apply',apply,True));d.exec();d.deleteLater()
    def show_notices(self):self.message('Project notices','\n\n'.join(f'{level.title()}: {message}' for level,message in getattr(self,'notices',[])) or 'No project warnings.')
    def preview_failed(self,message):
        if self.project:
            notice=('warning',message)
            if notice not in self.project.notices:self.project.notices.append(notice)
            self.notices=list(dict.fromkeys(getattr(self,'notices',[])+[notice]))
            count=sum(level=='warning' for level,_ in self.notices);self.status.setText(f'Ready · {count} notice'+('s' if count!=1 else ''))
    def explain_package(self):
        if self.project:
            p=self.project.package;counts={}
            for s in self.spec.scenes:counts[s.motion]=counts.get(s.motion,0)+1
            self.message('Explain Package',f'{p.title}\n{len(p.scenes)} scenes · {len(p.words)} timed words · {len(p.captions)} captions\n{p.fps} fps · {p.total_frames} frames\nMotion: '+', '.join(f'{k}: {v}' for k,v in counts.items()))
    def run_linter(self):
        if not self.project:return
        try:
            from .media import preflight_pro_media
            s=self.project.settings();warnings=preflight_pro_media(self.project.package,self.project.images,s.width,s.height,s.framing);self.message('Run Linter','\n\n'.join(warnings) or 'No media or reading-speed warnings found.')
        except Exception as exc:self.message('Linter error',str(exc))
    def open_guide(self):
        import sys
        root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1];QDesktopServices.openUrl(QUrl.fromLocalFile(str(root/'ATS_JSON_AUTHORING_GUIDE.md')))
    def message(self,title,text):
        d=Dialog(self);d.setWindowTitle(title);d.resize(600,380);v=QVBoxLayout(d);edit=QPlainTextEdit(text);edit.setReadOnly(True);v.addWidget(edit);v.addWidget(button('Close',d.accept));d.exec();d.deleteLater()
    def closeEvent(self,event):
        if self.export_dialog and self.export_dialog.worker:self.export_dialog.cancel_export();event.ignore();return
        self.closing=True;self.autosave_project();self.autosave.stop();self.mix_debounce.stop();self.player.stop();self.player.setSource(QUrl())
        if self.fullscreen:self.fullscreen.reject()
        self.preview.shutdown()
        for w in (self.mix_worker,self.wave_worker):
            if w and w.isRunning():w.requestInterruption();w.wait()
        shutil.rmtree(self.work,ignore_errors=True);event.accept()
