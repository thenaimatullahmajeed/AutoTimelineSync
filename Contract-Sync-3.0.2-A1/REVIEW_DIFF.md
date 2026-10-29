# D1–D5 integration review

Contract B / deliverable 3.0.2-A1. **Integration approved and packaged checks passed.** The earlier review archive retains its original pending-approval snapshot. The original renderer, audio implementation, enum lists and schema shape are unchanged. D3 is the sole approved acceptance-boundary change.

| Decision | Before | Candidate after | Code | Evidence |
|---|---|---|---|---|
| D1 | First parser/import error, old freeform Copy text | Validate all on the real import row; independent errors collected, original import is final oracle; exact Copy header/columns | sync_diagnostics.py; sync_ui.py | test_caption_id_and_creator_animation_collect_together; test_actual_launch_validate_all_button_and_copy; test_exact_copy_format |
| D2 | No mode/utilization report on import | Actual applied transition/cue counts, informational STANDARD/RICH/MAX/NONE classification, automatic editor report and copy button | sync_modes.py; sync_ui.py | test_mode_integer_thresholds; test_final_rich_actual_import_matches_expected_utilization; test_real_editor_shows_utilization_after_import |
| D3 | Signed 64-bit parser range, followed by settings rejection without JSON path | Reject only invalid style.seed earlier at $.style.seed with must be an integer between 0 and 2147483647 | sync_core.py | test_seed_rejected_early_exact_path; test_seed_boundaries_accepted |
| D4 | No creator RTL warning | WARN with the exact requested sentence for Arabic/Hebrew text; accepted data and pixels unchanged | sync_diagnostics.py:font_warnings | test_creator_rtl_warn_only; test_generic_rtl_no_creator_warning |
| D5 | No native script-font warning | WARN naming chosen font and suggested Hindi/Arabic/Urdu font when native glyphs are missing; fallback acknowledged | sync_diagnostics.py:font_warnings | test_script_font_warning; test_native_hindi_poppins_no_script_warning |

The review candidate loads the original verified core and applies the new modules in memory. It can be launched using launch_candidate.py, without replacing any installed file. The code-only diff contains the exact additive modules and bootstrap. Contract A text is retained verbatim in Inputs; proposed cross-chat corrections are in SYNC_ISSUES.md.
