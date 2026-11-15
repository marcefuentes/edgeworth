"""Shared typography: Roboto Mono."""

from __future__ import annotations

from pathlib import Path

import manimpango
from manim import Text, UL

_FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT = "Roboto Mono"

for _ttf in (_FONTS_DIR / "RobotoMono-Regular.ttf", _FONTS_DIR / "RobotoMono-Medium.ttf"):
    if _ttf.exists():
        manimpango.register_font(str(_ttf))

AXIS_TITLE_SIZE = 26
AXIS_NUMBER_SIZE = 24
NAME_SIZE = 32


def mono(
    text: str,
    *,
    font_size: int = 24,
    color=None,
    **kwargs,
) -> Text:
    kw = {"font": FONT, "font_size": font_size, **kwargs}
    if color is not None:
        kw["color"] = color
    return Text(text, **kw)


def person_name(name: str, color=None) -> Text:
    label = mono(name, font_size=NAME_SIZE, color=color)
    label.to_corner(UL, buff=0.35)
    return label
