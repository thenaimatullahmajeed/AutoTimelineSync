"""Deliver a signed APK only after the current installed APK's checks pass."""
from pathlib import Path
import json,hashlib,shutil,zipfile,subprocess
ROOT=Path(__file__).resolve().parents[1]
DELIVERY=Path.home()/'Downloads/AutoTimelineSync-ANDROID-3.0.2-A1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reports={}
for name in ['API30-Sync','API35','API35-Sync']:
    d=json.loads((ROOT/'Verification'/name/'results.json').read_text(encoding='utf-8'))
    assert d['failures']==0,(name,d['failures'])
    reports[name]=d
assert reports['API30-Sync']['count']>=23 and reports['API35']['count']>=57 and reports['API35-Sync']['count']>=23
assert json.loads((ROOT/'Verification/UI-release-smoke/result.json').read_text())['no_anr_overlay_in_smoke']
source_prompt=Path('C:/Users/naima/.codex/attachments/8ff2f95d-606f-4dba-893f-c412028de77e/Pasted text.txt')
prompt=ROOT/'assets/MAIN_MASTER_PROMPT_V5.2.5.txt'
assert sha(source_prompt)==sha(prompt)
apk=ROOT/'AutoTimelineSync-3.0.2-A1-ANDROID.apk'
with zipfile.ZipFile(apk) as z:
    assert z.read('assets/MAIN_MASTER_PROMPT_V5.2.5.txt')==prompt.read_bytes()
    assert json.loads(z.read('assets/sync-schema.json'))['contract_id']=='ATS_SYNC_2026-10-B'
for name in reports:
    clip=json.loads((ROOT/'Verification'/name/'clipboard-roundtrip.json').read_text(encoding='utf-8'))
    assert clip['match'] and clip['actual_characters']==clip['expected_characters']
readme='''# Auto Timeline Sync by Naimat — 3.0.2-A1 Android

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
'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')
decisions='''# Android 3.0.2-A1 decisions

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
- Clipboard metadata hides automatic previews for very long text while preserving all copied characters. This follows Android's documented flag and adds no APK clipboard-read permission. Platform System UI ANR in the stressed emulator is disclosed in verification; no unsupported causal claim is made.
- Private signing key remains outside source/delivery. Same certificate supports installing over the earlier APK.
'''
(ROOT/'DECISIONS.md').write_text(decisions,encoding='utf-8')
verification='# Android 3.0.2-A1 verification\n\nContract: ATS_SYNC_2026-10-B. Signed release APK installed on the test emulators.\n\n| Run | API | Checks | Failures | Scope |\n|---|---|---|---|---|\n'
for name,d in reports.items():verification+=f"| {name} | {d['api']} | {d['count']} | {d['failures']} | {'Latest sync/menu/clipboard regression run' if 'Sync' in name else 'Full native suite, including import/render/audio/MP4/service/cancel and new sync checks'} |\n"
verification+='''
The runs overlap; do not add them as a unique-test total. Earlier unsuccessful UI automation attempts are retained separately in FirstAttempt. The final full run and targeted rerun are the acceptance evidence, not the earlier failing attempts.

Real checks include the canonical 12-scene MAX JSON and the exact 34-scene final RICH JSON (22 non-cuts, eight fancy, three date cards, six SFX). Hindi Poppins was rendered to a frame using demo placeholders and visually inspected; this is not a second full Hindi MP4 export. The eight-second HD MP4 uses synthetic demo images and test tones. Its audio/video tracks, dimensions, frame count/duration and decodability were checked by instrumentation and ffprobe. Cancellation, foreground completion and private-cache cleanup were tested.

Actual Android 11 screenshots and fresh Android 15 UI smoke captures of the menu, compact master-prompt dialog and timeline were visually inspected before delivery. Prompt clipboard content equals the complete bundled original, not just the on-screen preview. Diagnostic and utilization Copy buttons exercise their real dialog callbacks.

During a stressed Android 15 emulator run, a System UI ANR overlay appeared even though ATS checks passed; those screenshots did not establish clean interactive UI. The emulator was restarted, contention reduced, and the live UI rechecked. Large clipboard previews are now redacted using the official Android flag, with exact full-content copy tested again. This is a mitigation, not proof of what caused that platform ANR. The full 57-check run preceded this small clipboard-only change; the final Android 15 sync/clipboard rerun verifies the delivered change.

No physical phone, every manufacturer's document picker, universal RTL, Windows pixel parity or 4K/60 performance is claimed. The original audio/image workflow and native platform limitations are described in README.md.
'''
(ROOT/'VERIFICATION_REPORT.md').write_text(verification,encoding='utf-8')
notes='''CONTRACT LOADED: ATS_SYNC_2026-10-B

Android 3.0.2-A1 now includes the B diagnostic exchange, utilization/classification, native font/RTL warnings, canvas override, persistent Repaste, timeline thumbnails and the exact Main Master Prompt V5.2.5 menu/Copy asset. Input JSON remains ATS_PACKAGE_V2. Do not add platform, mode, contract_id or prompt_version to authored ATS JSON.

Native SFX spacing now rejects cues within 350 ms instead of silently skipping. Author integer fields with integer tokens; fractional values reject. Native JSONObject serialization can canonicalize integral decimal tokens, so raw lexical parity is not claimed. Seed is integer 0 through 2147483647 with the shared exact path/message. Transition fallback uses a four-frame minimum; defaults use Windows rounding.

Shared authoring syntax and mode mathematics are aligned. Native effects/director/typography/sound can differ visually from Windows; no pixel identity, certified RTL or FFmpeg true-peak mastering parity is claimed. Author explicit effects; use Bottom with centered date cards. The attached V5.2.5 prompt was embedded unchanged. Mobile-specific notes supplement the existing Windows B contract rather than silently rewriting it.
'''
(ROOT/'ANDROID_SYNC_NOTES.md').write_text(notes,encoding='utf-8')
if DELIVERY.exists():raise FileExistsError('Delivery exists; never overwrite silently')
DELIVERY.mkdir()
for name in ['README.md','DECISIONS.md','VERIFICATION_REPORT.md','ANDROID_SYNC_NOTES.md']:
    shutil.copy2(ROOT/name,DELIVERY/name)
shutil.copy2(apk,DELIVERY/apk.name);shutil.copy2(prompt,DELIVERY/'Main Master Prompt V5.2.5.txt')
for name in reports:
    shutil.copytree(ROOT/'Verification'/name,DELIVERY/'Verification'/name)
shutil.copytree(ROOT/'Verification/UI-release-smoke',DELIVERY/'Verification/UI-release-smoke')
source_zip=DELIVERY/'AutoTimelineSync-3.0.2-A1-ANDROID-SOURCE.zip'
with zipfile.ZipFile(source_zip,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in ROOT.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ROOT)
        if rel.parts[0] not in {'src','res','assets','tools','tests'} and rel.name not in {'AndroidManifest.xml','README.md','DECISIONS.md','VERIFICATION_REPORT.md','ANDROID_SYNC_NOTES.md','requirements-build.txt'}:continue
        if any(x in ['__pycache__','build'] for x in rel.parts) or p.suffix in ['.apk','.idsig','.jks','.keystore','.pyc']:continue
        z.write(p,Path('AutoTimelineSync-Android-Source')/rel)
    assert not any('signing-password' in n or n.endswith(('.jks','.keystore')) for n in z.namelist())
probe=ROOT.parent/'ats_windows_3_0_2/core/runtime/ffmpeg/ffprobe.exe'
sample=ROOT/'Verification/API35/verified-export.mp4'
metadata=json.loads(subprocess.check_output([str(probe),'-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate,duration,nb_frames:stream_side_data=rotation:format=duration,size','-of','json',str(sample)]))
shutil.copy2(sample,DELIVERY/'Sample-Export-Test-Tones.mp4')
release={'product':'Auto Timeline Sync by Naimat','version':'3.0.2-A1 Android','contract':'ATS_SYNC_2026-10-B','apk_sha256':sha(apk),'source_zip_sha256':sha(source_zip),'prompt_sha256':sha(prompt),'prompt_byte_identical':True,'tests':{n:{'api':d['api'],'count':d['count'],'failures':d['failures']} for n,d in reports.items()},'export':metadata,'physical_phone_tested':False,'windows_pixel_parity':False}
(DELIVERY/'RELEASE_RESULTS.json').write_text(json.dumps(release,indent=2),encoding='utf-8')
direct=DELIVERY.parent/apk.name
if direct.exists():raise FileExistsError(direct)
shutil.copy2(apk,direct)
with zipfile.ZipFile(source_zip) as z:assert z.testzip() is None
assert sha(direct)==sha(apk)==sha(DELIVERY/apk.name)
print(json.dumps({'folder':str(DELIVERY),'apk':str(direct),'tests':release['tests'],'apk_mib':round(apk.stat().st_size/1048576,2)},indent=2))
