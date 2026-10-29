"""Paths to packaged visual assets."""

from pathlib import Path
import sys


def icon_path(name: str = "AutoTimelineSync.ico") -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "assets" / "icons" / name
