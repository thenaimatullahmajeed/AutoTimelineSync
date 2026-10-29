"""Informational house-rule classification; never alters a rendering decision."""
from collections import Counter
from fractions import Fraction
import math,json
from .visual_director import FANCY,TRANSITIONS
CUTS={'HARD_CUT','NONE'}
SUBTLE=TRANSITIONS-FANCY
UTILIZATION_LINE='Mode {mode}: {noncuts} non-cut of {boundaries}, {fancy} fancy, {dates} date cards, {sfx} sound cues, {overlays} overlays, features unused: {unused}.'

def classify_counts(types,energy='BALANCED',frequency=.15):
    """Exact integer percentage boundaries; input excludes first scene."""
    b=len(types);n=sum(t not in CUTS for t in types);f=sum(t in FANCY for t in types)
    repeated=any(a==z and a not in CUTS for a,z in zip(types,types[1:]))
    adjacent=any(a in FANCY and z in FANCY for a,z in zip(types,types[1:]))
    maximum=max(Counter(t for t in types if t in FANCY).values(),default=0)
    factor={'SUBTLE':.45,'BALANCED':1.,'HIGH_ENERGY':1.7}[energy]
    budget=max(1,math.ceil(b*frequency*factor)) if frequency else 0
    p=Fraction(1,4) if energy=='HIGH_ENERGY' else Fraction(3,20)
    standard_fancy=min(math.floor(b*p),budget)
    caps={'STANDARD':{'noncut_max':2*b//5,'fancy_max':standard_fancy,'same_fancy_max':2},
          'RICH':{'noncut_min':math.ceil(Fraction(11*b,20)),'noncut_max':7*b//10,'fancy_min':math.ceil(Fraction(b,5)),'fancy_max':b//4,'same_fancy_max':3},
          'MAX':{'noncut_required':b,'fancy_max':7*b//20,'same_fancy_max':3}}
    matches=[]
    if b and not repeated and not adjacent:
        if n==b and f<=caps['MAX']['fancy_max'] and maximum<=3:matches.append('MAX')
        if caps['RICH']['noncut_min']<=n<=caps['RICH']['noncut_max'] and caps['RICH']['fancy_min']<=f<=caps['RICH']['fancy_max'] and maximum<=3:matches.append('RICH')
        if n<=caps['STANDARD']['noncut_max'] and f<=standard_fancy and maximum<=2:matches.append('STANDARD')
    return {'mode':matches[0] if matches else 'NONE','matching_modes':matches,'boundaries':b,'noncuts':n,'fancy':f,
            'same_fancy_maximum':maximum,'adjacent_fancy':adjacent,'repeated_adjacent_noncut':repeated,
            'generated_director_budget':budget,'thresholds':caps,'enforcement':'INFO only; never reject or rewrite'}

def classify_package(package,spec,settings):
    raw=json.loads(package.source_json);scenes=raw['scenes'];plans=spec.scenes
    types=[s.transition_applied for s in plans[1:]]
    result=classify_counts(types,settings.visual_director.mode,settings.visual_director.frequency)
    reasons=[]
    if scenes[0].get('transition')!='HARD_CUT':reasons.append('HOUSE RULE: scene 001 must explicitly use HARD_CUT.')
    for i,(scene,plan) in enumerate(zip(scenes,plans)):
        path=f'$.scenes[{i}]'
        if 'motion' not in scene or 'transition' not in scene:reasons.append(path+': HOUSE RULE requires explicit motion and transition.')
        for key in ['motion_config','transition_config']:
            if key in scene and scene[key]=={}:reasons.append(path+'.'+key+': HOUSE RULE forbids an empty config.')
        if i and plan.transition_applied not in CUTS:
            config=scene.get('transition_config',{})
            if config.get('type')!=scene.get('transition'):reasons.append(path+': HOUSE RULE requires matching transition_config.type.')
            frames=config.get('frames')
            if isinstance(frames,bool) or not isinstance(frames,int) or not 4<=frames<=30:reasons.append(path+': HOUSE RULE requires explicit integer frames from 4 to 30.')
            minimum=math.ceil(max(4,math.ceil(.12*package.fps))/.45)
            if min(package.scenes[i-1].frame_count,package.scenes[i].frame_count)<minimum:reasons.append(path+': HOUSE RULE non-cut cannot fit both neighboring scenes.')
        requested=scene.get('transition_config',{}).get('type',scene.get('transition'))
        if i and requested not in CUTS and plan.transition_applied in CUTS:reasons.append(path+': requested non-cut fell back to a cut.')
    result['numeric_mode']=result['mode'];result['house_rule_issues']=reasons
    if reasons:result['mode']='NONE'
    result['editorial_checks']='Story relevance and whether a beat is fast need author review; the app does not infer them.'
    return result

def utilization(package,images,settings,spec=None):
    from .pro_spec import build_spec
    from .pro_audio import choose_cues
    from .capabilities import current_capabilities
    spec=spec or build_spec(package,images,settings)
    raw=json.loads(package.source_json);scenes=raw['scenes'];boundaries=spec.scenes[1:]
    cues=choose_cues(spec,0,raw.get('direction',{}).get('sfx_enabled',True))
    moments=spec.changes.get('moments',[]);counts=Counter(s.transition_applied for s in boundaries)
    n=len(boundaries);noncut=sum(v for k,v in counts.items() if k not in CUTS)
    used={'overlays':bool(spec.overlays),'DATE_CARD':any(m['type']=='DATE_CARD' for m in moments),
          'CIRCLE':any(m['type']=='CIRCLE' for m in moments),'PHOTO_NOTE':any(o['type']=='PHOTO_NOTE' for o in spec.overlays),
          'motion_config':any('motion_config' in s for s in scenes),'look_override':any('look_override' in s for s in scenes),
          'style':bool(raw.get('style')),'audio':bool(raw.get('audio')),'ending':bool(raw.get('ending')),
          'SFX':bool(cues),'finish':any(raw.get('direction',{}).get('finish',{}).values()),'music':bool(settings.music_path)}
    result={'scene_count':len(spec.scenes),'boundaries':n,'transitions_by_type':dict(counts),'noncut_boundaries':noncut,
        'noncut_share':noncut/n if n else 0,'fancy_boundaries':sum(v for k,v in counts.items() if k in FANCY),
        'moments_by_type':dict(Counter(m['type'] for m in moments)),'sfx_cue_count':len(cues),
        'overlays_by_type':dict(Counter(o['type'] for o in spec.overlays)),
        'scenes_using_motion_config':sum('motion_config' in s for s in scenes),
        'scenes_using_look_override':sum('look_override' in s for s in scenes),
        'supported_features_not_used':[k for k,v in used.items() if not v],
        'unused_transition_enums':sorted(set(current_capabilities()['enums']['transitions'])-set(counts)),
        'warnings':list(spec.warnings),'moment_notices':spec.changes.get('moment_notices',[])}
    result['classification']=classify_package(package,spec,settings);result['mode']=result['classification']['mode']
    result['utilization_line']=UTILIZATION_LINE.format(mode=result['mode'],noncuts=noncut,boundaries=n,
        fancy=result['fancy_boundaries'],dates=result['moments_by_type'].get('DATE_CARD',0),sfx=len(cues),
        overlays=len(spec.overlays),unused=', '.join(result['supported_features_not_used']) or 'none')
    result['note']='Actual applied transitions and cues; first scene excluded. House modes are information, never acceptance rules.'
    return result
