"""Truthful ATS 3 authoring capabilities; no legacy or layer advertising."""
from . import __version__
from .product import FORMATS,PRESETS,ProductSettings
from .pro_schema import STYLE_IDS,LOOK_IDS,TRANSITION_IDS,EASINGS,OVERLAYS,OVERLAY_STYLES,SFX_IDS
from .schema import MOTIONS,TOP_FIELDS,SCENE_FIELDS,WORD_FIELDS,CAPTION_FIELDS,MAX_PACKAGE_BYTES
from .project_settings import CAPTION_FONTS
from dataclasses import asdict

def current_capabilities():
    return {'tool':'Auto Timeline Sync by Naimat','version':__version__,'supported_schema_versions':['ATS_PACKAGE_V2'],
        'project_format':2,'project_extension':'.ats3','required_fields':{'package':sorted(TOP_FIELDS),
        'scene':sorted(SCENE_FIELDS-{'motion','transition'}),'word':sorted(WORD_FIELDS),'caption':sorted(CAPTION_FIELDS),
        'caption_style':['enabled','highlight_current_word']},
        'optional_fields':{'package':['format','direction','style','audio','overlays','ending','moments'],
            'scene':['motion','transition','motion_config','transition_config','sfx','look_override'],
            'caption_style':['preset','font','size','position','max_lines','text_color','accent_color','background','emphasis','animation'],
            'format':['orientation','aspect_ratio'],'direction':['energy','finish','voice_level','music_level','duck_db','sfx_enabled','transition_frequency'],
            'finish':['grain','vignette','contrast']},
        'enums':{'motions':sorted(MOTIONS),'transitions':sorted(TRANSITION_IDS),'caption_presets':list(PRESETS.values()),
                 'styles':sorted(STYLE_IDS),'looks':sorted(LOOK_IDS),'easings':sorted(EASINGS),'overlay_types':sorted(OVERLAYS),
                 'overlay_styles':sorted(OVERLAY_STYLES),'fonts':list(CAPTION_FONTS),'sfx':sorted(SFX_IDS)},
        'formats':{k:{'aspect_ratio':v[0],'tiers':v[1]} for k,v in FORMATS.items()},
        'defaults':{'fps_authoring':30,'orientation_if_no_votes':'VERTICAL','caption_preset':'Minimal Cinematic','font':'Inter',
            'energy':'BALANCED','music_level':.18,'voice_level':1,'duck_db':-9,'finish':{'grain':0,'vignette':0,'contrast':0}},
        'implemented':{'v2_import':True,'v3_import':False,'layer_engine':False,'remotion':False,'full_scene_images':True,
            'word_highlight':True,'date_card':True,'source_circle':True,'music_equal_power_loop':True,'director_always_on':True},
        'limits':{'json_bytes':MAX_PACKAGE_BYTES,'fps':[1,60],'circle_min_side':.03,'circle_max_area':.2,
            'invalid_moments':'skip with info notice','source_tracking':'static source box follows declared camera transform; no object detection',
            'preview_export':'shared compositor and shared audio mix/master; resolution, sampling and compression affect visual pixels'},
        'serialization':'one compact UTF-8 object, no BOM, newline or trailing data'}

def current_capabilities_json():
    import json
    return json.dumps(current_capabilities(),ensure_ascii=False,indent=2)
