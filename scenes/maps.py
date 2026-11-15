"""Individual indifference-curve + budget-line maps (agent × stage)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Dot,
    FadeIn,
    FadeOut,
    Scene,
    ValueTracker,
    VGroup,
    Write,
    always_redraw,
    linear,
)

from data import get_economy
from geometry import ppf_point, utility
from mobjects import BUDGET_COLOR, LabeledAxes
from style import mono, person_name


PPF_COLOR = "#43A047"
DOT_COLOR = "#76FF03"
AUTARKY_AXIS_MAX = 8.0
AUTARKY_SIZE = 5.5


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


def _stage_axis_max(stage, agent=None) -> tuple[float, float]:
    x_max = max(stage.total_x, 6.0)
    y_max = max(stage.total_y, 4.0)
    if agent is not None:
        x_max = max(x_max, agent.a_x)
        y_max = max(y_max, agent.a_y)
    return x_max, y_max


def _grey_for_level(t: float) -> str:
    """t in [0, 1]: 0 = dark grey, 1 = light grey."""
    t = max(0.0, min(1.0, t))
    c = int(70 + t * (210 - 70))
    return f"#{c:02x}{c:02x}{c:02x}"


class _PersonStageMap(Scene):
    agent_key: str = "a"
    stage_key: str = "autarky"

    def construct(self):
        eco = _economy()
        agent = eco.agent(self.agent_key)
        stage = eco.stage(self.stage_key)

        if self.agent_key == "a":
            produce, consume = stage.produce_a, stage.consume_a
        else:
            produce, consume = stage.produce_b, stage.consume_b

        if self.stage_key == "autarky":
            self._construct_autarky(eco, agent, stage, produce)
        else:
            self._construct_trade(eco, agent, stage, produce, consume)

    def _construct_autarky(self, eco, agent, stage, optimum):
        name = person_name(agent.name, color=agent.color)
        axes = LabeledAxes(
            AUTARKY_AXIS_MAX,
            AUTARKY_AXIS_MAX,
            eco.good_x,
            eco.good_y,
            width=AUTARKY_SIZE,
            height=AUTARKY_SIZE,
            tip_length=0.03,
        ).shift(LEFT * 0.6)

        def _w_label(u: float):
            lbl = mono(f"w = {u:.2f}", font_size=28)
            lbl.next_to(axes, RIGHT, buff=0.45)
            lbl.align_to(axes, UP).shift(DOWN * 0.3)
            return lbl

        self.play(FadeIn(name), FadeIn(axes))

        # --- 1) IC sweep: accumulate (low → high; darker → lighter) ---
        u_opt = utility(*optimum, eco.alpha)
        u_levels = [u_opt * f for f in (0.35, 0.55, 0.75, 0.95, 1.15, 1.35, 1.55)]
        u_lo, u_hi = u_levels[0], u_levels[-1]
        drawn = VGroup()
        w_lbl = None
        for u in u_levels:
            t = (u - u_lo) / (u_hi - u_lo)
            curve = axes.plot_ic(u, eco.alpha, _grey_for_level(t), stroke_width=3)
            new_w = _w_label(u)
            if w_lbl is None:
                self.play(Write(curve), FadeIn(new_w), run_time=0.4)
            else:
                self.play(Write(curve), FadeOut(w_lbl), FadeIn(new_w), run_time=0.4)
            w_lbl = new_w
            drawn.add(curve)

        # --- 2) Clear all indifference curves ---
        self.play(FadeOut(drawn), FadeOut(w_lbl), run_time=0.6)

        # --- 3) Budget + bright green dot ---
        t_lo, t_hi = 0.08, 0.92
        t_opt = max(t_lo, min(t_hi, optimum[0] / agent.a_x if agent.a_x else t_lo))
        tracker = ValueTracker(t_lo)

        def _bundle():
            return ppf_point(agent.a_x, agent.a_y, tracker.get_value())

        def _u():
            return utility(*_bundle(), eco.alpha)

        def _ic_color():
            u_corner = utility(*ppf_point(agent.a_x, agent.a_y, t_lo), eco.alpha)
            u = _u()
            t = 0.0 if u_opt <= u_corner else (u - u_corner) / (u_opt - u_corner + 1e-9)
            return _grey_for_level(max(0.0, min(1.0, t)))

        budget = axes.ppf_line(agent.a_x, agent.a_y, color=PPF_COLOR)
        dot = always_redraw(
            lambda: Dot(axes.c2p(*_bundle()), color=DOT_COLOR, radius=0.1)
        )
        cursors = always_redraw(
            lambda: axes.cursor_ticks(*_bundle(), DOT_COLOR)
        )
        self.play(Write(budget), FadeIn(dot), FadeIn(cursors))

        # --- 4) Dot alone: back and forth once ---
        self.play(tracker.animate.set_value(t_hi), run_time=2.0, rate_func=linear)
        self.play(tracker.animate.set_value(t_lo), run_time=2.0, rate_func=linear)

        # --- 5) Tangent ICs while dot keeps moving (a couple of times) ---
        live_ic = always_redraw(
            lambda: axes.plot_ic(_u(), eco.alpha, _ic_color(), stroke_width=3)
        )
        live_w = always_redraw(lambda: _w_label(_u()))
        self.add(live_ic, live_w)
        for _ in range(2):
            self.play(tracker.animate.set_value(t_hi), run_time=2.0, rate_func=linear)
            self.play(tracker.animate.set_value(t_lo), run_time=2.0, rate_func=linear)

        self.play(tracker.animate.set_value(t_opt), run_time=1.4, rate_func=linear)

        final_ic = axes.plot_ic(u_opt, eco.alpha, _grey_for_level(1.0), stroke_width=3.5)
        final_dot = Dot(axes.c2p(*optimum), color=DOT_COLOR, radius=0.1)
        final_cursors = axes.cursor_ticks(*optimum, DOT_COLOR)
        final_w = _w_label(u_opt)
        self.play(
            FadeOut(live_ic),
            FadeOut(live_w),
            FadeOut(dot),
            FadeOut(cursors),
            FadeIn(final_ic),
            FadeIn(final_dot),
            FadeIn(final_cursors),
            FadeIn(final_w),
            run_time=0.5,
        )
        self.wait(2)

    def _construct_trade(self, eco, agent, stage, produce, consume):
        x_max, y_max = _stage_axis_max(stage, agent)
        name = person_name(agent.name, color=agent.color)

        axes = LabeledAxes(
            x_max,
            y_max,
            eco.good_x,
            eco.good_y,
            width=6.0,
            height=4.2,
        ).shift(DOWN * 0.15)

        u0 = utility(*produce, eco.alpha)
        u1 = utility(*consume, eco.alpha)
        curves = [axes.plot_ic(u0, eco.alpha, agent.color, stroke_width=2)]
        if abs(u1 - u0) > 1e-3:
            curves.append(axes.plot_ic(u1, eco.alpha, agent.color, stroke_width=3))
        curves.append(
            axes.plot_ic(max(u0, u1) * 1.25, eco.alpha, agent.color, stroke_width=1.5)
        )

        omega_dot = Dot(axes.c2p(*produce), color="#FFFFFF", radius=0.08)
        consume_dot = Dot(axes.c2p(*consume), color=BUDGET_COLOR, radius=0.08)

        self.play(FadeIn(name), FadeIn(axes))
        for curve in curves:
            self.play(Write(curve), run_time=0.6)

        self.play(FadeIn(omega_dot))
        budget = axes.budget_line(produce, stage.price_x)
        self.play(Write(budget))
        self.play(FadeIn(consume_dot))
        self.wait(2)


class AgentAAutarkyMap(_PersonStageMap):
    agent_key = "a"
    stage_key = "autarky"


class AgentAExchangeMap(_PersonStageMap):
    agent_key = "a"
    stage_key = "exchange"


class AgentASpecializationMap(_PersonStageMap):
    agent_key = "a"
    stage_key = "specialization"


class AgentBAutarkyMap(_PersonStageMap):
    agent_key = "b"
    stage_key = "autarky"


class AgentBExchangeMap(_PersonStageMap):
    agent_key = "b"
    stage_key = "exchange"


class AgentBSpecializationMap(_PersonStageMap):
    agent_key = "b"
    stage_key = "specialization"
