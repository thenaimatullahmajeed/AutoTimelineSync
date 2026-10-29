# Auto Timeline Sync by Naimat — Windows 3.0.2

## Fixes

| Reported issue | Change | Verification |
|---|---|---|
| Canvas format cannot be changed | New import dropdown: From script (default), 9:16, 16:9, 1:1, 4:5. Uses the existing project orientation override and survives save/reopen. | All four ratios rendered and reopened in regression tests. Original JSON text is preserved. |
| Paste disappears after importing | Script row always exposes Paste/Repaste, including after invalid input. | Valid and invalid input states tested. |
| Empty image boxes in timeline | Actual source thumbnails load in a background worker and repeat within each clip, preserving image aspect. | All 34 images in the real project loaded; screenshot viewed. |
| Blurry preview | Preview renders at physical display pixels using device pixel ratio; smooth image sampling enabled. Fullscreen preview remains available with F11. | At 150% scale, 192×350 logical preview rendered at 288×525 pixels; screenshot viewed. |
| Import shortcut | Ctrl+I opens Import; Ctrl+N remains an alias. | Actual Qt keyboard shortcut dispatch tested. |
| Export stops near completion with -70 LUFS | LIMIT_ONLY now checks peaks, without imposing a LUFS target. Intentional silence exports with a notice. LOUDNORM rejects silence before video rendering. | Silent LIMIT_ONLY succeeds; silent LOUDNORM fails before rendering; audible LOUDNORM target verified. |
| Slow rendering | Balanced frame groups use available workers even for a small scene count. Fast uses automatic hardware selection with CPU fallback. Audio is encoded before video, and final mux copies both encoded tracks. Progress includes encoded frames/FPS, elapsed time and stage details. Stalled encoders are stopped instead of waiting indefinitely. | Same-input benchmark, full real Full HD project, packaged smoke and cancellation tests. |

## Actual results

| Test | Result |
|---|---|
| Focused regression suite | **13 passed**. Includes format persistence, repaste, Ctrl+I, thumbnail loading, preview pixel dimensions, obsolete schemas, loudness, silence and cancellation/cleanup. |
| Source import/export smoke | PASS; 8 seconds, 720×1280, 30 FPS, 240 frames, H.264/AAC. |
| Rebuilt executable import/export smoke | PASS; version 3.0.2; 13.984 seconds for the fixture. |
| Same eight-second CPU fixture | Installed 3.0.1 code: **35.578 s**; updated export: **17.406 s** (about 2× faster in this test). Both use native 720×1280 and the same input/frame data. Fast now uses a faster compression preset; the test output grew from 480 KB to 795 KB. |
| Real Hindi project | 34 images, 65 captions, 104.437551-second source audio. Full HD 1080×1920, 30 FPS, 3,133 video frames completed in **127.297 s** using h264_amf. Finalization progressed from 91% through verification to 100%. |
| Visual inspection | Real launch/editor/export screenshots, 34 timeline thumbnails and 150% scaling inspected. Packaged UI screenshot inspected before delivery. |

These timings are measured on this PC, not a guarantee for every video/device. Graphics, source images, effects, resolution and CPU/GPU affect speed. Fast trades compression efficiency for speed and can create a larger final MP4. It does not secretly lower the selected resolution.

The old log had `voice_volume: 0` and no music. Muted audio naturally measures near -70 LUFS. This release preserves intentional mute, identifies it in the export panel/report and removes the false LIMIT_ONLY loudness failure. It does not turn voice back on without your choice.

## Compatibility and recovery

ATS_PACKAGE_V2 and project_format 2 remain the input contracts. Canvas changes are local project overrides. The scene/spec/compositor/director remain the installed 3.0.1 implementation; image IDs, word timings, caption presets and effects are not replaced with a new engine.

The original `E:/AI/ATS-3.0-SOURCE` folder was unavailable. The installed 3.0.1 executable provided a 35-module baseline. Twenty-one original source modules were recovered from this project's own edit history and verified against the installed bytecode; fourteen modules remain recovered Python 3.12 bytecode. New fixes and export orchestration are readable source. This is a rebuildable recovered project, **not a claim that all original source was recovered**. Restore the original source backup when available for complete engine-source maintenance.

The original 117-test source suite was unavailable and was **not** rerun. This release ran the 13 focused tests, source and packaged smoke tests, the benchmark and the full real project described above. No 4K/60 FPS, exhaustive RTL certification or every GPU was tested.

## Evidence

`Verification/` contains regression results, smoke JSON, screenshots and performance reports. The full real test video is delivered separately in the release folder. Temporary export work folders are removed after success/failure/cancellation; final mux cache sampling includes its temporary MP4. The real-project timing was recorded before the last addition to cache-peak sampling; do not treat its earlier peak-cache figure as a full mux peak.
