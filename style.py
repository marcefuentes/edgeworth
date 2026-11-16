"""Shared typography: Roboto Mono."""

from __future__ import annotations

from pathlib import Path

import manimpango
from manim import DOWN, Dot, LEFT, Text, UL

_FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT = "Roboto Mono"

for _ttf in (_FONTS_DIR / "RobotoMono-Regular.ttf", _FONTS_DIR / "RobotoMono-Medium.ttf"):
    if _ttf.exists():
        manimpango.register_font(str(_ttf))

AXIS_TITLE_SIZE = 26
AXIS_NUMBER_SIZE = 24
NAME_SIZE = 32
NAME_STACK_BUFF = 0.12
DOT_COLOR = "#76FF03"
# Above ICs / contract curves (default z_index 0) for the whole narrative.
DOT_Z_INDEX = 10


def allocation_dot(point, *, radius: float = 0.1) -> Dot:
    """Green allocation marker; always drawn above ICs and contract curves."""
    return Dot(point, color=DOT_COLOR, radius=radius).set_z_index(DOT_Z_INDEX)
# Multiples of u_opt; stop at the optimum (never above).
IC_LEVEL_FACTORS = (0.35, 0.55, 0.75, 0.90, 1.0)


def grey_for_level(t: float) -> str:
    """t in [0, 1]: 0 = dark grey, 1 = light grey (IC family)."""
    t = max(0.0, min(1.0, t))
    c = int(70 + t * (210 - 70))
    return f"#{c:02x}{c:02x}{c:02x}"


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


def person_name_stacked(name: str, color=None, *, under=None) -> Text:
    """Second UL name (box-stage agent B): stacked under the primary name slot."""
    label = mono(name, font_size=NAME_SIZE, color=color)
    anchor = under if under is not None else person_name("Ag", color=color)
    label.next_to(anchor, DOWN, aligned_edge=LEFT, buff=NAME_STACK_BUFF)
    return label
