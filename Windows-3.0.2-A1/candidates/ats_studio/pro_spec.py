"""Deterministic, frame-aligned decisions shared by Pro preview and export."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from .schema import Package, PackageError


MOTION_PATHS = {
    "STATIC": (1.0, 1.0, 0, 0, 0, 0, "LINEAR"),
    "SLOW_PUSH_IN": (1.0, 1.085, 0, 0, 0, 0, "EASE_IN_OUT"),
    "SLOW_ZOOM_OUT": (1.085, 1.0, 0, 0, 0, 0, "EASE_IN_OUT"),
    "PAN_RIGHT": (1.11, 1.11, -.5, 0, .5, 0, "LINEAR"),
    "PAN_LEFT": (1.11, 1.11, .5, 0, -.5, 0, "LINEAR"),
    "PAN_DOWN": (1.11, 1.11, 0, -.5, 0, .5, "LINEAR"),
    "PAN_UP": (1.11, 1.11, 0, .5, 0, -.5, "LINEAR"),
    "GENTLE_DIAGONAL": (1.10, 1.10, -.4, -.4, .4, .4, "LINEAR"),
    "KEN_BURNS": (1.04, 1.12, -.22, -.15, .22, .20, "EASE_IN_OUT"),
    "TINY_PUNCH_IN": (1.0, 1.055, 0, 0, 0, 0, "EASE_OUT"),
    "SUBTLE_PARALLAX": (1.035, 1.09, -.25, -.1, .25, .1, "EASE_IN_OUT"),
}


def _presets_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "presets"


def user_presets_dir() -> Path:
    return Path(os.environ.get("APPDATA",str(Path.home()/"AppData"/"Roaming"))) / "AutoTimelineSync" / "presets"


def load_preset(kind: str, name: str) -> dict:
    if kind not in {"styles","looks"} or not name.replace("_","").isalnum():
        raise PackageError("Invalid preset kind or ID.")
    path = _presets_dir() / kind / f"{name}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PackageError(f"Installed {kind} preset {name} is missing or invalid.") from exc
    if data.get("id") != name:
        raise PackageError(f"Installed {kind} preset {name} has an invalid id.")
    required=({"look","transition_palette","transition_variety","sfx_density",
               "music","ambience","handheld","caption_preset"} if kind=="styles" else
              {"warm","monochrome","grain","vignette","soften","weave"})
    if not required.issubset(data):
        raise PackageError(f"Installed {kind} preset {name} is missing: {', '.join(sorted(required-set(data)))}")
    from .pro_schema import LOOK_IDS, TRANSITION_IDS, MUSIC_IDS, AMBIENCE_IDS
    if kind=="styles":
        palette=data["transition_palette"]
        if (not isinstance(data["look"],str) or data["look"] not in LOOK_IDS or not isinstance(palette,list) or
            any(not isinstance(t,str) or t not in TRANSITION_IDS for t in palette) or
            not isinstance(data["music"],str) or data["music"] not in MUSIC_IDS|{"NONE"} or
            not isinstance(data["ambience"],str) or data["ambience"] not in AMBIENCE_IDS|{"NONE"}):
            raise PackageError(f"Installed style preset {name} uses an unsupported asset ID.")
        for key in ("transition_variety","sfx_density","handheld"):
            value=data[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not 0<=value<=1:
                raise PackageError(f"Installed style preset {name}: {key} must be 0..1.")
    else:
        for key in required:
            value=data[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not -1<=value<=1:
                raise PackageError(f"Installed look preset {name}: {key} must be -1..1.")
    return data


def ease(value: float, name: str) -> float:
    x = max(0.0, min(1.0, value))
    if name == "EASE_IN":
        return x*x*x
    if name == "EASE_OUT":
        return 1-(1-x)**3
    if name == "EASE_IN_OUT":
        return x*x*(3-2*x)
    return x


@dataclass(frozen=True)
class ScenePlan:
    id: str
    image_id: str
    first_frame: int
    end_frame: int
    motion: str
    motion_config: dict
    transition_requested: str
    transition_applied: str
    transition_frames: int
    direction: str
    focus_x: float
    focus_y: float
    focus_source: str
    look: str
    look_intensity: float
    transition_ease: str = "EASE_IN_OUT"
    narrative_role: str = "EXPLANATION"

    @property
    def frames(self) -> int:
        return self.end_frame-self.first_frame


@dataclass(frozen=True)
class CaptionPlan:
    start_frame: int
    end_frame: int
    text: str
    words: tuple[tuple[int, int, str], ...]


@dataclass(frozen=True)
class RenderSpec:
    package: Package
    scenes: tuple[ScenePlan, ...]
    captions: tuple[CaptionPlan, ...]
    overlays: tuple[dict, ...]
    style_id: str
    style: dict
    seed: int
    auto_direct: bool
    strict_json: bool
    changes: dict
    warnings: tuple[str, ...]
    layers: tuple[dict, ...] = ()
    events: tuple[dict, ...] = ()
    layer_assets: dict = field(default_factory=dict)
    asset_records: tuple[dict, ...] = ()
    camera: tuple[dict, ...] = ()
    camera_shake_enabled: bool = False


def _seeded_unit(seed: int, label: str) -> float:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _seed(package: Package) -> int:
    from .renderer import _export_seed
    return package.pro.get("style", {}).get("seed", _export_seed(package))


def _saliency(path: Path) -> tuple[float, float, str]:
    path = Path(path).resolve()
    try:
        stat = path.stat()
    except OSError as exc:
        raise PackageError(f"Unreadable source image: {path.name}: {exc}") from exc
    return _saliency_cached(str(path), stat.st_mtime_ns, stat.st_size)


from functools import lru_cache


@lru_cache(maxsize=4096)
def _saliency_cached(path: str, modified_ns: int, file_size: int) -> tuple[float, float, str]:
    """Small deterministic edge-energy centroid; safe fallback to centre."""
    path = Path(path)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImageReader
    reader = QImageReader(str(path))
    size = reader.size()
    if not size.isValid():
        raise PackageError(f"Unreadable source image: {path.name}")
    reader.setScaledSize(size.scaled(48, 48, Qt.IgnoreAspectRatio))
    image = reader.read()
    if image.isNull():
        raise PackageError(f"Unreadable source image: {path.name}: {reader.errorString()}")
    sx=sy=weight=0.0
    for y in range(1, image.height()-1, 2):
        for x in range(1, image.width()-1, 2):
            c=image.pixelColor(x,y); right=image.pixelColor(x+1,y); down=image.pixelColor(x,y+1)
            edge=(abs(c.red()-right.red())+abs(c.green()-right.green())+abs(c.blue()-right.blue())+
                  abs(c.red()-down.red())+abs(c.green()-down.green())+abs(c.blue()-down.blue()))
            if edge > 25:
                sx += x*edge; sy += y*edge; weight += edge
    if weight < 1:
        return .5,.5,"center"
    return max(.2,min(.8,sx/weight/image.width())), max(.2,min(.8,sy/weight/image.height())), "saliency"


def _caption_chunks(package: Package, size: int) -> tuple[CaptionPlan, ...]:
    if not package.captions_enabled:
        return ()
    chunks: list[CaptionPlan] = []
    for caption in package.captions:
        words = [w for w in package.words
                 if caption.word_start_index <= w.index <= caption.word_end_index]
        groups=[]
        i=0
        while i<len(words):
            group=words[i:i+size]
            for j,word in enumerate(group[:-1]):
                if word.text.rstrip().endswith((".","!","?",",")) and j>=1:
                    group=group[:j+1];break
            if i+len(group)<len(words) and len(group)<4 and group[-1].text in {"Pope","King","Dr."}:
                group=words[i:i+len(group)+1]
            groups.append(group)
            i+=len(group)
        if not groups:continue
        boundaries=[round(caption.start*package.fps)]
        for old,new in zip(groups,groups[1:]):
            midpoint=(old[-1].end+new[0].start)/2
            boundaries.append(round(midpoint*package.fps))
        boundaries.append(round(caption.end*package.fps))
        for j,group in enumerate(groups):
            start=max(0,boundaries[j]);end=min(package.total_frames,boundaries[j+1])
            if end>start:
                chunks.append(CaptionPlan(start,end," ".join(w.text for w in group),
                    tuple((round(w.start*package.fps), round(w.end*package.fps), w.text) for w in group)))
    return tuple(chunks)


def build_spec(package: Package, images: dict[str, Path], settings) -> RenderSpec:
    from .pro_schema import STYLE_IDS, LOOK_IDS, TRANSITION_IDS
    extras = package.pro
    v2_style = extras.get("style", {})
    style_id = v2_style.get("preset", settings.style_preset)
    if style_id not in STYLE_IDS:
        raise PackageError(f"Unknown installed style preset: {style_id}")
    style = load_preset("styles", style_id)
    auto_options = extras.get("auto_direct", {})
    auto = auto_options.get("enabled", settings.auto_direct)
    strict = auto_options.get("strict_json", settings.strict_json)
    if getattr(settings,"product_version",0)==3:auto,strict=True,False
    variety = auto_options.get("transition_variety", style["transition_variety"])
    seed = _seed(package)
    warnings: list[str] = []
    scenes: list[ScenePlan] = []
    upgraded = 0
    from .visual_director import plan_scenes
    director = settings.visual_director
    decisions = []
    if director.enabled and not strict:
        decisions, director_warnings = plan_scenes(package, director)
        warnings.extend(director_warnings)
        seed = director.seed
        auto = True
    focus_cache: dict[str, tuple[float,float,str]] = {}
    for i, scene in enumerate(package.scenes):
        config = extras.get("scenes", [{}]*len(package.scenes))[i]
        motion = config.get("motion_config", {})
        tc = config.get("transition_config", {})
        requested = tc.get("type", scene.transition)
        applied = requested
        selected_motion = scene.motion
        decision = decisions[i] if decisions else None
        if decision:
            selected_motion = decision['motion']
            requested = decision['transition_requested']
            applied = decision['transition']
            if decision['motion_generated']:
                definition=MOTION_PATHS[selected_motion]
                amount=director.motion_intensity * ({'SUBTLE':.6,'BALANCED':1,'HIGH_ENERGY':1.35}[director.mode])
                # Limit extra crop to 10%; evidence/fit images use an even smaller push.
                if decision['role']=='IMPORTANT_EVIDENCE' or settings.aspect_policy in {'FIT','BLUR_FILL'}:amount=min(amount,.45)
                motion={**motion,'zoom_from':1+(definition[0]-1)*amount,
                        'zoom_to':1+(definition[1]-1)*amount, 'ease':definition[6],
                        'director':True}
            if applied!=scene.transition:upgraded+=1
        elif auto and not strict and requested == "HARD_CUT" and i > 0 and i < len(package.scenes)-1:
            before = package.scenes[i-1]
            sentence_end = before.voice_text.rstrip().endswith((".", "!", "?"))
            valid = (sentence_end and before.frame_count >= round(1.2*package.fps)
                     and scene.frame_count >= round(1.2*package.fps)
                     and scene.first_frame >= round(3*package.fps)
                     and bool(style["transition_palette"])
                     and scenes[-1].transition_applied in {"HARD_CUT", "NONE"})
            if valid and _seeded_unit(seed, f"boundary:{i}") < variety:
                choices = style["transition_palette"]
                applied = choices[min(len(choices)-1, int(_seeded_unit(seed, f"type:{i}")*len(choices)))]
                upgraded += 1
        if applied not in TRANSITION_IDS:
            raise PackageError(f"Unsupported Pro transition: {applied}")
        length = decision['frames'] if decision else tc.get("frames", 8 if applied in {"WHIP_PAN", "QUICK_PUSH"} else 12)
        if i == 0 or applied in {"HARD_CUT", "NONE"}:
            length = 0
        else:
            length = min(length, math.floor(.45*min(package.scenes[i-1].frame_count, scene.frame_count)), scene.frame_count-1)
            if length < 4:
                warnings.append(f"Scene {scene.id}: transition skipped because fewer than four frames fit.")
                applied, length = "HARD_CUT", 0
        if decision:
            decision['final_transition'] = applied
            decision['final_frames'] = length
        if scene.image_id not in focus_cache:
            focus_cache[scene.image_id] = _saliency(images[scene.image_id])
        fx,fy,source = focus_cache[scene.image_id]
        if "focus" in motion:
            fx,fy,source = motion["focus"]["x"],motion["focus"]["y"],"explicit"
        look_override = config.get("look_override", {})
        look = look_override.get("look", v2_style.get("look", style["look"]))
        intensity = look_override.get("intensity", v2_style.get("look_intensity",settings.look_intensity))
        if look not in LOOK_IDS:
            raise PackageError(f"Unknown installed look: {look}")
        scenes.append(ScenePlan(scene.id, scene.image_id, scene.first_frame, scene.end_frame,
            selected_motion, motion, requested, applied, length, tc.get("direction", "AUTO"),
            fx,fy,source,look,intensity,tc.get("ease", "EASE_IN_OUT"),
            decision['role'] if decision else 'EXPLANATION'))
    caption_style = extras.get("caption_style", {})
    chunk_size = int(caption_style.get("chunk_words", settings.chunk_words))
    if director.enabled:
        # Keep each supplied caption interval and every timed word unchanged.
        from .schema import frame_at
        captions=tuple(CaptionPlan(frame_at(c.start,package.fps),frame_at(c.end,package.fps),c.text,
            tuple((frame_at(w.start,package.fps),frame_at(w.end,package.fps),w.text)
                  for w in package.words if c.word_start_index<=w.index<=c.word_end_index))
            for c in package.captions) if package.captions_enabled else ()
    else:
        captions = _caption_chunks(package, chunk_size)
    layers=events=();layer_assets={};records=()
    spec = RenderSpec(package, tuple(scenes), captions, tuple(extras.get("overlays", [])),
        style_id, style, seed, auto, strict,
        {"transitions_upgraded": upgraded, "captions_rechunked": [len(package.captions), len(captions)],
         "visual_director": {"enabled":bool(decisions),"seed":seed,"mode":director.mode,
                             "decisions":decisions}},
        tuple(warnings),layers,events,layer_assets,tuple(records),tuple(extras.get('camera',[])),settings.shake)

    if getattr(settings,"product_version",0)==3:
        from .moments import validate_moments,circle_visible
        from .pro_compositor import ProCompositor
        valid,notices=validate_moments(package)
        comp=ProCompositor(spec,images,settings,cache_limit_bytes=64*1024**2)
        accepted=[]
        for moment in valid:
            if moment['type']=='CIRCLE':
                moment={**moment,'box':package.pro.get('moment_overrides',{}).get(moment['id'],moment['box'])}
                plan=next(s for s in spec.scenes if s.id==moment['scene_id'])
                if not circle_visible(moment,comp,plan):
                    notices.append(f"Moment {moment['id']} skipped: circle is outside the scene crop. Use Fit entire image or adjust its source box.");continue
            accepted.append(moment)
        from dataclasses import replace
        spec=replace(spec,changes={**spec.changes,'moments':accepted,'moment_notices':notices})
    return spec
