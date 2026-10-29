# Rebuilding the recovered Windows project

Use **Python 3.12**: some installed baseline modules remain Python 3.12 bytecode.
Install `requirements-build.txt`, then run `python build_windows.py` from this folder.
The source contains current assets/presets, fonts/licenses and a snapshot of the
installed baseline. `core/runtime/ffmpeg` must contain ffmpeg.exe and ffprobe.exe;
copy the runtime folder from the delivered portable app if it is not included in
your source archive. No service/API keys are needed.

New implementation is in `core/ats_studio/desktop_fixes.py`, `fast_export.py`,
`ui_parts/dialogs.py` and `core/launch.py`. The rest of the baseline is preserved.
Run `python -m pytest tests -q` for the focused suite. A rebuilt executable accepts
`--smoke-test OUTPUT_FOLDER` for an actual packaged import/export verification.

The recovery limitation is documented in RELEASE_REPORT.md. The original desktop
source folder was unavailable; this archive includes a mixture of verified source
and recovered bytecode. Retain an original full-source backup if it becomes available.
