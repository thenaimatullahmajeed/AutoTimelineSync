import sys,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bootstrap import ROOT
result=json.loads((ROOT/'Evidence/Acceptance/result.json').read_text(encoding='utf-8'))
cap=json.loads((ROOT/'ATS_CAPABILITIES.json').read_text(encoding='utf-8'))
suite=ET.parse(ROOT/'Evidence/pytest-results.xml').getroot().find('testsuite').attrib
baseline=ET.parse(ROOT/'Evidence/pytest-baseline.xml').getroot().find('testsuite').attrib
assert int(suite['errors'])==int(suite['failures'])==0
assert int(baseline['errors'])==int(baseline['failures'])==0
text=(ROOT/'Inputs/FINAL_RICH_03_ATS_PACKAGE_V2.json').read_text(encoding='utf-8')
diag=json.loads((ROOT/'Evidence/Acceptance/all-errors.json').read_text(encoding='utf-8'))
assert not any(e['severity'] in ['ERROR','SKIP'] for e in diag['diagnostics'])
source=Path(json.loads((ROOT/'Evidence/acceptance-input.json').read_text(encoding='utf-8'))['selected'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==result['json_sha256']
fit=json.loads((ROOT/'Evidence/Acceptance/caption-fit.json').read_text(encoding='utf-8'))
assert fit['all_fit'] and fit['caption_count']==65
shared=json.loads((ROOT/'Evidence/shared-contract-identity.json').read_text())
assert shared['shared_sections_1_to_8_identical']
def write(name,value):(ROOT/name).write_text(value,encoding='utf-8')
rows=[
 ('C0: three supplied inputs read and final package identified','PASS','Inputs; Evidence/acceptance-input.json; final JSON SHA-256 '+result['json_sha256']),
 ('Shared contract A identical on both supplied sides','PASS','Evidence/shared-contract-identity.json'),
 ('C0: contradictions disclosed','PASS','SYNC_ISSUES.md; cut config / Off animation / PHOTO_NOTE order tested'),
 ('C1: candidate capabilities and flat guide','PASS','ATS_CAPABILITIES.json; ATS_JSON_AUTHORING_GUIDE.md; test_contract_enums_and_current_seed_are_in_sync'),
 ('C1: fancy/subtle sets match real director','PASS','tools/generate_contract.py asserts set equality; 20 fancy, seven subtle'),
 ('C1: motion/config/style/look/SFX/caption descriptions','PASS','ATS_CAPABILITIES.json semantics sections; Evidence/semantics.json'),
 ('C1: measured Hindi fit table','PASS','CAPTION_FIT.md; advisory calibration, not a universal character limit'),
 ('C2: zero ERROR and unexpected SKIP','PASS','Evidence/Acceptance/all-errors.json; copy-errors.txt; test_final_rich_preflight_has_no_spurious_cue_plan_error'),
 ('C2: RICH, 22 non-cut of 33, eight fancy, three dates, six cues','PASS','Evidence/Acceptance/utilization.json; test_final_rich_actual_import_matches_expected_utilization'),
 ('C2: real audio used, 34 placeholders, actual import/export','PASS','Evidence/audio-location.json; Evidence/Acceptance/project.ats3; RICH-Hindi-Acceptance.mp4 and report'),
 ('C2: all 65 Poppins size-120 Center captions fit canvas','PASS','Evidence/Acceptance/caption-fit.json; all nine requested scene frames viewed'),
 ('C2: date cards remain visually clear','FAIL','Viewed frames/date-1840.png, date-1879.png, date-1930.png: centered captions overlap all three cards. Renderer fix not authorized by D6.'),
 ('C2: date-card Bottom authoring comparison','PASS','Evidence/Acceptance/workaround-bottom-date-1879.png viewed; no original JSON or renderer edited'),
 ('C2: transitions and ending fade visible','PASS','All nine extracted transition frames viewed; ending-before.png and ending-final.png; final image mean '+str(round(result['ending_pixel_means']['final_frame'],3))),
 ('C2: loudness mastering ran','PASS','MP4 report: LOUDNORM target -14; final AAC '+str(result['audio_stats']['after_aac']['integrated_lufs'])+' LUFS; peak '+str(result['audio_stats']['after_aac']['true_peak_dbtp'])+' dBTP'),
 ('C2: HIGH_ENERGY with all effects explicit','PASS','Evidence/Acceptance/energy-comparison.json: same resolved decisions and same five sampled pixel hashes for all three energies; seed 48127'),
 ('C3: candidate full available Windows suite plus sync regressions','PASS','Evidence/pytest-results.xml: '+suite['tests']+' tests, zero failures/errors/skips'),
 ('C3: unchanged baseline audit suite','PASS','Evidence/pytest-baseline.xml: '+baseline['tests']+' tests, zero failures/errors/skips; overlapping tests are not added as a unique total'),
 ('D1: collected errors and exact Copy button','PASS','test_caption_id_and_creator_animation_collect_together; test_actual_launch_validate_all_button_and_copy; test_existing_import_error_copy_uses_same_exchange_format'),
 ('D2: real editor report/copy after import','PASS','test_real_editor_shows_utilization_after_import; test_report_dialog_copy_buttons; viewed real-editor-utilization.png'),
 ('D3: early seed error at a real JSON path','PASS','test_seed_rejected_early_exact_path; test_seed_boundaries_accepted'),
 ('D4/D5: warning only, acceptance preserved','PASS','test_creator_rtl_warn_only; test_script_font_warning; 16 existing fixtures accepted by real ImportWorker'),
 ('D6: budgets remain unenforced and rendering/audio unchanged','PASS','test_budgets_never_reject_or_downgrade_explicit_effects; installed EXE hash unchanged'),
 ('C4: concrete diff and proposed contract B changelog','PASS','REVIEW_DIFF.md; CODE_REVIEW.diff; CONTRACT_CHANGES.json; CHANGELOG.md'),
 ('C4: integration build installed','FAIL','Held for your required approval of D1-D5 diff. No installed app or original core file replaced.'),
 ('C5: future sync exchange contract documented','PASS','CODEX_TO_CHATGPT_SYNC.md; the shared A block remains unchanged; B adoption follows integration approval')]
report='# SYNC CHECKLIST — Windows 3.0.2-A1 review candidate\n\nCONTRACT LOADED: ATS_SYNC_2026-10-A\n\nCandidate contract: ATS_SYNC_2026-10-B, proposed for both chats after approval. Shared A instructions are preserved verbatim. The original installed app remains unchanged.\n\n'
report+='| Item | PASS or FAIL | Evidence (file and test) |\n|---|---|---|\n'
report+='\n'.join('| '+' | '.join(row)+' |' for row in rows)+'\n'
report+='\n## Exact validator exchange\n\n```text\n'+(ROOT/'Evidence/Acceptance/copy-errors.txt').read_text(encoding='utf-8')+'\n```\n'
report+='\n## Exact utilization line\n\n'+result['utilization']['utilization_line']+'\n'
report+='\n## Export and review limits\n\nFull HD 1080 × 1920, 30 fps, 3,133 frames. Actual uploaded Hindi narration, not substitute audio. Total export call took '+str(result['render_seconds'])+' seconds, approximately 10 minutes 15 seconds. This measures the existing CPU renderer; no render-speed change was approved or made.\n\n'
report+='The nine requested steady frames, nine transition frames, three date-card frames and both ending frames were viewed. Hindi was readable and stayed within the canvas. The cards rendered the correct numbers but overlap the centered captions. This visual defect is not hidden behind the successful import/export result. Bottom caption positioning avoids the observed overlap without a renderer change; only a comparison frame was generated, preserving the supplied Center package.\n\n'
report+='Export warnings:\n\n'+''.join('- '+warning+'\n' for warning in result['export_warnings'])
report+='\nDUPLICATE_IMAGE is expected for these deliberately similar grid placeholders. FAST_CAPTION identifies caption 008; it is an existing advisory, not an import error. The every-spoken-year house rule also differs from the supplied sample, which omits a card for the aligned 1895 mention. Source JSON was retained unchanged.\n\n'
report+='Universal RTL rendering, GPU/Android behavior and complete dynamic error-template coverage remain UNKNOWN. The available recovered Windows suite and new tests were run; a missing historical full repository suite is not claimed. The review candidate depends on the verified local core/runtime and is not a newly installed portable release.\n'
write('SYNC_CHECKLIST.md',report)
handoff='''CONTRACT LOADED: ATS_SYNC_2026-10-A

Codex completed the 3.0.2-A1 source review candidate. Proposed next contract is ATS_SYNC_2026-10-B because the approved seed rule changes acceptance and diagnostics/utilization were added. Do not claim B is installed yet: C4 integration-build approval is pending. The shared A block was not edited, and its supplied two copies match byte-for-byte after normal newline decoding.

Read ATS_CAPABILITIES.json, ATS_JSON_AUTHORING_GUIDE.md, ERROR_CATALOGUE.md, SYNC_ISSUES.md and CHANGELOG.md. Mirror B in Section 00A only after the user confirms integration, then acknowledge the same ID in both chats. Use ATS_PACKAGE_V2 only; mode classification is utilization metadata, not a new JSON field.

Verified final RICH file was autodownload/files/03_ATS_PACKAGE_V2.json, not the older root-level names. It imported and exported unchanged with the actual 104.437551-second Hindi audio. Zero ERROR and zero SKIP. RICH result: 22 non-cut of 33, eight fancy, three date cards, six sound cues, zero overlays. All 65 Poppins size-120 Center captions fit the Full HD canvas. With all effects explicit, the three energies gave identical effect decisions and sampled pixels.

Important visual SYNC ISSUE: centered captions overlap the centered 1840, 1879 and 1930 DATE_CARDs. The 1879 card is heavily obscured. Existing Bottom caption positioning avoids that observed collision, as demonstrated by a new comparison frame. The supplied JSON and renderer were not altered. A future renderer collision-avoidance feature needs separate approval. Update authoring guidance with this limitation; do not claim collision detection exists.

The supplied sample also contains an aligned 1895 mention without a date card, despite the every-spoken-year HOUSE RULE. Report it as an authoring discrepancy, not a tool rejection. The export emitted an existing FAST_CAPTION warning for cue 008 and an expected duplicate-image warning for placeholders.

New tool candidate behaviors: collected diagnostics with original parser/import as final oracle; exact Copy errors format; actual import utilization and copy button; early $.style.seed rejection with "must be an integer between 0 and 2147483647"; WARN-only creator RTL and missing-native-script-glyph notices. No enum, JSON shape, renderer/audio, or creative budget acceptance changes. Never promise certified Arabic/Urdu layout, Android or GPU results.

Apply every correction in SYNC_ISSUES.md: cut frames accepted-but-ignored, Off animation accepted, PHOTO_NOTE perimeter either orientation, DATE_CARD versus CIRCLE containment distinction, Python-round transition defaults/no explicit 0.55-second cap, documented motion aliases, advisory fit limits, classifier precedence/adjacency interpretation, and seed message update after installation.
'''
write('CODEX_TO_CHATGPT_SYNC.md',handoff)
write('README.md','''# ATS sync review package — 3.0.2-A1

Start with SYNC_CHECKLIST.md and REVIEW_DIFF.md. CODE_REVIEW.diff contains the exact additive source. Capabilities, flat guide, error catalogue, semantics, caption-fit table and master-chat handoff are included.

RUN_CANDIDATE.cmd opens the review UI on this machine using its existing verified core and Python runtime. It does not install or replace the app. It is a source review launcher, not a standalone portable release. Build/install is held for the approval required in C4.

Evidence/Acceptance contains the actual test MP4, 34 placeholder images, original-input project, export report, extracted frames, all-errors text, utilization, caption geometry and energy comparisons. These placeholders test the engine, not final story artwork. The matched actual narration remains at the original Downloads path; it was not regenerated.

Tests and executable probe tools are included. The full available candidate Windows suite had 83 passing tests. An independent unchanged-baseline run had 88 passing tests. These runs overlap; they are not summed as unique tests. The original historical full suite was not available.

The installed app/core remains unchanged. Candidate B is proposed, not silently adopted on the other chat. All original shared A text and supplied master/patch/input JSON bytes are preserved in Inputs. See SYNC_ISSUES.md for every known disagreement and the existing Center/date-card visual collision.
''')
print('FINAL CHECKLIST',suite['tests'],'candidate tests;',baseline['tests'],'baseline tests;',len(rows),'checks')
