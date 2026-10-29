Contract: ATS_SYNC_2026-10-B | revision 3.0.2-A1 | Approved integration. Shared A input block is retained unchanged as historical evidence.

# Flat ChatGPT authoring contract — ATS_PACKAGE_V2

This contract was checked against Auto Timeline Sync Windows 3.0.2. This integration adds only the approved early seed guard to acceptance; renderer and audio are unchanged. Use ATS_PACKAGE_V2 only. A product version is not a schema version.

Output one complete compact UTF-8 JSON object, without BOM, Markdown, prose, comments or trailing data. This is the safe authoring format; the importer also tolerates ordinary JSON whitespace and complete code fences. Never invent fields. Use actual final audio duration and measured word timestamps; SRT alone does not provide word alignment. Do not stretch timestamps to fit effects.

Required root fields: schema, project_title, audio_duration, fps, scenes, words, captions, caption_style. Author format explicitly even though the parser can infer it when omitted. Author direction and moments explicitly for repeatability. Optional root blocks: style, audio, overlays, ending. No prompt_version, engine, global mode, auto_direct, layers, cutouts or Remotion fields.

FORMAT: VERTICAL with 9:16; HORIZONTAL with 16:9; SQUARE with 1:1; PORTRAIT with 4:5. Match numbered full-scene images. A wrong orientation/ratio pair rejects import. An image-ratio mismatch is a warning. Resolution, codec and framing are app/export choices, not JSON fields.

TIMING: finite relative seconds. FPS is an integer from 1 to 60. Default authoring fps is 30. Scene frame conversion is decimal round-half-up of time multiplied by fps. First scene begins at frame zero; adjacent boundaries meet at frame precision; each scene has at least one frame; final scene ends at the audio frame count. Keep authoring joins exact and final end equal to measured audio duration. Media mismatch of more than one frame rejects import.

IDS: scene IDs are sequential strings 001 onward, at least three digits; image_id equals scene ID and image filename stem. Caption IDs are independently sequential strings 001 onward. Never infer a 999-scene limit. Words have unique increasing integer indices; author positive contiguous indices starting at 1. Moment IDs are unique strings. Overlay IDs are strings of at most 120 characters; parser does not enforce their uniqueness. SFX id is a sound enum name, not a numeric cue ID.

WORDS/CAPTIONS: required arrays even when empty. Preserve measured words, punctuation and timings. Each caption selects an inclusive existing ordered word-index range. Text is exactly the space-joined selected words, with whitespace normalization only. Caption starts are ordered, and its end is later than its start. Word/caption timing tolerates at most one frame beyond audio, but never deliberately author beyond audio. There is no independent maximum word count or cue duration. For readability, use usually 2 to 6 words and at most two lines. Cover all speech once and contain selected word intervals in each cue as authoring rules; parser does not enforce those coverage/containment/nonoverlap rules.

TRANSITIONS: author motion and transition explicitly on every scene. Scene 001 uses HARD_CUT or NONE and has no SFX. transition_config.type, when present, wins over scene.transition; for clear authoring make them identical. A mismatch is accepted. Explicit effects are preserved regardless of energy or transition_frequency, subject to duration fitting and compatibility fallback. Director budget, adjacency and repetition protections operate on generated choices, not explicit ones. Even an empty motion_config or transition_config marks that scene's corresponding choice explicit; do not add empty placeholder configs when asking the director to choose.

Default non-cut duration uses Python round: WHIP_PAN, FILM_FLASH and GLITCH_TRANSITION use 0.24 seconds multiplied by fps; all other non-cuts use 0.42 seconds multiplied by fps. At 30 fps these are 7 and 13 frames respectively. HARD_CUT and NONE use zero. Explicit transition_config.frames is an integer from 4 to 30. Fitting takes the smallest of requested/default length, floor of 45 percent of the shorter neighboring scene, and incoming scene length minus one. The final effect needs at least max of 4 and ceil of 0.12 multiplied by fps frames; otherwise it becomes HARD_CUT with a warning. At 30 fps both neighbors need at least 9 frames for a configured effect; at 60 fps at least 18. Low-fps defaults may fall back even on long scenes. Effects occupy the incoming scene and never extend audio.


Use STATIC for readable evidence; slow push or zoom-out for explanation/suspense; pan for geography; a small punch for a justified reveal. Do not promise character animation, actual depth, object recognition or tracking from a flat image.

DIRECTION: energy SUBTLE/BALANCED/HIGH_ENERGY; default BALANCED. voice_level 0 to 1, default 1; music_level 0 to 1, default 0.18; duck_db minus 30 to 0, default minus 9. transition_frequency 0 to 1, default 0.15, affects generated transitions only. sfx_enabled is boolean, default true. finish grain/vignette/contrast each 0 to 1, default zero; zero disables the finishing amount. Finishing is applied before moments/captions. Levels are relative before mastering.

STYLE: preset and look must be listed IDs. look_intensity is 0 to 1. Use seed 48127 for repeatability; effective app-safe seed range is integer 0 to 2147483647. The parser rejects invalid seeds early at $.style.seed with: must be an integer between 0 and 2147483647. look_override uses optional look and intensity 0 to 1. Style and audio blocks are allowed with every caption preset.

AUDIO: import optional local music in the app. JSON configures level/ducking, never the music file. audio allows master and sfx only. audio.master.mode is LIMIT_ONLY, LOUDNORM or OFF; target_lufs is minus 23 to minus 9, default minus 14; true_peak_db is minus 3 to minus 0.5, default minus 1. audio.sfx.gain_db is minus 12 to 6, default zero. No audio.music, audio.ambience, audio.sfx.pack or density.

SFX: transition_config.sfx accepts an SFX ID or NONE. scenes[].sfx is an array of objects requiring id, with optional offset_ms, gain_db, variant, pitch_cents. offset_ms is minus 300 to 300, default zero; gain_db minus 30 to 6, default minus 22; pitch_cents minus 200 to 200, default zero; variant is AUTO or integer 1 to 9, default AUTO which resolves to 1. Resolved cue time stays inside audio. Cues need at least 350 ms spacing. Create Timeline runs cue preparation and rejects closer cues; parse_script alone does not check this spacing. Do not use both mechanisms on the same cut. Two scene cues can technically fit at minus 300 and plus 300 ms, but normally author one cue per cut. No engine count cap was found; recommended maximum is max of 1 and ceil of duration divided by 15. No first-scene SFX. Disabling SFX bypasses cue preparation but does not bypass numeric field validation.

MOMENTS: moments is an optional array; author an empty array when none. Invalid items are skipped with an information notice, not a package rejection. Both types use existing ordered word references and at least one frame. No start/end fields. DATE_CARD requires type, text, word_start_index, word_end_index; optional id, dim. Text is 1 to 80 characters; dim 0 to 0.8, default 0.65. The tool does not verify that text is a spoken date, and does not enforce count, spacing or overlap caps. Author only spoken date components, use the first meaningful occurrence, avoid overlap, and use at most min of 6 and 3 multiplied by ceil of duration divided by 60 cards.

CIRCLE additionally requires existing scene_id and box [x,y,width,height] in full-source coordinates. x and y are at least zero, width/height at least 0.03; box stays inside source bounds; area at most 0.20. Word interval stays within the scene; box stays inside the camera crop at every active frame or the marker is skipped. Code permits a one-frame circle and unlimited counts. For authoring use a mention lasting at least ceil of 0.4 multiplied by fps frames, at most one circle per scene and four per video, on small clearly visible held/touched objects only. Omit uncertain coordinates. No object detection enforces this semantic policy.

OVERLAYS: every type requires id, type, start, end. Optional text/text2, x/y/w/h, style, points, scene_id. id/text/text2 have at most 120 characters. Times run from zero to 10000000 and stay inside audio; end is later than start. Coordinates are 0 to 1. All seven types accept all six styles. Defaults: PLAIN, x 0.5, y 0.2, w 0.2, h 0.1; text empty. No total/per-type count cap; duplicate IDs are accepted. MAP_ROUTE accepts any point count including zero; at least two are needed to draw a line. Each point has exactly two coordinates. PHOTO_NOTE requires nonempty text, existing scene_id and exactly four convex source corners in TL/TR/BR/BL perimeter order. Each adjacent cross product has the same sign and magnitude more than 0.00000001. Code does not reject times outside that scene; drawing is restricted to when the referenced scene is active. Author all photo-note times inside the scene. HIGHLIGHT_BOX is output space, not source tracking. Prefer moments for dates/source circles.

CAPTIONS: enabled and highlight_current_word are required booleans. preset defaults to Minimal Cinematic. size is integer 50 to 180 percent, default 100; max_lines integer 1 to 2, default 2; position Top/Center/Bottom, default Bottom; font default Inter. Colors use #RRGGBB. Generic background choices: Shadow Only, Dark Brush, Solid Box, Paper, None. Emphasis is an array of existing word indices, each integer 0 to 1000000000; empty disables extra emphasis, omission allows number/uppercase emphasis.

The six creator presets reject any animation field: Hormozi Style, MrBeast / Viral Pop, Karaoke Highlight, Neon Glow, Minimal Cinematic, Highlighter Box. Documentary Highlight, Clean Subtitle and Typewriter accept POP/FADE/NONE, default POP. Off accepts valid styling fields but renders no captions. Invalid values are still checked even when rendering ignores the field. Typewriter reveals words, not handwriting.

All presets except Off honor position, size and supplied font family. Creator presets substitute their profile font for Arial/Segoe UI and fix font weight to their profile. Creator backgrounds ignore the supplied background. Hormozi/Viral honor text/accent/emphasis; Karaoke honors active text/accent, fixes inactive text to white at alpha 102, ignores emphasis. Neon honors text and accent glow but ignores emphasis. Cinematic honors text, ignores accent/emphasis. Highlighter fixes dark letters and white base box, honors active accent, ignores emphasis. Generic Documentary/Clean/Typewriter honor the listed styling fields.

FONTS: bundled Poppins natively covers the tested Hindi sample. DejaVu Sans covers tested Arabic; Noto Nastaliq Urdu covers tested Arabic/Urdu. Other accepted fonts may use fallback; acceptance by name is not script certification. Creator token layout is left-to-right and is unsuitable for certified multiword Arabic/Urdu reading order. Generic full RTL wrapping/highlighting is not certified. Do not promise RTL correctness or invent a language/font capability field.

ENDING: optional mode HOLD or FADE_OUT, frames integer 0 to 90, default 15 when specified. Fade occurs inside final frames, never extends audio.

ERROR LOOP: use the named paths in Copy errors for ChatGPT, fix only those paths and return the complete corrected JSON. The app's $.v1_contract label is an internal wrapper, never a JSON key. Scene n, caption n and word entry n use zero-based array position n minus one. A missing image requires its matching file, not renumbering scenes. WARN/INFO are not necessarily rejection; SKIP means the specified optional item was omitted.

SELF-CHECK: final measured audio/words agree; fields/types/enums exact; IDs and files match; frame coverage is continuous; caption text/index agreement is exact; aspect pair is valid; effects fit and remain readable; cues meet spacing; moments use inspected source coordinates; all optional unsupported keys omitted; output is one complete compact object. Do not claim an import/render test without running it.

## Exact enum lists

motions: GENTLE_DIAGONAL, IMPACT_PUNCH_IN, KEN_BURNS, PAN_DOWN, PAN_LEFT, PAN_RIGHT, PAN_UP, SLOW_PULL_OUT, SLOW_PUSH_IN, SLOW_ZOOM_OUT, STATIC, STATIC_HOLD, SUBTLE_PARALLAX, TINY_PUNCH_IN.

transitions: BRUSH_WIPE, BURN_LIGHT, CROSSFADE, DISSOLVE, DISSOLVE_BLUR, FADE_THROUGH_BLACK, FADE_THROUGH_WHITE, FILM_BURN, FILM_FLASH, GENTLE_DISSOLVE, GLITCH_TRANSITION, HARD_CUT, INK_SPREAD, INK_WIPE, IRIS_REVEAL, IRIS_WIPE, LIGHT_LEAK, LIGHT_LEAK_FLASH, NONE, PAPER_TEAR, QUICK_PUSH, SLIDE_SHADOW, SMOKE_DISSOLVE, TORN_CENTER_SPLIT, WHIP_PAN, ZOOM_BLUR, ZOOM_THROUGH.

caption_presets: Hormozi Style, MrBeast / Viral Pop, Karaoke Highlight, Neon Glow, Minimal Cinematic, Highlighter Box, Documentary Highlight, Clean Subtitle, Typewriter, Off.

styles: CLEAN_DOC, DARK_PSYCHOLOGY, FINANCE_PREMIUM, HISTORY_ARCHIVE, HISTORY_MEDIEVAL, LEGACY, MYSTERY_NOIR, REEL_CLEAN_LIGHT, SCIENCE_CLEAN, TECH_MODERN.

looks: AGED_PARCHMENT, ALBUMEN_1880S, CLEAN, CLEAN_DOC, DARK_NOIR, FINANCE_PREMIUM, KODAK_1970S, NITRATE_1930S, PRESS_PHOTO_1950S, SCIENCE_CLEAN, SILENT_FILM_1910S, TECH_MODERN, VHS_1980S.

easings: EASE_IN, EASE_IN_OUT, EASE_OUT, LINEAR.

overlay_types: DATE_STAMP, HIGHLIGHT_BOX, HOOK_CARD, LOWER_THIRD, MAP_ROUTE, PHOTO_NOTE, TEXT.

overlay_styles: ARCHIVE, ARROW, CIRCLE, MODERN, PLAIN, RECT.

fonts: Montserrat, Anton, Luckiest Guy, Bangers, Poppins, Bebas Neue, Arial, Segoe UI, Georgia, Consolas, DejaVu Sans, Liberation Sans, Source Code Pro, Inconsolata, Bitstream Vera Sans, Inter, Inter Black, Inter Bold, Inter Medium, Oswald, Playfair Display, Noto Nastaliq Urdu, Caveat.

sfx: BRUSH_SCRATCH, CAMERA_SHUTTER, FILM_CLICK, IMPACT_LOW, IMPACT_SOFT, INK_SPLASH, PAGE_TURN, PAPER_SLIDE, RISER_SHORT, STAMP_THUD, SWIPE_SOFT, TICK_SOFT, TYPEWRITER_KEY, WHOOSH_FAST, WHOOSH_SOFT.


## Object fields

$.format — required: orientation, aspect_ratio; optional: none.

$.direction — required: none; optional: duck_db, energy, finish, music_level, sfx_enabled, transition_frequency, voice_level.

$.direction.finish — required: none; optional: contrast, grain, vignette.

$ — required: audio_duration, caption_style, captions, fps, project_title, scenes, schema, words; optional: audio, direction, ending, format, moments, overlays, style.

$.style — required: none; optional: look, look_intensity, preset, seed.

$.audio — required: none; optional: master, sfx.

$.audio.sfx — required: none; optional: gain_db.

$.audio.master — required: none; optional: mode, target_lufs, true_peak_db.

$.caption_style — required: enabled, highlight_current_word; optional: accent_color, animation, background, emphasis, font, max_lines, position, preset, size, text_color.

$.scenes[] — required: end, id, image_id, start, voice_text; optional: look_override, motion, motion_config, sfx, transition, transition_config.

$.scenes[].motion_config — required: none; optional: blur, ease, focus, zoom_from, zoom_to.

$.scenes[].motion_config.focus — required: x, y; optional: none.

$.scenes[].transition_config — required: none; optional: direction, ease, frames, sfx, type.

$.scenes[].sfx[] — required: id; optional: gain_db, offset_ms, pitch_cents, variant.

$.scenes[].look_override — required: none; optional: intensity, look.

$.overlays[] — required: id, type, start, end; optional: h, points, scene_id, style, text, text2, w, x, y.

$.ending — required: none; optional: frames, mode.

$.words[] — required: end, index, start, text; optional: none.

$.captions[] — required: end, id, start, text, word_end_index, word_start_index; optional: none.


D3 EARLY SEED RULE: style.seed must be an integer from 0 to 2147483647. Invalid values reject at $.style.seed with exactly: must be an integer between 0 and 2147483647. This supersedes the historical signed-64-bit parse-only behavior.

MODE HOUSE RULES (informational, never import rejection):
(creative rules; the tool enforces none of them)
- B = scene count minus 1. FANCY set: BRUSH_WIPE, BURN_LIGHT, DISSOLVE_BLUR, FILM_BURN, FILM_FLASH, GLITCH_TRANSITION, INK_SPREAD, INK_WIPE, IRIS_REVEAL, IRIS_WIPE, LIGHT_LEAK, LIGHT_LEAK_FLASH, PAPER_TEAR, QUICK_PUSH, SLIDE_SHADOW, SMOKE_DISSOLVE, TORN_CENTER_SPLIT, WHIP_PAN, ZOOM_BLUR, ZOOM_THROUGH. SUBTLE set: CROSSFADE, DISSOLVE, FADE_THROUGH_BLACK, FADE_THROUGH_WHITE, GENTLE_DISSOLVE, HARD_CUT, NONE. A non-cut is any boundary whose transition is not HARD_CUT or NONE.
- STANDARD: at least 60 percent of boundaries are HARD_CUT or NONE; non-cuts at most floor(0.40 x B); fancy at most the smaller of floor(B x p) and the generated director budget (p is 0.25 for HIGH_ENERGY, else 0.15); no adjacent fancy; same fancy type at most 2.
- RICH (default for vertical videos under 3 minutes): non-cuts between 55 and 70 percent of B; fancy between ceil(0.20 x B) and floor(0.25 x B); no adjacent fancy; same fancy type at most 3.
- MAX (when the user asks for a transition on every image): every boundary after scene 001 is a non-cut; fancy at most floor(0.35 x B); no adjacent fancy; same fancy type at most 3; short effects (4 to 8 frames) on fast beats.
- All modes: scene 001 is HARD_CUT; every non-cut has a transition_config with type equal to the scene transition and an integer frames value from 4 to 30; both neighbouring scenes need at least 9 frames at 30 fps (18 at 60 fps); no empty motion_config or transition_config objects; no repeated type on consecutive non-cuts.
- The tool classifies a package as STANDARD, RICH, MAX or NONE using exactly these thresholds. If the tool's real FANCY or SUBTLE set differs from the lists above, Codex reports the difference as a SYNC ISSUE.

The classifier checks MAX, RICH, then STANDARD; no boundaries means NONE. Consecutive means adjacent boundaries. Story relevance and identifying fast beats need human/author review. It reports measurable violations and never changes effects.

COPY ERRORS FORMAT:
ATS_PACKAGE_V2 correction request. Fix only the paths below and return one complete corrected JSON object. Preserve all other fields.
path | rule | value | expected | severity
One diagnostic per line; escape embedded line breaks/pipes. SKIP and WARN do not reject. The original parser and timeline creation remain the final acceptance oracle.

UTILIZATION LINE:
Mode M: N non-cut of B, F fancy, D date cards, S sound cues, O overlays, features unused: X.

MOTION ALIASES:
IMPACT_PUNCH_IN: resolves to TINY_PUNCH_IN; zoom 1.0 to 1.055. Accepted alias; prefer the resolved name for clear authoring.
SLOW_PULL_OUT: resolves to SLOW_ZOOM_OUT; zoom 1.085 to 1.0. Accepted alias; prefer the resolved name for clear authoring.
STATIC_HOLD: resolves to STATIC; zoom 1.0 to 1.0. Accepted alias; prefer the resolved name for clear authoring.
SUBTLE_PARALLAX: resolves to SLOW_PUSH_IN; zoom 1.0 to 1.085. No real depth. Prefer SLOW_PUSH_IN; omission of this alias is a HOUSE RULE.

MOTION CONFIG:
zoom_from: Crop zoom at scene start; 1 means the base Fill/Fit crop; 2 means half its dimensions. Overrides the chosen motion path zoom start.
zoom_to: Crop zoom at scene end, interpolated with ease; overrides path zoom end. 1 to 2.
ease: Controls progress of zoom and pan. LINEAR is constant progress; EASE_IN/EASE_OUT/EASE_IN_OUT shape acceleration. TINY_PUNCH_IN with no explicit ease reaches its zoom over the first 35 percent.
focus: Both x and y required, normalized in the full source image. Sets crop center before pan offsets and edge clamping; it does not track an object.
blur: Temporal camera-crop sampling, 0 to 1: zero forces one sample; positive values use max of 2 and Python round of 4 times blur, up to 4 subframe samples. Blends nearby camera positions; does not animate objects.
example: {"motion":"SLOW_PUSH_IN","motion_config":{"zoom_from":1.03,"zoom_to":1.12,"ease":"EASE_IN_OUT","focus":{"x":0.5,"y":0.4},"blur":0.05}}

TRANSITION CONFIG:
direction: LEFT/RIGHT use horizontal travel, UP/DOWN vertical travel for QUICK_PUSH, WHIP_PAN and SLIDE_SHADOW. Other effects ignore this field. AUTO resolves during planning; supply an explicit direction for repeatability.
ease: Applies to transition progress before blending/masking, without changing frame count.
example: {"transition":"WHIP_PAN","transition_config":{"type":"WHIP_PAN","frames":7,"direction":"LEFT","ease":"EASE_OUT"}}

STYLE PRESETS:
V2 defaults look_intensity to zero, so choosing only a style preset does not activate color grading. Author an explicit nonzero intensity or scene look_override when wanted. Stored music/ambience, palettes and caption hints are legacy preset metadata, not permission to add unsupported JSON or override explicit transitions/caption choices.
CLEAN_DOC: Selects the CLEAN_DOC look: Light source softening, without warmth, monochrome blend, grain or vignette from this look.
DARK_PSYCHOLOGY: Selects the DARK_NOIR look: Cool blue tint, strong monochrome blend, grain and darkened edges.
FINANCE_PREMIUM: Selects the FINANCE_PREMIUM look: Slight cool tint with subtle monochrome blend, grain and edge shading.
HISTORY_ARCHIVE: Selects the AGED_PARCHMENT look: Warm tint, light monochrome blend, grain and darkened edges; no paper image is generated.
HISTORY_MEDIEVAL: Selects the AGED_PARCHMENT look: Warm tint, light monochrome blend, grain and darkened edges; no paper image is generated.
LEGACY: Selects the CLEAN look: No look grading.
MYSTERY_NOIR: Selects the DARK_NOIR look: Cool blue tint, strong monochrome blend, grain and darkened edges.
REEL_CLEAN_LIGHT: Selects the CLEAN look: No look grading.
SCIENCE_CLEAN: Selects the SCIENCE_CLEAN look: Very light cool tint, grain and edge shading.
TECH_MODERN: Selects the TECH_MODERN look: Cool tint, small monochrome blend, light grain and edge shading.

LOOKS:
Intensity scales the treatment. Soften is applied separately before camera movement by blending a quarter-resolution source, with blend capped at 0.35. CLEAN or intensity zero bypasses color grading. Weave requires shake, which V2 product settings disable. Explicit direction.finish is a separate finishing stage. Historical IDs describe an effect, not authentic archival provenance.
AGED_PARCHMENT: Warm tint, light monochrome blend, grain and darkened edges; no paper image is generated.
ALBUMEN_1880S: Strong warm tint with monochrome blend, grain and darkened edges.
CLEAN: No look grading.
CLEAN_DOC: Light source softening, without warmth, monochrome blend, grain or vignette from this look.
DARK_NOIR: Cool blue tint, strong monochrome blend, grain and darkened edges.
FINANCE_PREMIUM: Slight cool tint with subtle monochrome blend, grain and edge shading.
KODAK_1970S: Warm color treatment with light desaturation, grain and edge shading.
NITRATE_1930S: Strong monochrome film treatment, slight warmth, grain, dark edges and seeded flicker.
PRESS_PHOTO_1950S: Moderate monochrome blend, slight warmth, grain and edge shading.
SCIENCE_CLEAN: Very light cool tint, grain and edge shading.
SILENT_FILM_1910S: Nearly monochrome film treatment with grain, dark edges and seeded flicker.
TECH_MODERN: Cool tint, small monochrome blend, light grain and edge shading.
VHS_1980S: Cool/desaturated treatment with grain, purple tint and moving horizontal scanlines.

CREATOR CAPTION CHARACTER:
Hormozi Style: Bold uppercase, thick black outline, shadow and active-word pop; selected or emphasized words use accent.
MrBeast / Viral Pop: Bold uppercase, heavy outline/shadow, pop-bounce with slight rotation; selected or emphasized words use accent.
Karaoke Highlight: Dim inactive words, active word at supplied text color on a rounded accent box; no extra emphasis.
Neon Glow: Uppercase white text with layered accent glow and fade/scale; no active-word recolor or extra emphasis.
Minimal Cinematic: Sentence case, soft shadow and fade upward; no active accent or emphasis.
Highlighter Box: Dark letters on a white rounded box, active accent box and pop; supplied text color/background ignored.

SFX BUILT-IN FALLBACKS (suggested uses are HOUSE RULES):
BRUSH_SCRATCH: 0.5 seconds. Noise swell; a brush or document reveal.
CAMERA_SHUTTER: 0.2 seconds. Short synthetic noise click; a photo reveal.
FILM_CLICK: 0.2 seconds. Decaying 200 Hz tone/noise tick; an archive cut.
IMPACT_LOW: 0.58 seconds. Decaying low 50 Hz impact; a reveal.
IMPACT_SOFT: 0.46 seconds. Shorter decaying low impact; restrained emphasis.
INK_SPLASH: 0.2 seconds. Synthetic noise transient; an ink reveal, not recorded liquid.
PAGE_TURN: 0.62 seconds. Noise swell; page movement.
PAPER_SLIDE: 0.4 seconds. Short noise swell; document movement.
RISER_SHORT: 0.7 seconds. Noise swell; anticipation, not a pitched orchestral rise.
STAMP_THUD: 0.2 seconds. Decaying 200 Hz tone/noise tap; a date or document stamp.
SWIPE_SOFT: 0.36 seconds. Brief noise swell; a gentle swipe.
TICK_SOFT: 0.2 seconds. Short noise transient; a small evidence beat.
TYPEWRITER_KEY: 0.2 seconds. Short synthetic noise click; a text reveal.
WHOOSH_FAST: 0.45 seconds. Noise swell; fast travel or action.
WHOOSH_SOFT: 0.55 seconds. Longer noise swell; a gentler change of scene.

HINDI FIT GUIDANCE: Repeated widest tested independent letter; reserve peak 1.1 pop scale and stroke; two lines configured. Spaces and joined/combined graphemes have different widths. Creator auto-shrink can fit longer strings. These are conservative measured standalone-letter counts, not a universal character maximum. Use Poppins, measure actual text and inspect the export. Other presets have different nominal sizes.
9:16, Hormozi/Poppins ExtraBold, size 100: 7 widest-test standalone letters per nominal line before auto-shrink.
9:16, Hormozi/Poppins ExtraBold, size 120: 6 widest-test standalone letters per nominal line before auto-shrink.
9:16, Hormozi/Poppins ExtraBold, size 140: 5 widest-test standalone letters per nominal line before auto-shrink.
16:9, Hormozi/Poppins ExtraBold, size 100: 13 widest-test standalone letters per nominal line before auto-shrink.
16:9, Hormozi/Poppins ExtraBold, size 120: 11 widest-test standalone letters per nominal line before auto-shrink.
16:9, Hormozi/Poppins ExtraBold, size 140: 10 widest-test standalone letters per nominal line before auto-shrink.
1:1, Hormozi/Poppins ExtraBold, size 100: 14 widest-test standalone letters per nominal line before auto-shrink.
1:1, Hormozi/Poppins ExtraBold, size 120: 11 widest-test standalone letters per nominal line before auto-shrink.
1:1, Hormozi/Poppins ExtraBold, size 140: 10 widest-test standalone letters per nominal line before auto-shrink.
4:5, Hormozi/Poppins ExtraBold, size 100: 11 widest-test standalone letters per nominal line before auto-shrink.
4:5, Hormozi/Poppins ExtraBold, size 120: 9 widest-test standalone letters per nominal line before auto-shrink.
4:5, Hormozi/Poppins ExtraBold, size 140: 7 widest-test standalone letters per nominal line before auto-shrink.

D4/D5 WARNINGS: creator caption layout is left to right; multiword right-to-left order will be wrong. Missing native glyphs produce a font-specific warning and recommendation. Fallback may display characters; it does not certify layout. No rendering changes are made.
