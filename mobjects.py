"""Reusable Manim mobjects for Edgeworth boxes and preference maps."""

from __future__ import annotations

from manim import (
    DOWN,
    GREY_B,
    LEFT,
    RIGHT,
    UP,
    WHITE,
    Axes,
    Dot,
    Line,
    Text,
    VGroup,
    VMobject,
)

from geometry import clip_domain_for_ic, flip_to_a, utility


BUDGET_COLOR = "#E76F51"
CONTRACT_COLOR = "#264653"
ENDOWMENT_COLOR = WHITE


def _tick_step(span: float) -> float:
    if span <= 4:
        return 1
    if span <= 8:
        return 2
    return max(1, round(span / 4))


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
        tip_length: float = 0.15,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.x_max = x_max
        self.y_max = y_max
        self.axes = Axes(
            x_range=[0, x_max, _tick_step(x_max)],
            y_range=[0, y_max, _tick_step(y_max)],
            x_length=width,
            y_length=height,
            axis_config={
                # Avoid LaTeX dependency for tick labels.
                "include_numbers": False,
                "tip_length": tip_length,
                "color": GREY_B,
            },
            tips=True,
        )
        xl = Text(x_label, font_size=26).next_to(self.axes.x_axis, DOWN, buff=0.25)
        yl = Text(y_label, font_size=26).next_to(self.axes.y_axis, LEFT, buff=0.25)
        tick_labels = VGroup()
        step_x = _tick_step(x_max)
        step_y = _tick_step(y_max)
        x = step_x
        while x <= x_max + 1e-9:
            tick_labels.add(
                Text(f"{x:g}", font_size=18, color=GREY_B).next_to(
                    self.axes.coords_to_point(x, 0), DOWN, buff=0.12
                )
            )
            x += step_x
        y = step_y
        while y <= y_max + 1e-9:
            tick_labels.add(
                Text(f"{y:g}", font_size=18, color=GREY_B).next_to(
                    self.axes.coords_to_point(0, y), LEFT, buff=0.12
                )
            )
            y += step_y
        self.add(self.axes, xl, yl, tick_labels)

    def c2p(self, x: float, y: float):
        return self.axes.coords_to_point(x, y)

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
        # clip to axes
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
        if height is None:
            height = width * (total_y / total_x)
        self.axes_a = Axes(
            x_range=[0, total_x, _tick_step(total_x)],
            y_range=[0, total_y, _tick_step(total_y)],
            x_length=width,
            y_length=height,
            axis_config={
                "include_numbers": False,
                "tip_length": 0.12,
                "color": color_a,
            },
            tips=True,
        )
        # Box border
        bl = self.axes_a.coords_to_point(0, 0)
        br = self.axes_a.coords_to_point(total_x, 0)
        tl = self.axes_a.coords_to_point(0, total_y)
        tr = self.axes_a.coords_to_point(total_x, total_y)
        border = VMobject(color=GREY_B, stroke_width=2)
        border.set_points_as_corners([bl, br, tr, tl, bl])

        oa = Text(f"Oₐ ({agent_a_name})", font_size=22, color=color_a)
        oa.next_to(bl, DOWN + LEFT, buff=0.15)
        ob = Text(f"Oᵦ ({agent_b_name})", font_size=22, color=color_b)
        ob.next_to(tr, UP + RIGHT, buff=0.15)

        xa = Text(good_x, font_size=22, color=color_a).next_to(br, DOWN, buff=0.2)
        ya = Text(good_y, font_size=22, color=color_a).next_to(tl, LEFT, buff=0.2)
        xb = Text(good_x, font_size=22, color=color_b).next_to(tl, UP, buff=0.15)
        yb = Text(good_y, font_size=22, color=color_b).next_to(br, RIGHT, buff=0.15)

        # B axes tips (visual only): left from NE and down from NE
        tip_b_x = Line(tr, self.axes_a.coords_to_point(0, total_y), color=color_b, stroke_width=2)
        tip_b_y = Line(tr, self.axes_a.coords_to_point(total_x, 0), color=color_b, stroke_width=2)

        self.color_a = color_a
        self.color_b = color_b
        self.add(border, self.axes_a, tip_b_x, tip_b_y, oa, ob, xa, ya, xb, yb)

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
        # keep only points inside the box
        pts_a = [
            (x, y)
            for x, y in pts_a
            if 0 <= x <= self.total_x and 0 <= y <= self.total_y
        ]
        if len(pts_a) < 2:
            return VMobject()
        # sort by A's x for a stable path
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
        # intersections with box edges
        # y=0
        x = m / price_x
        if 0 <= x <= self.total_x:
            candidates.append((x, 0.0))
        # y=total_y
        x = (m - self.total_y) / price_x
        if 0 <= x <= self.total_x:
            candidates.append((x, self.total_y))
        # x=0
        y = m
        if 0 <= y <= self.total_y:
            candidates.append((0.0, y))
        # x=total_x
        y = m - price_x * self.total_x
        if 0 <= y <= self.total_y:
            candidates.append((self.total_x, y))
        # unique-ish
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


def make_utility_label(
    name: str,
    bundle: tuple[float, float],
    alpha: float,
    color: str,
    font_size: int = 28,
) -> Text:
    u = utility(bundle[0], bundle[1], alpha)
    return Text(f"{name}: u ≈ {u:.2f}", font_size=font_size, color=color)
