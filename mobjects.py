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
    FadeIn,
    FadeOut,
    FadeTransform,
    Line,
    ReplacementTransform,
    Rotate,
    Transform,
    VGroup,
    VMobject,
    smooth,
)

from geometry import EPS, clip_domain_for_ic, contract_point, flip_to_a
from style import AXIS_NUMBER_SIZE, AXIS_TITLE_SIZE, DOT_COLOR, mono


BUDGET_COLOR = "#E76F51"
CONTRACT_COLOR = DOT_COLOR  # brilliant green (same as allocation dot)
ENDOWMENT_COLOR = WHITE
TICK_SIZE = 0.08


def _stroke_only(color, stroke_width: float) -> VMobject:
    """Curve mobject with no fill (avoids area shading when opacity changes)."""
    curve = VMobject(stroke_width=stroke_width, fill_opacity=0)
    curve.set_stroke(color=color, width=stroke_width, opacity=1)
    return curve


def _tick_step(span: float) -> float:
    """Match map chrome: every 2 units on the usual 4–8 spans."""
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


def _axis_number_labels(
    axes: Axes, x_max: float, y_max: float, color=GREY_B
) -> VGroup:
    labels = VGroup()
    step_x = _tick_step(x_max)
    step_y = _tick_step(y_max)
    x = step_x
    while x <= x_max + 1e-9:
        labels.add(
            mono(f"{x:g}", font_size=AXIS_NUMBER_SIZE, color=color).next_to(
                axes.coords_to_point(x, 0), DOWN, buff=0.12
            )
        )
        x += step_x
    y = step_y
    while y <= y_max + 1e-9:
        labels.add(
            mono(f"{y:g}", font_size=AXIS_NUMBER_SIZE, color=color).next_to(
                axes.coords_to_point(0, y), LEFT, buff=0.12
            )
        )
        y += step_y
    return labels


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
        color=GREY_B,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.x_max = x_max
        self.y_max = y_max
        self.color = color
        self._step_x = _tick_step(x_max)
        self._step_y = _tick_step(y_max)
        self.axes = Axes(
            x_range=[0, x_max, self._step_x],
            y_range=[0, y_max, self._step_y],
            x_length=width,
            y_length=height,
            axis_config={
                "include_numbers": False,
                "color": color,
                "tick_size": TICK_SIZE,
            },
            tips=False,
        )
        _set_outward_ticks(self.axes.x_axis, DOWN)
        _set_outward_ticks(self.axes.y_axis, LEFT)
        # Same SW-anchored title placement as EdgeworthBox agent-A chrome.
        title_buff = 0.4
        bl = self.axes.coords_to_point(0, 0)
        xl = mono(x_label, font_size=AXIS_TITLE_SIZE, color=color)
        xl.next_to(bl, DOWN, buff=title_buff)
        xl.shift(RIGHT * (xl.width / 2 + 0.08))
        yl = mono(y_label, font_size=AXIS_TITLE_SIZE, color=color).rotate(PI / 2)
        yl.next_to(bl, LEFT, buff=title_buff)
        yl.shift(UP * (yl.height / 2 + 0.08))

        self.x_title = xl
        self.y_title = yl
        self.x_numbers = VGroup()
        self.y_numbers = VGroup()
        self.x_number_vals: list[float] = []
        self.y_number_vals: list[float] = []
        x = self._step_x
        while x <= x_max + 1e-9:
            self.x_number_vals.append(x)
            self.x_numbers.add(
                mono(f"{x:g}", font_size=AXIS_NUMBER_SIZE, color=color).next_to(
                    self.axes.coords_to_point(x, 0), DOWN, buff=0.12
                )
            )
            x += self._step_x
        y = self._step_y
        while y <= y_max + 1e-9:
            self.y_number_vals.append(y)
            self.y_numbers.add(
                mono(f"{y:g}", font_size=AXIS_NUMBER_SIZE, color=color).next_to(
                    self.axes.coords_to_point(0, y), LEFT, buff=0.12
                )
            )
            y += self._step_y

        self.add(self.axes, xl, yl, self.x_numbers, self.y_numbers)

    def c2p(self, x: float, y: float):
        return self.axes.coords_to_point(x, y)

    def play_shrink_to(
        self,
        scene,
        target_x: float,
        target_y: float,
        *,
        extra_anims: tuple = (),
        run_time: float = 1.4,
    ) -> None:
        """Shrink axes about the shared SW origin to ``(target_x, target_y)``.

        Ticks/numbers at or inside the target stay put; marks past the new
        frontier fade out (inverse of EdgeworthBox.play_grow_to).
        """
        sw = self.c2p(0, 0)
        new_br = self.c2p(target_x, 0)
        new_tl = self.c2p(0, target_y)

        x_axis = self.axes.x_axis
        y_axis = self.axes.y_axis
        x_ticks = x_axis.ticks
        y_ticks = y_axis.ticks
        x_axis.remove(x_ticks)
        y_axis.remove(y_ticks)
        scene.add(x_ticks, y_ticks)

        x_vals = list(x_axis.get_tick_range())
        y_vals = list(y_axis.get_tick_range())
        outer = VGroup()
        for tick, val in zip(x_ticks, x_vals):
            if val > target_x + 1e-9:
                outer.add(tick)
        for tick, val in zip(y_ticks, y_vals):
            if val > target_y + 1e-9:
                outer.add(tick)
        for label, val in zip(self.x_numbers, self.x_number_vals):
            if val > target_x + 1e-9:
                outer.add(label)
        for label, val in zip(self.y_numbers, self.y_number_vals):
            if val > target_y + 1e-9:
                outer.add(label)

        anims = [
            x_axis.animate.put_start_and_end_on(sw, new_br),
            y_axis.animate.put_start_and_end_on(sw, new_tl),
        ]
        if len(outer) > 0:
            anims.append(FadeOut(outer))
        anims.extend(extra_anims)
        scene.play(*anims, run_time=run_time)

    def cursor_ticks(
        self,
        x: float,
        y: float,
        color=None,
        *,
        tick_size: float = TICK_SIZE * 1.75,
        stroke_width: float = 4,
    ) -> VGroup:
        """Outward ticks on each axis at the projection of (x, y).

        Defaults to this chart's axis chrome color.
        """
        c = self.color if color is None else color
        px = self.c2p(x, 0)
        py = self.c2p(0, y)
        return VGroup(
            Line(px, px + DOWN * tick_size, color=c, stroke_width=stroke_width),
            Line(py, py + LEFT * tick_size, color=c, stroke_width=stroke_width),
        )

    def plot_ic(self, u: float, alpha: float, color: str, stroke_width: float = 3):
        pts = clip_domain_for_ic(u, alpha, self.x_max, self.y_max)
        if len(pts) < 2:
            return VMobject()
        curve = _stroke_only(color, stroke_width)
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
        agent_b_at_final: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.total_x = total_x
        self.total_y = total_y
        self.agent_a_name = agent_a_name
        self.agent_b_name = agent_b_name
        self.good_x = good_x
        self.good_y = good_y
        self._title_buff = 0.4
        self._agent_b_at_final = agent_b_at_final
        if height is None:
            height = width * (total_y / total_x)
        self._width = width
        self._height = height

        axis_cfg = {
            "include_numbers": False,
            "tick_size": TICK_SIZE,
        }
        self.axes_a = Axes(
            x_range=[0, total_x, _tick_step(total_x)],
            y_range=[0, total_y, _tick_step(total_y)],
            x_length=width,
            y_length=height,
            axis_config={**axis_cfg, "color": color_a},
            tips=False,
        )
        _set_outward_ticks(self.axes_a.x_axis, DOWN)
        _set_outward_ticks(self.axes_a.y_axis, LEFT)

        bl = self.axes_a.coords_to_point(0, 0)
        br = self.axes_a.coords_to_point(total_x, 0)
        tl = self.axes_a.coords_to_point(0, total_y)
        tr = self.axes_a.coords_to_point(total_x, total_y)
        self._bl, self._br, self._tl, self._tr = bl, br, tl, tr

        border = VMobject(color=GREY_B, stroke_width=2)
        border.set_points_as_corners([bl, br, tr, tl, bl])

        # Agent A titles + numbers (always final SW orientation)
        xa = mono(good_x, font_size=AXIS_TITLE_SIZE, color=color_a)
        xa.next_to(bl, DOWN, buff=self._title_buff)
        xa.shift(RIGHT * (xa.width / 2 + 0.08))
        ya = mono(good_y, font_size=AXIS_TITLE_SIZE, color=color_a).rotate(PI / 2)
        ya.next_to(bl, LEFT, buff=self._title_buff)
        ya.shift(UP * (ya.height / 2 + 0.08))
        labels_a = _axis_number_labels(self.axes_a, total_x, total_y, color_a)

        self.color_a = color_a
        self.color_b = color_b
        self.chrome_a = VGroup(self.axes_a, xa, ya, labels_a)
        self.border = border

        # Agent B: either already at NE, or starting as a normal SW chart to rotate in.
        self.b_geom, self.b_labels_sw, self.b_labels_ne = self._build_agent_b_parts(
            color_b
        )
        if agent_b_at_final:
            self.chrome_b = VGroup(self.b_geom, self.b_labels_ne)
            self.add(border, self.chrome_a, self.chrome_b)
        else:
            # Start in SW orientation (0 at SW); NE labels ready for after rotation.
            self.b_labels_ne.set_opacity(0)
            self.chrome_b = VGroup(self.b_geom, self.b_labels_sw)
            self.add(border, self.chrome_a, self.chrome_b, self.b_labels_ne)

    def _tick_values(self, span: float) -> list[float]:
        step = _tick_step(span)
        vals = []
        v = step
        while v <= span + 1e-9:
            vals.append(v)
            v += step
        return vals

    def _corner(self, x: float, y: float):
        """Live box corner in scene coords (safe after shifts)."""
        return self.axes_a.coords_to_point(x, y)

    def _axis_line(self, start, end, color: str) -> Line:
        return Line(start, end, color=color, stroke_width=2)

    def _make_b_sw_geom(self, color_b: str) -> VGroup:
        """Bottom+left axes for agent B in standard SW orientation, on the box edges."""
        bl = self._corner(0, 0)
        br = self._corner(self.total_x, 0)
        tl = self._corner(0, self.total_y)
        x_axis = self._axis_line(bl, br, color_b)
        y_axis = self._axis_line(bl, tl, color_b)
        x_ticks = _edge_ticks(
            [self._corner(x, 0) for x in self._tick_values(self.total_x)],
            DOWN,
            color_b,
        )
        y_ticks = _edge_ticks(
            [self._corner(0, y) for y in self._tick_values(self.total_y)],
            LEFT,
            color_b,
        )
        return VGroup(x_axis, y_axis, x_ticks, y_ticks)

    def _make_b_ne_geom(self, color_b: str) -> VGroup:
        """Top+right axes for agent B in final Edgeworth orientation, on the box edges."""
        tr = self._corner(self.total_x, self.total_y)
        tl = self._corner(0, self.total_y)
        br = self._corner(self.total_x, 0)
        x_axis = self._axis_line(tr, tl, color_b)  # B's x increases leftward
        y_axis = self._axis_line(tr, br, color_b)  # B's y increases downward
        x_ticks = _edge_ticks(
            [
                self._corner(self.total_x - bx, self.total_y)
                for bx in self._tick_values(self.total_x)
            ],
            UP,
            color_b,
        )
        y_ticks = _edge_ticks(
            [
                self._corner(self.total_x, self.total_y - by)
                for by in self._tick_values(self.total_y)
            ],
            RIGHT,
            color_b,
        )
        return VGroup(x_axis, y_axis, x_ticks, y_ticks)

    def _build_agent_b_parts(self, color_b: str):
        """Geometry + SW labels + NE labels for agent B."""
        total_x, total_y = self.total_x, self.total_y
        title_buff = self._title_buff
        bl = self._corner(0, 0)
        tr = self._corner(total_x, total_y)

        b_geom = (
            self._make_b_ne_geom(color_b)
            if self._agent_b_at_final
            else self._make_b_sw_geom(color_b)
        )

        # --- SW labels (readable in standard orientation) ---
        xb_sw = mono(self.good_x, font_size=AXIS_TITLE_SIZE, color=color_b)
        xb_sw.next_to(bl, DOWN, buff=title_buff)
        xb_sw.shift(RIGHT * (xb_sw.width / 2 + 0.08))
        yb_sw = mono(self.good_y, font_size=AXIS_TITLE_SIZE, color=color_b).rotate(
            PI / 2
        )
        yb_sw.next_to(bl, LEFT, buff=title_buff)
        yb_sw.shift(UP * (yb_sw.height / 2 + 0.08))
        labels_sw = VGroup()
        for x in self._tick_values(total_x):
            labels_sw.add(
                mono(f"{x:g}", font_size=AXIS_NUMBER_SIZE, color=color_b).next_to(
                    self._corner(x, 0), DOWN, buff=0.12
                )
            )
        for y in self._tick_values(total_y):
            labels_sw.add(
                mono(f"{y:g}", font_size=AXIS_NUMBER_SIZE, color=color_b).next_to(
                    self._corner(0, y), LEFT, buff=0.12
                )
            )
        b_labels_sw = VGroup(xb_sw, yb_sw, labels_sw)

        # --- NE labels (final Edgeworth orientation) ---
        xb_ne = mono(self.good_x, font_size=AXIS_TITLE_SIZE, color=color_b)
        xb_ne.next_to(tr, UP, buff=title_buff)
        xb_ne.shift(LEFT * (xb_ne.width / 2 + 0.08))
        yb_ne = mono(self.good_y, font_size=AXIS_TITLE_SIZE, color=color_b).rotate(
            -PI / 2
        )
        yb_ne.next_to(tr, RIGHT, buff=title_buff)
        yb_ne.shift(DOWN * (yb_ne.height / 2 + 0.08))
        labels_ne = VGroup()
        for bx in self._tick_values(total_x):
            pt = self._corner(total_x - bx, total_y)
            labels_ne.add(
                mono(f"{bx:g}", font_size=AXIS_NUMBER_SIZE, color=color_b).next_to(
                    pt, UP, buff=0.12
                )
            )
        for by in self._tick_values(total_y):
            pt = self._corner(total_x, total_y - by)
            labels_ne.add(
                mono(f"{by:g}", font_size=AXIS_NUMBER_SIZE, color=color_b).next_to(
                    pt, RIGHT, buff=0.12
                )
            )
        b_labels_ne = VGroup(xb_ne, yb_ne, labels_ne)

        return b_geom, b_labels_sw, b_labels_ne

    def play_rotate_b_into_box(
        self, scene, *extras, run_time: float = 2.5
    ) -> None:
        """Animate agent B's axes from SW orientation into the NE Edgeworth corner.

        Any *extras (e.g. B's SW optimum dot) rotate about the same center.
        """
        if self._agent_b_at_final:
            return
        # Geometric box center (not Axes.get_center — tips/ticks bias that).
        center = self.axes_a.coords_to_point(self.total_x / 2, self.total_y / 2)
        # Opacity — not FadeOut/FadeIn — so Scene.add/remove do not dissolve this
        # EdgeworthBox and promote its children (which drops the box from the scene).
        anims = [
            Rotate(self.b_geom, PI, about_point=center),
            self.b_labels_sw.animate.set_opacity(0),
        ]
        for m in extras:
            anims.append(Rotate(m, PI, about_point=center))
        scene.play(*anims, run_time=run_time, rate_func=smooth)
        # Settle onto canonical NE geom (identical edges) + final labels.
        ne_geom = self._make_b_ne_geom(self.color_b)
        scene.play(
            ReplacementTransform(self.b_geom, ne_geom),
            self.b_labels_ne.animate.set_opacity(1),
            run_time=0.3,
        )
        # Rebuild children to match agent_b_at_final=True: [border, chrome_a, chrome_b].
        old_chrome_b = self.chrome_b
        if ne_geom in old_chrome_b.submobjects:
            old_chrome_b.remove(ne_geom)
        if old_chrome_b in self.submobjects:
            self.remove(old_chrome_b)
        if self.b_labels_ne in self.submobjects:
            self.remove(self.b_labels_ne)
        self.b_geom = ne_geom
        self.chrome_b = VGroup(self.b_geom, self.b_labels_ne)
        self.add(self.chrome_b)
        self._agent_b_at_final = True
        # ReplacementTransform may have restructured scene tops; keep the box united.
        scene.add(self)

    def play_grow_to(
        self,
        scene,
        target: "EdgeworthBox",
        *,
        morphs: tuple = (),
        run_time: float = 1.6,
    ) -> None:
        """Grow the NE frontier to ``target``; SW ticks/numbers stay put.

        Axis lines lengthen about the shared SW origin. New ticks/numbers past
        the old totals fade in; agent B's NE chrome morphs with the corner.
        Optional ``morphs`` are ``(source, dest)`` pairs (e.g. ICs) transformed
        in parallel. The scene ends with ``target`` as the live box.
        """
        sw = self.c2p(0, 0)
        new_br = target.c2p(target.total_x, 0)
        new_tl = target.c2p(0, target.total_y)

        # Detach existing A ticks so lengthening the NumberLines cannot move them.
        x_axis = self.axes_a.x_axis
        y_axis = self.axes_a.y_axis
        x_ticks = x_axis.ticks
        y_ticks = y_axis.ticks
        x_axis.remove(x_ticks)
        y_axis.remove(y_ticks)
        scene.add(x_ticks, y_ticks)

        new_marks = VGroup()
        for x in target._tick_values(target.total_x):
            if x <= self.total_x + 1e-9:
                continue
            p = target.c2p(x, 0)
            tick = Line(p, p + DOWN * TICK_SIZE)
            tick.match_style(x_axis)
            label = mono(f"{x:g}", font_size=AXIS_NUMBER_SIZE, color=self.color_a).next_to(
                p, DOWN, buff=0.12
            )
            new_marks.add(tick, label)
        for y in target._tick_values(target.total_y):
            if y <= self.total_y + 1e-9:
                continue
            p = target.c2p(0, y)
            tick = Line(p, p + LEFT * TICK_SIZE)
            tick.match_style(y_axis)
            label = mono(f"{y:g}", font_size=AXIS_NUMBER_SIZE, color=self.color_a).next_to(
                p, LEFT, buff=0.12
            )
            new_marks.add(tick, label)

        border_target = target.border.copy()
        chrome_b_target = target.chrome_b.copy()
        anims = [
            Transform(self.border, border_target),
            x_axis.animate.put_start_and_end_on(sw, new_br),
            y_axis.animate.put_start_and_end_on(sw, new_tl),
            FadeTransform(self.chrome_b, chrome_b_target),
        ]
        if len(new_marks) > 0:
            anims.append(FadeIn(new_marks))
        for src, dst in morphs:
            anims.append(ReplacementTransform(src, dst))
        scene.play(*anims, run_time=run_time)

        # Swap to the canonical larger box (plotting / c2p stay correct).
        # Morph destinations stay — ReplacementTransform already put them on scene.
        scene.remove(self, x_ticks, y_ticks, new_marks, chrome_b_target)
        scene.add(target)

    def c2p(self, x: float, y: float):
        return self.axes_a.coords_to_point(x, y)

    def cursor_ticks(
        self,
        x: float,
        y: float,
        color_a=None,
        color_b=None,
        *,
        tick_size: float = TICK_SIZE * 1.75,
        stroke_width: float = 4,
    ) -> VGroup:
        """Outward ticks on A (SW) and B (NE) axes at allocation (x, y).

        Defaults to each agent's axis chrome color.
        """
        ca = self.color_a if color_a is None else color_a
        cb = self.color_b if color_b is None else color_b
        pa_x = self.c2p(x, 0)
        pa_y = self.c2p(0, y)
        pb_x = self.c2p(x, self.total_y)  # B's x on the top edge
        pb_y = self.c2p(self.total_x, y)  # B's y on the right edge
        return VGroup(
            Line(pa_x, pa_x + DOWN * tick_size, color=ca, stroke_width=stroke_width),
            Line(pa_y, pa_y + LEFT * tick_size, color=ca, stroke_width=stroke_width),
            Line(pb_x, pb_x + UP * tick_size, color=cb, stroke_width=stroke_width),
            Line(pb_y, pb_y + RIGHT * tick_size, color=cb, stroke_width=stroke_width),
        )

    def plot_ic_a(self, u: float, alpha: float, stroke_width: float = 3):
        pts = clip_domain_for_ic(u, alpha, self.total_x, self.total_y)
        if len(pts) < 2:
            return VMobject()
        curve = _stroke_only(self.color_a, stroke_width)
        curve.set_points_smoothly([self.c2p(x, y) for x, y in pts])
        return curve

    def plot_ic_b_sw(self, u: float, alpha: float, stroke_width: float = 3):
        """IC for B in SW (own-goods) orientation — rotate into the box with B's axes."""
        pts = clip_domain_for_ic(u, alpha, self.total_x, self.total_y)
        if len(pts) < 2:
            return VMobject()
        curve = _stroke_only(self.color_b, stroke_width)
        curve.set_points_smoothly([self.c2p(x, y) for x, y in pts])
        return curve

    def plot_ic_b(self, u: float, alpha: float, stroke_width: float = 3):
        """IC for B, drawn in final Edgeworth (A) coordinates."""
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
        curve = _stroke_only(self.color_b, stroke_width)
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

    def plot_contract(
        self,
        t0: float = 0.0,
        t1: float = 1.0,
        *,
        color: str = CONTRACT_COLOR,
        stroke_width: float = 2,
        n: int = 60,
    ) -> VMobject:
        """Segment of the contract curve (box diagonal for identical Cobb–Douglas)."""
        t0 = max(0.0, min(1.0, t0))
        t1 = max(0.0, min(1.0, t1))
        if t1 <= t0 + EPS:
            return VMobject()
        ts = [t0 + (t1 - t0) * i / (n - 1) for i in range(n)]
        curve = _stroke_only(color, stroke_width)
        curve.set_points_smoothly(
            [self.c2p(*contract_point(t, self.total_x, self.total_y)) for t in ts]
        )
        return curve
