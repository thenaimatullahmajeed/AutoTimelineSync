"""Register bundled fonts locally without installing them on Windows."""
from pathlib import Path
import sys

_loaded=False

def fonts_dir() -> Path:
    return Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))/"assets"/"fonts"

def register_bundled_fonts() -> tuple[str,...]:
    global _loaded
    from PySide6.QtGui import QFontDatabase
    if not _loaded:
        for path in sorted(fonts_dir().glob("*.ttf")):
            if QFontDatabase.addApplicationFont(str(path))<0:
                raise RuntimeError(f"Bundled font could not be loaded: {path.name}")
        _loaded=True
    return tuple(path.stem for path in sorted(fonts_dir().glob("*.ttf")))


def resolve_font_family(requested: str) -> str:
    """Keep missing OS fonts from falling back to the handwriting note font."""
    from PySide6.QtGui import QFontDatabase
    available=set(QFontDatabase.families())
    if requested in {"Inter Black","Inter Bold","Inter Medium"} and "Inter" in available:return "Inter"
    if requested in available:
        return requested
    fallback={"Arial":"Liberation Sans", "Segoe UI":"Liberation Sans",
              "Consolas":"Inconsolata", "Georgia":"DejaVu Sans"}.get(requested,"DejaVu Sans")
    return fallback if fallback in available else "Liberation Sans"
