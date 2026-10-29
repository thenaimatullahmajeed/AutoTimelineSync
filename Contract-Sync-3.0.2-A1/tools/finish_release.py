"""Finalize evidence only after the built executable has passed its checks."""
import copy,json,sys,hashlib,xml.etree.ElementTree as ET,difflib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT,application,install
application();install()
from ats_studio.sync_diagnostics import validate_all
smoke=json.loads((ROOT/'Evidence/packaged-smoke/portable-smoke.json').read_text())
sync=json.loads((ROOT/'Evidence/packaged-sync/sync-check.json').read_text(encoding='utf-8'))
assert smoke['ok'] and sync['ok'] and smoke['version']==sync['version']=='3.0.2-A1'
assert '3.0.2-A1' in smoke['title']
suite=ET.parse(ROOT/'Evidence/pytest-results-final.xml').getroot().find('testsuite').attrib
assert suite['failures']==suite['errors']=='0'
original=json.loads((ROOT/'Inputs/FINAL_RICH_03_ATS_PACKAGE_V2.json').read_text(encoding='utf-8'))
bottom=copy.deepcopy(original);bottom['caption_style']['position']='Bottom'
restored=copy.deepcopy(bottom);restored['caption_style']['position']='Center';assert restored==original
text=json.dumps(bottom,ensure_ascii=False,indent=2)
report=validate_all(text)
assert report['valid'] and not any(x['severity'] in ['ERROR','SKIP'] for x in report['diagnostics'])
(ROOT/'03_ATS_PACKAGE_V2_BOTTOM.json').write_text(text,encoding='utf-8')
(ROOT/'Evidence/bottom-json-validation.json').write_text(json.dumps({'changed_paths':['$.caption_style.position'],'before':'Center','after':'Bottom','report':report,'full_alternative_mp4_rendered':False,'viewed_comparison_frame':'Acceptance/workaround-bottom-date-1879.png'},ensure_ascii=False,indent=2),encoding='utf-8')
def read(name):return (ROOT/name).read_text(encoding='utf-8')
def write(name,text):(ROOT/name).write_text(text,encoding='utf-8')
decisions=read('DECISIONS.md')
approval='''
## Integration approval and release

On 2026-10-13 the user replied "jo better h wahi kro" to the C4 D1–D5 integration-build approval question. Decision: build the tested additive integration as a separate 3.0.2-A1 portable app. Keep the old delivered EXE and the verified core untouched. Original C4 hold above describes the earlier review stage and is now satisfied.

Contract ATS_SYNC_2026-10-B applies to this new build. The historical A input is unchanged. Adoption by the separate ChatGPT master-prompt chat remains external and must be acknowledged there.

Existing Center/date-card collision is disclosed. Supply a separate JSON changing only caption_style.position to Bottom, using an existing supported setting. No new renderer behavior, automatic collision avoidance, creative budgets, or audio processing is introduced. The alternative was parser-validated and its 1879 comparison frame viewed; a second full 104-second MP4 was not rendered.

Frozen packaging resolves contract/resources relative to the EXE instead of the source checkout. Main-window version title is 3.0.2-A1. These are release packaging changes, not engine changes. Packaged --sync-check and --smoke-test exercise the bundled importer, diagnostics and export.
'''
if '## Integration approval and release' not in decisions:write('DECISIONS.md',decisions+approval)
check=read('SYNC_CHECKLIST.md').replace('Windows 3.0.2-A1 review candidate','Windows 3.0.2-A1 final portable integration').replace('CONTRACT LOADED: ATS_SYNC_2026-10-A','CONTRACT LOADED: ATS_SYNC_2026-10-B')
check=check.replace('Candidate contract: ATS_SYNC_2026-10-B, proposed for both chats after approval. Shared A instructions are preserved verbatim. The original installed app remains unchanged.','Current portable contract: ATS_SYNC_2026-10-B. C4 integration approved by the user. Shared A inputs are preserved verbatim; the older installed app remains unchanged. The separate master-prompt chat must adopt B using the included handoff.')
check=check.replace('| C4: integration build installed | FAIL | Held for your required approval of D1-D5 diff. No installed app or original core file replaced. |','| C4: integration portable build | PASS | User approved; packaged-sync/sync-check.json and packaged-smoke/portable-smoke.json passed on the new EXE. Old installed app retained. |')
check=check.replace('B adoption follows integration approval','B is active in the new portable app; master-chat acknowledgement remains external')
check=check.replace('The review candidate depends on the verified local core/runtime and is not a newly installed portable release.','The new portable app includes its Python, Qt, fonts and FFmpeg runtime. It does not need the source checkout or the local development Python.')
check+='\n## Final packaged checks\n\n| Check | Result | Evidence |\n|---|---|---|\n| Final available source suite rerun | PASS: '+suite['tests']+' tests, zero failures/errors | Evidence/pytest-results-final.xml |\n| Bundled exact RICH import | PASS: 22 non-cuts, 8 fancy, 6 cues | Evidence/packaged-sync/sync-check.json |\n| Bundled seed rejection and three-error collection | PASS | Evidence/packaged-sync/copy-errors.txt |\n| Bundled Qt import and MP4 export | PASS: version 3.0.2-A1 | Evidence/packaged-smoke/portable-smoke.json |\n| Packaged editor screenshot | VIEWED | Evidence/packaged-smoke/portable-ui.png |\n| Bottom JSON | PASS parser; only position changed | Evidence/bottom-json-validation.json |\n\nThe packaged screenshot was visually inspected before delivery. The smoke export is an eight-second synthetic clip; the earlier full Hindi acceptance export used the original audio and exact original JSON. The corrected Bottom JSON was not rendered as a second full MP4.\n'
write('SYNC_CHECKLIST.md',check)
handoff=read('CODEX_TO_CHATGPT_SYNC.md').replace('CONTRACT LOADED: ATS_SYNC_2026-10-A','CONTRACT LOADED: ATS_SYNC_2026-10-B')
handoff=handoff.replace('Codex completed the 3.0.2-A1 source review candidate. Proposed next contract is ATS_SYNC_2026-10-B because the approved seed rule changes acceptance and diagnostics/utilization were added. Do not claim B is installed yet: C4 integration-build approval is pending.','Codex completed the approved 3.0.2-A1 final portable integration and verified the built EXE with real RICH import, collected-error/seed checks, and an eight-second Qt import/export smoke test. Its active contract is ATS_SYNC_2026-10-B because the approved seed rule changes acceptance and diagnostics/utilization were added.')
handoff=handoff.replace('Mirror B in Section 00A only after the user confirms integration, then acknowledge the same ID in both chats.','The user approved integration. Mirror B in Section 00A using these current files, then acknowledge CONTRACT LOADED: ATS_SYNC_2026-10-B. Do not claim this separate chat has acknowledged it before it replies.')
handoff=handoff.replace('New tool candidate behaviors:','New tool behaviors:').replace('seed message update after installation','seed message in the new portable build')
handoff+='\nA separate 03_ATS_PACKAGE_V2_BOTTOM.json changes only $.caption_style.position from Center to Bottom. Adopt Bottom when centered DATE_CARDs are present unless an inspected composition avoids overlap. The parser check passed and the 1879 comparison frame was viewed; no full alternative MP4 is claimed. All original inputs remain unchanged.\n'
write('CODEX_TO_CHATGPT_SYNC.md',handoff)
write('README.md','''# Auto Timeline Sync 3.0.2-A1 — FINAL PORTABLE

CONTRACT LOADED: ATS_SYNC_2026-10-B

Run AutoTimelineSync/AutoTimelineSync.exe in the delivered portable folder. No login, Supabase setup or Python installation is required. Extract the entire ZIP first and keep its folders together.

This build includes the approved D1–D5 integration: Validate all, Copy errors for ChatGPT, import utilization/Copy utilization, early seed validation and warning-only font/RTL diagnostics. Original engine, renderer and audio behavior are unchanged. The old 3.0.2 app is retained separately.

Read SYNC_CHECKLIST.md for exact PASS/FAIL results and limitations. The final available source suite passed 83 tests. The independent earlier baseline suite passed 88 tests; these overlapping runs are not summed. The built EXE passed the exact RICH import/seed/multi-error check and the Qt import/export smoke test.

03_ATS_PACKAGE_V2_BOTTOM.json uses the existing Bottom setting to avoid the observed centered date-card/caption overlap. Original JSON is preserved in Inputs. A comparison frame was viewed; no second full alternative MP4 was produced.

Send CODEX_TO_CHATGPT_SYNC.md plus ATS_CAPABILITIES.json, ATS_JSON_AUTHORING_GUIDE.md and SYNC_ISSUES.md to the ChatGPT master-prompt chat. B is active in this portable app; acknowledgement in that separate chat is still needed. Shared A inputs remain untouched.

Evidence/Acceptance contains the earlier full original-Hindi acceptance MP4 and placeholders. They verify behavior, not final story artwork. Universal RTL, GPU/Android results, exhaustive dynamic error-template coverage and the unavailable original historical full test suite are not claimed.
''')
review=read('REVIEW_DIFF.md').replace('Candidate B / deliverable 3.0.2-A1. **Not installed.** C4 requires approval of this diff before the integration build.','Contract B / deliverable 3.0.2-A1. **Integration approved and packaged checks passed.** The earlier review archive retains its original pending-approval snapshot.')
write('REVIEW_DIFF.md',review)
patch=[]
for p in [ROOT/'bootstrap.py',ROOT/'launch_candidate.py',ROOT/'launch_portable.py',ROOT/'tools/build_portable.py',*sorted((ROOT/'overlay/ats_studio').glob('*.py'))]:
    patch.extend(difflib.unified_diff([],p.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+p.relative_to(ROOT).as_posix()))
write('CODE_REVIEW.diff',''.join(patch))
changes=json.loads(read('CONTRACT_CHANGES.json'));changes['contract_id'].update(current='ATS_SYNC_2026-10-B',status='Integration approved; packaged checks passed; separate master-chat acknowledgement pending')
write('CONTRACT_CHANGES.json',json.dumps(changes,ensure_ascii=False,indent=2))
issues=read('SYNC_ISSUES.md').replace('After integration approval adopt candidate B and new error in both chats','B and the new error are active in the final portable app; mirror them in the master chat').replace('No installed classifier existed. Candidate checks','The original app had no classifier. The B portable build checks')
write('SYNC_ISSUES.md',issues)
oldexe=Path('C:/Users/naima/Downloads/AutoTimelineSync-3.0.2-WINDOWS-FINAL/AutoTimelineSync/AutoTimelineSync.exe')
assert hashlib.sha256(oldexe.read_bytes()).hexdigest()=='dcd94fd3694065470336bcb2e07efaee6ceb28a426277e3a74bf7b3f35bc901b'
newexe=ROOT/'Packaging/dist/AutoTimelineSync/AutoTimelineSync.exe'
write('Evidence/release-verification.json',json.dumps({'contract':'ATS_SYNC_2026-10-B','version':'3.0.2-A1','source_tests':suite,'packaged_sync':'PASS','packaged_import_export':'PASS','old_exe_unchanged':True,'new_exe_sha256':hashlib.sha256(newexe.read_bytes()).hexdigest()},indent=2))
print('Final release evidence complete; source tests',suite['tests'])
