# Auto Timeline Sync by Naimat — 3.0 JSON authoring guide

## Product and workflow

This is a new local app. Target **`ATS_PACKAGE_V2`**, not V1 or V3. Product version 3.0 is not a schema version. Projects use `.ats3`, `project_format: 2`; old `.atsproj` files are not imported. No Remotion, cutouts, independent image layers, video clips, login or Voice Studio.

Write narration first. After the final audio, SRT and measured word JSON arrive, deliver the visual theme, numbered **complete full-background scenes**, bulk prompts and one timed package. Do not alter application source, assemble image folders or edit generated images during content authoring. The user generates images and selects narration, image folder, JSON and optional local music. Create Timeline validates automatically. Export needs no creative configuration.

The app uses the Pro compositor and story director on every project. Explicit scene motion/transition choices are preserved; omitted choices are filled deterministically. Optional caption/energy/volume overrides can be reset to the script. Format and fps are not editor selectors.

## Capability matrix

| Capability | Supported and limits |
|---|---|
| Source images | Numbered PNG/JPG/JPEG/WebP; one complete scene per `001`, `002`, etc. No collage or alpha-layer assembly |
| Camera | Static, push/pull, pan, diagonal, Ken Burns, small punch; planar image movement, not reconstructed depth |
| Transitions | Listed 27 IDs; bounded inside incoming scene, timeline duration never extended |
| Captions | 9 curated presets plus Off; word highlighting needs measured word intervals; 1–2 lines; fit shrinks long cues |
| Caption animation | Creator profiles have fixed pop/bounce/glow/fade behavior; Typewriter reveals timed **words**, not handwritten strokes |
| Music | Optional MP3/WAV/M4A/FLAC; loop with up to 0.8 s equal-power overlap, 0.5 s entry and 1.5 s exit; shorter clips use half-length overlap |
| Audio | Narration, flagged-cut SFX, last/lowest music bed. Mono internal mix, stereo AAC output; no stereo spatial editing |
| Moments | Word-bound date cards and small source-image circles. No detection, OCR, segmentation or tracking |
| Finishing | Deterministic grain, vignette, contrast; applied to footage before date cards/captions; zero is off |
| Preview | Same Pro spec and compositor, including fullscreen. Resolution/sampling/compression can change visual pixels |
| Export | MP4, H.264 + AAC 192 kb/s, 48 kHz, BT.709 limited range; HD/Full HD/4K per format, Fast or Higher quality |
| Non-capabilities | Arbitrary keyframes, cutouts, animated character limbs, 3D, generated reference characters, arbitrary emoji animation, frame-identical third-party effects |

## Serialization and timing

Export **one UTF-8 JSON object on one physical line**, without BOM, comments, Markdown, prose, trailing whitespace/newline or a second object. First byte `{`, last `}`. Strict-parse the exact saved file; raw-decode must consume every character. The importer tolerates normal JSON whitespace, but authoring always exports the safe compact form. Duplicate keys, NaN/Infinity, unknown fields and files over **50 MiB** are rejected.

All script times are seconds from the **final audio**, never transcription wall-clock times. Frame conversion is decimal `round-half-up(time × fps)`. Scene 001 begins at frame zero, adjacent scene boundaries meet, every scene has ≥1 frame, and the last ends at the audio frame count. Media/audio mismatch of more than one frame blocks import; an accepted tiny discrepancy is information. Do not rescale voice timings to accommodate effects.

Words have unique increasing integer indices, nondecreasing starts, `end > start`, and timeline bounds. Preserve the supplied timings and punctuation. Captions have sequential IDs and ordered start times; their word-range endpoints must exist. Their text must equal the timed words in that range, with whitespace normalization only. Keep 2–6 words per cue, avoid overlapping cues and ensure each cue contains its word intervals. ATS preserves your cue intervals; it does not split them automatically.

## Full field reference

**R** means required. Other fields are optional. Invalid fields normally block import with a JSON path and expected value. **Moments alone soft-fail**: each invalid item is skipped with one information notice. Unknown fields inside moments skip that item.

### Package and format

| Field | Type / allowed values | Default / limits / behavior |
|---|---|---|
| `schema` R | string `ATS_PACKAGE_V2` | Other schemas rejected by ATS 3 |
| `project_title` R | nonempty string | Display name; may be renamed at import |
| `audio_duration` R | finite positive number | Exact final narration duration; rounded output frames must be >0 |
| `fps` R | integer 1–60 | Author at 30 unless requested otherwise; controls timing/render fps, no manual picker |
| `scenes` R | nonempty array | Ordered, complete gapless timeline |
| `words` R | array | Timed words; required key even if empty |
| `captions` R | array | Required key; may be empty or disabled |
| `caption_style` R | object | Required booleans below |
| `format` | object | Missing: nearest ratio majority from numbered folder; stable tie/no votes → Vertical |
| `format.orientation` R within format | `VERTICAL`, `HORIZONTAL`, `SQUARE`, `PORTRAIT` | Paired respectively with 9:16, 16:9, 1:1, 4:5 |
| `format.aspect_ratio` R within format | string `9:16`, `16:9`, `1:1`, `4:5` | Must match orientation; wrong pair blocks import |
| `direction`, `style`, `audio`, `overlays`, `ending`, `moments` | objects or arrays below | Missing values use the documented defaults |

| Format | HD | Full HD (default) | 4K tier |
|---|---|---|---|
| Vertical | 720×1280 | 1080×1920 | 2160×3840 |
| Horizontal | 1280×720 | 1920×1080 | 3840×2160 |
| Square | 720×720 | 1080×1080 | 2160×2160 |
| Portrait | 720×900 | 1080×1350 | 2160×2700 |

Image-format mismatch is a notice, not a blocker. Default framing is Fill frame (focus crop). Fit entire image is the single optional framing override in export/Look. Advanced format override is under Settings with a crop warning.

### Scenes, words, captions

| Field | Type / requirement | Default, range or effect |
|---|---|---|
| `scenes[].id` R | string | Sequential `001`, `002`… (minimum 3 digits, not a maximum scene count) |
| `image_id` R | string | Exactly same as scene ID and matching file stem; duplicate IDs/files rejected |
| `start`, `end` R | finite numbers | Gapless output-frame boundaries; end > start |
| `voice_text` R | string | Narration in this scene; used for director story cues |
| `motion` | motion ID below | Missing → director selects; explicit STATIC is preserved |
| `transition` | transition ID below | Transition **into this scene**; missing → director selects; first scene hard cut |
| `motion_config` | object | `focus`, `zoom_from`, `zoom_to`, `ease`, `blur` only in ATS 3 |
| `motion_config.focus` | `{x:number,y:number}` | Both required, 0–1 in source image; missing → edge saliency/center |
| `zoom_from`, `zoom_to` | numbers 1–2 | Motion's standard zoom endpoints; focal framing can crop further |
| `ease` | `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT` | Motion default; transition default EASE_IN_OUT |
| `blur` | number 0–1 | 0 disables temporal sampling; >0 uses 2–4 samples, costs render time |
| `transition_config` | object | `type`, `frames`, `direction`, `ease`, `sfx` |
| `transition_config.type` | transition ID | Overrides `transition` |
| `frames` | integer 4–30 | Typically 8 fast / 12 gentle; director clamps to 0.12–0.55 s and ≤45% of shorter neighboring scene; <4 available → hard cut + notice |
| `direction` | `LEFT`, `RIGHT`, `UP`, `DOWN`, `AUTO` | AUTO |
| `transition_config.sfx` | SFX ID or `NONE` | Missing/NONE = no sound. Marks this cut explicitly; not allowed on scene 001 |
| `scenes[].sfx` | array of cue objects | Default empty; also explicitly flags this cut |
| Cue `id` R | SFX ID | Unknown ID rejected |
| Cue `offset_ms` | number −300–300 | 0 relative to incoming scene start; resolved time must be inside timeline |
| Cue `gain_db` | number −30–6 | −22; actual gain limited under voice for audibility safety |
| Cue `variant` | `AUTO` or integer 1–9 | AUTO → variant 1; installed packs cycle variants |
| Cue `pitch_cents` | number −200–200 | 0; synthesized tonal sounds respond; not a general recorded-audio pitch editor |
| `look_override` | `{look, intensity}` | Optional per-scene look and 0–1 intensity; falls back to package style |
| `words[].index` R | integer | Unique increasing; use positive contiguous indices when authoring |
| Word `start`, `end` R | finite numbers | Measured timing; start ≥0, end >start, ≤duration + one frame |
| Word `text` R | nonempty string | One spoken token with punctuation |
| `captions[].id` R | string | Independent sequential `001`, `002`… |
| Caption `start`, `end` R | finite numbers | Ordered starts, end >start, within timeline tolerance |
| Caption `text` R | nonempty string | Must match words selected below |
| `word_start_index`, `word_end_index` R | integers | Existing ordered endpoints; includes all indexed words between them |

Motions: `STATIC`, `SLOW_PUSH_IN`, `SLOW_ZOOM_OUT`, `PAN_LEFT`, `PAN_RIGHT`, `PAN_UP`, `PAN_DOWN`, `GENTLE_DIAGONAL`, `KEN_BURNS`, `TINY_PUNCH_IN`. Accepted aliases: `STATIC_HOLD`, `SLOW_PULL_OUT`, `IMPACT_PUNCH_IN`. `SUBTLE_PARALLAX` is accepted only as a compatibility enum and falls back to a 2D push with a notice; do not author it.

Transitions: `HARD_CUT`, `NONE`, `CROSSFADE`, `GENTLE_DISSOLVE`, `DISSOLVE`, `FADE_THROUGH_BLACK`, `FADE_THROUGH_WHITE`, `QUICK_PUSH`, `WHIP_PAN`, `ZOOM_THROUGH`, `DISSOLVE_BLUR`, `SLIDE_SHADOW`, `LIGHT_LEAK_FLASH`, `FILM_BURN`, `IRIS_WIPE`, `INK_WIPE`, `BRUSH_WIPE`, `PAPER_TEAR`, `BURN_LIGHT`, `TORN_CENTER_SPLIT`, `ZOOM_BLUR`, `FILM_FLASH`, `LIGHT_LEAK`, `SMOKE_DISSOLVE`, `IRIS_REVEAL`, `INK_SPREAD`, `GLITCH_TRANSITION`. Prefer the restrained ones most of the time.

SFX IDs: `SWIPE_SOFT`, `WHOOSH_SOFT`, `WHOOSH_FAST`, `PAPER_SLIDE`, `PAGE_TURN`, `BRUSH_SCRATCH`, `CAMERA_SHUTTER`, `FILM_CLICK`, `IMPACT_LOW`, `IMPACT_SOFT`, `RISER_SHORT`, `INK_SPLASH`, `STAMP_THUD`, `TYPEWRITER_KEY`, `TICK_SOFT`. Mostly procedural stylizations, not authentic archival recordings. Keep explicit cues ≥350 ms apart; import preparation rejects closer cues. Local verified packs may extend IDs; portable defaults use the list above.

### Caption styling

| Field | Allowed / default | Effect and limits |
|---|---|---|
| `enabled` R | boolean | False turns off captions |
| `highlight_current_word` R | boolean | Uses word timestamps; cannot recover missing alignment |
| `preset` | string; default `Minimal Cinematic` | Exact names in table below |
| `font` | string; default `Inter` | Registered family; unsupported names rejected, unavailable supported OS fonts fall back |
| `size` | integer 50–180; default 100 | Percentage of preset's reference size, automatic fit still applies |
| `position` | `Top`, `Center`, `Bottom`; default Bottom | Platform-safe preset placement; Bottom is around 63% vertically in portrait, not the screen edge |
| `max_lines` | integer 1–2; default 2 | Automatic balanced wrapping/fit |
| `text_color`, `accent_color` | `#RRGGBB` | White text default; accent comes from preset; Highlighter fixed dark lettering and white base box |
| `background` | `Shadow Only`, `Dark Brush`, `Solid Box`, `Paper`, `None` | Default Shadow Only; applies to Documentary/Clean/Typewriter. Creator profiles use their own backgrounds |
| `emphasis` | array of existing word indices 0…1e9 | Missing → number/uppercase emphasis; empty → no extra emphasis. Visible on highlight-capable presets |
| `animation` | `POP`, `FADE`, `NONE` | Optional only on Documentary/Clean/Typewriter; fixed creator animations reject this field. Default POP on these generic styles |

| UI card | Exact JSON preset | Behavior |
|---|---|---|
| Hormozi | `Hormozi Style` | Caps, yellow active word, outlined pop |
| Viral Pop | `MrBeast / Viral Pop` | Caps, red active word, bounce/rotation |
| Karaoke | `Karaoke Highlight` | Dim inactive words, active purple box |
| Neon Glow | `Neon Glow` | White core, cyan glow, fade/scale |
| Cinematic | `Minimal Cinematic` | Sentence case, soft shadow, fade up, no active-word accent |
| Highlighter | `Highlighter Box` | Dark lettering, white box, yellow active-word box |
| Documentary | `Documentary Highlight` | Current-word green emphasis, optional background |
| Clean | `Clean Subtitle` | Quiet subtitle; no separate active accent by default |
| Typewriter | `Typewriter` | Timed word reveal, not handwriting |
| Off | `Off` | No captions |

Fonts accepted: Montserrat, Anton, Luckiest Guy, Bangers, Poppins, Bebas Neue, Arial, Segoe UI, Georgia, Consolas, DejaVu Sans, Liberation Sans, Source Code Pro, Inconsolata, Bitstream Vera Sans, Inter, Inter Black, Inter Bold, Inter Medium, Oswald, Playfair Display, Noto Nastaliq Urdu, Caveat. Not all complex-script shaping or RTL layouts are certified. Default Inter is consistent across normal and fullscreen preview and export.

### Direction, style, audio, ending

| Field | Default / allowed / limits | What it changes |
|---|---|---|
| `direction.energy` | BALANCED; SUBTLE/BALANCED/HIGH_ENERGY | Intensity/budget for omitted scene choices; explicit choices remain intact |
| `direction.transition_frequency` | .15; number 0–1 | Fancy-transition budget for omitted choices, scaled by energy; not a command to animate every cut |
| `direction.finish` | object; all 0 | `grain`, `vignette`, `contrast`, each number 0–1; deterministic footage finish |
| `direction.voice_level` | 1; number 0–1 | Single pre-master narration gain |
| `direction.music_level` | .18; number 0–1 | Single pre-master bed gain, not multiplied by a hidden −24 dB setting |
| `direction.duck_db` | −9; number −30–0 | Additional music attenuation during signal activity in narration |
| `direction.sfx_enabled` | true | False disables flagged cut SFX; no automatically invented SFX |
| `style.preset` | CLEAN_DOC | ID below; installed fixed style definition, no user preset migration |
| `style.look` | preset look | ID below |
| `style.look_intensity` | 0; number 0–1 | Separate existing look system; use modestly or omit in favor of finish |
| `style.seed` | 48127 in new director; signed 64-bit integer | Repeatable director/texture choices |
| `audio.sfx.gain_db` | 0; number −12–6 | Overall multiplier on flagged SFX, still speech-clamped |
| `audio.master.mode` | LIMIT_ONLY; LIMIT_ONLY/LOUDNORM/OFF | Measured shared preview/export mastering; OFF skips loudness enforcement |
| `audio.master.target_lufs` | −14; number −23…−9 | Output integrated loudness target |
| `audio.master.true_peak_db` | −1; number −3…−.5 | AAC true-peak ceiling |
| `ending.mode` | no ending effect; HOLD/FADE_OUT | Optional fade to black inside final frames, never extends audio |
| `ending.frames` | 15; integer 0–90 | Last-frame fade length; 0 disables |

All levels are **relative before mastering**; final mastering may adjust the whole mix while preserving its balance. Missing optional music is a notice and disables that bed. No music file means no synthetic fallback music. Clips longer than the timeline are trimmed without looping. Extremely short loops can sound repetitive even with crossfades.

Style IDs: CLEAN_DOC, HISTORY_ARCHIVE, HISTORY_MEDIEVAL, DARK_PSYCHOLOGY, FINANCE_PREMIUM, SCIENCE_CLEAN, TECH_MODERN, MYSTERY_NOIR, REEL_CLEAN_LIGHT, LEGACY. Look IDs: CLEAN, CLEAN_DOC, AGED_PARCHMENT, ALBUMEN_1880S, SILENT_FILM_1910S, NITRATE_1930S, PRESS_PHOTO_1950S, KODAK_1970S, VHS_1980S, DARK_NOIR, FINANCE_PREMIUM, SCIENCE_CLEAN, TECH_MODERN. LEGACY is just an installed style ID, not a separate engine mode.

### Moments — optional, never auto-detected

| Field | Type / allowed / default | Rules |
|---|---|---|
| `moments` | array; default empty | Each malformed item skipped with one info notice |
| `id` | unique string; default array-index string | Supply a stable ID for project overrides |
| `type` R | DATE_CARD or CIRCLE | Other types skipped |
| `word_start_index`, `word_end_index` R | existing ordered integer indices | Begin at first word start, end at last word end, decimal frame conversion |
| DATE_CARD `text` R | 1–80 characters | Big centered text with wrapping |
| DATE_CARD `dim` | number 0–.8; default .65 | Footage darkens, whole card fades in/out over ~150 ms |
| CIRCLE `scene_id` R | existing scene ID | Word range must be within that scene |
| CIRCLE `box` R | `[x,y,width,height]` | Source-image normalized, top-left origin, NOT output-frame coordinates; each side ≥.03, area ≤.20, inside source bounds |

The circle follows the identical scene crop/camera transform. It draws on in ~0.4 s. If its box lies outside the crop at any active frame it is skipped once, with an info notice. No image analysis invents a marker. Only highlight a **small clearly visible object held or touched by a person**, such as a ticket, photograph, letter, key or watch. Do not circle entire faces, people, tents, buildings or abstract empty space. If coordinates are uncertain, omit it. Advanced fallback: Alt+drag moves the currently timed circle; Alt+Shift+drag defines a new source box. This is stored only in the project override, and Reset to script clears it.

### Existing advanced overlays

Prefer moments for dates and source-attached circles. `overlays` remains optional for explicitly authored decorative material.

Each overlay requires `id` (text ≤120 chars), `type`, `start`, `end` (seconds inside audio, end >start). Optional `text`, `text2` (≤120 chars), `x`, `y`, `w`, `h` (0–1), `style`, `points` (`[[x,y],…]`, each 0–1), `scene_id`. Types: DATE_STAMP, HOOK_CARD, LOWER_THIRD, TEXT, HIGHLIGHT_BOX, MAP_ROUTE, PHOTO_NOTE. Styles: PLAIN, ARCHIVE, MODERN, RECT, CIRCLE, ARROW. Defaults: PLAIN, x=.5/y=.2, w=.2/h=.1 for boxes; text empty. Text cards auto-size/clamp; TEXT uses a centered 60%-width area. MAP_ROUTE draws connected normalized output points. HIGHLIGHT_BOX coordinates are **output space** and do not track a source object; use CIRCLE moments instead. PHOTO_NOTE requires text, existing scene_id and four convex source-image corners in perimeter order (TL,TR,BR,BL), then puts handwriting-like ink into that source before camera motion. It cannot infer blank-paper position or actual handwriting strokes.

Rejected in ATS 3 authoring: top-level `auto_direct`; `audio.music`, `audio.ambience`; `audio.sfx.pack` or `density`; `caption_style.chunk_words` or `safe_zone`; `motion_config.shake`; V3/layer/Remotion fields. Replace these with the supported direction/music/moment fields, or remove them. Do not invent synonyms.

## Selection guidance for ChatGPT

Default creative mood is **dark horror/mystery** when no other mood is given: Minimal Cinematic + SUBTLE, grain .10–.15, vignette .15–.25, contrast .05–.12. Documentary Highlight fits fact/date emphasis. Hormozi or Viral Pop fits upbeat short-form content; Karaoke fits teaching; Neon fits night/tech, Highlighter fits quotes. Keep at most two caption colors (white + accent).

Use restrained push/pan on roughly 60–80% of scenes; hold evidence still; one punch for a reveal. Keep 75–90% of boundaries hard cuts or gentle dissolves. Use fancy transitions on ≤15% of ordinary boundaries, ≤25% for high energy, never adjacent and never faster than the narration can read. Suggest 3–6 s holds but follow measured speech. A camera move cannot turn a single picture into character animation.

Date cards are for explicit spoken dates, not every number. Circles are sparse, small and narratively meaningful. Aim for 1–3 such moments per minute. Flag SFX on a few important cuts, with ≥350 ms spacing; silence is a valid default. Default music .18 and duck −9 dB; do not insist music must exist. Avoid over-darkening text/evidence or using grain to conceal unclear pictures.

## Self-check and exact fixes

1. Final audio duration, measured words and SRT are the same recording; convert wall-clock transcript times to relative seconds.
2. Schema V2; IDs sequential; numbered filenames match; scene first/joins/last checked at output frames.
3. Caption text equals selected timed words, indices exist, intervals cover spoken words, cues stay readable.
4. Format pair exact; active objects survive the chosen crop throughout camera motion.
5. Only listed fields/enums; 0–1 values are numbers, boolean fields true/false; no placeholder STATIC if automatic direction is desired.
6. Circle boxes are source coordinates, not frame coordinates, small held/touched objects only; date-card timing derived from words.
7. SFX only explicitly flagged later cuts, not scene 001; cues not closer than 350 ms.
8. Strict-parse the EXACT compact export and check full consumption. Return a complete corrected package when an ATS Copy for ChatGPT message arrives.

| Error | Exact fix |
|---|---|
| Extra data | Re-export the same object compactly with zero trailing characters; do not redesign the schema first |
| `$.schema` expected V2 | Set ATS_PACKAGE_V2 and remove unsupported layer/legacy fields |
| `$.format.aspect_ratio` | Use the ratio paired with the supplied orientation |
| Scene gap/overlap | Set each next start to previous end; verify decimal frame rounding |
| Missing image ID | Generate/rename the complete matching numbered scene; no assembly script |
| Duplicate image ID | Keep only one supported file per numeric stem |
| Caption text mismatch | Copy the exact words in word_start_index…word_end_index into text |
| Audio mismatch | Use exact final narration metadata and matching timed words, not estimated script duration |
| Circle skipped | Correct source box/word range, use Fit entire image, or omit the marker; export remains available |
| Unsupported field | Remove it or use documented exact name; never hide an ignored field in JSON |

## Examples and true validation

Complete compact examples: [vertical](Examples/ATS3_vertical.json), [horizontal](Examples/ATS3_horizontal.json). Both use a fictional 8-second ticket story with 2 scene images, 16 timed words, 4 captions, one circle and one date card. The verification harness supplies matching synthetic narration/images/music; these are test fixtures, not recorded speech. **Both passed the real ATS 3 validator and media checks.** The export verification result and screenshots are under `Verification/3.0/`; see BUILD_REPORT.md for the executed results and limits.
