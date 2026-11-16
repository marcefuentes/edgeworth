"""Shared chart placement: fixed SW origin and common units per good."""

from __future__ import annotations

from manim import DOWN, LEFT

# One manim-unit per good, keyed off the 6-wide autarky/exchange box at width 5.0.
CHART_UNIT = 5.0 / 6.0
# SW corner of every chart (maps + Edgeworth boxes).
CHART_SW = LEFT * 3.4 + DOWN * 2.5


def pin_sw(mobject, sw_point):
    """Shift ``mobject`` so ``sw_point`` lands on ``CHART_SW``."""
    mobject.shift(CHART_SW - sw_point)
    return mobject


def chart_size(total_x: float, total_y: float) -> tuple[float, float]:
    """Pixel size of a chart with the shared unit scale."""
    return total_x * CHART_UNIT, total_y * CHART_UNIT
