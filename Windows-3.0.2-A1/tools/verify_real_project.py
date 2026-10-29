"""Capture current user-project UI and compare the actual baseline/fixed pipeline."""
from pathlib import Path
import os,sys,json,time,threading
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_SCALE_FACTOR','1.5')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings,QEventLoop,QTimer
from dataclasses import replace
from ats_studio import pro_renderer
baseline_export=pro_renderer.export_pro_video
from ats_studio.desktop_fixes import apply
apply()
from ats_studio.fast_export import export_pro_video
from ats_studio.product import Project
from ats_studio.pro_spec import build_spec
from ats_studio.fonts import register_bundled_fonts
from ats_studio.ui import MainWindow
from ats_studio.ui_parts.dialogs import LaunchDialog,ExportDialog
app=QApplication([]);register_bundled_fonts()
out=ROOT/'Verification/real';out.mkdir(parents=True,exist_ok=True)
def wait(seconds):
    loop=QEventLoop();QTimer.singleShot(round(seconds*1000),loop.quit);loop.exec()
p=Project.load('C:/Users/naima/OneDrive/Desktop/The Great Hedge of India - Hindi Short.ats3')
w=MainWindow(show_launch=False);w.store=QSettings(str(out/'settings.ini'),QSettings.IniFormat)
w.resize(1280,800);w.show();w.apply_project(p)
deadline=time.monotonic()+15
while len(w.timeline.canvas.thumbnails)<len(p.images) and time.monotonic()<deadline:wait(.05)
w.seek_seconds(18);wait(1)
w.grab().save(str(out/'editor-1280x800-dpr1.5.png'))
d=LaunchDialog(w,p);d.show();wait(.7);d.grab().save(str(out/'launch-ready-dpr1.5.png'));d.reject()
e=ExportDialog(p,w);e.show();wait(.3);e.grab().save(str(out/'export-dpr1.5.png'));e.reject()
geometry=dict(dpr=w.preview.devicePixelRatioF(),preview_logical=[w.preview.frame_rect().width(),w.preview.frame_rect().height()],
    render_pixels=[w.preview.image.width(),w.preview.image.height()],thumbnails=len(w.timeline.canvas.thumbnails),images=len(p.images))
(out/'ui-geometry.json').write_text(json.dumps(geometry,indent=2))
w.close();wait(.2)

# Identical eight-second fixture, dimensions, input frames and worker request.
fixture=ROOT/'Verification/smoke-final'
script=(ROOT/'core/Examples/ATS3_vertical.json').read_text()
bench=Project('Comparison',str(fixture/'narration.wav'),str(fixture/'images'),script).validate()
settings=replace(bench.settings(tier=0),encoder='CPU x264')
results={}
for label,exporter in [('baseline_3_0_1',baseline_export),('fixed_3_0_2',export_pro_video)]:
    target=out/(label+'.mp4')
    if target.exists():raise RuntimeError('Use a fresh benchmark output folder.')
    start=time.monotonic()
    try:
        result=exporter(bench.effective_package(),bench.images,Path(bench.narration),target,settings,threading.Event(),lambda *x:None)
        results[label]=dict(status='PASS',seconds=round(time.monotonic()-start,3),bytes=target.stat().st_size,result=result)
    except Exception as exc:results[label]=dict(status='FAIL',seconds=round(time.monotonic()-start,3),error=str(exc))
    print(json.dumps({label:results[label]}),flush=True)
(out/'benchmark.json').write_text(json.dumps(results,indent=2),encoding='utf8')

# Full real Hindi project, without overwriting the user's original video.
target=out/'The Great Hedge of India - 3.0.2 verification.mp4'
start=time.monotonic();events=[]
def progress(stage,value,detail):
    if not events or stage!=events[-1]['stage'] or value-events[-1]['percent']>=5:
        event=dict(stage=stage,percent=round(value,2),elapsed=round(time.monotonic()-start,2),detail=detail)
        events.append(event);print(json.dumps(event),flush=True)
result=export_pro_video(p.effective_package(),p.images,Path(p.narration),target,
    replace(p.settings(tier=1),encoder='Auto'),threading.Event(),progress)
(out/'real-export.json').write_text(json.dumps(dict(result=result,events=events),indent=2),encoding='utf8')
