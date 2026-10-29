"""Presentation options shared by the preview, project file, and renderer."""

from __future__ import annotations

from dataclasses import dataclass
from .caption_presets import NEW_CAPTION_PRESETS, PROFILES


FORMATS = {
    "16:9 Landscape": ((1280, 720), (1920, 1080), (3840, 2160)),
    "9:16 Vertical": ((720, 1280), (1080, 1920), (2160, 3840)),
    "1:1 Square": ((1080, 1080),),
    "4:5 Portrait": ((1080, 1350),),
}
FRAMING = ("Fill Frame", "Fit Entire Image")
CAPTION_PRESETS = (*NEW_CAPTION_PRESETS, "Documentary Highlight", "Clean Subtitle", "Typewriter", "Off")
CAPTION_FONTS = ("Montserrat", "Anton", "Luckiest Guy", "Bangers", "Poppins", "Bebas Neue", "Arial", "Segoe UI", "Georgia", "Consolas", "DejaVu Sans",
                 "Liberation Sans", "Source Code Pro", "Inconsolata", "Bitstream Vera Sans")


def format_for_size(width: int, height: int) -> str:
    for name, sizes in FORMATS.items():
        if (width, height) in sizes:
            return name
    return "16:9 Landscape"


@dataclass(frozen=True)
class CaptionSettings:
    preset: str = "Documentary Highlight"
    text_size: int = 100  # percent of preset size
    position: str = "Bottom"
    max_lines: int = 2
    safe_margin: int = 7  # percent of frame height
    custom_y: int = 75  # percent from top when Custom is selected
    font_family: str = "Inter"
    text_color: str = "#FFFFFF"
    highlight_hex: str | None = None
    background_style: str = "Dark Brush"
    outline_strength: int = 60
    shadow_strength: int = 40
    outline_on: bool = True
    shadow_on: bool = True

    def __post_init__(self) -> None:
        if self.preset not in CAPTION_PRESETS:
            raise ValueError("Unknown caption preset")
        if self.position not in {"Bottom", "Center", "Top", "Custom"}:
            raise ValueError("Unknown caption position")
        if not 50 <= self.text_size <= 180 or self.max_lines not in (1, 2):
            raise ValueError("Invalid caption size or line count")
        if not 0 <= self.safe_margin <= 30:
            raise ValueError("Invalid caption safe margin")
        if not 10 <= self.custom_y <= 90:
            raise ValueError("Invalid custom caption position")
        if self.font_family not in CAPTION_FONTS:
            raise ValueError("Unsupported caption font")
        for color in (self.text_color, self.highlight_hex):
            if color is not None and (len(color) != 7 or color[0] != "#" or
                                      any(c not in "0123456789abcdefABCDEF" for c in color[1:])):
                raise ValueError("Invalid caption color")
        if self.background_style not in {"Dark Brush", "Shadow Only", "Solid Box", "Paper", "None"}:
            raise ValueError("Invalid caption background")
        if not 0 <= self.outline_strength <= 100 or not 0 <= self.shadow_strength <= 100:
            raise ValueError("Invalid caption outline or shadow")

    def font_size(self, frame_height: int) -> int:
        if self.preset in PROFILES:
            return max(12,round(frame_height*PROFILES[self.preset]['size']/1920*self.text_size/100))
        factor = {
            "Documentary Highlight": .045, "Cinematic Story": .051,
            "Minimal Documentary": .038, "Storytelling Pop": .057,
            "Clean Subtitle": .043, "Bold Story": .056, "Typewriter": .043,
        }.get(self.preset, .045)
        return max(12, round(frame_height * factor * self.text_size / 100))

    def highlight_color(self) -> str | None:
        if self.highlight_hex is not None:
            return self.highlight_hex
        if self.preset in PROFILES:return PROFILES[self.preset]['accent']
        if self.preset in {"Documentary Highlight", "Word Highlight"}:
            return "#9AF01C" if self.preset == "Documentary Highlight" else "#ffe900"
        if self.preset in {"Cinematic Story", "Storytelling Pop", "Bold Story"}:
            return "#ffe18a"
        return None

    def text_layout(self, tokens: list[str], frame_width: int, frame_height: int) -> tuple[int, int | None]:
        """Return a bounded font size and optional two-line split for a caption."""
        size = self.font_size(frame_height)
        if not tokens:
            return size, None
        split = None
        chars = sum(len(word) + 1 for word in tokens)
        capacity = max(1, frame_width * .84 / (size * .55))
        if self.max_lines == 2 and chars > capacity and len(tokens) > 1:
            cumulative = 0
            split = 1
            for index, word in enumerate(tokens[:-1], 1):
                cumulative += len(word) + 1
                if abs(cumulative - chars/2) < abs(sum(len(w)+1 for w in tokens[:split]) - chars/2):
                    split = index
        if split:
            chars = max(sum(len(w)+1 for w in tokens[:split]),
                        sum(len(w)+1 for w in tokens[split:]))
        size = max(12, min(size, int(frame_width * .84 / max(1, chars*.55))))
        return size, split
