"""Additive ATS_PACKAGE_V2 validation; the V1 validator remains authoritative."""

from __future__ import annotations

from dataclasses import replace
import json
import math
from typing import Any, Callable

from .schema import (CAPTION_STYLE_FIELDS, SCENE_FIELDS, TOP_FIELDS,
                     Package, PackageError)


STYLE_IDS = frozenset({"LEGACY", "CLEAN_DOC", "HISTORY_ARCHIVE", "HISTORY_MEDIEVAL",
    "DARK_PSYCHOLOGY", "FINANCE_PREMIUM", "SCIENCE_CLEAN", "TECH_MODERN", "MYSTERY_NOIR", "REEL_CLEAN_LIGHT"})
LOOK_IDS = frozenset({"CLEAN", "CLEAN_DOC", "AGED_PARCHMENT", "ALBUMEN_1880S",
    "SILENT_FILM_1910S", "NITRATE_1930S", "PRESS_PHOTO_1950S", "KODAK_1970S",
    "VHS_1980S", "DARK_NOIR", "FINANCE_PREMIUM", "SCIENCE_CLEAN", "TECH_MODERN"})
TRANSITION_IDS = frozenset({"HARD_CUT", "NONE", "CROSSFADE", "GENTLE_DISSOLVE",
    "FADE_THROUGH_BLACK", "FADE_THROUGH_WHITE", "QUICK_PUSH", "WHIP_PAN",
    "ZOOM_THROUGH", "DISSOLVE_BLUR", "SLIDE_SHADOW", "LIGHT_LEAK_FLASH",
    "FILM_BURN", "IRIS_WIPE", "INK_WIPE", "BRUSH_WIPE", "PAPER_TEAR"})
from .visual_director import TRANSITIONS as DIRECTOR_TRANSITIONS
TRANSITION_IDS = TRANSITION_IDS | DIRECTOR_TRANSITIONS
EASINGS = frozenset({"LINEAR", "EASE_IN", "EASE_OUT", "EASE_IN_OUT"})
OVERLAYS = frozenset({"DATE_STAMP", "HOOK_CARD", "LOWER_THIRD", "TEXT",
                      "HIGHLIGHT_BOX", "MAP_ROUTE", "PHOTO_NOTE"})
OVERLAY_STYLES = frozenset({"PLAIN", "ARCHIVE", "MODERN", "RECT", "CIRCLE", "ARROW"})
SFX_IDS = frozenset({"SWIPE_SOFT", "WHOOSH_SOFT", "WHOOSH_FAST", "PAPER_SLIDE",
    "PAGE_TURN", "BRUSH_SCRATCH", "CAMERA_SHUTTER", "FILM_CLICK", "IMPACT_LOW",
    "IMPACT_SOFT", "RISER_SHORT", "INK_SPLASH", "STAMP_THUD", "TYPEWRITER_KEY",
    "TICK_SOFT"})
MUSIC_IDS = frozenset({"DARK_DRONE_A", "DARK_DRONE_B", "TENSION_PULSE_A",
    "WARM_PAD_A", "FINANCE_PULSE_A", "TECH_AMBIENT_A"})
AMBIENCE_IDS = frozenset({"ROOM_TONE_STONE", "CANDLE_ROOM", "CROWD_MURMUR",
                          "WIND_SOFT", "CITY_NIGHT_SOFT"})


class Checker:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        if len(self.errors) < 50:
            self.errors.append(f"{path}: {message}")

    def object(self, value: Any, path: str, allowed: set[str]) -> dict:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return {}
        for key in value.keys() - allowed:
            self.error(f"{path}.{key}", "unknown field")
        return value

    def array(self, value: Any, path: str) -> list:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        return value

    def number(self, value: Any, path: str, lo: float, hi: float, integer: bool = False) -> None:
        valid = (isinstance(value, int) if integer else isinstance(value, (int, float))) and not isinstance(value, bool)
        try:
            finite=valid and math.isfinite(value)
        except (OverflowError,ValueError):
            finite=False
        if not finite or not lo <= value <= hi:
            kind = "integer" if integer else "number"
            self.error(path, f"must be a {kind} between {lo:g} and {hi:g}")

    def enum(self, value: Any, path: str, allowed: frozenset[str] | set[str]) -> None:
        if not isinstance(value, str) or value not in allowed:
            self.error(path, f"must be one of {', '.join(sorted(allowed))}")

    def boolean(self, value: Any, path: str) -> None:
        if not isinstance(value, bool):
            self.error(path, "must be true or false")

    def string(self, value: Any, path: str, max_chars: int = 120) -> None:
        if not isinstance(value, str) or len(value) > max_chars:
            self.error(path, f"must be text of at most {max_chars} characters")


def _validate_product_fields(raw, check):
    if "format" in raw:
        from .product import FORMATS
        item=check.object(raw["format"],"$.format",{"orientation","aspect_ratio"})
        check.enum(item.get("orientation"),"$.format.orientation",set(FORMATS))
        if item.get("orientation") in FORMATS and item.get("aspect_ratio")!=FORMATS[item["orientation"]][0]:
            check.error("$.format.aspect_ratio","expected "+FORMATS[item["orientation"]][0])
    if "direction" in raw:
        d=check.object(raw["direction"],"$.direction",{"energy","finish","voice_level","music_level","duck_db","sfx_enabled","transition_frequency"})
        if "energy" in d:check.enum(d["energy"],"$.direction.energy",{"SUBTLE","BALANCED","HIGH_ENERGY"})
        for key in ("voice_level","music_level","transition_frequency"):
            if key in d:check.number(d[key],"$.direction."+key,0,1)
        if "duck_db" in d:check.number(d["duck_db"],"$.direction.duck_db",-30,0)
        if "sfx_enabled" in d:check.boolean(d["sfx_enabled"],"$.direction.sfx_enabled")
        if "finish" in d:
            f=check.object(d["finish"],"$.direction.finish",{"grain","vignette","contrast"})
            for key in f:
                if key in {"grain","vignette","contrast"}:check.number(f[key],"$.direction.finish."+key,0,1)
    c=raw.get("caption_style",{})
    if isinstance(c,dict):
        from .project_settings import CAPTION_FONTS
        if "font" in c:check.enum(c["font"],"$.caption_style.font",set(CAPTION_FONTS))
        if "size" in c:check.number(c["size"],"$.caption_style.size",50,180,True)
        if "position" in c:check.enum(c["position"],"$.caption_style.position",{"Top","Center","Bottom"})
        if "background" in c:check.enum(c["background"],"$.caption_style.background",{"Shadow Only","Dark Brush","Solid Box","Paper","None"})
        import re
        for key in ("text_color","accent_color"):
            if key in c and (not isinstance(c[key],str) or not re.fullmatch(r"#[0-9a-fA-F]{6}",c[key])):check.error("$.caption_style."+key,"expected #RRGGBB")


def _validate_v2(raw: dict, check: Checker) -> None:
    _validate_product_fields(raw, check)
    check.object(raw, "$", set(TOP_FIELDS) | {"style", "audio", "overlays", "ending", "auto_direct", "format", "direction", "moments"})
    for key in TOP_FIELDS:
        if key not in raw:
            check.error(f"$.{key}", "required field is missing")
    style = check.object(raw["style"], "$.style", {"preset", "look", "look_intensity", "seed"}) if "style" in raw else {}
    for key, allowed in (("preset", STYLE_IDS), ("look", LOOK_IDS)):
        if key in style:
            check.enum(style[key], f"$.style.{key}", allowed)
    if "look_intensity" in style:
        check.number(style["look_intensity"], "$.style.look_intensity", 0, 1)
    if "seed" in style:
        check.number(style["seed"], "$.style.seed", -(2**63), 2**63-1, True)

    audio = check.object(raw["audio"], "$.audio", {"music", "ambience", "sfx", "master"}) if "audio" in raw else {}
    audio_fields = {
        "music": ({"track_id", "gain_db", "duck_db", "fade_in_s", "fade_out_s"},
                  {"gain_db": (-40, 0), "duck_db": (-30, -4), "fade_in_s": (0, 10), "fade_out_s": (0, 10)}),
        "ambience": ({"bed_id", "gain_db"}, {"gain_db": (-50, -10)}),
        "sfx": ({"pack", "density", "gain_db"}, {"density": (0, 1), "gain_db": (-12, 6)}),
        "master": ({"mode", "target_lufs", "true_peak_db"}, {"target_lufs": (-23, -9), "true_peak_db": (-3, -.5)}),
    }
    for section, (fields, ranges) in audio_fields.items():
        if section not in audio:
            continue
        item = check.object(audio[section], f"$.audio.{section}", fields)
        for key, (lo, hi) in ranges.items():
            if key in item:
                check.number(item[key], f"$.audio.{section}.{key}", lo, hi)
        if section == "music" and "track_id" in item:
            check.enum(item["track_id"], "$.audio.music.track_id", MUSIC_IDS | {"NONE"})
        if section == "ambience" and "bed_id" in item:
            check.enum(item["bed_id"], "$.audio.ambience.bed_id", AMBIENCE_IDS | {"NONE"})
        if section == "sfx" and "pack" in item:
            check.enum(item["pack"], "$.audio.sfx.pack", {"SFX_ARCHIVE_V1"})
        if section == "master" and "mode" in item:
            check.enum(item["mode"], "$.audio.master.mode", {"LIMIT_ONLY", "LOUDNORM", "OFF"})

    caption = check.object(raw.get("caption_style", {}), "$.caption_style",
        set(CAPTION_STYLE_FIELDS) | {"chunk_words", "max_lines", "emphasis", "animation", "safe_zone", "preset", "font", "size", "position", "text_color", "accent_color", "background"})
    for key in CAPTION_STYLE_FIELDS:
        if key not in caption:
            check.error("$.caption_style."+key,"required field is missing")
    for key, lo, hi in (("chunk_words", 2, 4), ("max_lines",1,2)):
        if key in caption:
            check.number(caption[key], f"$.caption_style.{key}", lo, hi, True)
    for key, allowed in (("animation", {"POP", "FADE", "NONE"}),
                         ("safe_zone", {"AUTO", "PORTRAIT_9_16", "LANDSCAPE_16_9"})):
        if key in caption:
            check.enum(caption[key], f"$.caption_style.{key}", allowed)
    if "preset" in caption:
        from .project_settings import CAPTION_PRESETS
        check.enum(caption["preset"], "$.caption_style.preset", set(CAPTION_PRESETS))
    if "emphasis" in caption:
        words=raw.get("words",[])
        indexes={w.get("index") for w in words if isinstance(w,dict) and isinstance(w.get("index"),int)} if isinstance(words,list) else set()
        for i,value in enumerate(check.array(caption["emphasis"],"$.caption_style.emphasis")):
            check.number(value,f"$.caption_style.emphasis[{i}]",0,10**9,True)
            if isinstance(value,int) and value not in indexes:
                check.error(f"$.caption_style.emphasis[{i}]","word index does not exist")

    scenes = check.array(raw.get("scenes", []), "$.scenes")
    for i, value in enumerate(scenes):
        path = f"$.scenes[{i}]"
        item = check.object(value, path, set(SCENE_FIELDS) | {"motion_config", "transition_config", "sfx", "look_override"})
        for key in SCENE_FIELDS:
            if key not in item and key not in {"motion","transition"}:
                check.error(path+"."+key,"required field is missing")
        motion = check.object(item["motion_config"], path+".motion_config",
            {"focus", "zoom_from", "zoom_to", "ease", "shake", "blur"}) if "motion_config" in item else {}
        if "focus" in motion:
            focus = check.object(motion["focus"], path+".motion_config.focus", {"x", "y"})
            for xy in ("x", "y"):
                if xy in focus:
                    check.number(focus[xy], path+f".motion_config.focus.{xy}", 0, 1)
                else:
                    check.error(path+f".motion_config.focus.{xy}","required field is missing")
        for key in ("zoom_from", "zoom_to"):
            if key in motion:
                check.number(motion[key], path+".motion_config."+key, 1, 2)
        for key in ("shake", "blur"):
            if key in motion:
                check.number(motion[key], path+".motion_config."+key, 0, 1)
        if "ease" in motion:
            check.enum(motion["ease"], path+".motion_config.ease", EASINGS)
        trans = check.object(item["transition_config"], path+".transition_config",
            {"type", "frames", "direction", "ease", "sfx"}) if "transition_config" in item else {}
        for key, allowed in (("type", TRANSITION_IDS), ("direction", {"LEFT", "RIGHT", "UP", "DOWN", "AUTO"}),
                             ("ease", EASINGS), ("sfx", SFX_IDS | {"NONE"})):
            if key in trans:
                check.enum(trans[key], path+".transition_config."+key, allowed)
        if "frames" in trans:
            check.number(trans["frames"], path+".transition_config.frames", 4, 30, True)
        for j, cue in enumerate(check.array(item["sfx"], path+".sfx") if "sfx" in item else []):
            cp = path+f".sfx[{j}]"
            cue = check.object(cue, cp, {"id", "offset_ms", "gain_db", "variant", "pitch_cents"})
            if "id" in cue:
                check.enum(cue["id"], cp+".id", SFX_IDS)
            else:
                check.error(cp+".id","required field is missing")
            for key, lo, hi in (("offset_ms", -300, 300), ("gain_db", -30, 6), ("pitch_cents", -200, 200)):
                if key in cue:
                    check.number(cue[key], cp+"."+key, lo, hi)
            if "variant" in cue and cue["variant"] != "AUTO":
                check.number(cue["variant"], cp+".variant", 1, 9, True)
            if isinstance(item.get("start"),(int,float)) and isinstance(cue.get("offset_ms",0),(int,float)):
                time=item["start"]+cue.get("offset_ms",0)/1000
                duration=raw.get("audio_duration")
                if isinstance(duration,(int,float)) and not 0<=time<duration:
                    check.error(cp+".offset_ms","resolved cue time is outside the timeline")
        if "look_override" in item:
            look = check.object(item["look_override"], path+".look_override", {"look", "intensity"})
            if "look" in look:
                check.enum(look["look"], path+".look_override.look", LOOK_IDS)
            if "intensity" in look:
                check.number(look["intensity"], path+".look_override.intensity", 0, 1)

    for i, value in enumerate(check.array(raw["overlays"], "$.overlays") if "overlays" in raw else []):
        path = f"$.overlays[{i}]"
        item = check.object(value, path, {"id", "type", "start", "end", "text", "text2",
                                          "x", "y", "w", "h", "points", "style", "scene_id"})
        for key in ("id", "type", "start", "end"):
            if key not in item:
                check.error(path+"."+key, "required field is missing")
        if "type" in item:
            check.enum(item["type"], path+".type", OVERLAYS)
        if "style" in item:
            check.enum(item["style"],path+".style",OVERLAY_STYLES)
        for key in ("id", "text", "text2"):
            if key in item:
                check.string(item[key], path+"."+key)
        for key in ("start", "end"):
            if key in item:
                check.number(item[key], path+"."+key, 0, 10**7)
                if isinstance(raw.get("audio_duration"),(int,float)) and isinstance(item[key],(int,float)) and item[key]>raw["audio_duration"]:
                    check.error(path+"."+key,"must be inside the audio timeline")
        for key in ("x", "y", "w", "h"):
            if key in item:
                check.number(item[key], path+"."+key, 0, 1)
        if "points" in item:
            for j, point in enumerate(check.array(item["points"], path+".points")):
                if not isinstance(point, list) or len(point) != 2:
                    check.error(path+f".points[{j}]", "must be [x,y]")
                else:
                    for k, coordinate in enumerate(point):
                        check.number(coordinate, path+f".points[{j}][{k}]", 0, 1)
        if item.get("type")=="PHOTO_NOTE":
            if item.get("scene_id") not in {s.get("id") for s in raw.get("scenes",[]) if isinstance(s,dict)}:
                check.error(path+".scene_id", "must reference an existing scene")
            if not isinstance(item.get("text"),str) or not item["text"].strip():
                check.error(path+".text", "photo note text is required")
            pts=item.get("points",[])
            if not isinstance(pts,list) or len(pts)!=4:
                check.error(path+".points", "must contain four source-image corners: top-left, top-right, bottom-right, bottom-left")
            elif all(isinstance(p,list) and len(p)==2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in p) for p in pts):
                turns=[(pts[(j+1)%4][0]-pts[j][0])*(pts[(j+2)%4][1]-pts[(j+1)%4][1])-(pts[(j+1)%4][1]-pts[j][1])*(pts[(j+2)%4][0]-pts[(j+1)%4][0]) for j in range(4)]
                if not (all(t>1e-8 for t in turns) or all(t < -1e-8 for t in turns)):
                    check.error(path+".points", "corners must form a convex nonzero quadrilateral in perimeter order")
        if isinstance(item.get("start"), (int, float)) and isinstance(item.get("end"), (int, float)):
            if item["end"] <= item["start"]:
                check.error(path+".end", "must be greater than start")

    if "ending" in raw:
        ending = check.object(raw["ending"], "$.ending", {"mode", "frames"})
        if "mode" in ending:
            check.enum(ending["mode"], "$.ending.mode", {"HOLD", "FADE_OUT"})
        if "frames" in ending:
            check.number(ending["frames"], "$.ending.frames", 0, 90, True)
    if "auto_direct" in raw:
        direct = check.object(raw["auto_direct"], "$.auto_direct",
                              {"enabled", "transition_variety", "sfx", "pattern_interrupt", "strict_json"})
        for key in ("enabled", "sfx", "pattern_interrupt", "strict_json"):
            if key in direct:
                check.boolean(direct[key], "$.auto_direct."+key)
        if "transition_variety" in direct:
            check.number(direct["transition_variety"], "$.auto_direct.transition_variety", 0, 1)


def parse_v2(raw: dict, source: str, parse_v1: Callable[[str], Package]) -> Package:
    check = Checker()
    _validate_v2(raw, check)
    if check.errors:
        raise PackageError("V2 validation failed:\n" + "\n".join(check.errors))
    base = {key: raw[key] for key in TOP_FIELDS}
    base["schema"] = "ATS_PACKAGE_V1"
    base["caption_style"] = {key: raw["caption_style"][key] for key in CAPTION_STYLE_FIELDS}
    base["scenes"] = [{key: scene.get(key,"STATIC" if key=="motion" else "HARD_CUT") for key in SCENE_FIELDS} for scene in raw["scenes"]]
    try:
        package = parse_v1(json.dumps(base, ensure_ascii=False, separators=(",", ":")))
    except (PackageError, KeyError, TypeError) as exc:
        raise PackageError(f"$.v1_contract: {exc}") from exc
    extras = {key: raw[key] for key in ("style", "audio", "overlays", "ending", "auto_direct", "caption_style", "format", "direction", "moments")
              if key in raw}
    extras["scenes"] = [{key: value for key, value in item.items() if key not in SCENE_FIELDS}
                        for item in raw["scenes"]]
    return replace(package, source_json=source, schema_version="ATS_PACKAGE_V2", pro=extras)
