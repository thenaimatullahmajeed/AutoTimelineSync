# Auto Timeline Sync by Naimat — 3.0.2-A1 Android

Contract: ATS_SYNC_2026-10-B. Input schema: ATS_PACKAGE_V2 only.

## Install/update

1. Copy AutoTimelineSync-3.0.2-A1-ANDROID.apk to your phone.
2. Open it from Files and allow installation from that app if Android asks.
3. Install it over the earlier ATS APK. The same signing key is retained; uninstalling is not required. Keep your source audio/images available when reopening projects.

Minimum Android 8.0 (API 26). Offline: no account, cloud key, Python or separate FFmpeg installation is required. The verification APK is for development and is not included as an app to install.

## Main Master Prompt V5.2.5

Open the three-dot menu, select Main Master Prompt V5.2.5, then tap Copy. This copies the complete original attached prompt, including all sections. The small dialog shows its character count instead of laying out a very long document. Prompt content was not rewritten. Clipboard equality was tested against the bundled text. Very long clipboard contents use Android's redacted system preview flag; the pasted text remains complete. See [Android clipboard documentation](https://developer.android.com/develop/ui/views/touch-and-input/copy-paste).

## New functionality

- Validate all on the JSON row and in the menu; independent known field errors are collected, with the real parser as the import oracle.
- Copy errors for ChatGPT uses the shared path | rule | value | expected | severity format.
- Utilization report and Copy utilization; actual native transition, moment, SFX, overlay/config counts, unused features, and informational STANDARD/RICH/MAX/NONE.
- Font coverage and creator RTL warnings. Warnings do not reject packages.
- Canvas ratio override, default From script (Auto). Original JSON is retained and project overrides save/reopen correctly.
- Repaste remains available. Ctrl+I opens import on an attached keyboard.
- Actual numbered-image thumbnails on the timeline, loaded in a bounded background cache.
- Preview rendering is off the UI thread, with frame reuse and a physical-pixel Full HD width cap for fullscreen.
- Reused encoder texture storage, coordinate buffers and shader locations. Rendering speed still depends on the phone, codec, resolution and effects.
- Native SFX now rejects cues closer than 350 ms, including simultaneous scene/transition cues. Invalid seed and integer fields are rejected at their JSON paths. Non-cut minimum/default frame handling matches the shared contract rules.

## Existing functionality retained

Audio + numbered images + V2 JSON, optional looping/ducking music, ten canonical motions and four mapped aliases, 27 transition names, nine caption presets plus Off, date/circle moments, seven overlays, 13 looks, camera configs, local audio mastering, ending fade, project save/reopen and H.264 + AAC MP4 export.

## Limits

This is a native Android renderer, not a pixel-identical Windows renderer. Related named transitions can share native effect families. Native director choices for omitted effects can differ; the master prompt authors explicit effects. Android LOUDNORM uses K-weighted gated loudness and a sample-peak ceiling; oversampled true-peak parity with FFmpeg is not certified. RTL layout remains uncertified. Use Bottom captions with centered date cards; automatic collision avoidance was not added. Physical-phone speed and 4K/60 capability were not measured here.

See VERIFICATION_REPORT.md and RELEASE_RESULTS.json for exact evidence.
