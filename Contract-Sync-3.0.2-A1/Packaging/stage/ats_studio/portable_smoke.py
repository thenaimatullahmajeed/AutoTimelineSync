"""Unattended release verification, reachable only with --smoke-test."""
from pathlib import Path
import json,sys,wave,time
import numpy as np
from PySide6.QtCore import QEventLoop,QTimer
from PySide6.QtGui import QImage,QColor
from .product import Project
from .ui import MainWindow
from .ui_parts.dialogs import LaunchDialog,ExportDialog
from . import __version__

def run(app,output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    def wait(seconds):
        loop=QEventLoop();QTimer.singleShot(round(seconds*1000),loop.quit);loop.exec()
    w=None
    try:
        root=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
        script=(root/'Examples'/'ATS3_vertical.json').read_text(encoding='utf-8')
        images=output/'images';images.mkdir(exist_ok=True)
        for ident,color in [('001','#19333D'),('002','#322F44')]:
            image=QImage(360,640,QImage.Format_RGB888);image.fill(QColor(color));image.save(str(images/(ident+'.png')))
        audio=output/'narration.wav';positions=np.arange(8*48000)
        with wave.open(str(audio),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes((np.sin(positions*2*np.pi*330/48000)*8000).astype('<i2').tobytes())
        project=Project('Portable smoke',str(audio),str(images),script)
        w=MainWindow(False);w.show();launch=LaunchDialog(w,project);launch.show();deadline=time.monotonic()+90
        while not launch.create.isEnabled() and time.monotonic()<deadline:wait(.1)
        if not launch.create.isEnabled():raise RuntimeError(launch.summary.text())
        launch.create.click();w.apply_project(launch.result_project,launch.spec);launch.deleteLater();wait(.5);w.grab().save(str(output/'portable-ui.png'))
        export=ExportDialog(w.project,w);export.path.setText(str(output/'portable-smoke.mp4'));export.tier.setCurrentIndex(0);export.show();export.start_export();deadline=time.monotonic()+180
        while export.worker and time.monotonic()<deadline:wait(.2)
        if not export.result:raise RuntimeError(export.status.text())
        result={'ok':True,'version':__version__,'result':export.result,'title':w.windowTitle()};export.reject();w.close();wait(.2)
        (output/'portable-smoke.json').write_text(json.dumps(result,default=str,indent=2),encoding='utf-8');return 0
    except Exception as exc:
        if w:w.close()
        (output/'portable-smoke.json').write_text(json.dumps({'ok':False,'error':str(exc)},indent=2),encoding='utf-8');return 1
