"""The ATS_PACKAGE_V1 contract shared by the UI and renderer."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal, DecimalException, ROUND_HALF_UP
import json
import math
import re
from typing import Any


MOTIONS = frozenset({
    "STATIC", "SLOW_PUSH_IN", "SLOW_ZOOM_OUT", "PAN_LEFT", "PAN_RIGHT",
    "PAN_UP", "PAN_DOWN", "GENTLE_DIAGONAL", "KEN_BURNS",
    "TINY_PUNCH_IN", "SUBTLE_PARALLAX",
})
TRANSITIONS = frozenset({
    "HARD_CUT", "CROSSFADE", "GENTLE_DISSOLVE", "FADE_THROUGH_BLACK",
    "FADE_THROUGH_WHITE", "QUICK_PUSH", "NONE",
})
from .visual_director import TRANSITIONS as DIRECTOR_TRANSITIONS
TRANSITIONS = TRANSITIONS | DIRECTOR_TRANSITIONS
MOTIONS = MOTIONS | {"STATIC_HOLD", "SLOW_PULL_OUT", "IMPACT_PUNCH_IN"}
TOP_FIELDS = frozenset({
    "schema", "project_title", "audio_duration", "fps", "scenes", "words",
    "captions", "caption_style",
})
SCENE_FIELDS = frozenset({
    "id", "image_id", "start", "end", "voice_text", "motion", "transition",
})
WORD_FIELDS = frozenset({"index", "start", "end", "text"})
CAPTION_FIELDS = frozenset({
    "id", "start", "end", "text", "word_start_index", "word_end_index",
})
CAPTION_STYLE_FIELDS = frozenset({"enabled", "highlight_current_word"})
MAX_PACKAGE_BYTES = 50 * 1024 * 1024


class PackageError(ValueError):
    """An actionable JSON, schema, or timeline validation error."""


@dataclass(frozen=True)
class Scene:
    id: str
    image_id: str
    start: float
    end: float
    voice_text: str
    motion: str
    transition: str
    first_frame: int
    end_frame: int

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.first_frame


@dataclass(frozen=True)
class Word:
    index: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Caption:
    id: str
    start: float
    end: float
    text: str
    word_start_index: int
    word_end_index: int


@dataclass(frozen=True)
class Package:
    title: str
    audio_duration: float
    fps: int
    scenes: tuple[Scene, ...]
    words: tuple[Word, ...]
    captions: tuple[Caption, ...]
    captions_enabled: bool
    highlight_current_word: bool
    total_frames: int
    source_json: str
    schema_version: str = "ATS_PACKAGE_V1"
    pro: dict = field(default_factory=dict)


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PackageError(f"{label} must be a number.")
    try:
        value = float(value)
    except (OverflowError, ValueError) as exc:
        raise PackageError(f"{label} must be finite.") from exc
    if not math.isfinite(value):
        raise PackageError(f"{label} must be finite.")
    return value


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PackageError(f"{label} must be an integer.")
    return value


def _fields(value: Any, required: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise PackageError(f"{label} must be an object.")
    missing = sorted(required - value.keys())
    extra = sorted(value.keys() - required)
    if missing:
        raise PackageError(f"{label} is missing: {', '.join(missing)}.")
    if extra:
        raise PackageError(f"{label} contains unsupported field(s): {', '.join(extra)}.")
    return value


def _pairs_unique(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PackageError(f'Duplicate JSON key: "{key}".')
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PackageError(f"Invalid JSON number: {value}.")


def _normalize_json_text(text: str) -> str:
    text = text.lstrip("\ufeff").strip()
    fence = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", text, re.I | re.S)
    if fence:
        text = fence.group(1).strip()
    return text


def frame_at(seconds: float, fps: int) -> int:
    try:
        return int((Decimal(str(seconds)) * fps).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (DecimalException, OverflowError, ValueError) as exc:
        raise PackageError("Timeline time is too large for frame-accurate processing.") from exc


def parse_package(text: str) -> Package:
    """Accept normal JSON whitespace and optional complete Markdown fences."""
    if not isinstance(text, str):
        raise PackageError("Paste one ATS_PACKAGE_V1 JSON object first.")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError as exc:
        raise PackageError("Package text must be valid UTF-8.") from exc
    if size > MAX_PACKAGE_BYTES:
        raise PackageError("ATS JSON exceeds the 50 MB safety limit.")
    source = _normalize_json_text(text)
    if not source:
        raise PackageError("Paste one ATS_PACKAGE_V1 JSON object first.")
    try:
        raw = json.loads(source, object_pairs_hook=_pairs_unique, parse_constant=_reject_constant)
    except PackageError:
        raise
    except json.JSONDecodeError as exc:
        raise PackageError(f"JSON syntax error at line {exc.lineno}, column {exc.colno}: {exc.msg}.") from exc
    except ValueError as exc:
        raise PackageError(f"JSON number or value is too large: {exc}.") from exc
    if isinstance(raw, dict) and raw.get("schema") in {"ATS_PACKAGE_V2", "ATS_PACKAGE_V3"}:
        raise PackageError("This ATS edition accepts ATS_PACKAGE_V1 still-image timelines only. Layered packages are no longer supported.")
    top = _fields(raw, TOP_FIELDS, "Package")
    if top["schema"] != "ATS_PACKAGE_V1":
        raise PackageError('Package schema must be "ATS_PACKAGE_V1".')
    title = top["project_title"]
    if not isinstance(title, str) or not title.strip():
        raise PackageError("project_title must be nonempty text.")
    duration = _number(top["audio_duration"], "audio_duration")
    if duration <= 0:
        raise PackageError("audio_duration must be greater than zero.")
    fps = _integer(top["fps"], "fps")
    if not 1 <= fps <= 60:
        raise PackageError("fps must be between 1 and 60.")
    if not isinstance(top["scenes"], list) or not top["scenes"]:
        raise PackageError("scenes must be a nonempty array.")
    if not isinstance(top["words"], list):
        raise PackageError("words must be an array.")
    if not isinstance(top["captions"], list):
        raise PackageError("captions must be an array.")
    style = _fields(top["caption_style"], CAPTION_STYLE_FIELDS, "caption_style")
    if not all(isinstance(style[key], bool) for key in CAPTION_STYLE_FIELDS):
        raise PackageError("caption_style values must be true or false.")

    total_frames = frame_at(duration, fps)
    scenes: list[Scene] = []
    for i, entry in enumerate(top["scenes"], 1):
        label = f"Scene {i:03d}"
        if not isinstance(entry, dict):
            raise PackageError(f"{label} must be an object.")
        # Keep old explicit choices; omitted visual fields are filled during Sync.
        obj = _fields({"motion": "STATIC", "transition": "HARD_CUT", **entry}, SCENE_FIELDS, label)
        sid, iid = obj["id"], obj["image_id"]
        if not isinstance(sid, str) or not re.fullmatch(r"\d{3,}", sid):
            raise PackageError(f"{label} id must be zero-padded numeric text such as 001.")
        if sid != f"{i:03d}":
            raise PackageError(f'{label} id should be "{i:03d}", received "{sid}".')
        if iid != sid:
            raise PackageError(f'{label} image_id must match its id "{sid}".')
        start = _number(obj["start"], f"{label} start")
        end = _number(obj["end"], f"{label} end")
        if start < 0 or end <= start:
            raise PackageError(f"{label} needs 0 <= start < end.")
        first_frame, end_frame = frame_at(start, fps), frame_at(end, fps)
        if end_frame <= first_frame:
            raise PackageError(f"{label} is shorter than one output frame at {fps} FPS.")
        if scenes and first_frame != scenes[-1].end_frame:
            kind = "gap" if first_frame > scenes[-1].end_frame else "overlap"
            raise PackageError(f"{label} has a {kind} after scene {i-1:03d} at output-frame precision.")
        if not scenes and first_frame != 0:
            raise PackageError("First scene must start at timeline origin (frame 0).")
        voice = obj["voice_text"]
        if not isinstance(voice, str):
            raise PackageError(f"{label} voice_text must be text.")
        motion, transition = obj["motion"], obj["transition"]
        if isinstance(motion,str):
            motion = {"STATIC_HOLD":"STATIC", "SLOW_PULL_OUT":"SLOW_ZOOM_OUT",
                      "IMPACT_PUNCH_IN":"TINY_PUNCH_IN"}.get(motion,motion)
        if not isinstance(motion, str) or not isinstance(transition, str):
            raise PackageError(f"{label} motion and transition values must be text.")
        # Keep V1 package compatibility while rendering stills with hard cuts only.
        scenes.append(Scene(sid, iid, start, end, voice, "STATIC", "HARD_CUT", first_frame, end_frame))
    if scenes[-1].end_frame != total_frames:
        raise PackageError(
            f"Last scene ends at frame {scenes[-1].end_frame}; audio_duration requires frame {total_frames}."
        )

    words: list[Word] = []
    seen_indexes: set[int] = set()
    for i, entry in enumerate(top["words"], 1):
        label = f"Word entry {i}"
        obj = _fields(entry, WORD_FIELDS, label)
        index = _integer(obj["index"], f"{label} index")
        start = _number(obj["start"], f"{label} start")
        end = _number(obj["end"], f"{label} end")
        if index in seen_indexes or (words and index <= words[-1].index):
            raise PackageError(f"{label} index must be unique and increasing.")
        if start < 0 or end <= start or end > duration + 1 / fps:
            raise PackageError(f"{label} timing is outside the audio.")
        if words and start < words[-1].start:
            raise PackageError(f"{label} is out of chronological order.")
        if not isinstance(obj["text"], str) or not obj["text"].strip():
            raise PackageError(f"{label} text must be nonempty.")
        words.append(Word(index, start, end, obj["text"]))
        seen_indexes.add(index)

    captions: list[Caption] = []
    for i, entry in enumerate(top["captions"], 1):
        label = f"Caption {i:03d}"
        obj = _fields(entry, CAPTION_FIELDS, label)
        cid = obj["id"]
        if not isinstance(cid, str) or cid != f"{i:03d}":
            raise PackageError(f'{label} id should be "{i:03d}".')
        start = _number(obj["start"], f"{label} start")
        end = _number(obj["end"], f"{label} end")
        if start < 0 or end <= start or end > duration + 1 / fps:
            raise PackageError(f"{label} timing is outside the audio.")
        if captions and start < captions[-1].start:
            raise PackageError(f"{label} is out of chronological order.")
        if not isinstance(obj["text"], str) or not obj["text"].strip():
            raise PackageError(f"{label} text must be nonempty.")
        first = _integer(obj["word_start_index"], f"{label} word_start_index")
        last = _integer(obj["word_end_index"], f"{label} word_end_index")
        if first > last or first not in seen_indexes or last not in seen_indexes:
            raise PackageError(f"{label} references missing or reversed word indexes.")
        captions.append(Caption(cid, start, end, obj["text"], first, last))

    return Package(title.strip(), duration, fps, tuple(scenes), tuple(words), tuple(captions),
                   style["enabled"], style["highlight_current_word"], total_frames, source)
