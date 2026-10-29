import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'core'))
import pytest
from PySide6.QtWidgets import QApplication
from ats_studio.desktop_fixes import apply
apply()

@pytest.fixture(scope='session')
def app():
    application=QApplication.instance() or QApplication([])
    from ats_studio.fonts import register_bundled_fonts
    register_bundled_fonts()
    return application

@pytest.fixture
def project(tmp_path,app):
    import json,wave,numpy as np
    from PySide6.QtGui import QImage,QColor,QPainter,QPen
    from ats_studio.product import Project
    root=Path(__file__).resolve().parents[1]/'core'
    j=json.loads((root/'Examples/ATS3_vertical.json').read_text())
    j['audio_duration']=2;j['scenes']=j['scenes'][:1];j['scenes'][0]['end']=2
    j['words']=j['words'][:4];j['captions']=j['captions'][:1];j['moments']=[]
    j['direction']['sfx_enabled']=False;j['direction']['finish']={'grain':0,'vignette':0,'contrast':0}
    folder=tmp_path/'images';folder.mkdir()
    image=QImage(360,640,QImage.Format_RGB888);image.fill(QColor('#185586'))
    painter=QPainter(image);painter.setPen(QPen(QColor('#ffcc22'),18));painter.drawEllipse(75,200,210,210);painter.end()
    image.save(str(folder/'001.png'))
    audio=tmp_path/'voice.wav';samples=(np.sin(np.arange(96000)*2*np.pi*330/48000)*3000).astype('<i2')
    with wave.open(str(audio),'wb') as w:w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(samples.tobytes())
    return Project('Regression test',str(audio),str(folder),json.dumps(j)).validate()
