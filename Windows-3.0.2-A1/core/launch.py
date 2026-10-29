"""Auto Timeline Sync 3.0.2 Windows entry point."""
from ats_studio.desktop_fixes import apply
apply()
from ats_studio.__main__ import main
if __name__=='__main__':
    import sys
    if '--help' in sys.argv:
        print('Auto Timeline Sync 3.0.2\nLaunch without arguments, or --smoke-test OUTPUT_FOLDER for development verification.')
    elif '--smoke-test' in sys.argv:
        from pathlib import Path
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont
        from ats_studio.fonts import register_bundled_fonts
        from ats_studio.portable_smoke import run
        app=QApplication([sys.argv[0]]);register_bundled_fonts();app.setFont(QFont('Inter',10))
        index=sys.argv.index('--smoke-test')
        output=sys.argv[index+1] if len(sys.argv)>index+1 else 'Verification/portable-smoke'
        sys.exit(run(app,output))
    else:
        main()
