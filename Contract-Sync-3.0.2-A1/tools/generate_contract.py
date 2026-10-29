"""Generate review contract and flat guide from verified code and evidence."""
import sys,json,copy,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,CORE,application,install
application();install()
from ats_studio.sync_core import CONTRACT_ID,SEED_ERROR
from ats_studio.sync_modes import FANCY,SUBTLE,UTILIZATION_LINE
from ats_studio.sync_diagnostics import COPY_HEADER,COPY_COLUMNS,RTL_WARNING
from ats_studio.product import parse_script
from ats_studio.caption_presets import PROFILES
baseline=ROOT.parent/'ats_contract_audit_3_0_2'
c=json.loads((baseline/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
evidence=json.loads((ROOT/'Evidence/semantics.json').read_text(encoding='utf-8'))
sync=(ROOT/'Inputs/FINAL_SYNC_INSTRUCTION.txt').read_text(encoding='utf-8')
modes=sync.split('5. TRANSITION MODES',1)[1].split('6. UTILIZATION LINE',1)[0].strip()
expected_fancy=set(modes.split('FANCY set:',1)[1].split('. SUBTLE set:',1)[0].strip().split(', '))
assert expected_fancy==set(FANCY)
changelog='Contract B: D1 collected diagnostics and D2 utilization; D3 rejects style.seed outside 0 to 2147483647 at its JSON path; D4/D5 add warnings only. Rendering/audio unchanged. Integration approved by the user on 2026-10-13; the new portable build is separate from the old installed app.'
c.update(version='3.0.2-A1',contract_snapshot='2026-10-13',contract_id=CONTRACT_ID,contract_version='3.0.2-A1',supersedes_contract_id='ATS_SYNC_2026-10-A',contract_status='APPROVED INTEGRATION; see packaged verification in SYNC_CHECKLIST.md',contract_changelog=[changelog],
    fancy_set=sorted(FANCY),subtle_set=sorted(SUBTLE),mode_definitions={'exact_shared_section_5':modes,'enforcement':'INFO HOUSE RULE only','precedence':['MAX','RICH','STANDARD','NONE'],'zero_boundaries':'NONE','consecutive_noncut_interpretation':'adjacent timeline boundaries, both non-cuts','editorial_semantics':'not machine verified'},
    copy_errors_format={'line_1':COPY_HEADER,'line_2':COPY_COLUMNS,'row_fields':['path','rule','value','expected','severity'],'cell_escaping':'line breaks escaped and literal pipes serialized as Unicode escapes so each diagnostic occupies one row'},
    utilization_line_format='Mode M: N non-cut of B, F fancy, D date cards, S sound cues, O overlays, features unused: X.',
    utilization_template=UTILIZATION_LINE,caption_fit=evidence['caption_fit'])
c['mode_definitions'].update({
 'STANDARD':{'noncut_max':'floor(0.40 * B)','hard_cut_none_min_share':.60,'fancy_max':'min(floor(B * p), generated director budget)','p':{'HIGH_ENERGY':.25,'other':.15},'same_fancy_max':2,'adjacent_fancy':False},
 'RICH':{'noncut_min':'ceil(0.55 * B)','noncut_max':'floor(0.70 * B)','fancy_min':'ceil(0.20 * B)','fancy_max':'floor(0.25 * B)','same_fancy_max':3,'adjacent_fancy':False,'author_default':'vertical videos under three minutes'},
 'MAX':{'noncut_required':'B','fancy_max':'floor(0.35 * B)','same_fancy_max':3,'adjacent_fancy':False,'fast_beat_frames_recommendation':[4,8]},
 'common':{'first_scene':'explicit HARD_CUT','matching_config_on_each_noncut':True,'frames':[4,30],'no_empty_configs':True,'adjacent_noncut_same_type':False,'frame_fit':'at least nine neighboring frames at 30 fps; eighteen at 60 fps; general formula in transitions section','explicit_motion_and_transition':True},
 'generated_director_budget':'frequency zero gives zero; otherwise max(1, ceil(B * frequency * factor)); SUBTLE factor 0.45, BALANCED 1, HIGH_ENERGY 1.7'})
seed=c['fields']['$.style.seed'];seed.update(minimum=0,maximum=2147483647,effective_error=SEED_ERROR,effective_error_json_path='$.style.seed',source='overlay/ats_studio/sync_core.py:apply_seed_guard',enforcement='REJECT')
c['validation_layers']['all_errors']='Optional collected diagnostics; production parser and Create Timeline pipeline remain final acceptance oracle, with approved D3 seed guard.'
c['motions_aliases']=evidence['motions']
c['motion_config_semantics']={
 'zoom_from':'Crop zoom at scene start; 1 means the base Fill/Fit crop; 2 means half its dimensions. Overrides the chosen motion path zoom start.',
 'zoom_to':'Crop zoom at scene end, interpolated with ease; overrides path zoom end. 1 to 2.',
 'ease':'Controls progress of zoom and pan. LINEAR is constant progress; EASE_IN/EASE_OUT/EASE_IN_OUT shape acceleration. TINY_PUNCH_IN with no explicit ease reaches its zoom over the first 35 percent.',
 'focus':'Both x and y required, normalized in the full source image. Sets crop center before pan offsets and edge clamping; it does not track an object.',
 'blur':'Temporal camera-crop sampling, 0 to 1: zero forces one sample; positive values use max of 2 and Python round of 4 times blur, up to 4 subframe samples. Blends nearby camera positions; does not animate objects.',
 'example':{'motion':'SLOW_PUSH_IN','motion_config':{'zoom_from':1.03,'zoom_to':1.12,'ease':'EASE_IN_OUT','focus':{'x':.5,'y':.4},'blur':.05}}}
c['transition_config_semantics']={'direction':'LEFT/RIGHT use horizontal travel, UP/DOWN vertical travel for QUICK_PUSH, WHIP_PAN and SLIDE_SHADOW. Other effects ignore this field. AUTO resolves during planning; supply an explicit direction for repeatability.',
 'ease':'Applies to transition progress before blending/masking, without changing frame count.',
 'example':{'transition':'WHIP_PAN','transition_config':{'type':'WHIP_PAN','frames':7,'direction':'LEFT','ease':'EASE_OUT'}}}
look_desc={
 'CLEAN':'No look grading.', 'CLEAN_DOC':'Light source softening, without warmth, monochrome blend, grain or vignette from this look.',
 'DARK_NOIR':'Cool blue tint, strong monochrome blend, grain and darkened edges.', 'AGED_PARCHMENT':'Warm tint, light monochrome blend, grain and darkened edges; no paper image is generated.',
 'ALBUMEN_1880S':'Strong warm tint with monochrome blend, grain and darkened edges.', 'SILENT_FILM_1910S':'Nearly monochrome film treatment with grain, dark edges and seeded flicker.',
 'NITRATE_1930S':'Strong monochrome film treatment, slight warmth, grain, dark edges and seeded flicker.', 'PRESS_PHOTO_1950S':'Moderate monochrome blend, slight warmth, grain and edge shading.',
 'KODAK_1970S':'Warm color treatment with light desaturation, grain and edge shading.', 'VHS_1980S':'Cool/desaturated treatment with grain, purple tint and moving horizontal scanlines.',
 'TECH_MODERN':'Cool tint, small monochrome blend, light grain and edge shading.', 'SCIENCE_CLEAN':'Very light cool tint, grain and edge shading.',
 'FINANCE_PREMIUM':'Slight cool tint with subtle monochrome blend, grain and edge shading.'}
c['look_descriptions']={f.stem:{'description':look_desc[f.stem],'coefficients':json.loads(f.read_text()),'source':str(f.relative_to(CORE))} for f in (CORE/'presets/looks').glob('*.json')}
c['look_notes']='Intensity scales the treatment. Soften is applied separately before camera movement by blending a quarter-resolution source, with blend capped at 0.35. CLEAN or intensity zero bypasses color grading. Weave requires shake, which V2 product settings disable. Explicit direction.finish is a separate finishing stage. Historical IDs describe an effect, not authentic archival provenance.'
c['style_descriptions']={k:{'description':f"Selects the {v['first_scene_look']} look: {look_desc[v['first_scene_look']]}",'verified_default_intensity':v['first_scene_intensity'],'raw_preset':v['stored']} for k,v in evidence['styles'].items()}
c['style_notes']='V2 defaults look_intensity to zero, so choosing only a style preset does not activate color grading. Author an explicit nonzero intensity or scene look_override when wanted. Stored music/ambience, palettes and caption hints are legacy preset metadata, not permission to add unsupported JSON or override explicit transitions/caption choices.'
sounds={'BRUSH_SCRATCH':(.5,'Noise swell; a brush or document reveal.'),'CAMERA_SHUTTER':(.2,'Short synthetic noise click; a photo reveal.'),'FILM_CLICK':(.2,'Decaying 200 Hz tone/noise tick; an archive cut.'),'IMPACT_LOW':(.58,'Decaying low 50 Hz impact; a reveal.'),'IMPACT_SOFT':(.46,'Shorter decaying low impact; restrained emphasis.'),'INK_SPLASH':(.2,'Synthetic noise transient; an ink reveal, not recorded liquid.'),'PAGE_TURN':(.62,'Noise swell; page movement.'),'PAPER_SLIDE':(.4,'Short noise swell; document movement.'),'RISER_SHORT':(.7,'Noise swell; anticipation, not a pitched orchestral rise.'),'STAMP_THUD':(.2,'Decaying 200 Hz tone/noise tap; a date or document stamp.'),'SWIPE_SOFT':(.36,'Brief noise swell; a gentle swipe.'),'TICK_SOFT':(.2,'Short noise transient; a small evidence beat.'),'TYPEWRITER_KEY':(.2,'Short synthetic noise click; a text reveal.'),'WHOOSH_FAST':(.45,'Noise swell; fast travel or action.'),'WHOOSH_SOFT':(.55,'Longer noise swell; a gentler change of scene.')}
assert set(sounds)==set(c['enums']['sfx'])
c['sfx_descriptions']={k:{'seconds':v[0],'description':v[1],'source':'pro_audio._procedural_cue:159-182','scope':'built-in procedural fallback; an installed user asset can replace it'} for k,v in sounds.items()}
creator={'Hormozi Style':'Bold uppercase, thick black outline, shadow and active-word pop; selected or emphasized words use accent.', 'MrBeast / Viral Pop':'Bold uppercase, heavy outline/shadow, pop-bounce with slight rotation; selected or emphasized words use accent.', 'Karaoke Highlight':'Dim inactive words, active word at supplied text color on a rounded accent box; no extra emphasis.', 'Neon Glow':'Uppercase white text with layered accent glow and fade/scale; no active-word recolor or extra emphasis.', 'Minimal Cinematic':'Sentence case, soft shadow and fade upward; no active accent or emphasis.', 'Highlighter Box':'Dark letters on a white rounded box, active accent box and pop; supplied text color/background ignored.'}
c['creator_caption_character']={k:{'description':creator[k],'profile':{**v,'weight':int(v['weight'])}} for k,v in PROFILES.items()}
c['new_warnings']=[{'path':'$.caption_style.preset','rule':'creator_rtl','severity':'WARN','message':RTL_WARNING},{'path':'$.caption_style.font','rule':'script_font','severity':'WARN','message':'{font} lacks native glyphs for some {script} characters; recommend {recommended}. Font fallback may render them; layout is not certified.'}]
catalog=c['error_catalogue'];catalog['cases']=[x for x in catalog['cases'] if x.get('path_under_test')!='$.style.seed']
b=json.loads((CORE/'Examples/ATS3_vertical.json').read_text())
for value in [-1,2147483648,True,1.5,None,'1',0,2147483647]:
 d=copy.deepcopy(b);d['style']={'seed':value}
 case={'name':'candidate_seed:'+repr(value),'path_under_test':'$.style.seed','invalid_snippet':{'style':{'seed':value}}}
 try:parse_script(json.dumps(d));case['status']='ACCEPT'
 except Exception as exc:case.update(status='REJECT',message=str(exc),app_paths=['$.style.seed'])
 catalog['cases'].append(case)
catalog['scope']='Current candidate messages plus historical source literal inventory. D3 seed cases replayed against candidate. Full dynamic templates remain UNKNOWN.'
(ROOT/'ATS_CAPABILITIES.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')

guide=(baseline/'ATS_JSON_AUTHORING_GUIDE.md').read_text(encoding='utf-8')
# Keep all still-valid fields and limits, but replace the superseded seed account.
lines=guide.splitlines()
lines=[line for line in lines if not line.startswith('AUTHORING BUDGETS ARE RECOMMENDATIONS:')]
guide='\n'.join(lines)
guide=guide.replace('Its V2 parser and content renderer are unchanged from the shipped 3.0.1 baseline.','This integration adds only the approved early seed guard to acceptance; renderer and audio are unchanged.')
guide=guide.replace('The structural parser accepts signed 64-bit seeds, but timeline settings reject values outside the narrower range without a JSON path. Do not author the wider range.','The parser rejects invalid seeds early at $.style.seed with: must be an integer between 0 and 2147483647.')
guide='Contract: '+CONTRACT_ID+' | revision 3.0.2-A1 | Approved integration. Shared A input block is retained unchanged as historical evidence.\n\n'+guide
guide+='\n\nD3 EARLY SEED RULE: style.seed must be an integer from 0 to 2147483647. Invalid values reject at $.style.seed with exactly: '+SEED_ERROR+'. This supersedes the historical signed-64-bit parse-only behavior.\n'
guide+='\nMODE HOUSE RULES (informational, never import rejection):\n'+modes+'\n'
guide+='\nThe classifier checks MAX, RICH, then STANDARD; no boundaries means NONE. Consecutive means adjacent boundaries. Story relevance and identifying fast beats need human/author review. It reports measurable violations and never changes effects.\n'
guide+='\nCOPY ERRORS FORMAT:\n'+COPY_HEADER+'\n'+COPY_COLUMNS+'\nOne diagnostic per line; escape embedded line breaks/pipes. SKIP and WARN do not reject. The original parser and timeline creation remain the final acceptance oracle.\n'
guide+='\nUTILIZATION LINE:\n'+c['utilization_line_format']+'\n'
guide+='\nMOTION ALIASES:\n'
for k,v in evidence['motions'].items():guide+=k+': resolves to '+v['resolved']+'; zoom '+str(v['path'][0])+' to '+str(v['path'][1])+'. '+('No real depth. Prefer SLOW_PUSH_IN; omission of this alias is a HOUSE RULE.' if k=='SUBTLE_PARALLAX' else 'Accepted alias; prefer the resolved name for clear authoring.')+'\n'
for label,key in [('MOTION CONFIG','motion_config_semantics'),('TRANSITION CONFIG','transition_config_semantics')]:
 guide+='\n'+label+':\n'
 for k,v in c[key].items():guide+=k+': '+(json.dumps(v,separators=(',',':')) if isinstance(v,dict) else v)+'\n'
guide+='\nSTYLE PRESETS:\n'+c['style_notes']+'\n'
for k,v in c['style_descriptions'].items():guide+=k+': '+v['description']+'\n'
guide+='\nLOOKS:\n'+c['look_notes']+'\n'
for k,v in c['look_descriptions'].items():guide+=k+': '+v['description']+'\n'
guide+='\nCREATOR CAPTION CHARACTER:\n'
for k,v in creator.items():guide+=k+': '+v+'\n'
guide+='\nSFX BUILT-IN FALLBACKS (suggested uses are HOUSE RULES):\n'
for k,v in sounds.items():guide+=k+': '+str(v[0])+' seconds. '+v[1]+'\n'
guide+='\nHINDI FIT GUIDANCE: '+evidence['caption_fit']['method']+' These are conservative measured standalone-letter counts, not a universal character maximum. Use Poppins, measure actual text and inspect the export. Other presets have different nominal sizes.\n'
for row in evidence['caption_fit']['rows']:guide+=f"{row['ratio']}, Hormozi/Poppins ExtraBold, size {row['size_percent']}: {row['conservative_standalone_letter_count']} widest-test standalone letters per nominal line before auto-shrink.\n"
guide+='\nD4/D5 WARNINGS: '+RTL_WARNING+'. Missing native glyphs produce a font-specific warning and recommendation. Fallback may display characters; it does not certify layout. No rendering changes are made.\n'
guide=guide.replace('>=','at least ').replace('<=','at most ').replace('≥','at least ').replace('≤','at most ').replace('<','less than ').replace('>','greater than ')
assert '<' not in guide and '>' not in guide
(ROOT/'ATS_JSON_AUTHORING_GUIDE.md').write_text(guide,encoding='utf-8')
errors=['# Candidate error catalogue\n\nContract '+CONTRACT_ID+'. Exact observed messages; dynamic completeness remains UNKNOWN.\n']
seen=set()
for case in catalog['cases']:
 msg=case.get('message') or '\n'.join(case.get('notices',[]))
 if msg and msg not in seen:
  seen.add(msg);errors.append('## '+case['name']+'\n\nPath: '+str(case.get('app_paths',case.get('path_under_test','UNKNOWN')))+'\n\n```text\n'+msg+'\n```\n')
for warn in c['new_warnings']:errors.append('## '+warn['rule']+'\n\n'+warn['path']+' | WARN\n\n'+warn['message']+'\n')
(ROOT/'ERROR_CATALOGUE.md').write_text('\n'.join(errors),encoding='utf-8')
(ROOT/'CHANGELOG.md').write_text('# Contract B integration\n\n'+changelog+'\n\nThe shared A input text has not been edited. Supply the B contract files and CODEX_TO_CHATGPT_SYNC.md to the master-prompt chat, then adopt the same B ID there. Cross-chat adoption is not claimed until acknowledged by that chat.\n',encoding='utf-8')
print('Generated candidate contract, guide and catalogue',CONTRACT_ID)
