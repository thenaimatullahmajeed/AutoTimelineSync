"""D1 review candidate: independent diagnostics plus production acceptance oracle."""
import copy,json,math,re,sys,argparse
from pathlib import Path
from bootstrap import ROOT,CORE
from ats_studio.schema import frame_at,_pairs_unique,_reject_constant,MAX_PACKAGE_BYTES
from ats_studio.pro_schema import Checker
from ats_studio.product import parse_script,script_settings
from ats_studio.moments import validate_moments

def get_path(data,path):
    value=data
    for token in re.findall(r'[^.\[\]]+',path.lstrip('$.')):
        try:value=value[int(token) if isinstance(value,list) else token]
        except (KeyError,IndexError,ValueError,TypeError):return {'missing':True}
    return value

def validate_all(text,images=None,audio=None):
    errors=[]
    def add(path,message,expected='',severity='ERROR',rule='validation',app_path=None):
        entry={'path':path,'rule':rule,'value':get_path(raw,path) if isinstance(raw,dict) else raw,'expected':expected or message,'severity':severity,'message':message,'app_path':app_path if app_path is not None else path}
        if not any(e['path']==path and e['message']==message for e in errors):errors.append(entry)
    raw=None
    if not isinstance(text,str):
        add('$','Input must be JSON text.',rule='input');return {'valid':False,'diagnostics':errors}
    if len(text.encode('utf-8'))>MAX_PACKAGE_BYTES:
        add('$','$: JSON exceeds the 50 MiB safety limit.',rule='json_bytes');return {'valid':False,'diagnostics':errors}
    from ats_studio.schema import _normalize_json_text
    try:raw=json.loads(_normalize_json_text(text),object_pairs_hook=_pairs_unique,parse_constant=_reject_constant)
    except Exception as exc:
        add('$',str(exc),rule='json_syntax');return {'valid':False,'diagnostics':errors}
    if not isinstance(raw,dict):
        add('$','$ must be an object.',rule='object');return {'valid':False,'diagnostics':errors}
    contract=json.loads((ROOT/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
    fields=contract['fields']
    class Collect(Checker):
        def error(self,path,message):add(path,message,rule='field')
    check=Collect()
    def visit(value,path):
        pattern=re.sub(r'\[\d+\]','[]',path)
        rule=fields.get(pattern)
        if rule:
            typ=rule['type']
            if typ=='object':
                if not isinstance(value,dict):check.object(value,path,set(rule.get('allowed',rule.get('required',[]))));return
                allowed=set(rule.get('allowed',rule.get('required',[])))
                unknown=set(value)-allowed
                for key in sorted(unknown):add(path+'.'+key,'unknown field',sorted(allowed),rule='allowed_fields')
                for key in rule.get('required',[]):
                    if key not in value:add(path+'.'+key,'required field is missing',rule='required')
            elif typ=='array':
                if not isinstance(value,list):check.array(value,path);return
            elif typ in ('number','integer') and rule.get('minimum') is not None and rule.get('maximum') is not None:check.number(value,path,int(rule['minimum']) if isinstance(rule['minimum'],str) else rule['minimum'],int(rule['maximum']) if isinstance(rule['maximum'],str) else rule['maximum'],typ=='integer')
            elif typ=='enum':check.enum(value,path,set(rule['allowed']))
            elif typ=='boolean':check.boolean(value,path)
            elif typ=='string':
                if 'pattern' in rule:
                    if not isinstance(value,str) or not re.fullmatch(rule['pattern'],value):add(path,'expected #RRGGBB',rule='color')
                elif 'max_chars' in rule:check.string(value,path,rule['max_chars'])
            elif pattern.endswith('.variant'):
                if value!='AUTO':check.number(value,path,1,9,True)
        if isinstance(value,dict):
            for key,item in value.items():
                if path=='$' and key=='moments':continue
                visit(item,path+'.'+key)
        elif isinstance(value,list):
            for i,item in enumerate(value):visit(item,f'{path}[{i}]')
    visit(raw,'$')
    # Production policy messages are sampled from the real parser on isolated
    # valid fixtures, preserving exact wording while collecting independent rules.
    base=json.loads((CORE/'Examples/ATS3_vertical.json').read_text())
    def policy(path,value):
        isolated=copy.deepcopy(base);tokens=re.findall(r'[^.\[\]]+',path.lstrip('$.'));target=isolated
        for token in tokens[:-1]:
            if isinstance(target,list):target=target[int(token)]
            else:target=target.setdefault(token,{})
        target[tokens[-1]]=value
        if path=='$.caption_style.animation':isolated['caption_style']['preset']=raw.get('caption_style',{}).get('preset')
        try:parse_script(json.dumps(isolated))
        except Exception as exc:add(path,str(exc),rule='product_policy')
    if raw.get('schema')!='ATS_PACKAGE_V2':policy('$.schema',raw.get('schema'))
    for path in ['$.auto_direct','$.audio.music','$.audio.ambience','$.audio.sfx.pack','$.audio.sfx.density','$.caption_style.chunk_words','$.caption_style.safe_zone']:
        value=get_path(raw,path)
        if value!={'missing':True}:policy(path,value)
    style=raw.get('caption_style')
    if isinstance(style,dict) and isinstance(style.get('preset'),str) and style.get('preset') in {'Hormozi Style','MrBeast / Viral Pop','Karaoke Highlight','Neon Glow','Minimal Cinematic','Highlighter Box'} and 'animation' in style:policy('$.caption_style.animation',style['animation'])
    scenes=raw.get('scenes');words=raw.get('words');captions=raw.get('captions');duration=raw.get('audio_duration');fps=raw.get('fps')
    def finite(v):
        try:return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
        except (ValueError,OverflowError):return False
    if not isinstance(raw.get('project_title'),str) or not raw.get('project_title','').strip():add('$.project_title','project_title must be nonempty text.')
    if not finite(duration) or duration<=0:add('$.audio_duration','audio_duration must be greater than zero.')
    if not isinstance(fps,int) or isinstance(fps,bool) or not 1<=fps<=60:add('$.fps','fps must be between 1 and 60.')
    if not isinstance(scenes,list) or not scenes:add('$.scenes','scenes must be a nonempty array.')
    for name,value in [('words',words),('captions',captions)]:
        if not isinstance(value,list):add('$.'+name,name+' must be an array.')
    fmt=raw.get('format')
    if isinstance(fmt,dict) and fmt.get('orientation') in contract['formats'] and fmt.get('aspect_ratio')!=contract['formats'][fmt['orientation']]['aspect_ratio']:add('$.format.aspect_ratio','expected '+contract['formats'][fmt['orientation']]['aspect_ratio'])
    seed=raw.get('style',{}).get('seed') if isinstance(raw.get('style'),dict) else None
    if seed is not None and (not isinstance(seed,int) or isinstance(seed,bool) or not 0<=seed<=2147483647):add('$.style.seed','must be an integer between 0 and 2147483647',rule='settings_seed',app_path='$.style.seed')
    times_ok=finite(duration) and duration>0 and isinstance(fps,int) and not isinstance(fps,bool) and 1<=fps<=60
    previous=None
    if isinstance(scenes,list):
        for i,s in enumerate(scenes):
            if not isinstance(s,dict):continue
            path=f'$.scenes[{i}]';expected=f'{i+1:03d}'
            for key in ['start','end']:
                if not finite(s.get(key)):add(path+'.'+key,f'Scene {expected} {key} must be a finite number.',rule='time_number')
            if s.get('id')!=expected:add(path+'.id',f'Scene {expected} id should be "{expected}".',expected,app_path='$.v1_contract')
            if s.get('image_id')!=s.get('id'):add(path+'.image_id',f'Scene {expected} image_id must match its id "{s.get("id")}".',app_path='$.v1_contract')
            for key in ['motion','transition']:
                if key in s:check.enum(s[key],path+'.'+key,set(contract['enums']['motions' if key=='motion' else 'transitions']))
            if i==0 and s.get('transition','HARD_CUT') not in {'HARD_CUT','NONE'}:add(path+'.transition','Scene 001 must use HARD_CUT or NONE; it has no preceding image to transition from.',app_path='$.v1_contract')
            mc=s.get('motion_config')
            if isinstance(mc,dict) and 'shake' in mc:add(path+'.motion_config.shake','unsupported in ATS 3.0; remove it. Use deliberate motion and finishing instead.')
            tc=s.get('transition_config',{})
            if i==0 and (s.get('sfx') or isinstance(tc,dict) and tc.get('sfx') not in (None,'NONE')):add('$.scenes[0].sfx','$.scenes[0].sfx: first scene has no cut. Place SFX on a later flagged cut.')
            if times_ok and finite(s.get('start')) and finite(s.get('end')):
                start,end=s['start'],s['end']
                if start<0 or end<=start:add(path+'.end',f'Scene {expected} needs 0 <= start < end.',app_path='$.v1_contract')
                else:
                    first,last=frame_at(start,fps),frame_at(end,fps)
                    if last<=first:add(path+'.end',f'Scene {expected} is shorter than one output frame at {fps} FPS.',app_path='$.v1_contract')
                    if i==0 and first!=0:add(path+'.start','First scene must start at timeline origin (frame 0).',app_path='$.v1_contract')
                    if previous is not None and first!=previous:add(path+'.start',f'Scene {expected} has a {"gap" if first>previous else "overlap"} after scene {i:03d} at output-frame precision.',app_path='$.v1_contract')
                    previous=last
            if not isinstance(s.get('voice_text'),str):add(path+'.voice_text',f'Scene {expected} voice_text must be text.',app_path='$.v1_contract')
    if times_ok and previous is not None and previous!=frame_at(duration,fps):add('$.scenes[-1].end',f'Last scene ends at frame {previous}; audio_duration requires frame {frame_at(duration,fps)}.',app_path='$.v1_contract')
    indices={};prior_index=None;prior_start=None
    if isinstance(words,list):
        for i,w in enumerate(words):
            if not isinstance(w,dict):continue
            path=f'$.words[{i}]';index=w.get('index');start=w.get('start');end=w.get('end')
            for key in ['start','end']:
                if not finite(w.get(key)):add(path+'.'+key,f'Word entry {i+1} {key} must be a finite number.',rule='time_number')
            if not isinstance(index,int) or isinstance(index,bool):add(path+'.index',f'Word entry {i+1} index must be an integer.',app_path='$.v1_contract')
            else:
                if index in indices or prior_index is not None and index<=prior_index:add(path+'.index',f'Word entry {i+1} index must be unique and increasing.',app_path='$.v1_contract')
                indices[index]=w;prior_index=index
            if not isinstance(w.get('text'),str) or not w.get('text','').strip():add(path+'.text',f'Word entry {i+1} text must be nonempty.',app_path='$.v1_contract')
            if times_ok and finite(start) and finite(end):
                if start<0 or end<=start or end>duration+1/fps:add(path+'.end',f'Word entry {i+1} timing is outside the audio.',app_path='$.v1_contract')
                if prior_start is not None and start<prior_start:add(path+'.start',f'Word entry {i+1} is out of chronological order.',app_path='$.v1_contract')
                prior_start=start
    prior_start=None
    if isinstance(captions,list):
        for i,c in enumerate(captions):
            if not isinstance(c,dict):continue
            path=f'$.captions[{i}]';expected=f'{i+1:03d}';first,last=c.get('word_start_index'),c.get('word_end_index')
            for key in ['start','end']:
                if not finite(c.get(key)):add(path+'.'+key,f'Caption {expected} {key} must be a finite number.',rule='time_number')
            if not isinstance(c.get('text'),str) or not c.get('text','').strip():add(path+'.text',f'Caption {expected} text must be nonempty.',app_path='$.v1_contract')
            if c.get('id')!=expected:add(path+'.id',f'Caption {expected} id should be "{expected}".',expected,app_path='$.v1_contract')
            if not isinstance(first,int) or not isinstance(last,int) or isinstance(first,bool) or isinstance(last,bool) or first not in indices or last not in indices or first>last:add(path+'.word_start_index',f'Caption {expected} references missing or reversed word indexes.',app_path='$.v1_contract')
            else:
                timed=' '.join(w['text'] for k,w in indices.items() if first<=k<=last and isinstance(w.get('text'),str))
                if ' '.join(str(c.get('text','')).split())!=' '.join(timed.split()):add(path+'.text',f'$.captions[{i}].text: expected timed-word text {timed!r}. Keep caption text and word indices identical.',timed)
            if times_ok and finite(c.get('start')) and finite(c.get('end')):
                if c['start']<0 or c['end']<=c['start'] or c['end']>duration+1/fps:add(path+'.end',f'Caption {expected} timing is outside the audio.',app_path='$.v1_contract')
                if prior_start is not None and c['start']<prior_start:add(path+'.start',f'Caption {expected} is out of chronological order.',app_path='$.v1_contract')
                prior_start=c['start']
    # Original validators remain the acceptance oracle, catching rules not yet
    # represented by the structured prototype rather than silently accepting.
    package=None
    try:package=parse_script(text);settings=script_settings(package,raw.get('format',{}).get('orientation','VERTICAL'))
    except Exception as exc:
        for line in str(exc).splitlines():
            if line=='V2 validation failed:':continue
            match=re.match(r'(\$[^:]*):\s*(.*)',line)
            path,msg=match.groups() if match else ('$',line)
            if not any(msg in e['message'] for e in errors):add(path,msg,rule='production_oracle')
    if package:
        valid,notices=validate_moments(package)
        for notice in notices:add(notice.split(' skipped:')[0],notice,severity='SKIP',rule='moment')
        # Match Project.effective_package's product marker and plan attributes.
        # Raw parsed Scene objects are not renderer plans; the legacy cue branch
        # would otherwise read transition_applied from the wrong object type.
        from types import SimpleNamespace
        from ats_studio.pro_audio import choose_cues
        from dataclasses import replace
        cue_package=replace(package,pro={**package.pro,'product_version':3})
        cue_plans=[SimpleNamespace(id=s.id,first_frame=s.first_frame,frames=s.frame_count,
            motion=s.motion,transition_applied=s.transition) for s in package.scenes]
        try:choose_cues(SimpleNamespace(package=cue_package,scenes=cue_plans,seed=settings.visual_director.seed,
            auto_direct=False,strict_json=True),0,raw.get('direction',{}).get('sfx_enabled',True))
        except Exception as exc:
            line=str(exc);match=re.match(r'(\$[^:]*):\s*(.*)',line);path,msg=match.groups() if match else ('$',line);add(path,msg,rule='cue_spacing')
        if images and audio:
            from ats_studio.media import validate_media
            try:
                mapped,_,messages=validate_media(package,Path(audio),Path(images))
                for message in messages:
                    duration_info='within one output frame' in message
                    add('$.audio_duration' if duration_info else '$',message,severity='INFO' if duration_info else 'WARN',rule='media',app_path=None)
                if not any(e['severity']=='ERROR' for e in errors):
                    from ats_studio.pro_spec import build_spec
                    spec=build_spec(package,mapped,settings)
                    for message in spec.warnings:add('$',message,severity='WARN',rule='render_spec')
                    for message in spec.changes.get('moment_notices',[]):
                        if not any(e['message']==message for e in errors):
                            add(message.split(' skipped:')[0] if message.startswith('$') else '$',message,severity='SKIP',rule='moment_crop')
            except Exception as exc:add('$',str(exc),rule='media')
    errors.extend(font_warnings(raw))
    return {'valid':not any(e['severity']=='ERROR' for e in errors),'diagnostics':errors,'scope':'Review candidate: collected diagnostics with production parser/cue/media oracle. Syntax errors must be fixed before field inspection.'}

COPY_HEADER='ATS_PACKAGE_V2 correction request. Fix only the paths below and return one complete corrected JSON object. Preserve all other fields.'
COPY_COLUMNS='path | rule | value | expected | severity'
RTL_WARNING='creator caption layout is left to right; multiword right-to-left order will be wrong'

def copy_message(result):
    def cell(value):return str(value).replace('\r','\\r').replace('\n','\\n').replace('|','\\u007c')
    lines=[COPY_HEADER,COPY_COLUMNS]
    for entry in result['diagnostics']:
        values=[entry['path'],entry['rule'],json.dumps(entry['value'],ensure_ascii=False),entry['expected'],entry['severity']]
        lines.append(' | '.join(cell(v) for v in values))
    return '\n'.join(lines)

def font_warnings(raw):
    """Native glyph checks; fallback is acknowledged and never changes acceptance."""
    if not isinstance(raw,dict):return []
    style=raw.get('caption_style',{})
    if not isinstance(style,dict):return []
    captions=raw.get('captions',[])
    if not isinstance(captions,list):return []
    text=' '.join(c.get('text','') for c in captions if isinstance(c,dict) and isinstance(c.get('text'),str))
    from .caption_presets import PROFILES
    from .fonts import resolve_font_family
    from PySide6.QtGui import QFont,QRawFont
    preset=style.get('preset','Minimal Cinematic');font_name=style.get('font','Inter')
    if not isinstance(font_name,str) or not isinstance(preset,str):return []
    result=[]
    def warn(path,rule,value,message):
        result.append({'path':path,'rule':rule,'value':value,'expected':message,'severity':'WARN','message':message,'app_path':path})
    if preset in PROFILES and re.search('[\u0590-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb1d-\ufdff\ufe70-\ufeff]',text):
        warn('$.caption_style.preset','creator_rtl',preset,RTL_WARNING)
    actual=PROFILES[preset]['font'] if preset in PROFILES and font_name in {'Arial','Segoe UI'} else font_name
    font=QFont(resolve_font_family(actual));font.setPixelSize(60)
    if preset in PROFILES:font.setWeight(PROFILES[preset]['weight'])
    raw_font=QRawFont.fromFont(font)
    urdu=bool(re.search('[ٹڈڑںےھہگچپژ]',text))
    scripts=[('Hindi','[\u0900-\u097f]','Poppins'),('Urdu' if urdu else 'Arabic','[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]','Noto Nastaliq Urdu' if urdu else 'DejaVu Sans')]
    for script,pattern,recommended in scripts:
        chars=set(re.findall(pattern,text))
        missing=[c for c in chars if not raw_font.supportsCharacter(ord(c))]
        if missing:
            warn('$.caption_style.font','script_font',font_name,f'{font_name} lacks native glyphs for some {script} characters; recommend {recommended}. Font fallback may render them; layout is not certified.')
    return result
