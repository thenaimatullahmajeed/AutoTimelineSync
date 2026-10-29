# Auto Timeline Sync by Naimat 3.0

## Start and export

1. Extract the **whole portable folder**, then run AutoTimelineSync.exe. Keep `_internal` and `runtime` beside it.
2. The New project dialog opens automatically. Select final narration, numbered full-scene images and the ChatGPT ATS_PACKAGE_V2 JSON. You can paste JSON instead of opening a file.
3. Background music is optional. Choose MP3, WAV, M4A or FLAC; ATS repeats and crossfades it to the narration automatically.
4. Once validation succeeds, click **Create Timeline**. An error includes a **Copy for ChatGPT** action to request a complete corrected package.
5. Click **Export**, choose an output filename and optionally resolution/quality/framing, then Export MP4.

The script chooses the format, fps, captions, camera motion, transitions and special moments. No engine setup or login is required. HD/Full HD/4K use the script's aspect ratio. Full HD + Fast is the default; Higher quality costs more render time. Fit entire image avoids source cropping. A progress bar shows stage, elapsed time and stage remaining estimate; time during audio/finalization is recalculated rather than extrapolated from scene rendering.

## Optional adjustments

| Location | Available |
|---|---|
| Captions | 9 style cards + Off; optional size/position under Customize |
| Look | Energy; one framing override under Fine-tune |
| Sound / Voice & Music track headers | Linked gain sliders with live percentage; preview audio rebuilds after a short pause in adjustment |
| Reset to script | Clears optional settings and circle overrides |
| Format chip | Read-only JSON format or image-majority format |
| Settings | Advanced format override with a crop warning |
| Ready / notices | Actual warnings and separate information, including skipped moments |
| View | Fullscreen Pro preview, preview safe zones and caption visibility; safe-zone guides never appear in exports |
| Help > Explain Package | Summarizes scene/word/caption counts and selected motion |
| Help > Run Linter | Checks source decoding, image aspect/duplication, short holds and reading speed; heuristics are notices, not proof of content correctness |

The timeline only seeks; it is not a manual clip editor. Music lane shows loop seam marks. Circles are JSON-defined and tied to source-image coordinates, not detected. If a circle falls outside the camera crop, it is skipped once without blocking export. Advanced correction while the moment is active: **Alt+drag** moves its box; **Alt+Shift+drag** defines a resized source box. Date cards darken the footage and display word-timed text.

## Projects and files

- Save with File > Save project. New projects use `.ats3`, project_format 2. Old `.atsproj` files and V1/V3 packages are not imported.
- File > Import reopens the input dialog. **Cancel keeps your current project.** Creating another timeline commits the new inputs.
- Saved projects are autosaved each minute and at close. An unsaved recovery file is written to `%LOCALAPPDATA%\AutoTimelineSync3\recovery.ats3`; open it through Open project if needed.
- The MP4 is accompanied by `.mp4.report.json` and a progress log. The report lists actual dimensions/fps, selected transitions, audio levels, cache and stage timings.
- Existing MP4s are not overwritten; choose a new filename. Render work is bounded and cleaned by the engine after export/cancellation; preview temporary files are scoped to this app session.

## Compatibility

Give **CHATGPT_MASTER_PROMPT_ATS_V3.txt** and **ATS_JSON_AUTHORING_GUIDE.md** to the authoring chat. Both bundled master-prompt filenames contain the same current instructions. “V3” in the prompt filename means revision; **the JSON schema is ATS_PACKAGE_V2**.

No cutouts, Remotion, multi-image layers, Voice Studio, licensing or Supabase setup is part of this product. A single still can pan/zoom and transition, but cannot animate people or reconstruct real depth. Preview shares the compositor; output resolution and H.264 compression can change its pixels. Word highlight needs real word timestamps. An SRT alone does not provide those.
