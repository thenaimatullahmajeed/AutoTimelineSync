# Candidate error catalogue

Contract ATS_SYNC_2026-10-B. Exact observed messages; dynamic completeness remains UNKNOWN.

## null:$.schema

Path: ['$.schema']

```text
$.schema: expected "ATS_PACKAGE_V2" for ATS 3.0. Ask ChatGPT to update this package.
```

## null:$.project_title

Path: ['$.v1_contract']

```text
$.v1_contract: project_title must be nonempty text.
```

## null:$.audio_duration

Path: ['$.v1_contract']

```text
$.v1_contract: audio_duration must be a number.
```

## null:$.fps

Path: ['$.v1_contract']

```text
$.v1_contract: fps must be an integer.
```

## null:$.format

Path: ['$.format', '$.format.orientation']

```text
V2 validation failed:
$.format: must be an object
$.format.orientation: must be one of HORIZONTAL, PORTRAIT, SQUARE, VERTICAL
```

## unknown:$.format

Path: ['$.format.INVENTED']

```text
V2 validation failed:
$.format.INVENTED: unknown field
```

## null:$.format.orientation

Path: ['$.format.orientation']

```text
V2 validation failed:
$.format.orientation: must be one of HORIZONTAL, PORTRAIT, SQUARE, VERTICAL
```

## null:$.format.aspect_ratio

Path: ['$.format.aspect_ratio']

```text
V2 validation failed:
$.format.aspect_ratio: expected 9:16
```

## null:$.direction

Path: ['$.direction']

```text
V2 validation failed:
$.direction: must be an object
```

## unknown:$.direction

Path: ['$.direction.INVENTED']

```text
V2 validation failed:
$.direction.INVENTED: unknown field
```

## null:$.direction.energy

Path: ['$.direction.energy']

```text
V2 validation failed:
$.direction.energy: must be one of BALANCED, HIGH_ENERGY, SUBTLE
```

## null:$.direction.finish

Path: ['$.direction.finish']

```text
V2 validation failed:
$.direction.finish: must be an object
```

## unknown:$.direction.finish

Path: ['$.direction.finish.INVENTED']

```text
V2 validation failed:
$.direction.finish.INVENTED: unknown field
```

## null:$.direction.finish.grain

Path: ['$.direction.finish.grain']

```text
V2 validation failed:
$.direction.finish.grain: must be a number between 0 and 1
```

## null:$.direction.finish.vignette

Path: ['$.direction.finish.vignette']

```text
V2 validation failed:
$.direction.finish.vignette: must be a number between 0 and 1
```

## null:$.direction.finish.contrast

Path: ['$.direction.finish.contrast']

```text
V2 validation failed:
$.direction.finish.contrast: must be a number between 0 and 1
```

## null:$.direction.voice_level

Path: ['$.direction.voice_level']

```text
V2 validation failed:
$.direction.voice_level: must be a number between 0 and 1
```

## null:$.direction.music_level

Path: ['$.direction.music_level']

```text
V2 validation failed:
$.direction.music_level: must be a number between 0 and 1
```

## null:$.direction.duck_db

Path: ['$.direction.duck_db']

```text
V2 validation failed:
$.direction.duck_db: must be a number between -30 and 0
```

## null:$.direction.sfx_enabled

Path: ['$.direction.sfx_enabled']

```text
V2 validation failed:
$.direction.sfx_enabled: must be true or false
```

## null:$.direction.transition_frequency

Path: ['$.direction.transition_frequency']

```text
V2 validation failed:
$.direction.transition_frequency: must be a number between 0 and 1
```

## null:$.scenes

Path: []

```text
'NoneType' object is not iterable
```

## null:$.scenes[0]

Path: ['$.scenes[0]', '$.scenes[0].end', '$.scenes[0].start', '$.scenes[0].voice_text', '$.scenes[0].image_id', '$.scenes[0].id']

```text
V2 validation failed:
$.scenes[0]: must be an object
$.scenes[0].end: required field is missing
$.scenes[0].start: required field is missing
$.scenes[0].voice_text: required field is missing
$.scenes[0].image_id: required field is missing
$.scenes[0].id: required field is missing
```

## unknown:$.scenes[0]

Path: ['$.scenes[0].INVENTED']

```text
V2 validation failed:
$.scenes[0].INVENTED: unknown field
```

## null:$.scenes[0].id

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 id must be zero-padded numeric text such as 001.
```

## null:$.scenes[0].image_id

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 image_id must match its id "001".
```

## null:$.scenes[0].start

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 start must be a number.
```

## null:$.scenes[0].end

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 end must be a number.
```

## null:$.scenes[0].voice_text

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 voice_text must be text.
```

## null:$.scenes[0].motion

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 has unsupported motion: None.
```

## null:$.scenes[0].transition

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 has unsupported transition: None.
```

## null:$.scenes[0].motion_config

Path: ['$.scenes[0].motion_config']

```text
V2 validation failed:
$.scenes[0].motion_config: must be an object
```

## unknown:$.scenes[0].motion_config

Path: ['$.scenes[0].motion_config.INVENTED']

```text
V2 validation failed:
$.scenes[0].motion_config.INVENTED: unknown field
```

## null:$.scenes[0].motion_config.focus

Path: ['$.scenes[0].motion_config.focus', '$.scenes[0].motion_config.focus.x', '$.scenes[0].motion_config.focus.y']

```text
V2 validation failed:
$.scenes[0].motion_config.focus: must be an object
$.scenes[0].motion_config.focus.x: required field is missing
$.scenes[0].motion_config.focus.y: required field is missing
```

## unknown:$.scenes[0].motion_config.focus

Path: ['$.scenes[0].motion_config.focus.INVENTED']

```text
V2 validation failed:
$.scenes[0].motion_config.focus.INVENTED: unknown field
```

## null:$.scenes[0].motion_config.focus.x

Path: ['$.scenes[0].motion_config.focus.x']

```text
V2 validation failed:
$.scenes[0].motion_config.focus.x: must be a number between 0 and 1
```

## null:$.scenes[0].motion_config.focus.y

Path: ['$.scenes[0].motion_config.focus.y']

```text
V2 validation failed:
$.scenes[0].motion_config.focus.y: must be a number between 0 and 1
```

## null:$.scenes[1]

Path: ['$.scenes[1]', '$.scenes[1].end', '$.scenes[1].start', '$.scenes[1].voice_text', '$.scenes[1].image_id', '$.scenes[1].id', '$.overlays[0].scene_id']

```text
V2 validation failed:
$.scenes[1]: must be an object
$.scenes[1].end: required field is missing
$.scenes[1].start: required field is missing
$.scenes[1].voice_text: required field is missing
$.scenes[1].image_id: required field is missing
$.scenes[1].id: required field is missing
$.overlays[0].scene_id: must reference an existing scene
```

## unknown:$.scenes[1]

Path: ['$.scenes[1].INVENTED']

```text
V2 validation failed:
$.scenes[1].INVENTED: unknown field
```

## null:$.scenes[1].id

Path: ['$.overlays[0].scene_id']

```text
V2 validation failed:
$.overlays[0].scene_id: must reference an existing scene
```

## null:$.scenes[1].image_id

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 image_id must match its id "002".
```

## null:$.scenes[1].start

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 start must be a number.
```

## null:$.scenes[1].end

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 end must be a number.
```

## null:$.scenes[1].voice_text

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 voice_text must be text.
```

## null:$.scenes[1].motion

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 has unsupported motion: None.
```

## null:$.scenes[1].transition

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 has unsupported transition: None.
```

## null:$.scenes[1].transition_config

Path: ['$.scenes[1].transition_config']

```text
V2 validation failed:
$.scenes[1].transition_config: must be an object
```

## unknown:$.scenes[1].transition_config

Path: ['$.scenes[1].transition_config.INVENTED']

```text
V2 validation failed:
$.scenes[1].transition_config.INVENTED: unknown field
```

## null:$.scenes[1].transition_config.type

Path: ['$.scenes[1].transition_config.type']

```text
V2 validation failed:
$.scenes[1].transition_config.type: must be one of BRUSH_WIPE, BURN_LIGHT, CROSSFADE, DISSOLVE, DISSOLVE_BLUR, FADE_THROUGH_BLACK, FADE_THROUGH_WHITE, FILM_BURN, FILM_FLASH, GENTLE_DISSOLVE, GLITCH_TRANSITION, HARD_CUT, INK_SPREAD, INK_WIPE, IRIS_REVEAL, IRIS_WIPE, LIGHT_LEAK, LIGHT_LEAK_FLASH, NONE, PAPER_TEAR, QUICK_PUSH, SLIDE_SHADOW, SMOKE_DISSOLVE, TORN_CENTER_SPLIT, WHIP_PAN, ZOOM_BLUR, ZOOM_THROUGH
```

## null:$.scenes[1].transition_config.frames

Path: ['$.scenes[1].transition_config.frames']

```text
V2 validation failed:
$.scenes[1].transition_config.frames: must be a integer between 4 and 30
```

## null:$.scenes[1].transition_config.direction

Path: ['$.scenes[1].transition_config.direction']

```text
V2 validation failed:
$.scenes[1].transition_config.direction: must be one of AUTO, DOWN, LEFT, RIGHT, UP
```

## null:$.scenes[1].transition_config.ease

Path: ['$.scenes[1].transition_config.ease']

```text
V2 validation failed:
$.scenes[1].transition_config.ease: must be one of EASE_IN, EASE_IN_OUT, EASE_OUT, LINEAR
```

## null:$.scenes[1].transition_config.sfx

Path: ['$.scenes[1].transition_config.sfx']

```text
V2 validation failed:
$.scenes[1].transition_config.sfx: must be one of BRUSH_SCRATCH, CAMERA_SHUTTER, FILM_CLICK, IMPACT_LOW, IMPACT_SOFT, INK_SPLASH, NONE, PAGE_TURN, PAPER_SLIDE, RISER_SHORT, STAMP_THUD, SWIPE_SOFT, TICK_SOFT, TYPEWRITER_KEY, WHOOSH_FAST, WHOOSH_SOFT
```

## null:$.scenes[1].motion_config

Path: ['$.scenes[1].motion_config']

```text
V2 validation failed:
$.scenes[1].motion_config: must be an object
```

## unknown:$.scenes[1].motion_config

Path: ['$.scenes[1].motion_config.INVENTED']

```text
V2 validation failed:
$.scenes[1].motion_config.INVENTED: unknown field
```

## null:$.scenes[1].motion_config.focus

Path: ['$.scenes[1].motion_config.focus', '$.scenes[1].motion_config.focus.x', '$.scenes[1].motion_config.focus.y']

```text
V2 validation failed:
$.scenes[1].motion_config.focus: must be an object
$.scenes[1].motion_config.focus.x: required field is missing
$.scenes[1].motion_config.focus.y: required field is missing
```

## unknown:$.scenes[1].motion_config.focus

Path: ['$.scenes[1].motion_config.focus.INVENTED']

```text
V2 validation failed:
$.scenes[1].motion_config.focus.INVENTED: unknown field
```

## null:$.scenes[1].motion_config.focus.x

Path: ['$.scenes[1].motion_config.focus.x']

```text
V2 validation failed:
$.scenes[1].motion_config.focus.x: must be a number between 0 and 1
```

## null:$.scenes[1].motion_config.focus.y

Path: ['$.scenes[1].motion_config.focus.y']

```text
V2 validation failed:
$.scenes[1].motion_config.focus.y: must be a number between 0 and 1
```

## null:$.scenes[1].motion_config.zoom_from

Path: ['$.scenes[1].motion_config.zoom_from']

```text
V2 validation failed:
$.scenes[1].motion_config.zoom_from: must be a number between 1 and 2
```

## null:$.scenes[1].motion_config.zoom_to

Path: ['$.scenes[1].motion_config.zoom_to']

```text
V2 validation failed:
$.scenes[1].motion_config.zoom_to: must be a number between 1 and 2
```

## null:$.scenes[1].motion_config.blur

Path: ['$.scenes[1].motion_config.blur']

```text
V2 validation failed:
$.scenes[1].motion_config.blur: must be a number between 0 and 1
```

## null:$.scenes[1].motion_config.ease

Path: ['$.scenes[1].motion_config.ease']

```text
V2 validation failed:
$.scenes[1].motion_config.ease: must be one of EASE_IN, EASE_IN_OUT, EASE_OUT, LINEAR
```

## null:$.scenes[1].sfx

Path: ['$.scenes[1].sfx']

```text
V2 validation failed:
$.scenes[1].sfx: must be an array
```

## null:$.scenes[1].sfx[0]

Path: ['$.scenes[1].sfx[0]', '$.scenes[1].sfx[0].id']

```text
V2 validation failed:
$.scenes[1].sfx[0]: must be an object
$.scenes[1].sfx[0].id: required field is missing
```

## unknown:$.scenes[1].sfx[0]

Path: ['$.scenes[1].sfx[0].INVENTED']

```text
V2 validation failed:
$.scenes[1].sfx[0].INVENTED: unknown field
```

## null:$.scenes[1].sfx[0].id

Path: ['$.scenes[1].sfx[0].id']

```text
V2 validation failed:
$.scenes[1].sfx[0].id: must be one of BRUSH_SCRATCH, CAMERA_SHUTTER, FILM_CLICK, IMPACT_LOW, IMPACT_SOFT, INK_SPLASH, PAGE_TURN, PAPER_SLIDE, RISER_SHORT, STAMP_THUD, SWIPE_SOFT, TICK_SOFT, TYPEWRITER_KEY, WHOOSH_FAST, WHOOSH_SOFT
```

## null:$.scenes[1].sfx[0].variant

Path: ['$.scenes[1].sfx[0].variant']

```text
V2 validation failed:
$.scenes[1].sfx[0].variant: must be a integer between 1 and 9
```

## null:$.scenes[1].sfx[0].gain_db

Path: ['$.scenes[1].sfx[0].gain_db']

```text
V2 validation failed:
$.scenes[1].sfx[0].gain_db: must be a number between -30 and 6
```

## null:$.scenes[1].sfx[0].pitch_cents

Path: ['$.scenes[1].sfx[0].pitch_cents']

```text
V2 validation failed:
$.scenes[1].sfx[0].pitch_cents: must be a number between -200 and 200
```

## null:$.scenes[1].sfx[0].offset_ms

Path: ['$.scenes[1].sfx[0].offset_ms']

```text
V2 validation failed:
$.scenes[1].sfx[0].offset_ms: must be a number between -300 and 300
```

## null:$.scenes[1].look_override

Path: ['$.scenes[1].look_override']

```text
V2 validation failed:
$.scenes[1].look_override: must be an object
```

## unknown:$.scenes[1].look_override

Path: ['$.scenes[1].look_override.INVENTED']

```text
V2 validation failed:
$.scenes[1].look_override.INVENTED: unknown field
```

## null:$.scenes[1].look_override.look

Path: ['$.scenes[1].look_override.look']

```text
V2 validation failed:
$.scenes[1].look_override.look: must be one of AGED_PARCHMENT, ALBUMEN_1880S, CLEAN, CLEAN_DOC, DARK_NOIR, FINANCE_PREMIUM, KODAK_1970S, NITRATE_1930S, PRESS_PHOTO_1950S, SCIENCE_CLEAN, SILENT_FILM_1910S, TECH_MODERN, VHS_1980S
```

## null:$.scenes[1].look_override.intensity

Path: ['$.scenes[1].look_override.intensity']

```text
V2 validation failed:
$.scenes[1].look_override.intensity: must be a number between 0 and 1
```

## null:$.words

Path: ['$.caption_style.emphasis[0]']

```text
V2 validation failed:
$.caption_style.emphasis[0]: word index does not exist
```

## unknown:$.words[0]

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 1 contains unsupported field(s): INVENTED.
```

## null:$.words[0].start

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 1 start must be a number.
```

## null:$.words[0].end

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 1 end must be a number.
```

## null:$.words[0].text

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 1 text must be nonempty.
```

## null:$.words[1]

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 must be an object.
```

## unknown:$.words[1]

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 contains unsupported field(s): INVENTED.
```

## null:$.words[1].index

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 index must be an integer.
```

## null:$.words[1].start

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 start must be a number.
```

## null:$.words[1].end

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 end must be a number.
```

## null:$.words[1].text

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 text must be nonempty.
```

## null:$.captions

Path: ['$.v1_contract']

```text
$.v1_contract: captions must be an array.
```

## null:$.captions[0]

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 must be an object.
```

## unknown:$.captions[0]

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 contains unsupported field(s): INVENTED.
```

## null:$.captions[0].id

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 id should be "001".
```

## null:$.captions[0].start

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 start must be a number.
```

## null:$.captions[0].end

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 end must be a number.
```

## null:$.captions[0].text

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 text must be nonempty.
```

## null:$.captions[0].word_start_index

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 word_start_index must be an integer.
```

## null:$.captions[0].word_end_index

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 word_end_index must be an integer.
```

## null:$.captions[1]

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 must be an object.
```

## unknown:$.captions[1]

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 contains unsupported field(s): INVENTED.
```

## null:$.captions[1].id

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 id should be "002".
```

## null:$.captions[1].start

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 start must be a number.
```

## null:$.captions[1].end

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 end must be a number.
```

## null:$.captions[1].text

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 text must be nonempty.
```

## null:$.captions[1].word_start_index

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 word_start_index must be an integer.
```

## null:$.captions[1].word_end_index

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 002 word_end_index must be an integer.
```

## null:$.caption_style

Path: ['$.caption_style', '$.caption_style.highlight_current_word', '$.caption_style.enabled']

```text
V2 validation failed:
$.caption_style: must be an object
$.caption_style.highlight_current_word: required field is missing
$.caption_style.enabled: required field is missing
```

## unknown:$.caption_style

Path: ['$.caption_style.INVENTED']

```text
V2 validation failed:
$.caption_style.INVENTED: unknown field
```

## null:$.caption_style.enabled

Path: ['$.v1_contract']

```text
$.v1_contract: caption_style values must be true or false.
```

## null:$.caption_style.preset

Path: ['$.caption_style.preset']

```text
V2 validation failed:
$.caption_style.preset: must be one of Clean Subtitle, Documentary Highlight, Highlighter Box, Hormozi Style, Karaoke Highlight, Minimal Cinematic, MrBeast / Viral Pop, Neon Glow, Off, Typewriter
```

## null:$.caption_style.font

Path: ['$.caption_style.font']

```text
V2 validation failed:
$.caption_style.font: must be one of Anton, Arial, Bangers, Bebas Neue, Bitstream Vera Sans, Caveat, Consolas, DejaVu Sans, Georgia, Inconsolata, Inter, Inter Black, Inter Bold, Inter Medium, Liberation Sans, Luckiest Guy, Montserrat, Noto Nastaliq Urdu, Oswald, Playfair Display, Poppins, Segoe UI, Source Code Pro
```

## null:$.caption_style.background

Path: ['$.caption_style.background']

```text
V2 validation failed:
$.caption_style.background: must be one of Dark Brush, None, Paper, Shadow Only, Solid Box
```

## null:$.caption_style.size

Path: ['$.caption_style.size']

```text
V2 validation failed:
$.caption_style.size: must be a integer between 50 and 180
```

## null:$.caption_style.position

Path: ['$.caption_style.position']

```text
V2 validation failed:
$.caption_style.position: must be one of Bottom, Center, Top
```

## null:$.caption_style.max_lines

Path: ['$.caption_style.max_lines']

```text
V2 validation failed:
$.caption_style.max_lines: must be a integer between 1 and 2
```

## null:$.caption_style.text_color

Path: ['$.caption_style.text_color']

```text
V2 validation failed:
$.caption_style.text_color: expected #RRGGBB
```

## null:$.caption_style.accent_color

Path: ['$.caption_style.accent_color']

```text
V2 validation failed:
$.caption_style.accent_color: expected #RRGGBB
```

## null:$.caption_style.emphasis

Path: ['$.caption_style.emphasis']

```text
V2 validation failed:
$.caption_style.emphasis: must be an array
```

## null:$.caption_style.emphasis[0]

Path: ['$.caption_style.emphasis[0]']

```text
V2 validation failed:
$.caption_style.emphasis[0]: must be a integer between 0 and 1e+09
```

## null:$.caption_style.animation

Path: ['$.caption_style.animation']

```text
V2 validation failed:
$.caption_style.animation: must be one of FADE, NONE, POP
```

## null:$.style

Path: ['$.style']

```text
V2 validation failed:
$.style: must be an object
```

## unknown:$.style

Path: ['$.style.INVENTED']

```text
V2 validation failed:
$.style.INVENTED: unknown field
```

## null:$.style.preset

Path: ['$.style.preset']

```text
V2 validation failed:
$.style.preset: must be one of CLEAN_DOC, DARK_PSYCHOLOGY, FINANCE_PREMIUM, HISTORY_ARCHIVE, HISTORY_MEDIEVAL, LEGACY, MYSTERY_NOIR, REEL_CLEAN_LIGHT, SCIENCE_CLEAN, TECH_MODERN
```

## null:$.style.look

Path: ['$.style.look']

```text
V2 validation failed:
$.style.look: must be one of AGED_PARCHMENT, ALBUMEN_1880S, CLEAN, CLEAN_DOC, DARK_NOIR, FINANCE_PREMIUM, KODAK_1970S, NITRATE_1930S, PRESS_PHOTO_1950S, SCIENCE_CLEAN, SILENT_FILM_1910S, TECH_MODERN, VHS_1980S
```

## null:$.style.look_intensity

Path: ['$.style.look_intensity']

```text
V2 validation failed:
$.style.look_intensity: must be a number between 0 and 1
```

## null:$.audio

Path: ['$.audio']

```text
V2 validation failed:
$.audio: must be an object
```

## unknown:$.audio

Path: ['$.audio.INVENTED']

```text
V2 validation failed:
$.audio.INVENTED: unknown field
```

## null:$.audio.master

Path: ['$.audio.master']

```text
V2 validation failed:
$.audio.master: must be an object
```

## unknown:$.audio.master

Path: ['$.audio.master.INVENTED']

```text
V2 validation failed:
$.audio.master.INVENTED: unknown field
```

## null:$.audio.master.mode

Path: ['$.audio.master.mode']

```text
V2 validation failed:
$.audio.master.mode: must be one of LIMIT_ONLY, LOUDNORM, OFF
```

## null:$.audio.master.target_lufs

Path: ['$.audio.master.target_lufs']

```text
V2 validation failed:
$.audio.master.target_lufs: must be a number between -23 and -9
```

## null:$.audio.master.true_peak_db

Path: ['$.audio.master.true_peak_db']

```text
V2 validation failed:
$.audio.master.true_peak_db: must be a number between -3 and -0.5
```

## null:$.audio.sfx

Path: ['$.audio.sfx']

```text
V2 validation failed:
$.audio.sfx: must be an object
```

## unknown:$.audio.sfx

Path: ['$.audio.sfx.INVENTED']

```text
V2 validation failed:
$.audio.sfx.INVENTED: unknown field
```

## null:$.audio.sfx.gain_db

Path: ['$.audio.sfx.gain_db']

```text
V2 validation failed:
$.audio.sfx.gain_db: must be a number between -12 and 6
```

## null:$.overlays

Path: ['$.overlays']

```text
V2 validation failed:
$.overlays: must be an array
```

## null:$.overlays[0]

Path: ['$.overlays[0]', '$.overlays[0].id', '$.overlays[0].type', '$.overlays[0].start', '$.overlays[0].end']

```text
V2 validation failed:
$.overlays[0]: must be an object
$.overlays[0].id: required field is missing
$.overlays[0].type: required field is missing
$.overlays[0].start: required field is missing
$.overlays[0].end: required field is missing
```

## unknown:$.overlays[0]

Path: ['$.overlays[0].INVENTED']

```text
V2 validation failed:
$.overlays[0].INVENTED: unknown field
```

## null:$.overlays[0].id

Path: ['$.overlays[0].id']

```text
V2 validation failed:
$.overlays[0].id: must be text of at most 120 characters
```

## null:$.overlays[0].type

Path: ['$.overlays[0].type']

```text
V2 validation failed:
$.overlays[0].type: must be one of DATE_STAMP, HIGHLIGHT_BOX, HOOK_CARD, LOWER_THIRD, MAP_ROUTE, PHOTO_NOTE, TEXT
```

## null:$.overlays[0].style

Path: ['$.overlays[0].style']

```text
V2 validation failed:
$.overlays[0].style: must be one of ARCHIVE, ARROW, CIRCLE, MODERN, PLAIN, RECT
```

## null:$.overlays[0].start

Path: ['$.overlays[0].start']

```text
V2 validation failed:
$.overlays[0].start: must be a number between 0 and 1e+07
```

## null:$.overlays[0].end

Path: ['$.overlays[0].end']

```text
V2 validation failed:
$.overlays[0].end: must be a number between 0 and 1e+07
```

## null:$.overlays[0].text

Path: ['$.overlays[0].text', '$.overlays[0].text']

```text
V2 validation failed:
$.overlays[0].text: must be text of at most 120 characters
$.overlays[0].text: photo note text is required
```

## null:$.overlays[0].text2

Path: ['$.overlays[0].text2']

```text
V2 validation failed:
$.overlays[0].text2: must be text of at most 120 characters
```

## null:$.overlays[0].x

Path: ['$.overlays[0].x']

```text
V2 validation failed:
$.overlays[0].x: must be a number between 0 and 1
```

## null:$.overlays[0].y

Path: ['$.overlays[0].y']

```text
V2 validation failed:
$.overlays[0].y: must be a number between 0 and 1
```

## null:$.overlays[0].w

Path: ['$.overlays[0].w']

```text
V2 validation failed:
$.overlays[0].w: must be a number between 0 and 1
```

## null:$.overlays[0].h

Path: ['$.overlays[0].h']

```text
V2 validation failed:
$.overlays[0].h: must be a number between 0 and 1
```

## null:$.overlays[0].points

Path: ['$.overlays[0].points', '$.overlays[0].points']

```text
V2 validation failed:
$.overlays[0].points: must be an array
$.overlays[0].points: must contain four source-image corners: top-left, top-right, bottom-right, bottom-left
```

## null:$.overlays[0].points[0]

Path: ['$.overlays[0].points[0]']

```text
V2 validation failed:
$.overlays[0].points[0]: must be [x,y]
```

## null:$.overlays[0].points[0][0]

Path: ['$.overlays[0].points[0][0]']

```text
V2 validation failed:
$.overlays[0].points[0][0]: must be a number between 0 and 1
```

## null:$.overlays[0].points[0][1]

Path: ['$.overlays[0].points[0][1]']

```text
V2 validation failed:
$.overlays[0].points[0][1]: must be a number between 0 and 1
```

## null:$.overlays[0].points[1]

Path: ['$.overlays[0].points[1]']

```text
V2 validation failed:
$.overlays[0].points[1]: must be [x,y]
```

## null:$.overlays[0].points[1][0]

Path: ['$.overlays[0].points[1][0]']

```text
V2 validation failed:
$.overlays[0].points[1][0]: must be a number between 0 and 1
```

## null:$.overlays[0].points[1][1]

Path: ['$.overlays[0].points[1][1]']

```text
V2 validation failed:
$.overlays[0].points[1][1]: must be a number between 0 and 1
```

## null:$.ending

Path: ['$.ending']

```text
V2 validation failed:
$.ending: must be an object
```

## unknown:$.ending

Path: ['$.ending.INVENTED']

```text
V2 validation failed:
$.ending.INVENTED: unknown field
```

## null:$.ending.mode

Path: ['$.ending.mode']

```text
V2 validation failed:
$.ending.mode: must be one of FADE_OUT, HOLD
```

## null:$.ending.frames

Path: ['$.ending.frames']

```text
V2 validation failed:
$.ending.frames: must be a integer between 0 and 90
```

## missing:project_title

Path: ['$.project_title']

```text
V2 validation failed:
$.project_title: required field is missing
```

## missing:audio_duration

Path: ['$.audio_duration']

```text
V2 validation failed:
$.audio_duration: required field is missing
```

## missing:fps

Path: ['$.fps']

```text
V2 validation failed:
$.fps: required field is missing
```

## missing:scenes

Path: ['$.scenes', '$.overlays[0].scene_id']

```text
V2 validation failed:
$.scenes: required field is missing
$.overlays[0].scene_id: must reference an existing scene
```

## missing:words

Path: ['$.words', '$.caption_style.emphasis[0]']

```text
V2 validation failed:
$.words: required field is missing
$.caption_style.emphasis[0]: word index does not exist
```

## missing:captions

Path: ['$.captions']

```text
V2 validation failed:
$.captions: required field is missing
```

## missing:caption_style

Path: ['$.caption_style', '$.caption_style.highlight_current_word', '$.caption_style.enabled']

```text
V2 validation failed:
$.caption_style: required field is missing
$.caption_style.highlight_current_word: required field is missing
$.caption_style.enabled: required field is missing
```

## value:$.audio_duration:0

Path: ['$.scenes[1].sfx[0].offset_ms', '$.overlays[0].start', '$.overlays[0].end']

```text
V2 validation failed:
$.scenes[1].sfx[0].offset_ms: resolved cue time is outside the timeline
$.overlays[0].start: must be inside the audio timeline
$.overlays[0].end: must be inside the audio timeline
```

## value:$.fps:0

Path: ['$.v1_contract']

```text
$.v1_contract: fps must be between 1 and 60.
```

## value:$.scenes[0].id:002

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 id should be "001", received "002".
```

## value:$.scenes[0].start:-1

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 needs 0 <= start < end.
```

## value:$.scenes[0].start:0.1

Path: ['$.v1_contract']

```text
$.v1_contract: First scene must start at timeline origin (frame 0).
```

## value:$.scenes[0].end:0.001

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 is shorter than one output frame at 30 FPS.
```

## value:$.scenes[1].start:4.1

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 has a gap after scene 001 at output-frame precision.
```

## value:$.scenes[1].start:3.9

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 has a overlap after scene 001 at output-frame precision.
```

## value:$.scenes[1].end:7.9

Path: ['$.v1_contract']

```text
$.v1_contract: Last scene ends at frame 237; audio_duration requires frame 240.
```

## value:$.scenes[0].motion:BAD

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 has unsupported motion: BAD.
```

## value:$.scenes[0].transition:CROSSFADE

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 001 must use HARD_CUT or NONE; it has no preceding image to transition from.
```

## value:$.scenes[1].transition:BAD

Path: ['$.v1_contract']

```text
$.v1_contract: Scene 002 has unsupported transition: BAD.
```

## value:$.words[1].index:1

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 index must be unique and increasing.
```

## value:$.words[1].start:0

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 2 is out of chronological order.
```

## value:$.words[0].start:-1

Path: ['$.v1_contract']

```text
$.v1_contract: Word entry 1 timing is outside the audio.
```

## value:$.captions[0].end:9

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 timing is outside the audio.
```

## value:$.captions[0].text:invented

Path: ['$.captions[0].text']

```text
$.captions[0].text: expected timed-word text 'At midnight, the ticket'. Keep caption text and word indices identical.
```

## value:$.captions[0].word_start_index:999

Path: ['$.v1_contract']

```text
$.v1_contract: Caption 001 references missing or reversed word indexes.
```

## value:$.overlays[0].text:

Path: ['$.overlays[0].text']

```text
V2 validation failed:
$.overlays[0].text: photo note text is required
```

## value:$.overlays[0].points:[]

Path: ['$.overlays[0].points']

```text
V2 validation failed:
$.overlays[0].points: must contain four source-image corners: top-left, top-right, bottom-right, bottom-left
```

## value:$.overlays[0].points:[[0, 0], [1, 1], [0, 1],

Path: ['$.overlays[0].points']

```text
V2 validation failed:
$.overlays[0].points: corners must form a convex nonzero quadrilateral in perimeter order
```

## value:$.overlays[0].points:[[2, 0], [1, 0], [1, 1],

Path: ['$.overlays[0].points[0][0]', '$.overlays[0].points']

```text
V2 validation failed:
$.overlays[0].points[0][0]: must be a number between 0 and 1
$.overlays[0].points: corners must form a convex nonzero quadrilateral in perimeter order
```

## value:$.overlays[0].points:[[1]]

Path: ['$.overlays[0].points[0]', '$.overlays[0].points']

```text
V2 validation failed:
$.overlays[0].points[0]: must be [x,y]
$.overlays[0].points: must contain four source-image corners: top-left, top-right, bottom-right, bottom-left
```

## value:$.overlays[0].end:9

Path: ['$.overlays[0].end']

```text
V2 validation failed:
$.overlays[0].end: must be inside the audio timeline
```

## value:$.overlays[0].end:4

Path: ['$.overlays[0].end']

```text
V2 validation failed:
$.overlays[0].end: must be greater than start
```

## value:$.overlays[0].text:xxxxxxxxxxxxxxxxxxxxxxxx

Path: ['$.overlays[0].text']

```text
V2 validation failed:
$.overlays[0].text: must be text of at most 120 characters
```

## missing:$.scenes[1].sfx[0].id

Path: ['$.scenes[1].sfx[0].id']

```text
V2 validation failed:
$.scenes[1].sfx[0].id: required field is missing
```

## missing:$.scenes[1].motion_config.focus.x

Path: ['$.scenes[1].motion_config.focus.x']

```text
V2 validation failed:
$.scenes[1].motion_config.focus.x: required field is missing
```

## missing:$.overlays[0].id

Path: ['$.overlays[0].id']

```text
V2 validation failed:
$.overlays[0].id: required field is missing
```

## missing:$.overlays[0].type

Path: ['$.overlays[0].type']

```text
V2 validation failed:
$.overlays[0].type: required field is missing
```

## missing:$.overlays[0].start

Path: ['$.overlays[0].start']

```text
V2 validation failed:
$.overlays[0].start: required field is missing
```

## missing:$.overlays[0].end

Path: ['$.overlays[0].end']

```text
V2 validation failed:
$.overlays[0].end: required field is missing
```

## missing:$.caption_style.enabled

Path: ['$.caption_style.enabled']

```text
V2 validation failed:
$.caption_style.enabled: required field is missing
```

## missing:$.caption_style.highlight_current_word

Path: ['$.caption_style.highlight_current_word']

```text
V2 validation failed:
$.caption_style.highlight_current_word: required field is missing
```

## forbidden:$.auto_direct

Path: ['$.auto_direct']

```text
$.auto_direct: remove this field; ATS 3.0 always runs the director.
```

## forbidden:$.audio.music

Path: ['$.audio.music']

```text
$.audio.music: unsupported in ATS 3.0. Import an optional music file; use direction.music_level and direction.duck_db.
```

## forbidden:$.audio.ambience

Path: ['$.audio.ambience']

```text
$.audio.ambience: unsupported in ATS 3.0. Import an optional music file; use direction.music_level and direction.duck_db.
```

## forbidden:$.audio.sfx.pack

Path: ['$.audio.sfx.pack']

```text
V2 validation failed:
$.audio.sfx.pack: must be one of SFX_ARCHIVE_V1
```

## forbidden:$.audio.sfx.density

Path: ['$.audio.sfx.density']

```text
$.audio.sfx.density: remove this field. Flag individual scene cuts with transition_config.sfx or scenes[].sfx.
```

## forbidden:$.caption_style.chunk_words

Path: ['$.caption_style.chunk_words']

```text
$.caption_style.chunk_words: remove this field. ATS 3.0 preserves supplied caption intervals and uses a fixed platform-safe layout.
```

## forbidden:$.caption_style.safe_zone

Path: ['$.caption_style.safe_zone']

```text
$.caption_style.safe_zone: remove this field. ATS 3.0 preserves supplied caption intervals and uses a fixed platform-safe layout.
```

## forbidden:$.scenes[1].motion_config.shake

Path: ['$.scenes[1].motion_config.shake']

```text
$.scenes[1].motion_config.shake: unsupported in ATS 3.0; remove it. Use deliberate motion and finishing instead.
```

## creator:Hormozi Style

Path: ['$.caption_style.animation']

```text
$.caption_style.animation: this creator preset has a fixed animation; remove animation.
```

## first_scene_sfx

Path: ['$.scenes[0].sfx']

```text
$.scenes[0].sfx: first scene has no cut. Place SFX on a later flagged cut.
```

## sfx_spacing

Path: ['$.scenes[1].sfx']

```text
$.scenes[1].sfx: cue is within 350 ms of another explicit cue
```

## json:

Path: ['$']

```text
$: invalid JSON: Expecting value: line 1 column 1 (char 0)
```

## json:{

Path: ['$']

```text
$: invalid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

## json:{}{}

Path: ['$']

```text
$: invalid JSON: Extra data: line 1 column 3 (char 2)
```

## json:{"schema":"ATS_PACKAGE_V2","fps":NaN}

Path: ['$']

```text
$: invalid JSON: Invalid JSON number: NaN.
```

## json:{"schema":"ATS_PACKAGE_V2","fps":30,"fps":30}

Path: ['$']

```text
$: invalid JSON: Duplicate JSON key: "fps".
```

## size_limit

Path: ['$']

```text
$: JSON exceeds the 50 MiB safety limit.
```

## moment:id

Path: $.moments[0]

```text
$.moments[0] skipped: id must be unique text.
```

## moment:type

Path: $.moments[0]

```text
$.moments[0] skipped: type must be DATE_CARD or CIRCLE.
```

## moment:text

Path: $.moments[0]

```text
$.moments[0] skipped: text must be 1–80 characters.
```

## moment:dim

Path: $.moments[0]

```text
$.moments[0] skipped: dim must be 0–0.8.
```

## moment:word_start_index

Path: $.moments[0]

```text
$.moments[0] skipped: word indices must reference an ordered range in words.
```

## moment:INVENTED

Path: $.moments[0]

```text
$.moments[0] skipped: unknown DATE_CARD field.
```

## moment:duplicate

Path: $.moments[1]

```text
$.moments[1] skipped: id must be unique text.
```

## moment:zero_frame

Path: $.moments[0]

```text
$.moments[0] skipped: word timing must span at least one frame.
```

## moment:wrong_container

Path: $.moments

```text
$.moments skipped: expected an array.
```

## circle:scene_id

Path: $.moments[0]

```text
$.moments[0] skipped: scene_id must exist.
```

## circle:box

Path: $.moments[0]

```text
$.moments[0] skipped: box must fit source image, each side ≥0.03, area ≤0.20.
```

## circle:box

Path: $.moments[0]

```text
$.moments[0] skipped: box must be [x,y,width,height] in source-image coordinates.
```

## circle:word_start_index

Path: $.moments[0]

```text
$.moments[0] skipped: word range must be inside the referenced scene.
```

## circle:INVENTED

Path: $.moments[0]

```text
$.moments[0] skipped: unknown CIRCLE field.
```

## candidate_seed:-1

Path: ['$.style.seed']

```text
V2 validation failed:
$.style.seed: must be an integer between 0 and 2147483647
```

## creator_rtl

$.caption_style.preset | WARN

creator caption layout is left to right; multiword right-to-left order will be wrong

## script_font

$.caption_style.font | WARN

{font} lacks native glyphs for some {script} characters; recommend {recommended}. Font fallback may render them; layout is not certified.
