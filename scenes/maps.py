"""Individual indifference-curve + budget-line maps (agent × stage)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    Dot,
    FadeIn,
    FadeOut,
    ReplacementTransform,
    Scene,
    ValueTracker,
    VGroup,
    Write,
    always_redraw,
    linear,
)

from data import get_economy
from geometry import EPS, ppf_point, utility
from layout import chart_size, pin_sw
from mobjects import BUDGET_COLOR, LabeledAxes
from style import (
    DOT_COLOR,
    IC_LEVEL_FACTORS,
    grey_for_level,
    person_name,
    person_name_stacked,
)


PPF_COLOR = "#43A047"
AUTARKY_AXIS_X_MAX = 8.0
AUTARKY_AXIS_Y_MAX = 6.0


def _make_autarky_axes(eco, color) -> LabeledAxes:
    width, height = chart_size(AUTARKY_AXIS_X_MAX, AUTARKY_AXIS_Y_MAX)
    axes = LabeledAxes(
        AUTARKY_AXIS_X_MAX,
        AUTARKY_AXIS_Y_MAX,
        eco.good_x,
        eco.good_y,
        width=width,
        height=height,
        color=color,
    )
    return pin_sw(axes, axes.c2p(0, 0))


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


def _stage_axis_max(stage, agent=None) -> tuple[float, float]:
    x_max = max(stage.total_x, 6.0)
    y_max = max(stage.total_y, 4.0)
    if agent is not None:
        x_max = max(x_max, agent.a_x)
        y_max = max(y_max, agent.a_y)
    return x_max, y_max


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

    def _agent_name(self, agent, *, stacked: bool = False):
        """Primary UL name, or stacked agent-B slot (matches box stages)."""
        if stacked:
            return person_name_stacked(agent.name, color=agent.color)
        return person_name(agent.name, color=agent.color)

    def _recolor_map_frame(self, axes, name, agent, *, stacked: bool = False):
        """Swap person name + axis chrome color; keep geometry and ICs in place."""
        new_name = self._agent_name(agent, stacked=stacked)
        axes.color = agent.color
        self.play(
            FadeOut(name),
            FadeIn(new_name),
            axes.animate.set_color(agent.color),
            run_time=0.7,
        )
        return new_name

    def _play_ppf_optimum(
        self,
        axes,
        agent,
        optimum,
        eco,
        *,
        bare_pass: bool,
        existing_budget=None,
        existing_dot=None,
        existing_ic=None,
    ):
        """PPF + green dot (+ optional bare pass), then live ICs, then settle.

        ``existing_budget``: if set, keep that line (already morphed to this
        agent's PPF) and only introduce the cursors.
        ``existing_dot``: reuse the same green dot (move it; never fade it out).
        ``existing_ic``: IC already through the start bundle (e.g. after a
        handoff); faded when the live IC pass begins.
        """
        u_opt = utility(*optimum, eco.alpha)
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
            return grey_for_level(max(0.0, min(1.0, t)))

        budget = (
            existing_budget
            if existing_budget is not None
            else axes.ppf_line(agent.a_x, agent.a_y, color=PPF_COLOR)
        )
        start = axes.c2p(*_bundle())
        if existing_dot is None:
            dot = Dot(start, color=DOT_COLOR, radius=0.1)
            new_dot = True
        else:
            dot = existing_dot
            new_dot = False
        # Cursor ticks match axis chrome (agent color), not the green dot.
        axes.color = agent.color
        cursors = always_redraw(
            lambda: axes.cursor_ticks(*_bundle(), agent.color)
        )
        intro = []
        if existing_budget is None:
            intro.append(Write(budget))
        if new_dot:
            intro.append(FadeIn(dot))
        else:
            intro.append(dot.animate.move_to(start))
        intro.append(FadeIn(cursors))
        self.play(*intro)

        dot.add_updater(lambda m: m.move_to(axes.c2p(*_bundle())))

        if bare_pass:
            self.play(tracker.animate.set_value(t_hi), run_time=2.0, rate_func=linear)
            self.play(tracker.animate.set_value(t_lo), run_time=2.0, rate_func=linear)

        live_ic = always_redraw(
            lambda: axes.plot_ic(_u(), eco.alpha, _ic_color(), stroke_width=3)
        )
        self.add(live_ic)
        # One full PPF pass with the live IC, then settle on the optimum.
        first = [tracker.animate.set_value(t_hi)]
        if existing_ic is not None:
            first.append(FadeOut(existing_ic))
        self.play(*first, run_time=2.0, rate_func=linear)
        self.play(tracker.animate.set_value(t_lo), run_time=2.0, rate_func=linear)

        self.play(tracker.animate.set_value(t_opt), run_time=1.4, rate_func=linear)

        dot.clear_updaters()
        final_ic = axes.plot_ic(u_opt, eco.alpha, grey_for_level(1.0), stroke_width=3.5)
        final_cursors = axes.cursor_ticks(*optimum, agent.color)
        self.play(
            FadeOut(live_ic),
            FadeOut(cursors),
            FadeIn(final_ic),
            FadeIn(final_cursors),
            dot.animate.move_to(axes.c2p(*optimum)),
            run_time=0.5,
        )
        self.wait(1.2)
        return budget, final_ic, dot, final_cursors

    def _construct_autarky(self, eco, agent, stage, optimum, *, intro: str = "together"):
        """Single-agent autarky map (individual scenes)."""
        name = self._agent_name(agent, stacked=self.agent_key == "b")
        axes = _make_autarky_axes(eco, agent.color)

        if intro == "crossfade":
            outgoing = list(self.mobjects)
            self.play(
                *[FadeOut(m) for m in outgoing],
                FadeIn(name),
                FadeIn(axes),
                run_time=0.6,
            )
        else:
            self.play(FadeIn(name), FadeIn(axes))

        u_opt = utility(*optimum, eco.alpha)
        u_levels = [u_opt * f for f in IC_LEVEL_FACTORS]
        u_lo, u_hi = u_levels[0], u_levels[-1]
        drawn = VGroup()
        for u in u_levels:
            t = (u - u_lo) / (u_hi - u_lo)
            curve = axes.plot_ic(u, eco.alpha, grey_for_level(t), stroke_width=3)
            self.play(Write(curve), run_time=0.4)
            drawn.add(curve)

        self.play(FadeOut(drawn), run_time=0.6)
        self._play_ppf_optimum(axes, agent, optimum, eco, bare_pass=True)
        self.wait(0.8)

    def _construct_paired_autarky_maps(self, eco):
        """Shared prefs: Gonzalo ICs → Iván recolor → Gonzalo PPF → Iván PPF+ICs.

        Returns map leftovers used to morph into the autarky Edgeworth box.
        """
        agent_a = eco.agent("a")
        agent_b = eco.agent("b")
        stage = eco.stage("autarky")
        opt_a, opt_b = stage.produce_a, stage.produce_b

        name = person_name(agent_a.name, color=agent_a.color)
        axes = _make_autarky_axes(eco, agent_a.color)
        self.play(FadeIn(name), FadeIn(axes))

        # --- 1) Gonzalo IC family ---
        u_opt_a = utility(*opt_a, eco.alpha)
        u_levels = [u_opt_a * f for f in IC_LEVEL_FACTORS]
        u_lo, u_hi = u_levels[0], u_levels[-1]
        drawn = VGroup()
        for u in u_levels:
            t = (u - u_lo) / (u_hi - u_lo)
            curve = axes.plot_ic(u, eco.alpha, grey_for_level(t), stroke_width=3)
            self.play(Write(curve), run_time=0.4)
            drawn.add(curve)

        # --- 2) Same ICs under Iván's name/colors ---
        name = self._recolor_map_frame(axes, name, agent_b, stacked=True)
        self.wait(1.0)

        # --- 3) Back to Gonzalo; clear ICs; PPF with bare pass then live ICs ---
        name = self._recolor_map_frame(axes, name, agent_a)
        self.play(FadeOut(drawn), run_time=0.6)
        budget_a, final_ic_a, dot, final_cursors_a = self._play_ppf_optimum(
            axes, agent_a, opt_a, eco, bare_pass=True
        )

        # --- 4) Morph Gonzalo's PPF → Iván's; move the green dot with a live IC ---
        self.play(FadeOut(final_cursors_a), run_time=0.35)
        budget_b = axes.ppf_line(agent_b.a_x, agent_b.a_y, color=PPF_COLOR)
        new_name = self._agent_name(agent_b, stacked=True)
        axes.color = agent_b.color
        start_bundle = opt_a
        end_bundle = ppf_point(agent_b.a_x, agent_b.a_y, 0.08)
        u_lo = utility(*start_bundle, eco.alpha)
        u_hi = utility(*end_bundle, eco.alpha)
        u_min, u_max = min(u_lo, u_hi), max(u_lo, u_hi)
        handoff = ValueTracker(0.0)

        def _handoff_bundle():
            t = handoff.get_value()
            return (
                start_bundle[0] + t * (end_bundle[0] - start_bundle[0]),
                start_bundle[1] + t * (end_bundle[1] - start_bundle[1]),
            )

        def _handoff_ic():
            u = max(utility(*_handoff_bundle(), eco.alpha), EPS)
            # Keep the stroke readable even when utility falls toward Iván's start.
            if u_max <= u_min + 1e-9:
                level = 1.0
            else:
                level = 0.35 + 0.65 * (u - u_min) / (u_max - u_min)
            return axes.plot_ic(
                u, eco.alpha, grey_for_level(level), stroke_width=3.5
            )

        live_handoff = always_redraw(_handoff_ic)
        dot.clear_updaters()
        dot.add_updater(lambda m: m.move_to(axes.c2p(*_handoff_bundle())))
        self.add(live_handoff)
        self.bring_to_front(live_handoff, dot)
        self.play(
            FadeOut(final_ic_a),
            FadeOut(name),
            FadeIn(new_name),
            axes.animate.set_color(agent_b.color),
            ReplacementTransform(budget_a, budget_b),
            handoff.animate.set_value(1.0),
            run_time=1.2,
        )
        dot.clear_updaters()
        dot.move_to(axes.c2p(*end_bundle))
        handoff_ic = axes.plot_ic(
            max(u_hi, EPS), eco.alpha, grey_for_level(1.0), stroke_width=3.5
        )
        self.add(handoff_ic)
        self.bring_to_front(handoff_ic, dot)
        self.remove(live_handoff)
        name = new_name
        budget_b, final_ic, final_dot, final_cursors = self._play_ppf_optimum(
            axes,
            agent_b,
            opt_b,
            eco,
            bare_pass=False,
            existing_budget=budget_b,
            existing_dot=dot,
            existing_ic=handoff_ic,
        )
        self.wait(0.5)
        return {
            "axes": axes,
            "name": name,
            "budget": budget_b,
            "ic": final_ic,
            "dot": final_dot,
            "cursors": final_cursors,
        }

    def _construct_trade(self, eco, agent, stage, produce, consume):
        x_max, y_max = _stage_axis_max(stage, agent)
        name = self._agent_name(agent, stacked=self.agent_key == "b")
        width, height = chart_size(x_max, y_max)

        axes = LabeledAxes(
            x_max,
            y_max,
            eco.good_x,
            eco.good_y,
            width=width,
            height=height,
            color=agent.color,
        )
        pin_sw(axes, axes.c2p(0, 0))

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


class AutarkyMaps(_PersonStageMap):
    """Shared IC family, then Gonzalo PPF search, then Iván PPF+ICs."""

    def construct(self):
        self._construct_paired_autarky_maps(_economy())
