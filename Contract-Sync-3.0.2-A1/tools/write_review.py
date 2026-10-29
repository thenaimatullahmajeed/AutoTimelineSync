import sys,json,hashlib,difflib,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,CORE
baseline=ROOT.parent/'ats_contract_audit_3_0_2'
old=json.loads((baseline/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
new=json.loads((ROOT/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
assert old['enums']==new['enums']
def write(name,text):(ROOT/name).write_text(text,encoding='utf-8')
rows=[
 ('D1','First parser/import error, old freeform Copy text','Validate all on the real import row; independent errors collected, original import is final oracle; exact Copy header/columns','sync_diagnostics.py; sync_ui.py','test_caption_id_and_creator_animation_collect_together; test_actual_launch_validate_all_button_and_copy; test_exact_copy_format'),
 ('D2','No mode/utilization report on import','Actual applied transition/cue counts, informational STANDARD/RICH/MAX/NONE classification, automatic editor report and copy button','sync_modes.py; sync_ui.py','test_mode_integer_thresholds; test_final_rich_actual_import_matches_expected_utilization; test_real_editor_shows_utilization_after_import'),
 ('D3','Signed 64-bit parser range, followed by settings rejection without JSON path','Reject only invalid style.seed earlier at $.style.seed with must be an integer between 0 and 2147483647','sync_core.py','test_seed_rejected_early_exact_path; test_seed_boundaries_accepted'),
 ('D4','No creator RTL warning','WARN with the exact requested sentence for Arabic/Hebrew text; accepted data and pixels unchanged','sync_diagnostics.py:font_warnings','test_creator_rtl_warn_only; test_generic_rtl_no_creator_warning'),
 ('D5','No native script-font warning','WARN naming chosen font and suggested Hindi/Arabic/Urdu font when native glyphs are missing; fallback acknowledged','sync_diagnostics.py:font_warnings','test_script_font_warning; test_native_hindi_poppins_no_script_warning')]
text='# D1–D5 integration review\n\nCandidate B / deliverable 3.0.2-A1. **Not installed.** C4 requires approval of this diff before the integration build. The original renderer, audio implementation, enum lists and schema shape are unchanged. D3 is the sole approved acceptance-boundary change.\n\n'
text+='| Decision | Before | Candidate after | Code | Evidence |\n|---|---|---|---|---|\n'
text+='\n'.join('| '+' | '.join(r)+' |' for r in rows)+'\n'
text+='\nThe review candidate loads the original verified core and applies the new modules in memory. It can be launched using launch_candidate.py, without replacing any installed file. The code-only diff contains the exact additive modules and bootstrap. Contract A text is retained verbatim in Inputs; proposed cross-chat corrections are in SYNC_ISSUES.md.\n'
write('REVIEW_DIFF.md',text)
patch=[]
for p in [ROOT/'bootstrap.py',ROOT/'launch_candidate.py',*sorted((ROOT/'overlay/ats_studio').glob('*.py'))]:
    relative=str(p.relative_to(ROOT)).replace('\\','/')
    patch.extend(difflib.unified_diff([],p.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+relative))
write('CODE_REVIEW.diff',''.join(patch))
change={'contract_id':{'before':'ATS_SYNC_2026-10-A','candidate':new['contract_id'],'status':'pending integration and cross-chat adoption'},
        'schema':'ATS_PACKAGE_V2 unchanged; no fields added','enums_changed':False,'seed':{'before':old['fields']['$.style.seed'],'candidate':new['fields']['$.style.seed']},
        'warnings':new['new_warnings'],'installed_app_replaced':False}
write('CONTRACT_CHANGES.json',json.dumps(change,ensure_ascii=False,indent=2))
fit=new['caption_fit'];lines=['# Measured Hindi caption-fit guidance\n',fit['status']+'. '+fit['method']+'\n',
 'Preset: Hormozi Style. Font: Poppins ExtraBold. This is a conservative widest-letter calibration before automatic shrink, not a codepoint/grapheme hard limit. It does not certify every font/preset or composition.\n',
 '| Ratio | Test resolution | Size 100 | Size 120 | Size 140 |\n|---|---|---|---|---|']
for ratio in ['9:16','16:9','1:1','4:5']:
    rows=[x for x in fit['rows'] if x['ratio']==ratio]
    lines.append('| '+ratio+' | '+' × '.join(map(str,rows[0]['resolution']))+' | '+' | '.join(str(x['conservative_standalone_letter_count']) for x in rows)+' |')
lines.append('\nReal Hindi captions contain combining marks and different-width letters; their visible/grapheme count can differ from len(text). The renderer can shrink longer text. Final package fit is checked separately on all 65 cues and exported frames.\n')
write('CAPTION_FIT.md','\n'.join(lines))
print('Wrote review diff, change summary and fit table')
