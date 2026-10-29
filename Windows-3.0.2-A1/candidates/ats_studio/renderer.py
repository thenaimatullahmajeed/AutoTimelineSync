"""Bounded-cache, single video encode export using the bundled FFmpeg."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from dataclasses import asdict
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from typing import Callable

from . import __version__

from .media import bundled_binary
from .project_settings import CAPTION_PRESETS, CaptionSettings, FRAMING
from .schema import Caption, Package, PackageError, Scene, Word


@dataclass(frozen=True)
class RenderSettings:
    width: int = 1920
    height: int = 1080
    caption_preset: str = "Documentary Highlight"
    caption_size: int = 100
    caption_position: str = "Bottom"
    caption_max_lines: int = 2
    caption_safe_margin: int = 7
    caption_custom_y: int = 75
    framing: str = "Fill Frame"
    shake: bool = False
    shake_strength: int = 18
    noise: bool = False
    noise_strength: int = 12
    encoder_preset: str = "veryfast"
    crf: int = 20
    chunk_scenes: int = 12
    max_cache_gb: float = 8.0
    caption_font: str = "Arial"
    caption_text_color: str = "#FFFFFF"
    caption_highlight_color: str | None = None
    caption_background: str = "Dark Brush"
    caption_outline: int = 60
    caption_shadow: int = 40
    caption_outline_on: bool = True
    caption_shadow_on: bool = True
    backend: str = "LEGACY"
    style_preset: str = "CLEAN_DOC"
    auto_direct: bool = False
    strict_json: bool = False
    look_intensity: float = 0.8
    quality_tier: str = "STANDARD"
    workers: int = 1
    encoder: str = "CPU x264"
    sfx_density: float = 0.45
    sfx_intensity: str = 'PUNCHY'
    sfx_max_per_second: int = 3
    music_track: str = "STYLE_DEFAULT"
    music_path: str = ""
    music_volume: float = 1.0
    ambience: str = "STYLE_DEFAULT"
    master_mode: str = "LIMIT_ONLY"
    debug_stems: bool = False
    chunk_words: int = 3
    caption_animation: str = "POP"
    caption_safe_zone: str = "AUTO"

    @property
    def captions(self) -> CaptionSettings:
        return CaptionSettings(self.caption_preset, self.caption_size,
                               self.caption_position, self.caption_max_lines,
                               self.caption_safe_margin, self.caption_custom_y,
                               self.caption_font, self.caption_text_color,
                               self.caption_highlight_color, self.caption_background,
                               self.caption_outline, self.caption_shadow,
                               self.caption_outline_on, self.caption_shadow_on)


Progress = Callable[[str, float, str], None]


class RenderCancelled(Exception):
    pass


def _motion_expr(motion: str, frames: int) -> str:
    n = max(1, frames - 1)
    p = f"min(on/{n},1)"
    if motion == "STATIC":
        z, x, y = "1", "0", "0"
    elif motion == "SLOW_PUSH_IN":
        z, x, y = f"1+0.085*{p}", "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    elif motion == "SLOW_ZOOM_OUT":
        z, x, y = f"1.085-0.085*{p}", "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    elif motion == "PAN_RIGHT":
        z, x, y = "1.11", f"(iw-iw/zoom)*{p}", "(ih-ih/zoom)/2"
    elif motion == "PAN_LEFT":
        z, x, y = "1.11", f"(iw-iw/zoom)*(1-{p})", "(ih-ih/zoom)/2"
    elif motion == "PAN_DOWN":
        z, x, y = "1.11", "(iw-iw/zoom)/2", f"(ih-ih/zoom)*{p}"
    elif motion == "PAN_UP":
        z, x, y = "1.11", "(iw-iw/zoom)/2", f"(ih-ih/zoom)*(1-{p})"
    elif motion == "GENTLE_DIAGONAL":
        z, x, y = "1.10", f"(iw-iw/zoom)*{p}", f"(ih-ih/zoom)*{p}"
    elif motion == "KEN_BURNS":
        z, x, y = f"1.04+0.08*{p}", f"(iw-iw/zoom)*0.25*{p}", f"(ih-ih/zoom)*0.55*{p}"
    elif motion == "TINY_PUNCH_IN":
        z, x, y = f"1+0.055*min(on/{max(1,round(frames*0.35))},1)", "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    else:  # SUBTLE_PARALLAX: a restrained depth-like drift from one flat source.
        z, x, y = f"1.035+0.055*{p}", f"(iw-iw/zoom)*0.35*{p}", f"(ih-ih/zoom)*(0.35+0.2*{p})"
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}"


def _video_chain(input_index: int, label: str, frames: int, motion: str,
                  settings: RenderSettings, fps: int) -> str:
    zoom = _motion_expr(motion, frames)
    if settings.framing == "Fill Frame":
        frame = (f"scale={settings.width}:{settings.height}:force_original_aspect_ratio=increase,"
                 f"crop={settings.width}:{settings.height}")
    else:
        frame = (f"scale={settings.width}:{settings.height}:force_original_aspect_ratio=decrease,"
                 f"pad={settings.width}:{settings.height}:(ow-iw)/2:(oh-ih)/2:color=black")
    return (f"[{input_index}:v]{frame},{zoom}:s={settings.width}x{settings.height}:fps={fps},"
            f"trim=end_frame={frames},settb=1/{fps},"
            f"setsar=1,format=yuv420p[{label}]")


def _transition_name(value: str) -> str:
    return {
        "CROSSFADE": "fade", "GENTLE_DISSOLVE": "dissolve",
        "FADE_THROUGH_BLACK": "fadeblack", "FADE_THROUGH_WHITE": "fadewhite",
        "QUICK_PUSH": "slideleft",
    }[value]


def _ass_time(seconds: float) -> str:
    centis = max(0, round(seconds * 100))
    hours, remainder = divmod(centis, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def _ass_style(settings: RenderSettings) -> tuple[str, str, int, int]:
    captions = settings.captions
    size = captions.font_size(settings.height)
    margin = round(settings.height * captions.safe_margin / 100)
    if settings.caption_preset == "Documentary Highlight":
        return "&H00FFFFFF", "&H001CF09A", size, margin
    if settings.caption_preset == "Dark Cinematic":
        return "&H00E8EEF3", "&H00414358", size, margin
    return "&H00FFFFFF", "&H0000E9FF", size, margin


def _ass_color(hex_color: str) -> str:
    value = hex_color.lstrip("#")
    return f"&H00{value[4:6]}{value[2:4]}{value[0:2]}&"


def _caption_events(caption: Caption, words: tuple[Word, ...], local_start: float,
                    local_end: float, offset: float, highlight_color: str | None,
                    settings: RenderSettings) -> list[str]:
    relevant = [w for w in words if caption.word_start_index <= w.index <= caption.word_end_index]
    tokens = caption.text.split()
    if len(tokens) != len(relevant):
        tokens = [w.text for w in relevant]
    if not tokens:
        return []
    font_size, split = settings.captions.text_layout(tokens, settings.width, settings.height)
    position = (f"\\pos({settings.width//2},{round(settings.height*settings.caption_custom_y/100)})"
                if settings.caption_position == "Custom" else "")
    boundaries = [local_start, local_end]
    if highlight_color:
        boundaries.extend(w.start for w in relevant if local_start < w.start < local_end)
        boundaries.extend(w.end for w in relevant if local_start < w.end < local_end)
    boundaries = sorted(set(boundaries))
    events = []
    for start, end in zip(boundaries, boundaries[1:]):
        if end - start < 0.005:
            continue
        middle = (start + end) / 2
        active = next((i for i, w in enumerate(relevant) if w.start <= middle < w.end), None)
        parts = []
        for i, token in enumerate(tokens):
            escaped = _ass_escape(token)
            if i == active and highlight_color:
                escaped = "{\\c" + highlight_color + "}" + escaped + "{\\c" + _ass_color(settings.caption_text_color) + "}"
            parts.append(escaped)
        text = "".join((r"\N" if i == split else (" " if i else "")) + part
                       for i, part in enumerate(parts))
        text = "{\\fs" + str(font_size) + position + "}" + text
        events.append(
            f"Dialogue: 0,{_ass_time(start-offset)},{_ass_time(end-offset)},Default,,0,0,0,,{text}"
        )
    return events


def _write_ass(path: Path, package: Package, settings: RenderSettings,
               first_scene: Scene, last_scene: Scene) -> None:
    primary, secondary, size, margin = _ass_style(settings)
    primary = _ass_color(settings.caption_text_color)
    alignment = (8 if settings.caption_position == "Top" else
                 5 if settings.caption_position in {"Center", "Custom"} else 2)
    outline = round(5 * settings.caption_outline / 100, 1) if settings.caption_outline_on else 0
    shadow = round(3 * settings.caption_shadow / 100, 1) if settings.caption_shadow_on else 0
    border_style = 3 if settings.caption_background in {"Dark Brush", "Solid Box", "Paper"} else 1
    back_color = ("&H20000000" if settings.caption_background == "Solid Box" else
                  "&H60000000" if settings.caption_background == "Dark Brush" else
                  "&H00F5F5F5" if settings.caption_background == "Paper" else "&HFF000000")
    bold = 0 if settings.caption_preset in {"Typewriter", "Minimal Documentary", "Clean Subtitle"} else -1
    italic = -1 if settings.caption_preset == "Storytelling Pop" else 0
    wrap_style = 2 if settings.caption_max_lines == 1 else 0
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {settings.width}
PlayResY: {settings.height}
WrapStyle: {wrap_style}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{settings.caption_font},{size},{primary},{secondary},&H00000000,{back_color},{bold},{italic},0,0,100,100,0,0,{border_style},{outline},{shadow},{alignment},70,70,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    offset = first_scene.first_frame / package.fps
    end = last_scene.end_frame / package.fps
    lines = [header]
    highlight_color = None
    if package.highlight_current_word and settings.captions.highlight_color():
        color = settings.captions.highlight_color().lstrip("#")
        highlight_color = f"&H00{color[4:6]}{color[2:4]}{color[0:2]}&"
    for caption in package.captions:
        a, b = max(offset, caption.start), min(end, caption.end)
        if b <= a:
            continue
        lines.extend(_caption_events(caption, package.words, a, b, offset, highlight_color, settings))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _chunk_command(package: Package, scenes: tuple[Scene, ...], images: dict[str, Path],
                   settings: RenderSettings, work: Path, index: int) -> tuple[list[str], Path]:
    ffmpeg = str(bundled_binary("ffmpeg"))
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
               "-stats_period", "0.5", "-progress", "pipe:1"]
    graph: list[str] = []
    output_labels = []
    input_index = 0
    for scene in scenes:
        command += ["-i", str(images[scene.image_id])]
        main_label = f"main{scene.id}"
        graph.append(_video_chain(input_index, main_label, scene.frame_count,
                                  scene.motion, settings, package.fps))
        input_index += 1
        if scene.id != "001" and scene.transition not in {"HARD_CUT", "NONE"}:
            transition_frames = min(max(2, round(package.fps * (0.20 if scene.transition == "QUICK_PUSH" else 0.40))),
                                    scene.frame_count - 1)
            if transition_frames >= 2:
                previous = package.scenes[int(scene.id) - 2]
                command += ["-i", str(images[previous.image_id])]
                prev_label = f"prev{scene.id}"
                graph.append(_video_chain(input_index, prev_label, transition_frames,
                                          "STATIC", settings, package.fps))
                input_index += 1
                result_label = f"scene{scene.id}"
                graph.append(
                    f"[{prev_label}][{main_label}]xfade=transition={_transition_name(scene.transition)}:"
                    f"duration={transition_frames/package.fps:.6f}:offset=0,"
                    f"tpad=stop_mode=clone:stop={transition_frames+2},"
                    f"trim=end_frame={scene.frame_count}[{result_label}]"
                )
                output_labels.append(f"[{result_label}]")
                continue
        output_labels.append(f"[{main_label}]")
    graph.append("".join(output_labels) + f"concat=n={len(scenes)}:v=1:a=0[assembled]")
    label = "assembled"
    if settings.shake is True and settings.shake_strength > 0:
        amplitude = 1.0 + settings.shake_strength * 0.11
        graph.append(
            f"[{label}]scale={math.ceil(settings.width*1.04)}:{math.ceil(settings.height*1.04)},"
            f"crop={settings.width}:{settings.height}:"
            f"x='(in_w-out_w)/2+{amplitude:.2f}*sin(n*0.71)':"
            f"y='(in_h-out_h)/2+{amplitude:.2f}*sin(n*1.13)'[shaken]"
        )
        label = "shaken"
    if settings.noise:
        noise_value = max(1, round(settings.noise_strength * 0.45))
        graph.append(f"[{label}]noise=alls={noise_value}:allf=t+u[grained]")
        label = "grained"
    if package.captions_enabled and settings.caption_preset != "Off" and package.captions:
        ass_path = work / f"captions-{index:04d}.ass"
        _write_ass(ass_path, package, settings, scenes[0], scenes[-1])
        graph.append(f"[{label}]ass={ass_path.name}[captioned]")
        label = "captioned"
    graph.append(f"[{label}]format=yuv420p[outv]")
    script = work / f"graph-{index:04d}.txt"
    script.write_text(";\n".join(graph), encoding="utf-8")
    target = work / f"chunk-{index:04d}.mp4"
    command += ["-filter_complex_script", script.name, "-map", "[outv]",
                "-an", "-frames:v", str(sum(s.frame_count for s in scenes)),
                "-c:v", "libx264", "-preset", settings.encoder_preset, "-crf", str(settings.crf),
                "-pix_fmt", "yuv420p", "-r", str(package.fps), "-g", str(package.fps * 2),
                "-bf", "0", "-y", target.name]
    return command, target


def _working_set_bytes(handle: int) -> int:
    """Windows working-set sample; zero on hosts without the native API."""
    if os.name != "nt":
        return 0
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    api = ctypes.windll.psapi.GetProcessMemoryInfo
    api.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_uint32]
    api.restype = ctypes.c_int
    return int(counters.WorkingSetSize) if api(ctypes.c_void_p(handle), ctypes.byref(counters), counters.cb) else 0


def _run_ffmpeg(command: list[str], cwd: Path, cancel: threading.Event,
                on_line: Callable[[dict[str, str]], None],
                monitor: Callable[[subprocess.Popen], None] | None = None) -> None:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, bufsize=1, creationflags=creationflags)
    lines: queue.Queue[str] = queue.Queue()
    errors: deque[str] = deque(maxlen=30)

    def read_stdout() -> None:
        assert process.stdout
        for line in process.stdout:
            lines.put(line.rstrip("\r\n"))

    def read_stderr() -> None:
        assert process.stderr
        for line in process.stderr:
            errors.append(line.rstrip("\r\n"))

    threading.Thread(target=read_stdout, daemon=True).start()
    threading.Thread(target=read_stderr, daemon=True).start()
    status: dict[str, str] = {}
    try:
        while process.poll() is None or not lines.empty():
            if monitor is not None:
                monitor(process)
            if cancel.is_set():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise RenderCancelled()
            try:
                line = lines.get(timeout=0.25)
            except queue.Empty:
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                status[key] = value
                if key == "progress":
                    on_line(status.copy())
                    status.clear()
        code = process.wait(timeout=5)
        if code:
            detail = "\n".join(errors) or f"FFmpeg exited with code {code}."
            raise PackageError(detail[-3000:])
    finally:
        if process.poll() is None:
            process.kill()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()


def _concat_manifest(path: Path, chunks: list[Path]) -> None:
    lines = ["ffconcat version 1.0"]
    for chunk in chunks:
        lines.append(f"file '{chunk.name}'")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _cleanup_stale_work(output_dir: Path) -> int:
    """Remove only this app's marked, old temporary sessions in the selected folder."""
    cleaned = 0
    now = time.time()
    for entry in os.scandir(output_dir):
        if not entry.is_dir(follow_symlinks=False):
            continue
        if not re.fullmatch(r"\..+\.ats-work-[0-9a-f]{10}", entry.name):
            continue
        folder = Path(entry.path)
        marker = folder / ".ats-temporary-session.json"
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
            if data.get("ats_temp") != 1 or now-float(data["created"]) < 24*3600:
                continue
            if folder.resolve().parent != output_dir.resolve():
                continue
            shutil.rmtree(folder)
            cleaned += 1
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return cleaned


def _probe_video(path: Path, package: Package, settings: RenderSettings) -> dict:
    command = [str(bundled_binary("ffprobe")), "-v", "error", "-show_entries",
               "format=duration:stream=codec_name,codec_type,width,height,nb_frames,duration,"
               "r_frame_rate,pix_fmt,color_range,color_space,color_primaries,color_transfer,sample_rate,channels",
               "-of", "json", str(path)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=45,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if done.returncode:
        raise PackageError(f"Export validation failed: {done.stderr.strip()}")
    data = json.loads(done.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not video or not audio:
        raise PackageError("Export validation failed: video or audio stream is missing.")
    if video.get("width") != settings.width or video.get("height") != settings.height:
        raise PackageError("Export validation failed: output dimensions are incorrect.")
    try:
        video_frames = int(video["nb_frames"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PackageError("Export validation failed: output frame count is unavailable.") from exc
    if video_frames != package.total_frames:
        raise PackageError(
            f"Export validation failed: expected {package.total_frames} video frames, got {video_frames}."
        )
    if abs(float(data["format"]["duration"]) - package.audio_duration) > max(0.15, 3/package.fps):
        raise PackageError("Export validation failed: output duration differs from the package.")
    return data


def _export_seed(package: Package) -> int:
    identity = f"{package.title}\0{package.audio_duration}\0{len(package.scenes)}"
    return int.from_bytes(hashlib.sha256(identity.encode("utf-8")).digest()[:8], "big")


def _caption_event_count(work: Path) -> int:
    return sum(path.read_text(encoding="utf-8").count("\nDialogue:")
               for path in work.glob("captions-*.ass"))


def export_video(package: Package, images: dict[str, Path], audio_path: Path,
                 output_path: Path, settings: RenderSettings,
                 cancel: threading.Event, progress: Progress) -> dict[str, float]:
    """Encode compressed chunks once, then mux with stream-copy video."""
    if settings.backend != "LEGACY" or package.schema_version != "ATS_PACKAGE_V1":
        raise PackageError("This ATS edition exports ATS_PACKAGE_V1 still-image timelines only.")
    if output_path.exists():
        raise PackageError(f"Output already exists: {output_path}. Choose another name.")
    if settings.caption_preset not in CAPTION_PRESETS:
        raise PackageError("Unknown caption preset.")
    if settings.framing not in FRAMING:
        raise PackageError("Unknown image framing.")
    settings.captions
    if settings.width % 2 or settings.height % 2 or min(settings.width, settings.height) < 240:
        raise PackageError("Output dimensions must be even and at least 240 pixels.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output_path.parent).free < 256 * 1024**2:
        raise PackageError("Less than 256 MB of free space is available for export.")
    log_path = output_path.with_name(output_path.name + ".log")
    report_path = output_path.with_name(output_path.name + ".report.json")
    log_path.write_text(f"ATS {__version__} export\nOutput: {output_path}\n"
                        f"Settings: {json.dumps(asdict(settings), ensure_ascii=False, sort_keys=True)}\n",
                        encoding="utf-8")
    last_log = [0.0, ""]

    def announce(stage: str, percent: float, detail: str) -> None:
        progress(stage, percent, detail)
        now = time.monotonic()
        if stage != last_log[1] or now - last_log[0] >= 5:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {percent:.2f}% {stage}: {detail}\n")
            last_log[:] = [now, stage]

    cleaned = _cleanup_stale_work(output_path.parent)
    if cleaned:
        announce("Cleanup", 0, f"Removed {cleaned} stale ATS temporary session(s)")
    token = uuid.uuid4().hex[:10]
    session_dir = output_path.parent / f".{output_path.stem}.ats-work-{token}"
    session_dir.mkdir(parents=False, exist_ok=False)
    (session_dir / ".ats-temporary-session.json").write_text(
        json.dumps({"ats_temp": 1, "created": time.time()}), encoding="utf-8"
    )
    partial = output_path.with_name(f".{output_path.stem}.{token}.part.mp4")
    chunks: list[Path] = []
    peak_cache = 0
    peak_ram_bytes = 0
    completed_frames = 0
    started = time.monotonic()
    stage_times: dict[str, float | list[float]] = {"chunks_s": []}
    try:
        groups = [package.scenes[i:i+settings.chunk_scenes]
                  for i in range(0, len(package.scenes), settings.chunk_scenes)]
        for i, scenes in enumerate(groups, 1):
            if cancel.is_set():
                raise RenderCancelled()
            command, chunk = _chunk_command(package, scenes, images, settings, session_dir, i)
            count = sum(scene.frame_count for scene in scenes)
            announce("Rendering video", completed_frames / package.total_frames * 94,
                     f"Chunk {i}/{len(groups)} · scene {scenes[0].id}–{scenes[-1].id}")

            def on_chunk(status: dict[str, str], base: int = completed_frames) -> None:
                try:
                    current = min(count, int(status.get("frame", "0")))
                except ValueError:
                    current = 0
                speed = status.get("speed", "")
                announce("Rendering video", (base + current) / package.total_frames * 94,
                         f"Scene {scenes[0].id}–{scenes[-1].id} · {base+current:,}/{package.total_frames:,} frames · {speed}")

            def monitor_chunk(process: subprocess.Popen) -> None:
                nonlocal peak_cache, peak_ram_bytes
                current_bytes = chunk.stat().st_size if chunk.exists() else 0
                consumed = sum(p.stat().st_size for p in chunks) + current_bytes
                peak_cache = max(peak_cache, consumed)
                peak_ram_bytes = max(peak_ram_bytes,
                                     _working_set_bytes(int(process._handle)) +
                                     _working_set_bytes(int(ctypes.windll.kernel32.GetCurrentProcess()))) if os.name == "nt" else peak_ram_bytes
                if consumed > settings.max_cache_gb * 1024**3:
                    raise PackageError(
                        f"Temporary video reached {consumed/1024**3:.1f} GB. "
                        "Export stopped at the selected cache limit."
                    )
                if shutil.disk_usage(output_path.parent).free < 64 * 1024**2:
                    raise PackageError("Export stopped: less than 64 MB of free disk space remains.")

            chunk_started = time.monotonic()
            _run_ffmpeg(command, session_dir, cancel, on_chunk, monitor_chunk)
            stage_times["chunks_s"].append(round(time.monotonic() - chunk_started, 3))
            if not chunk.exists() or chunk.stat().st_size == 0:
                raise PackageError(f"Chunk {i} produced no video.")
            chunks.append(chunk)
            completed_frames += count
            peak_cache = max(peak_cache, sum(p.stat().st_size for p in chunks))
            if peak_cache > settings.max_cache_gb * (1024**3):
                raise PackageError(
                    f"Temporary video reached {peak_cache/1024**3:.1f} GB. "
                    "Export stopped at the selected cache limit."
                )
        caption_events = _caption_event_count(session_dir)
        captions_requested = package.captions_enabled and bool(package.captions)
        captions_active = captions_requested and settings.caption_preset != "Off"
        if captions_active and caption_events == 0:
            raise PackageError("Captions were requested, but no ASS dialogue was generated. Export stopped.")
        manifest = session_dir / "chunks.ffconcat"
        _concat_manifest(manifest, chunks)
        announce("Finalizing MP4", 94, "Joining encoded chunks and audio without video re-encode")
        command = [str(bundled_binary("ffmpeg")), "-hide_banner", "-loglevel", "error",
                   "-nostdin", "-stats_period", "0.5", "-progress", "pipe:1",
                   "-f", "concat", "-safe", "0", "-i", manifest.name,
                   "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0",
                   "-c:v", "copy",
                   "-c:a", "aac", "-b:a", "192k", "-y", str(partial)]

        def on_mux(status: dict[str, str]) -> None:
            value = status.get("out_time", "00:00:00")
            try:
                hours, minutes, seconds = value.split(":")
                done = int(hours)*3600 + int(minutes)*60 + float(seconds)
            except (ValueError, TypeError):
                done = 0
            announce("Finalizing MP4", 94 + min(5, done/package.audio_duration*5),
                     f"Audio + video mux · {status.get('speed', '')}")

        mux_started = time.monotonic()
        def monitor_mux(process: subprocess.Popen) -> None:
            nonlocal peak_ram_bytes
            if os.name == "nt":
                peak_ram_bytes = max(peak_ram_bytes,
                    _working_set_bytes(int(process._handle)) +
                    _working_set_bytes(int(ctypes.windll.kernel32.GetCurrentProcess())))

        _run_ffmpeg(command, session_dir, cancel, on_mux, monitor_mux)
        stage_times["mux_s"] = round(time.monotonic() - mux_started, 3)
        announce("Verifying", 99, "Checking output streams and duration")
        verify_started = time.monotonic()
        facts = _probe_video(partial, package, settings)
        stage_times["verify_s"] = round(time.monotonic() - verify_started, 3)
        os.replace(partial, output_path)
        video = next(s for s in facts["streams"] if s["codec_type"] == "video")
        audio = next(s for s in facts["streams"] if s["codec_type"] == "audio")
        report = {
            "tool_version": __version__, "render_backend": "Legacy FFmpeg v1.2.2",
            "package_sha256": hashlib.sha256(package.source_json.encode("utf-8")).hexdigest(),
            "seed": _export_seed(package), "settings": asdict(settings),
            "quality_tier": "Legacy higher quality" if settings.encoder_preset == "medium" else "Legacy fast",
            "encoder": "libx264", "stage_timings": stage_times,
            "peak_cache_gb": peak_cache / 1024**3,
            "peak_ram_mb": round(peak_ram_bytes / 1024**2, 1) if peak_ram_bytes else None,
            "scenes": [{"id": s.id, "motion": s.motion,
                        "motion_params": None, "ease": "LINEAR", "focus_source": "center",
                        "transition_requested": s.transition,
                        "transition_applied": (s.transition if s.id == "001" or s.transition in {"HARD_CUT", "NONE"}
                                               or min(max(2, round(package.fps * (0.20 if s.transition == "QUICK_PUSH" else 0.40))),
                                                      s.frame_count - 1) >= 2 else "HARD_CUT"),
                        "look": None, "sfx_cues": [], "overlays": []} for s in package.scenes],
            "captions": {"requested": captions_requested, "active": captions_active,
                         "package_intervals": len(package.captions), "ass_dialogue_events": caption_events,
                         "pixel_verified": False},
            "audio_stats": {"before_aac": None, "after_aac": None, "master_iterations": 0},
            "auto_direct": {"enabled": False, "changes": {}},
            "warnings": (["Package requests captions, but the project caption preset is Off."]
                         if captions_requested and not captions_active else []),
            "final_file": {"path": str(output_path), "bytes": output_path.stat().st_size,
                           "duration_s": float(facts["format"]["duration"]),
                           "width": video["width"], "height": video["height"],
                           "fps": video.get("r_frame_rate"), "frames": int(video["nb_frames"]),
                           "color_range": video.get("color_range"), "color_space": video.get("color_space"),
                           "color_primaries": video.get("color_primaries"),
                           "color_transfer": video.get("color_transfer"),
                           "audio_codec": audio.get("codec_name"), "sample_rate": audio.get("sample_rate")},
        }
        from .capabilities import current_capabilities
        report["capabilities"] = current_capabilities()
        stage_times["total_s"] = round(time.monotonic() - started, 3)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        announce("Complete", 100, f"Saved {output_path.name}")
        return {"elapsed_seconds": time.monotonic()-started,
                "peak_cache_gb": peak_cache/1024**3,
                 "output_gb": output_path.stat().st_size/1024**3,
                 "report_path": str(report_path), "log_path": str(log_path)}
    except Exception as exc:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"FAILED: {type(exc).__name__}: {exc}\n")
        raise
    finally:
        if partial.exists():
            partial.unlink()
        shutil.rmtree(session_dir, ignore_errors=True)
