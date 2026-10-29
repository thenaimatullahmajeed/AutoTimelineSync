from dataclasses import replace
from pathlib import Path
import json,threading,time
import pytest
from PySide6.QtCore import Qt,QSettings
from PySide6.QtGui import QAction
from PySide6.QtTest import QTest
from ats_studio.product import Project,FORMATS
from ats_studio.pro_spec import build_spec
from ats_studio.pro_compositor import ProCompositor
from ats_studio.schema import PackageError
from ats_studio.renderer import RenderCancelled
from ats_studio.ui_parts.dialogs import LaunchDialog,ImportWorker
from ats_studio.ui import MainWindow
from ats_studio.fast_export import export_pro_video

def wait(app,condition,seconds=10):
    deadline=time.monotonic()+seconds
    while not condition() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
    assert condition()

@pytest.mark.parametrize('orientation',list(FORMATS))
def test_canvas_override_persists_and_renders(project,app,tmp_path,orientation):
    dialog=LaunchDialog(current=project);original=project.script
    dialog.format_choice.setCurrentIndex(dialog.format_choice.findData(orientation))
    pending=Project(project.name,project.narration,project.image_folder,project.script)
    worker=ImportWorker(pending,dialog);pending.validate()
    settings=pending.settings(tier=0);assert (settings.width,settings.height)==FORMATS[orientation][1][0]
    spec=build_spec(pending.effective_package(),pending.images,settings)
    image=ProCompositor(spec,pending.images,settings).render_frame(15)
    assert (image.width(),image.height())==(settings.width,settings.height)
    path=tmp_path/'ratio.ats3';pending.save(str(path));loaded=Project.load(str(path))
    assert loaded.settings(tier=0).width==settings.width and loaded.script==original
    dialog.reject();worker.deleteLater();app.processEvents()

def test_repaste_available_after_valid_or_invalid_json(project,app):
    dialog=LaunchDialog(current=project);dialog.present_rows(project)
    assert not dialog.rows['script'].paste.isHidden()
    assert dialog.rows['script'].paste.text()=='Repaste'
    dialog.script_text='{broken';dialog.changed();dialog.show_error('Invalid JSON')
    assert not dialog.rows['script'].paste.isHidden()
    assert not dialog.create.isEnabled();dialog.reject();app.processEvents()

def test_ctrl_i_dispatches_import_shortcut(app,tmp_path,monkeypatch):
    seen=[];monkeypatch.setattr(MainWindow,'import_project',lambda self:seen.append(True))
    window=MainWindow(show_launch=False);window.store=QSettings(str(tmp_path/'settings.ini'),QSettings.IniFormat)
    window.show();window.activateWindow();app.processEvents()
    action=next(a for a in window.findChildren(QAction) if a.text().startswith('Import'))
    assert 'Ctrl+I' in [key.toString() for key in action.shortcuts()]
    QTest.keyClick(window,Qt.Key_I,Qt.ControlModifier);app.processEvents()
    assert seen;window.close();app.processEvents()

def test_actual_timeline_thumbnail_and_physical_preview_size(project,app,tmp_path):
    window=MainWindow(show_launch=False);window.store=QSettings(str(tmp_path/'settings.ini'),QSettings.IniFormat)
    window.resize(1280,800);window.show();window.apply_project(project)
    wait(app,lambda:len(window.timeline.canvas.thumbnails)==len(project.images))
    thumbnail=window.timeline.canvas.thumbnails['001'];assert not thumbnail.isNull()
    wait(app,lambda:not window.preview.image.isNull())
    rect=window.preview.frame_rect();dpr=window.preview.devicePixelRatioF()
    assert window.preview.image.height()>=round(rect.height()*min(dpr,1920/max(rect.width(),rect.height())))-1
    window.grab().save(str(tmp_path/'editor.png'))
    window.close();app.processEvents()

@pytest.mark.parametrize('schema',['ATS_PACKAGE_V1','ATS_PACKAGE_V3'])
def test_obsolete_schema_still_rejected(project,schema):
    from ats_studio.product import parse_script
    j=json.loads(project.script);j['schema']=schema
    with pytest.raises(PackageError):parse_script(json.dumps(j))

def test_silent_limit_only_exports_instead_of_false_lufs_failure(project,tmp_path):
    settings=replace(project.settings(tier=0),width=360,height=640,voice_volume=0,encoder='CPU x264')
    output=tmp_path/'silent.mp4';events=[]
    export_pro_video(project.effective_package(),project.images,Path(project.narration),output,settings,threading.Event(),lambda *e:events.append(e))
    report=json.loads(output.with_name(output.name+'.report.json').read_text())
    assert output.stat().st_size>1000
    assert report['audio_stats']['after_aac']['integrated_lufs']<=-69
    assert any('silent' in warning for warning in report['warnings'])
    assert [e[1] for e in events]==sorted(e[1] for e in events) and events[-1][1]==100
    assert not list(tmp_path.glob('.*.ats-work-*'))

def test_silent_loudnorm_fails_before_video_and_cleans_cache(project,tmp_path):
    j=json.loads(project.script);j['audio']={'master':{'mode':'LOUDNORM','target_lufs':-16,'true_peak_db':-1}}
    project.script=json.dumps(j);project.validate()
    settings=replace(project.settings(tier=0),voice_volume=0,width=360,height=640)
    events=[];output=tmp_path/'fail.mp4'
    with pytest.raises(PackageError,match='cannot normalize silence'):
        export_pro_video(project.effective_package(),project.images,Path(project.narration),output,settings,threading.Event(),lambda *e:events.append(e))
    assert not output.exists() and not any(e[0]=='Rendering video' for e in events)
    assert not list(tmp_path.glob('.*.ats-work-*'))

def test_loudnorm_target_and_tracks(project,tmp_path):
    j=json.loads(project.script);j['audio']={'master':{'mode':'LOUDNORM','target_lufs':-16,'true_peak_db':-1}}
    project.script=json.dumps(j);project.validate();output=tmp_path/'normal.mp4'
    settings=replace(project.settings(tier=0),width=360,height=640,encoder='CPU x264')
    export_pro_video(project.effective_package(),project.images,Path(project.narration),output,settings,threading.Event(),lambda *e:None)
    report=json.loads(output.with_name(output.name+'.report.json').read_text())
    assert abs(report['audio_stats']['after_aac']['integrated_lufs']+16)<=1
    assert report['audio_stats']['after_aac']['true_peak_dbtp']<=-.9
    assert report['final_file']['frames']==60 and report['final_file']['audio_codec']=='aac'

def test_cancel_during_encoding_leaves_no_output(project,tmp_path):
    stop=threading.Event();output=tmp_path/'cancel.mp4'
    settings=replace(project.settings(tier=0),width=360,height=640,encoder='CPU x264')
    def progress(stage,value,detail):
        if stage=='Rendering video':stop.set()
    with pytest.raises(RenderCancelled):
        export_pro_video(project.effective_package(),project.images,Path(project.narration),output,settings,stop,progress)
    assert not output.exists() and not list(tmp_path.glob('.*.ats-work-*'))
