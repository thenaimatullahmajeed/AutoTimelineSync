# Android 3.0.2-A1 verification

Contract: ATS_SYNC_2026-10-B. Signed release APK installed on the test emulators.

| Run | API | Checks | Failures | Scope |
|---|---|---|---|---|
| API30-Sync | 30 | 23 | 0 | Latest sync/menu/clipboard regression run |
| API35 | 35 | 57 | 0 | Full native suite, including import/render/audio/MP4/service/cancel and new sync checks |
| API35-Sync | 35 | 23 | 0 | Latest sync/menu/clipboard regression run |

The runs overlap; do not add them as a unique-test total. Earlier unsuccessful UI automation attempts are retained separately in FirstAttempt. The final full run and targeted rerun are the acceptance evidence, not the earlier failing attempts.

Real checks include the canonical 12-scene MAX JSON and the exact 34-scene final RICH JSON (22 non-cuts, eight fancy, three date cards, six SFX). Hindi Poppins was rendered to a frame using demo placeholders and visually inspected; this is not a second full Hindi MP4 export. The eight-second HD MP4 uses synthetic demo images and test tones. Its audio/video tracks, dimensions, frame count/duration and decodability were checked by instrumentation and ffprobe. Cancellation, foreground completion and private-cache cleanup were tested.

Actual Android 11 screenshots and fresh Android 15 UI smoke captures of the menu, compact master-prompt dialog and timeline were visually inspected before delivery. Prompt clipboard content equals the complete bundled original, not just the on-screen preview. Diagnostic and utilization Copy buttons exercise their real dialog callbacks.

During a stressed Android 15 emulator run, a System UI ANR overlay appeared even though ATS checks passed; those screenshots did not establish clean interactive UI. The emulator was restarted, contention reduced, and the live UI rechecked. Large clipboard previews are now redacted using the official Android flag, with exact full-content copy tested again. This is a mitigation, not proof of what caused that platform ANR. The full 57-check run preceded this small clipboard-only change; the final Android 15 sync/clipboard rerun verifies the delivered change.

No physical phone, every manufacturer's document picker, universal RTL, Windows pixel parity or 4K/60 performance is claimed. The original audio/image workflow and native platform limitations are described in README.md.
