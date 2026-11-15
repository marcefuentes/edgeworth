"""Reusable Manim mobjects for Edgeworth boxes and preference maps."""

from __future__ import annotations

from manim import (
    DOWN,
    GREY_B,
    LEFT,
    PI,
    RIGHT,
    UP,
    WHITE,
    Axes,
    Dot,
    Line,
    VGroup,
    VMobject,
)

from geometry import EPS, clip_domain_for_ic, flip_to_a
from style import AXIS_NUMBER_SIZE, AXIS_TITLE_SIZE, mono


BUDGET_COLOR = "#E76F51"
CONTRACT_COLOR = "#264653"
ENDOWMENT_COLOR = WHITE
TICK_SIZE = 0.08


def _tick_step(span: float) -> float:
    if span <= 4:
        return 1
    if span <= 8:
        return 2
    return max(1, round(span / 4))


def _set_outward_ticks(axis, outward, tick_size: float = TICK_SIZE) -> None:
    """Replace Manim's centered ticks with ticks that only point ``outward``."""
    if getattr(axis, "ticks", None) is not None:
        axis.remove(axis.ticks)
    ticks = VGroup()
    for val in axis.get_tick_range():
        p = axis.number_to_point(val)
        tick = Line(p, p + outward * tick_size)
        tick.match_style(axis)
        ticks.add(tick)
    axis.add(ticks)
    axis.ticks = ticks


def _edge_ticks(points_along_axis, outward, color, tick_size: float = TICK_SIZE) -> VGroup:
    """Ticks sitting on a box edge (e.g. agent B's NE axes)."""
    ticks = VGroup()
    for p in points_along_axis:
        tick = Line(p, p + outward * tick_size, color=color, stroke_width=2)
        ticks.add(tick)
    return ticks


class LabeledAxes(VGroup):
    def __init__(
        self,
        x_max: float,
        y_max: float,
        x_label: str,
        y_label: str,
        *,
        width: float = 5.5,
        height: float = 4.0,
        tip_length: float = 0.03,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.x_max = x_max
        self.y_max = y_max
        self._step_x = _tick_step(x_max)
        self._step_y = _tick_step(y_max)
        self.axes = Axes(
            x_range=[0, x_max, self._step_x],
            y_range=[0, y_max, self._step_y],
            x_length=width,
            y_length=height,
            axis_config={
                "include_numbers": False,
                "tip_length": tip_length,
                "color": GREY_B,
                "tick_size": TICK_SIZE,
            },
            tips=True,
        )
        _set_outward_ticks(self.axes.x_axis, DOWN)
        _set_outward_ticks(self.axes.y_axis, LEFT)
        xl = mono(x_label, font_size=AXIS_TITLE_SIZE).next_to(
            self.axes.x_axis, DOWN, buff=0.35
        )
        yl = (
            mono(y_label, font_size=AXIS_TITLE_SIZE)
            .rotate(PI / 2)
            .next_to(self.axes.y_axis, LEFT, buff=0.4)
        )

        number_group = VGroup()
        x = self._step_x
        while x <= x_max + 1e-9:
            number_group.add(
                mono(f"{x:g}", font_size=AXIS_NUMBER_SIZE, color=GREY_B).next_to(
                    self.axes.coords_to_point(x, 0), DOWN, buff=0.12
                )
            )
            x += self._step_x
        y = self._step_y
        while y <= y_max + 1e-9:
            number_group.add(
                mono(f"{y:g}", font_size=AXIS_NUMBER_SIZE, color=GREY_B).next_to(
                    self.axes.coords_to_point(0, y), LEFT, buff=0.12
                )
            )
            y += self._step_y

        self.add(self.axes, xl, yl, number_group)

    def c2p(self, x: float, y: float):
        return self.axes.coords_to_point(x, y)

    def cursor_ticks(
        self,
        x: float,
        y: float,
        color,
        *,
        tick_size: float = TICK_SIZE * 1.75,
        stroke_width: float = 4,
    ) -> VGroup:
        """Outward green ticks on each axis at the projection of (x, y)."""
        px = self.c2p(x, 0)
        py = self.c2p(0, y)
        return VGroup(
            Line(px, px + DOWN * tick_size, color=color, stroke_width=stroke_width),
            Line(py, py + LEFT * tick_size, color=color, stroke_width=stroke_width),
        )

    def plot_ic(self, u: float, alpha: float, color: str, stroke_width: float = 3):
        pts = clip_domain_for_ic(u, alpha, self.x_max, self.y_max)
        if len(pts) < 2:
            return VMobject()
        curve = VMobject(color=color, stroke_width=stroke_width)
        curve.set_points_smoothly([self.c2p(x, y) for x, y in pts])
        return curve

    def budget_line(
        self,
        endowment: tuple[float, float],
        price_x: float,
        color: str = BUDGET_COLOR,
    ):
        m = price_x * endowment[0] + endowment[1]
        x0, y0 = 0.0, m
        x1, y1 = m / price_x, 0.0
        x0, y0 = max(0, x0), min(self.y_max, y0)
        if y0 > self.y_max:
            y0 = self.y_max
            x0 = (m - y0) / price_x
        x1 = min(self.x_max, x1)
        y1 = m - price_x * x1
        if y1 < 0:
            y1 = 0
            x1 = m / price_x
        return Line(self.c2p(x0, y0), self.c2p(x1, y1), color=color, stroke_width=3)

    def ppf_line(self, a_x: float, a_y: float, color: str = "#43A047"):
        """Linear production-possibility frontier from (0, a_y) to (a_x, 0)."""
        x0, y0 = 0.0, min(a_y, self.y_max)
        if a_y > self.y_max and a_y > EPS:
            x0 = a_x * (1.0 - self.y_max / a_y)
            y0 = self.y_max
        x1, y1 = min(a_x, self.x_max), 0.0
        if a_x > self.x_max and a_x > EPS:
            y1 = a_y * (1.0 - self.x_max / a_x)
            x1 = self.x_max
        return Line(self.c2p(x0, y0), self.c2p(x1, y1), color=color, stroke_width=4)


class EdgeworthBox(VGroup):
    """Rectangle with dual origins: agent A SW, agent B NE."""

    def __init__(
        self,
        total_x: float,
        total_y: float,
        agent_a_name: str,
        agent_b_name: str,
        good_x: str,
        good_y: str,
        color_a: str,
        color_b: str,
        *,
        width: float = 5.5,
        height: float = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.total_x = total_x
        self.total_y = total_y
        # Names kept for callers; drawn by scenes (upper-left), not on the box.
        self.agent_a_name = agent_a_name
        self.agent_b_name = agent_b_name
        if height is None:
            height = width * (total_y / total_x)
        self.axes_a = Axes(
            x_range=[0, total_x, _tick_step(total_x)],
            y_range=[0, total_y, _tick_step(total_y)],
            x_length=width,
            y_length=height,
            axis_config={
                "include_numbers": False,
                "tip_length": 0.03,
                "color": color_a,
                "tick_size": TICK_SIZE,
            },
            tips=True,
        )
        _set_outward_ticks(self.axes_a.x_axis, DOWN)
        _set_outward_ticks(self.axes_a.y_axis, LEFT)

        bl = self.axes_a.coords_to_point(0, 0)
        br = self.axes_a.coords_to_point(total_x, 0)
        tl = self.axes_a.coords_to_point(0, total_y)
        tr = self.axes_a.coords_to_point(total_x, total_y)
        border = VMobject(color=GREY_B, stroke_width=2)
        border.set_points_as_corners([bl, br, tr, tl, bl])

        xa = mono(good_x, font_size=AXIS_TITLE_SIZE, color=color_a).next_to(
            br, DOWN, buff=0.35
        )
        ya = (
            mono(good_y, font_size=AXIS_TITLE_SIZE, color=color_a)
            .rotate(PI / 2)
            .next_to(tl, LEFT, buff=0.4)
        )
        xb = mono(good_x, font_size=AXIS_TITLE_SIZE, color=color_b).next_to(
            tl, UP, buff=0.2
        )
        yb = (
            mono(good_y, font_size=AXIS_TITLE_SIZE, color=color_b)
            .rotate(PI / 2)
            .next_to(br, RIGHT, buff=0.35)
        )

        tip_b_x = Line(tr, tl, color=color_b, stroke_width=2)
        tip_b_y = Line(tr, br, color=color_b, stroke_width=2)
        b_x_pts = [
            self.axes_a.coords_to_point(x, total_y)
            for x in self.axes_a.x_axis.get_tick_range()
            if x > 0
        ]
        b_y_pts = [
            self.axes_a.coords_to_point(total_x, y)
            for y in self.axes_a.y_axis.get_tick_range()
            if y > 0
        ]
        ticks_b_x = _edge_ticks(b_x_pts, UP, color_b)
        ticks_b_y = _edge_ticks(b_y_pts, RIGHT, color_b)

        self.color_a = color_a
        self.color_b = color_b
        self.add(
            border,
            self.axes_a,
            tip_b_x,
            tip_b_y,
            ticks_b_x,
            ticks_b_y,
            xa,
            ya,
            xb,
            yb,
            _axis_number_labels(self.axes_a, total_x, total_y),
        )

    def c2p(self, x: float, y: float):
        return self.axes_a.coords_to_point(x, y)

    def plot_ic_a(self, u: float, alpha: float, stroke_width: float = 3):
        pts = clip_domain_for_ic(u, alpha, self.total_x, self.total_y)
        if len(pts) < 2:
            return VMobject()
        curve = VMobject(color=self.color_a, stroke_width=stroke_width)
        curve.set_points_smoothly([self.c2p(x, y) for x, y in pts])
        return curve

    def plot_ic_b(self, u: float, alpha: float, stroke_width: float = 3):
        """IC for B, drawn in A-coordinates."""
        pts_b = clip_domain_for_ic(u, alpha, self.total_x, self.total_y)
        if len(pts_b) < 2:
            return VMobject()
        pts_a = [flip_to_a(p, self.total_x, self.total_y) for p in pts_b]
        pts_a = [
            (x, y)
            for x, y in pts_a
            if 0 <= x <= self.total_x and 0 <= y <= self.total_y
        ]
        if len(pts_a) < 2:
            return VMobject()
        pts_a.sort(key=lambda p: p[0])
        curve = VMobject(color=self.color_b, stroke_width=stroke_width)
        curve.set_points_smoothly([self.c2p(x, y) for x, y in pts_a])
        return curve

    def budget_through(
        self,
        endowment_a: tuple[float, float],
        price_x: float,
        color: str = BUDGET_COLOR,
    ):
        m = price_x * endowment_a[0] + endowment_a[1]
        candidates = []
        x = m / price_x
        if 0 <= x <= self.total_x:
            candidates.append((x, 0.0))
        x = (m - self.total_y) / price_x
        if 0 <= x <= self.total_x:
            candidates.append((x, self.total_y))
        y = m
        if 0 <= y <= self.total_y:
            candidates.append((0.0, y))
        y = m - price_x * self.total_x
        if 0 <= y <= self.total_y:
            candidates.append((self.total_x, y))
        uniq = []
        for p in candidates:
            if not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 for q in uniq):
                uniq.append(p)
        if len(uniq) < 2:
            return VMobject()
        uniq.sort(key=lambda p: p[0])
        return Line(self.c2p(*uniq[0]), self.c2p(*uniq[-1]), color=color, stroke_width=3)

    def allocation_dot(self, bundle_a: tuple[float, float], color: str = ENDOWMENT_COLOR):
        return Dot(self.c2p(*bundle_a), color=color, radius=0.08)
