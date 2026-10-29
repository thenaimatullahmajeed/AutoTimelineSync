# Android 3.0.2-A1 decisions

- Work is isolated in ats_android_3_0_2_A1; original Android 3.0.1 and Windows releases are retained.
- User authorized the latest mobile functionality and the V5.2.5 menu/copy feature. Schema stays ATS_PACKAGE_V2, shared contract ID B; no licensing, Voice Studio, Remotion or cutout pipeline is added.
- Preserve the attached master prompt byte-for-byte. Menu uses a compact Copy dialog to avoid laying out over 100,000 characters before copying.
- Diagnostics are additive: independently check known code-derived fields, then consult the native production parser. Syntax errors must be fixed first. Exhaustive malformed-combination coverage is not claimed.
- Mode thresholds/classification are informational and never creative-budget rejection rules. Counts reflect native applied effects/cues, not a promise of Windows pixel parity.
- Deliberate native acceptance corrections: exact 32-bit nonnegative seed path/message; integer-field validation; native JSON serialization may canonicalize integral decimal tokens; cue spacing rejects instead of silently skipping; media duration tolerance is one output frame. Non-cut fallback minimum is four frames and default rounding follows Windows banker rounding.
- Use bundled-font cmap evidence for native-glyph warnings, acknowledging fallback; RTL warning is advisory, not a rendering fix.
- Canvas selection is a project override, preserving the supplied JSON. UI responsiveness changes use a serial preview worker, two output buffers and separate bounded thumbnails. Encoder texture/buffer reuse does not change the Canvas composition.
- UI test automation initially failed on modal focus, uppercase native labels and clipboard read privacy. Recheck actual menu/dialog buttons and clipboard content; reading clipboard in the test driver uses a shell test permission. The release APK requests no such extra permission.
- Native renderer, font layout, procedural sound and mastering remain native implementations; do not claim byte/pixel identity or physical-phone performance.
- Private signing key remains outside source/delivery. Same certificate supports installing over the earlier APK.
