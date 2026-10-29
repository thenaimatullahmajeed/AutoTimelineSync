"""Load the review candidate over the unchanged, verified Windows runtime."""
import os,sys
from pathlib import Path
FROZEN=bool(getattr(sys,'frozen',False))
ROOT=Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
CORE=ROOT if FROZEN else Path(os.environ.get('ATS_SOURCE_CORE',str(ROOT.parent/'ats_windows_3_0_2/core')))
if not FROZEN and not CORE.is_dir():
    CORE=Path('C:/Users/naima/.codex/.chatgpt-projects/g-p-6ab65feb00b48191a24211d8511a485f/ats_windows_3_0_2/core')
sys.dont_write_bytecode=True
if sys.stdout is not None and hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
if not FROZEN:sys.path.insert(0,str(CORE))
import ats_studio
if not FROZEN:ats_studio.__path__.insert(0,str(ROOT/'overlay/ats_studio'))
ats_studio.__version__='3.0.2-A1'
APP=None

def application():
    global APP
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    from ats_studio.fonts import register_bundled_fonts
    APP=QApplication.instance() or QApplication([])
    register_bundled_fonts();APP.setFont(QFont('Inter',10))
    return APP

def install(ui=False):
    from ats_studio.sync_core import apply_seed_guard
    apply_seed_guard()
    if ui:
        from ats_studio.desktop_fixes import apply
        apply()
        from ats_studio.sync_ui import apply as apply_ui
        apply_ui()
        from ats_studio.ui import MainWindow
        if not getattr(MainWindow,'_sync_version_title',False):
            original=MainWindow.__init__
            def init(self,*args,**kwargs):
                original(self,*args,**kwargs)
                self.setWindowTitle('Auto Timeline Sync by Naimat · 3.0.2-A1')
            MainWindow.__init__=init
            MainWindow._sync_version_title=True

