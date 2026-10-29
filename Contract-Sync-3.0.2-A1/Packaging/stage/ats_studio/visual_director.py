"""Local, deterministic story decisions; never changes the source timeline."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import re

TRANSITIONS = frozenset({
    "HARD_CUT", "NONE", "CROSSFADE", "GENTLE_DISSOLVE", "DISSOLVE",
    "FADE_THROUGH_BLACK", "FADE_THROUGH_WHITE", "QUICK_PUSH", "WHIP_PAN",
    "ZOOM_THROUGH", "DISSOLVE_BLUR", "SLIDE_SHADOW", "LIGHT_LEAK_FLASH",
    "FILM_BURN", "IRIS_WIPE", "INK_WIPE", "BRUSH_WIPE", "PAPER_TEAR",
    "BURN_LIGHT", "TORN_CENTER_SPLIT", "ZOOM_BLUR", "FILM_FLASH",
    "LIGHT_LEAK", "SMOKE_DISSOLVE", "IRIS_REVEAL", "INK_SPREAD",
    "GLITCH_TRANSITION",
})
MOTIONS = frozenset({"STATIC", "SLOW_PUSH_IN", "SLOW_ZOOM_OUT", "PAN_LEFT",
    "PAN_RIGHT", "PAN_UP", "PAN_DOWN", "GENTLE_DIAGONAL", "KEN_BURNS", "TINY_PUNCH_IN"})
FANCY = TRANSITIONS - {"HARD_CUT", "NONE", "CROSSFADE", "GENTLE_DISSOLVE", "DISSOLVE",
    "FADE_THROUGH_BLACK", "FADE_THROUGH_WHITE"}

@dataclass(frozen=True)
class VisualDirectorSettings:
    enabled: bool = False
    mode: str = "BALANCED"
    frequency: float = .15
    motion_intensity: float = .55
    burn_intensity: float = .55
    torn_edge_intensity: float = .45
    min_duration: float = .12
    max_duration: float = .55
    seed: int = 48127
    preserve_explicit: bool = True
    transition_allowlist: tuple[str, ...] = ()
    motion_allowlist: tuple[str, ...] = ()

    def __post_init__(self):
        if self.mode not in {"SUBTLE", "BALANCED", "HIGH_ENERGY"}:
            raise ValueError("Unknown Visual Director intensity")
        for key in ("frequency", "motion_intensity", "burn_intensity", "torn_edge_intensity"):
            value=getattr(self,key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
                raise ValueError(f"Visual Director {key} must be between 0 and 1")
        if not (.08 <= self.min_duration <= self.max_duration <= 1.2):
            raise ValueError("Effect durations must satisfy 0.08 <= minimum <= maximum <= 1.2 seconds")
        if isinstance(self.seed,bool) or not isinstance(self.seed,int) or not 0<=self.seed<=2147483647:
            raise ValueError("Visual Director seed must be 0..2147483647")
        if not set(self.transition_allowlist)<=TRANSITIONS or not set(self.motion_allowlist)<=MOTIONS:
            raise ValueError("Director allowlist contains unsupported effect names")

    @classmethod
    def from_dict(cls, data):
        data=dict(data or {})
        for key in ("transition_allowlist","motion_allowlist"):
            if key in data: data[key]=tuple(data[key])
        return cls(**data)

RULES = {
    "SHOCKING_REVEAL": (("shocking",4),("unbelievable",4),("turned out",3),("secretly",2),("never existed",4)),
    "DISCOVERY": (("discovered",4),("found",2),("revealed",4),("realized",3),("different plan",3)),
    "IMPORTANT_EVIDENCE": (("evidence",4),("document",3),("photograph",3),("letter",3),("order",2),("proof",4)),
    "MYSTERY": (("mystery",4),("vanished",4),("unexplained",4),("unknown",3),("missing",3)),
    "SUSPENSE": (("waiting",3),("midnight",3),("danger",3),("fear",2),("silence",3),("locked",3)),
    "CONFLICT": (("opposed",4),("challenge",3),("feared stalin",3),("refused",4),("argued",3),("spoke up",3)),
    "ACTION": (("battle",4),("attack",3),("assault",4),("counterattack",4),("strike",3),("offensive",3)),
    "EMOTIONAL_BEAT": (("courage",4),("lives",3),("loss",3),("grief",4),("sacrifice",4),("patience",3)),
    "CONSEQUENCE": (("as a result",4),("survived",3),("helped",2),("aftermath",4),("saved",3)),
    "ESTABLISHING": (("city",3),("landscape",4),("arrived",3),("countryside",3),("across",1)),
    "HISTORICAL_CONTEXT": (("in 1942",4),("in 1943",4),("year later",3),("during",2),("century",3)),
    "TRANSITIONAL": (("meanwhile",4),("years later",3),("then",1)),
    "CONCLUSION": (("follow for",6),("remember",2),("in the end",4),("legacy",3)),
    "EXPLANATION": (("because",2),("prepared",3),("defensive",2),("plan",2),("meant",2)),
}

def classify(text, index, count):
    text=(text or "").casefold()
    if index==count-1 and ("follow" in text or "legacy" in text): return "CONCLUSION",1.0
    scores={role:sum(weight for phrase,weight in entries if re.search(r"\b"+re.escape(phrase)+r"\b",text)) for role,entries in RULES.items()}
    if index==0: scores["HOOK"]=max(3,max(scores.values(),default=0)+1)
    role=max(scores,key=scores.get)
    score=scores[role]
    return (role,min(1,score/6)) if score else ("EXPLANATION",0.0)

def unit(seed, label):
    return int.from_bytes(hashlib.sha256(f"{seed}:{label}".encode()).digest()[:8],"big")/2**64

def choose(seed,label,weighted,allowed):
    options=[(name,weight) for name,weight in weighted if name in allowed]
    if not options:return "HARD_CUT" if "HARD_CUT" in allowed else "STATIC"
    target=unit(seed,label)*sum(w for _,w in options)
    for name,weight in options:
        target-=weight
        if target<=0:return name
    return options[-1][0]

MOTION_CHOICES = {
    "HOOK": [("TINY_PUNCH_IN",2),("SLOW_PUSH_IN",4),("STATIC",2)],
    "ESTABLISHING": [("PAN_LEFT",3),("PAN_RIGHT",3),("SLOW_PUSH_IN",2)],
    "EXPLANATION": [("STATIC",3),("SLOW_PUSH_IN",3),("SLOW_ZOOM_OUT",2)],
    "IMPORTANT_EVIDENCE": [("STATIC",4),("SLOW_PUSH_IN",4)],
    "DISCOVERY": [("SLOW_PUSH_IN",4),("TINY_PUNCH_IN",2)],
    "SHOCKING_REVEAL": [("TINY_PUNCH_IN",3),("SLOW_PUSH_IN",3)],
    "MYSTERY": [("SLOW_PUSH_IN",5),("STATIC",2)],
    "SUSPENSE": [("SLOW_PUSH_IN",5),("STATIC",2)],
    "ACTION": [("PAN_RIGHT",2),("SLOW_PUSH_IN",3),("TINY_PUNCH_IN",2)],
    "CONFLICT": [("SLOW_PUSH_IN",4),("STATIC",2)],
    "EMOTIONAL_BEAT": [("STATIC",3),("SLOW_PUSH_IN",3),("SLOW_ZOOM_OUT",2)],
    "CONCLUSION": [("STATIC",5),("SLOW_ZOOM_OUT",3)],
}
DRAMATIC = {
    "DISCOVERY": [("BURN_LIGHT",3),("TORN_CENTER_SPLIT",3),("IRIS_REVEAL",2)],
    "SHOCKING_REVEAL": [("FILM_FLASH",3),("BURN_LIGHT",3),("ZOOM_BLUR",2)],
    "IMPORTANT_EVIDENCE": [("TORN_CENTER_SPLIT",3),("INK_SPREAD",1)],
    "ACTION": [("WHIP_PAN",3),("ZOOM_BLUR",3)],
    "CONFLICT": [("TORN_CENTER_SPLIT",3),("BURN_LIGHT",1)],
    "TRANSITIONAL": [("LIGHT_LEAK",2),("SMOKE_DISSOLVE",2)],
}

def plan_scenes(package, settings, capabilities=TRANSITIONS):
    """Return visual decisions; all IDs/frames come from the validated package."""
    data=json_from_source(package.source_json)
    raw_scenes=data.get("scenes",[])
    seed=settings.seed
    identity=hashlib.sha256(package.source_json.encode()).hexdigest()[:16]
    allowed=set(settings.transition_allowlist or TRANSITIONS)&set(capabilities)
    allowed.add("HARD_CUT")
    motions=set(settings.motion_allowlist or MOTIONS)
    motions.add("STATIC")
    used={};previous="HARD_CUT";previous_motion=None;decisions=[];warnings=[]
    mode_factor={"SUBTLE":.45,"BALANCED":1,"HIGH_ENERGY":1.7}[settings.mode]
    budget=max(1,math.ceil((len(package.scenes)-1)*settings.frequency*mode_factor)) if settings.frequency else 0
    fancy_count=0
    for i,scene in enumerate(package.scenes):
        raw=raw_scenes[i] if i<len(raw_scenes) else {}
        role,confidence=classify(scene.voice_text,i,len(package.scenes))
        explicit_motion="motion" in raw or "motion_config" in raw
        explicit_transition="transition" in raw or "transition_config" in raw
        motion=scene.motion
        transition=raw.get("transition_config",{}).get("type",scene.transition)
        label=f"{identity}:{scene.id}"
        if not settings.preserve_explicit or not explicit_motion:
            choices=MOTION_CHOICES.get(role,[("SLOW_PUSH_IN",3),("STATIC",3),("PAN_LEFT",1)])
            if previous_motion in {"SLOW_PUSH_IN","PAN_LEFT","PAN_RIGHT"}:
                choices=[(m,w*.3 if m==previous_motion else w) for m,w in choices]
            motion=choose(seed,label+":motion",choices,motions)
            if scene.frame_count<package.fps*.65:motion="STATIC"
        if motion=="SUBTLE_PARALLAX":
            motion="SLOW_PUSH_IN";warnings.append(f"Scene {scene.id}: depth layers absent; SUBTLE_PARALLAX uses a 2D push-in.")
        if i==0:transition="HARD_CUT"
        elif not settings.preserve_explicit or not explicit_transition:
            standard=[("HARD_CUT",6),("CROSSFADE",2),("DISSOLVE",2)]
            if role in {"ACTION","CONFLICT","HOOK"}:standard=[("HARD_CUT",9),("CROSSFADE",1)]
            if role in {"MYSTERY","SUSPENSE","EMOTIONAL_BEAT","CONCLUSION"}:standard=[("HARD_CUT",4),("DISSOLVE",5)]
            transition=choose(seed,label+":standard",standard,allowed)
            eligible=(confidence>.25 and role in DRAMATIC and fancy_count<budget and previous not in FANCY
                      and min(scene.frame_count,package.scenes[i-1].frame_count)>=package.fps*1.0)
            if eligible and unit(seed,label+":fancy") < min(.8,settings.frequency*mode_factor*2.5):
                choices=[(name,w/(1+used.get(name,0)*3)) for name,w in DRAMATIC[role] if name!=previous]
                transition=choose(seed,label+":reveal",choices,allowed)
            # Do not combine a punch with an energetic zoom/flash transition.
            if transition in {"ZOOM_BLUR","WHIP_PAN","FILM_FLASH"} and motion=="TINY_PUNCH_IN" and not (explicit_motion and settings.preserve_explicit):
                motion="SLOW_PUSH_IN"
        requested=transition
        if transition not in capabilities:
            warnings.append(f"Scene {scene.id}: {transition} unavailable; using HARD_CUT.")
            transition="HARD_CUT"
        length=0
        if i and transition not in {"HARD_CUT","NONE"}:
            requested_frames=raw.get("transition_config",{}).get("frames") if explicit_transition and settings.preserve_explicit else None
            nominal=(.24 if transition in {"WHIP_PAN","FILM_FLASH","GLITCH_TRANSITION"} else .42)
            length=int(requested_frames or round(max(settings.min_duration,min(settings.max_duration,nominal))*package.fps))
            length=min(length,math.floor(.45*min(package.scenes[i-1].frame_count,scene.frame_count)),scene.frame_count-1)
            if length<max(2,math.ceil(settings.min_duration*package.fps)):
                warnings.append(f"Scene {scene.id}: effect does not fit; using HARD_CUT.")
                transition,length="HARD_CUT",0
        if transition in FANCY:fancy_count+=1
        used[transition]=used.get(transition,0)+1
        decisions.append({"id":scene.id,"role":role,"confidence":confidence,"motion":motion,
            "transition_requested":requested,"transition":transition,"frames":length,
            "motion_generated":not(settings.preserve_explicit and explicit_motion),
            "preserved_motion":settings.preserve_explicit and explicit_motion,
            "preserved_transition":settings.preserve_explicit and explicit_transition})
        previous=transition;previous_motion=motion
    return decisions,warnings

def json_from_source(text):
    import json
    return json.loads(text)
