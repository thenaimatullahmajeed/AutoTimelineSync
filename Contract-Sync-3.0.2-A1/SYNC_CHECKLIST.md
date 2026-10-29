# SYNC CHECKLIST — Windows 3.0.2-A1 final portable integration

CONTRACT LOADED: ATS_SYNC_2026-10-B

Current portable contract: ATS_SYNC_2026-10-B. C4 integration approved by the user. Shared A inputs are preserved verbatim; the older installed app remains unchanged. The separate master-prompt chat must adopt B using the included handoff.

| Item | PASS or FAIL | Evidence (file and test) |
|---|---|---|
| C0: three supplied inputs read and final package identified | PASS | Inputs; Evidence/acceptance-input.json; final JSON SHA-256 51d7f349854df695d535debde8cff62e9ab69af20f91d63ba04673674e9b8633 |
| Shared contract A identical on both supplied sides | PASS | Evidence/shared-contract-identity.json |
| C0: contradictions disclosed | PASS | SYNC_ISSUES.md; cut config / Off animation / PHOTO_NOTE order tested |
| C1: candidate capabilities and flat guide | PASS | ATS_CAPABILITIES.json; ATS_JSON_AUTHORING_GUIDE.md; test_contract_enums_and_current_seed_are_in_sync |
| C1: fancy/subtle sets match real director | PASS | tools/generate_contract.py asserts set equality; 20 fancy, seven subtle |
| C1: motion/config/style/look/SFX/caption descriptions | PASS | ATS_CAPABILITIES.json semantics sections; Evidence/semantics.json |
| C1: measured Hindi fit table | PASS | CAPTION_FIT.md; advisory calibration, not a universal character limit |
| C2: zero ERROR and unexpected SKIP | PASS | Evidence/Acceptance/all-errors.json; copy-errors.txt; test_final_rich_preflight_has_no_spurious_cue_plan_error |
| C2: RICH, 22 non-cut of 33, eight fancy, three dates, six cues | PASS | Evidence/Acceptance/utilization.json; test_final_rich_actual_import_matches_expected_utilization |
| C2: real audio used, 34 placeholders, actual import/export | PASS | Evidence/audio-location.json; Evidence/Acceptance/project.ats3; RICH-Hindi-Acceptance.mp4 and report |
| C2: all 65 Poppins size-120 Center captions fit canvas | PASS | Evidence/Acceptance/caption-fit.json; all nine requested scene frames viewed |
| C2: date cards remain visually clear | FAIL | Viewed frames/date-1840.png, date-1879.png, date-1930.png: centered captions overlap all three cards. Renderer fix not authorized by D6. |
| C2: date-card Bottom authoring comparison | PASS | Evidence/Acceptance/workaround-bottom-date-1879.png viewed; no original JSON or renderer edited |
| C2: transitions and ending fade visible | PASS | All nine extracted transition frames viewed; ending-before.png and ending-final.png; final image mean 5.321 |
| C2: loudness mastering ran | PASS | MP4 report: LOUDNORM target -14; final AAC -14.7 LUFS; peak -4.5 dBTP |
| C2: HIGH_ENERGY with all effects explicit | PASS | Evidence/Acceptance/energy-comparison.json: same resolved decisions and same five sampled pixel hashes for all three energies; seed 48127 |
| C3: candidate full available Windows suite plus sync regressions | PASS | Evidence/pytest-results.xml: 83 tests, zero failures/errors/skips |
| C3: unchanged baseline audit suite | PASS | Evidence/pytest-baseline.xml: 88 tests, zero failures/errors/skips; overlapping tests are not added as a unique total |
| D1: collected errors and exact Copy button | PASS | test_caption_id_and_creator_animation_collect_together; test_actual_launch_validate_all_button_and_copy; test_existing_import_error_copy_uses_same_exchange_format |
| D2: real editor report/copy after import | PASS | test_real_editor_shows_utilization_after_import; test_report_dialog_copy_buttons; viewed real-editor-utilization.png |
| D3: early seed error at a real JSON path | PASS | test_seed_rejected_early_exact_path; test_seed_boundaries_accepted |
| D4/D5: warning only, acceptance preserved | PASS | test_creator_rtl_warn_only; test_script_font_warning; 16 existing fixtures accepted by real ImportWorker |
| D6: budgets remain unenforced and rendering/audio unchanged | PASS | test_budgets_never_reject_or_downgrade_explicit_effects; installed EXE hash unchanged |
| C4: concrete diff and proposed contract B changelog | PASS | REVIEW_DIFF.md; CODE_REVIEW.diff; CONTRACT_CHANGES.json; CHANGELOG.md |
| C4: integration portable build | PASS | User approved; packaged-sync/sync-check.json and packaged-smoke/portable-smoke.json passed on the new EXE. Old installed app retained. |
| C5: future sync exchange contract documented | PASS | CODEX_TO_CHATGPT_SYNC.md; the shared A block remains unchanged; B is active in the new portable app; master-chat acknowledgement remains external |

## Exact validator exchange

```text
ATS_PACKAGE_V2 correction request. Fix only the paths below and return one complete corrected JSON object. Preserve all other fields.
path | rule | value | expected | severity
```

## Exact utilization line

Mode RICH: 22 non-cut of 33, 8 fancy, 3 date cards, 6 sound cues, 0 overlays, features unused: overlays, CIRCLE, PHOTO_NOTE, motion_config, look_override, style, music.

## Export and review limits

Full HD 1080 × 1920, 30 fps, 3,133 frames. Actual uploaded Hindi narration, not substitute audio. Total export call took 614.985 seconds, approximately 10 minutes 15 seconds. This measures the existing CPU renderer; no render-speed change was approved or made.

The nine requested steady frames, nine transition frames, three date-card frames and both ending frames were viewed. Hindi was readable and stayed within the canvas. The cards rendered the correct numbers but overlap the centered captions. This visual defect is not hidden behind the successful import/export result. Bottom caption positioning avoids the observed overlap without a renderer change; only a comparison frame was generated, preserving the supplied Center package.

Export warnings:

- DUPLICATE_IMAGE: 33 consecutive scene pair(s) look alike; first scene 002.
- FAST_CAPTION: 1 caption(s) exceed 20 characters/s; first 008.

DUPLICATE_IMAGE is expected for these deliberately similar grid placeholders. FAST_CAPTION identifies caption 008; it is an existing advisory, not an import error. The every-spoken-year house rule also differs from the supplied sample, which omits a card for the aligned 1895 mention. Source JSON was retained unchanged.

Universal RTL rendering, GPU/Android behavior and complete dynamic error-template coverage remain UNKNOWN. The available recovered Windows suite and new tests were run; a missing historical full repository suite is not claimed. The new portable app includes its Python, Qt, fonts and FFmpeg runtime. It does not need the source checkout or the local development Python.

## Final packaged checks

| Check | Result | Evidence |
|---|---|---|
| Final available source suite rerun | PASS: 83 tests, zero failures/errors | Evidence/pytest-results-final.xml |
| Bundled exact RICH import | PASS: 22 non-cuts, 8 fancy, 6 cues | Evidence/packaged-sync/sync-check.json |
| Bundled seed rejection and three-error collection | PASS | Evidence/packaged-sync/copy-errors.txt |
| Bundled Qt import and MP4 export | PASS: version 3.0.2-A1 | Evidence/packaged-smoke/portable-smoke.json |
| Packaged editor screenshot | VIEWED | Evidence/packaged-smoke/portable-ui.png |
| Bottom JSON | PASS parser; only position changed | Evidence/bottom-json-validation.json |

The packaged screenshot was visually inspected before delivery. The smoke export is an eight-second synthetic clip; the earlier full Hindi acceptance export used the original audio and exact original JSON. The corrected Bottom JSON was not rendered as a second full MP4.
