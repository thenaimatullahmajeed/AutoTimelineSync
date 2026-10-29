from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt, QCoreApplication

from .assets import icon_path
from .ui import MainWindow
from PySide6.QtGui import QIcon


def main() -> int:
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("Auto Timeline Sync")
    app.setWindowIcon(QIcon(str(icon_path())))
    from .fonts import register_bundled_fonts
    register_bundled_fonts()
    if '--smoke-test' in sys.argv:
        from .portable_smoke import run
        return run(app,sys.argv[sys.argv.index('--smoke-test')+1])
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
