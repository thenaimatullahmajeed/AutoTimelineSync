"""ATS 3 product contract and project state, independent of UI widgets."""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from pathlib import Path
import json
import math
from collections import Counter
from .schema import Package, PackageError, parse_package, frame_at
from .renderer import RenderSettings
from .visual_director import VisualDirectorSettings

FORMATS = {"VERTICAL": ("9:16", ((720,1280),(1080,1920),(2160,3840))),
           "HORIZONTAL": ("16:9", ((1280,720),(1920,1080),(3840,2160))),
           "SQUARE": ("1:1", ((720,720),(1080,1080),(2160,2160))),
           "PORTRAIT": ("4:5", ((720,900),(1080,1350),(2160,2700)))}
PRESETS = {"Hormozi": "Hormozi Style", "Viral Pop": "MrBeast / Viral Pop", "Karaoke": "Karaoke Highlight",
           "Neon Glow": "Neon Glow", "Cinematic": "Minimal Cinematic", "Highlighter": "Highlighter Box",
           "Documentary": "Documentary Highlight", "Clean": "Clean Subtitle", "Typewriter": "Typewriter", "Off": "Off"}

@dataclass(frozen=True)
class ProductSettings(RenderSettings):
    product_version: int = 3
    backend: str = "PRO"
    auto_direct: bool = True
    strict_json: bool = False
    caption_font: str = "Inter"
    caption_preset: str = "Minimal Cinematic"
    look_intensity: float = 0.0
    music_track: str = "NONE"
    ambience: str = "NONE"
    music_volume: float = .18
    voice_volume: float = 1.0
    music_duck_db: float = -9.0
    finish_grain: float = 0.0
    finish_vignette: float = 0.0
    finish_contrast: float = 0.0
    visual_director: VisualDirectorSettings = field(default_factory=lambda: VisualDirectorSettings(enabled=True))

def parse_script(text: str) -> Package:
    from .schema import _normalize_json_text, _pairs_unique, _reject_constant,MAX_PACKAGE_BYTES
    if not isinstance(text,str) or len(text.encode('utf-8'))>MAX_PACKAGE_BYTES:raise PackageError('$: JSON exceeds the 50 MiB safety limit.')
    try:
        raw=json.loads(_normalize_json_text(text),object_pairs_hook=_pairs_unique,parse_constant=_reject_constant)
    except (ValueError,TypeError) as exc:raise PackageError(f'$: invalid JSON: {exc}') from exc
    if isinstance(raw,dict) and raw.get('schema')=='ATS_PACKAGE_V1':
        raise PackageError('$.schema: ATS_PACKAGE_V1 came from an obsolete master prompt. Update ChatGPT instructions to ATS MASTER PROMPT v3.0.1; set schema to "ATS_PACKAGE_V2". Remove obsolete sections: auto_direct, audio.music, audio.ambience, audio.sfx.pack, audio.sfx.density, caption_style.chunk_words, caption_style.safe_zone, scenes[].motion_config.shake, layers, assets, generation, composition, camera. Preserve the matching narration, words, captions and scene timing.')
    if not isinstance(raw,dict) or raw.get('schema')!='ATS_PACKAGE_V2':
        raise PackageError('$.schema: expected "ATS_PACKAGE_V2" for ATS 3.0. Ask ChatGPT to update this package.')
    package = parse_package(text)
    if package.schema_version != "ATS_PACKAGE_V2":
        raise PackageError('$.schema: expected "ATS_PACKAGE_V2" for ATS 3.0. Ask ChatGPT to update this package.')
    if "auto_direct" in package.pro:
        raise PackageError('$.auto_direct: remove this field; ATS 3.0 always runs the director.')
    audio=package.pro.get('audio',{})
    for key in ('music','ambience'):
        if key in audio:raise PackageError(f'$.audio.{key}: unsupported in ATS 3.0. Import an optional music file; use direction.music_level and direction.duck_db.')
    for key in ('pack','density'):
        if key in audio.get('sfx',{}):raise PackageError(f'$.audio.sfx.{key}: remove this field. Flag individual scene cuts with transition_config.sfx or scenes[].sfx.')
    caption=package.pro.get('caption_style',{})
    for key in ('chunk_words','safe_zone'):
        if key in caption:raise PackageError(f'$.caption_style.{key}: remove this field. ATS 3.0 preserves supplied caption intervals and uses a fixed platform-safe layout.')
    from .caption_presets import PROFILES
    if 'animation' in caption and caption.get('preset','Minimal Cinematic') in PROFILES:
        raise PackageError('$.caption_style.animation: this creator preset has a fixed animation; remove animation.')
    for i,item in enumerate(package.pro.get('scenes',[])):
        if 'shake' in item.get('motion_config',{}):raise PackageError(f'$.scenes[{i}].motion_config.shake: unsupported in ATS 3.0; remove it. Use deliberate motion and finishing instead.')
        if i==0 and (item.get('sfx') or item.get('transition_config',{}).get('sfx','NONE')!='NONE'):
            raise PackageError('$.scenes[0].sfx: first scene has no cut. Place SFX on a later flagged cut.')
    for i,caption in enumerate(package.captions):
        expected=' '.join(w.text for w in package.words if caption.word_start_index<=w.index<=caption.word_end_index)
        if ' '.join(caption.text.split())!=' '.join(expected.split()):
            raise PackageError(f'$.captions[{i}].text: expected timed-word text {expected!r}. Keep caption text and word indices identical.')
    return package

def infer_format(images: dict[str, Path]) -> str:
    from PySide6.QtGui import QImageReader
    votes = Counter()
    for path in images.values():
        reader=QImageReader(str(path)); reader.setAutoTransform(True); size=reader.size()
        if size.isValid():
            ratio=size.width()/size.height()
            votes[min(FORMATS, key=lambda key:abs(math.log(ratio/(FORMATS[key][1][1][0]/FORMATS[key][1][1][1]))))]+=1
    # Stable tie: vertical, the product's short-form default.
    return max(FORMATS,key=lambda key:votes[key])

def script_settings(package: Package, orientation: str, music: str = "", overrides: dict | None = None,
                    tier: int = 1, quality: str = "STANDARD", framing: str = "FILL") -> ProductSettings:
    caption=package.pro.get("caption_style",{}); direction=package.pro.get("direction",{})
    values={"preset":caption.get("preset","Minimal Cinematic"), "energy":direction.get("energy","BALANCED"),
            "voice_volume":direction.get("voice_level",1), "music_volume":direction.get("music_level",.18),
            "position":caption.get("position","Bottom"), "size":caption.get("size",100),
            "font":caption.get("font","Inter")}
    values.update({k:v for k,v in (overrides or {}).items() if k in values})
    finish=direction.get("finish",{})
    width,height=FORMATS[orientation][1][tier]
    return ProductSettings(width=width,height=height,quality_tier=quality,aspect_policy=framing,
        framing="Fill Frame" if framing=="FILL" else "Fit Entire Image",
        music_path=music if music and Path(music).is_file() else "", music_volume=values['music_volume'],
        voice_volume=values['voice_volume'],music_duck_db=direction.get('duck_db',-9),
        caption_preset=values['preset'],caption_font=values['font'],caption_position=values['position'],
        caption_size=values['size'],caption_max_lines=caption.get('max_lines',2),
        caption_text_color=caption.get('text_color','#FFFFFF'),caption_highlight_color=caption.get('accent_color'),
        caption_background=caption.get('background','Shadow Only'),
        finish_grain=finish.get('grain',0),finish_vignette=finish.get('vignette',0),finish_contrast=finish.get('contrast',0),
        visual_director=VisualDirectorSettings(enabled=True,mode=values['energy'],
            transition_frequency=direction.get('transition_frequency',.15),seed=package.pro.get('style',{}).get('seed',48127)))

@dataclass
class Project:
    name: str
    narration: str
    image_folder: str
    script: str
    music: str = ""
    package: Package | None = None
    images: dict[str,Path] = field(default_factory=dict)
    orientation: str = "VERTICAL"
    notices: list[tuple[str,str]] = field(default_factory=list)
    overrides: dict = field(default_factory=dict)
    moment_overrides: dict = field(default_factory=dict)
    saved_path: str = ""

    def validate(self):
        from .media import validate_media, probe_audio
        from .moments import validate_moments
        self.package=parse_script(self.script)
        self.images,_,messages=validate_media(self.package,Path(self.narration),Path(self.image_folder))
        self.orientation=self.package.pro.get('format',{}).get('orientation',infer_format(self.images))
        self.notices=[('info' if 'within one output frame' in message else 'warning',message) for message in messages]
        if infer_format(self.images)!=self.orientation:
            self.notices.append(('warning','Images differ from the script format. Fill frame may crop them; Fit entire image preserves them.'))
        if self.music:
            if not Path(self.music).is_file():self.notices.append(('warning','Background music is missing. Export will use narration without that file.'))
            else:probe_audio(Path(self.music))
        _,messages=validate_moments(self.package)
        self.notices.extend(('info',m) for m in messages)
        return self

    def effective_package(self):
        if not self.package:raise PackageError('Create a timeline first.')
        pro={**self.package.pro,'moment_overrides':self.moment_overrides}
        return replace(self.package,pro=pro)

    def settings(self, **kwargs):
        return script_settings(self.effective_package(),self.overrides.get('orientation',self.orientation),self.music,self.overrides,**kwargs)

    def save(self,path: str):
        data={'project_format':2,'name':self.name,'narration':self.narration,'image_folder':self.image_folder,
              'script':self.script,'music':self.music,'overrides':self.overrides,'moment_overrides':self.moment_overrides}
        target=Path(path); temp=target.with_suffix(target.suffix+'.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        temp.replace(target); self.saved_path=str(target)

    @classmethod
    def load(cls,path: str):
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        allowed={'project_format','name','narration','image_folder','script','music','overrides','moment_overrides'}
        if data.get('project_format')!=2 or data.keys()-allowed:
            raise PackageError('Expected an ATS 3.0 project (project_format 2). Old projects cannot be opened.')
        overrides=data.get('overrides',{})
        if not isinstance(overrides,dict) or overrides.keys()-{'preset','energy','voice_volume','music_volume','position','size','font','orientation','framing'}:
            raise PackageError('Project contains unsupported override keys. Expected ATS 3.0 overrides only.')
        data.pop('project_format'); project=cls(**data); project.saved_path=path
        return project.validate()

class StageETA:
    """Never extrapolate rendering speed into audio or mux/verification stages."""
    def __init__(self):self.stage=None;self.started=0.;self.initial=0.
    def update(self,percent:float,now:float):
        stage=0 if percent<90 else 1 if percent<91 else 2 if percent<96 else 3
        if stage!=self.stage:self.stage,self.started,self.initial=stage,now,percent
        upper=(90,91,96,100)[stage]; elapsed=now-self.started; delta=percent-self.initial
        return max(0,(upper-percent)*elapsed/delta) if delta>.2 and elapsed>2 else None
