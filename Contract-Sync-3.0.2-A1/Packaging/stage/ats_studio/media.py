"""Read-only discovery and validation of audio and numbered source images."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from .schema import Package, PackageError, frame_at


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def bundled_binary(name: str) -> Path:
    filename = f"{name}.exe" if os.name == "nt" else name
    roots = [Path(sys.executable).resolve().parent]
    if getattr(sys, "_MEIPASS", None):
        roots.append(Path(sys._MEIPASS))
    roots.append(Path(__file__).resolve().parents[1])
    for root in roots:
        for candidate in (root / "runtime" / "ffmpeg" / filename,
                          root / "_internal" / "runtime" / "ffmpeg" / filename):
            if candidate.is_file():
                return candidate
    # Development fallback only; the packaged application includes its own binaries.
    installed = Path("C:/Program Files/Auto Timeline Sync/runtime/ffmpeg") / filename
    if installed.is_file():
        return installed
    found = shutil.which(filename)
    if found:
        return Path(found)
    raise PackageError(f"Bundled {filename} was not found. Reinstall the complete ATS folder.")


def scan_images(folder: Path) -> tuple[dict[str, Path], list[str]]:
    if not folder.is_dir():
        raise PackageError(f"Image folder does not exist: {folder}")
    images: dict[str, Path] = {}
    warnings: list[str] = []
    for entry in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_file() or entry.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if not re.fullmatch(r"\d{3,}", entry.stem):
            warnings.append(f"Ignored unnumbered image: {entry.name}")
            continue
        if entry.stem in images:
            raise PackageError(
                f'Duplicate image ID {entry.stem}: {images[entry.stem].name} and {entry.name}.'
            )
        images[entry.stem] = entry
    if not images:
        raise PackageError("No numbered PNG, JPG, JPEG or WebP files were found.")
    return images, warnings


def probe_audio(path: Path) -> tuple[float, str]:
    if not path.is_file():
        raise PackageError(f"Audio file does not exist: {path}")
    command = [str(bundled_binary("ffprobe")), "-v", "error", "-show_entries",
               "format=duration:stream=codec_name,codec_type", "-of", "json", str(path)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=45,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if done.returncode:
        raise PackageError(f"Cannot read audio: {done.stderr.strip() or path.name}")
    try:
        info = json.loads(done.stdout)
        duration = float(info["format"]["duration"])
        audio_stream = next(s for s in info["streams"] if s["codec_type"] == "audio")
        codec = audio_stream["codec_name"]
    except (KeyError, ValueError, StopIteration, TypeError) as exc:
        raise PackageError("Selected file has no readable audio stream or duration.") from exc
    if duration <= 0:
        raise PackageError("Audio duration must be greater than zero.")
    return duration, codec


def validate_media(package: Package, audio_path: Path, image_folder: Path) -> tuple[dict[str, Path], float, list[str]]:
    synthetic_canvas=package.schema_version=='ATS_PACKAGE_V3' and package.pro.get('composition',{}).get('show_plates') is False
    try:images, warnings = scan_images(image_folder)
    except PackageError as exc:
        if synthetic_canvas and image_folder.is_dir() and str(exc)=='No numbered PNG, JPG, JPEG or WebP files were found.':images={};warnings=[]
        else:raise
    if synthetic_canvas:
        from .user_data import user_data_root
        from PIL import Image
        background=user_data_root()/'layer-assets'/'virtual-canvas.png';background.parent.mkdir(parents=True,exist_ok=True)
        if not background.exists():Image.new('RGB',(360,640),'#E5E5E5').save(background)
        referenced={layer['image_id'] for layer in package.pro.get('layers',[]) if 'image_id' in layer}
        for scene in package.scenes:
            if scene.image_id not in images and scene.image_id not in referenced:images[scene.image_id]=background
    for scene in package.scenes:
        if scene.image_id not in images:
            raise PackageError(
                f'Scene {scene.id} references image_id "{scene.image_id}", but no matching image was found.'
            )
    layer_stems={a['file'] for a in package.pro.get('assets',[]) if a.get('source','IMAGE')=='IMAGE'}
    for stem in layer_stems:
        if stem not in images:raise PackageError(f'Layer asset {stem} is missing from the selected image folder.')
    unused = set(images) - {scene.image_id for scene in package.scenes} - layer_stems
    if unused:
        warnings.append(f"{len(unused)} extra numbered image(s) are not used by this package.")
    actual_duration, _ = probe_audio(audio_path)
    if abs(frame_at(actual_duration, package.fps) - package.total_frames) > 1:
        raise PackageError(
            f"Audio is {actual_duration:.3f}s but package says {package.audio_duration:.3f}s. "
            "Use the final audio and its matching JSON."
        )
    if abs(actual_duration - package.audio_duration) > 0.005:
        warnings.append(
            f"Audio duration differs by {abs(actual_duration-package.audio_duration)*1000:.0f} ms; "
            "this is within one output frame."
        )
    return images, actual_duration, warnings


def preflight_pro_media(package: Package, images: dict[str, Path], width: int,
                        height: int, framing: str) -> list[str]:
    """Decode image thumbnails outside the UI thread and collect actionable QA warnings."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImageReader

    def inspect(entry: tuple[str, Path]) -> tuple[str, float, int]:
        image_id, path = entry
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        size = reader.size()
        if not size.isValid():
            raise PackageError(f"CORRUPT_IMAGE [{image_id}]: Cannot read image header: {path.name}")
        reader.setScaledSize(size.scaled(16, 16, Qt.IgnoreAspectRatio))
        thumb = reader.read()
        if thumb.isNull():
            raise PackageError(f"CORRUPT_IMAGE [{image_id}]: {path.name}: {reader.errorString()}")
        pixels = [thumb.pixelColor(x,y) for y in range(16) for x in range(16)]
        gray = [c.red()*3+c.green()*6+c.blue() for c in pixels]
        mean = sum(gray)/len(gray)
        bits = sum((1 << i) for i,value in enumerate(gray[:64]) if value >= mean)
        return image_id, size.width()/size.height(), bits

    with ThreadPoolExecutor(max_workers=4) as pool:
        details = dict((key,(ratio,bits)) for key,ratio,bits in pool.map(inspect, images.items()))
    warnings=[]
    used={scene.image_id for scene in package.scenes}
    output_ratio=width/height
    crop=[]
    for image_id in sorted(used):
        ratio=details[image_id][0]
        if min(ratio/output_ratio,output_ratio/ratio)<.75:crop.append(image_id)
    if crop:
        warnings.append(f"ASPECT_MISMATCH: {len(crop)} plate(s) differ by more than 25%; affected scene/image ids: {', '.join(crop)}. Framing: {framing}.")
    duplicates=[]
    for before,after in zip(package.scenes,package.scenes[1:]):
        if before.image_id!=after.image_id and details[before.image_id][1]==details[after.image_id][1]:
            duplicates.append(after.id)
    if duplicates:
        warnings.append(f"DUPLICATE_IMAGE: {len(duplicates)} consecutive scene pair(s) look alike; first scene {duplicates[0]}.")
    short=[s.id for s in package.scenes if s.frame_count/package.fps<.8]
    long=[s.id for s in package.scenes if s.frame_count/package.fps>6]
    if short:warnings.append(f"SHORT_HOLD: {len(short)} scene(s) under 0.8 s; first scene {short[0]}.")
    if long and not (package.schema_version=='ATS_PACKAGE_V3' and package.pro.get('composition',{}).get('show_plates') is False):warnings.append(f"LONG_HOLD: {len(long)} scene(s) over 6 s; first scene {long[0]}.")
    fast=[c.id for c in package.captions if len(c.text)/(c.end-c.start)>20]
    if fast:warnings.append(f"FAST_CAPTION: {len(fast)} caption(s) exceed 20 characters/s; first {fast[0]}.")
    return warnings


def aspect_report(package, images, width, height, policy):
    from PySide6.QtGui import QImageReader
    result=[];output=width/height
    for scene in package.scenes:
        size=QImageReader(str(images[scene.image_id])).size()
        if size.isValid():
            ratio=size.width()/size.height();difference=1-min(ratio/output,output/ratio)
            if difference>.25:result.append({'scene_id':scene.id,'source_dimensions':[size.width(),size.height()],'source_ratio':ratio,'output_ratio':output,'difference_fraction':difference,'policy':policy})
    return result
