"""Edgeworth-box scenes for the three stages."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    DOWN,
    LEFT,
    Dot,
    FadeIn,
    FadeOut,
    Scene,
    Transform,
    ValueTracker,
    VGroup,
    Write,
    always_redraw,
)

from data import get_economy
from geometry import contract_lens_t_range, utility
from mobjects import BUDGET_COLOR, CONTRACT_COLOR, EdgeworthBox
from style import DOT_COLOR, IC_LEVEL_FACTORS, grey_for_level, mono, person_name

DIM_OPACITY = 0.22


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


def _pair_name(eco):
    """Two names stacked upper-left (only non-axis text on box charts)."""
    a = person_name(eco.agent_a.name, color=eco.agent_a.color)
    b = mono(eco.agent_b.name, font_size=32, color=eco.agent_b.color)
    b.next_to(a, DOWN, aligned_edge=LEFT, buff=0.12)
    return a, b


def _ic_levels(u_opt: float) -> list[float]:
    return [u_opt * f for f in IC_LEVEL_FACTORS]


class AutarkyBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("autarky")
        name_a, name_b = _pair_name(eco)
        box = EdgeworthBox(
            stage.total_x,
            stage.total_y,
            eco.agent_a.name,
            eco.agent_b.name,
            eco.good_x,
            eco.good_y,
            eco.agent_a.color,
            eco.agent_b.color,
            agent_b_at_final=False,
        ).shift(DOWN * 0.2)

        # Dot starts on Iván's SW chart at his optimum; 180° rotation lands it
        # on the final Edgeworth allocation (consume_a).
        eq = Dot(box.c2p(*stage.consume_b), color=DOT_COLOR, radius=0.1)
        self.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box))

        u_b = utility(*stage.consume_b, eco.alpha)
        u_a = utility(*stage.consume_a, eco.alpha)

        # Focus Iván: dim Gonzalo; show Iván's axes + his SW optimum
        self.play(
            box.chrome_a.animate.set_opacity(DIM_OPACITY),
            name_a.animate.set_opacity(DIM_OPACITY),
            box.chrome_b.animate.set_opacity(1),
            name_b.animate.set_opacity(1),
            FadeIn(eq),
            run_time=0.5,
        )
        self.wait(0.4)

        # --- Iván ICs on his SW chart, then keep only the optimum ---
        levels_b = _ic_levels(u_b)
        drawn_b = VGroup()
        for u in levels_b:
            t = (u - levels_b[0]) / (levels_b[-1] - levels_b[0])
            curve = box.plot_ic_b_sw(u, eco.alpha, stroke_width=3)
            curve.set_color(grey_for_level(t))
            self.play(Write(curve), run_time=0.4)
            drawn_b.add(curve)
        opt_b = drawn_b[-1]
        lower_b = VGroup(*drawn_b[:-1])
        self.play(FadeOut(lower_b), opt_b.animate.set_stroke(width=3.5), run_time=0.6)

        # Rotate Iván's axes + optimum IC + dot into the NE Edgeworth corner
        box.play_rotate_b_into_box(self, eq, opt_b, run_time=2.5)
        eq.move_to(box.c2p(*stage.consume_a))
        # Snap IC to exact Edgeworth geometry after the rotate.
        final_b = box.plot_ic_b(u_b, eco.alpha, stroke_width=3.5)
        final_b.set_color(opt_b.get_color())
        self.remove(opt_b)
        self.add(final_b)
        opt_b = final_b

        # Focus Gonzalo: dim Iván's chrome + name
        self.play(
            box.chrome_b.animate.set_opacity(DIM_OPACITY),
            name_b.animate.set_opacity(DIM_OPACITY),
            box.chrome_a.animate.set_opacity(1),
            name_a.animate.set_opacity(1),
            run_time=0.5,
        )

        # --- Gonzalo (agent A): ICs up to optimum, then keep only that curve ---
        levels_a = _ic_levels(u_a)
        drawn_a = VGroup()
        for u in levels_a:
            t = (u - levels_a[0]) / (levels_a[-1] - levels_a[0])
            curve = box.plot_ic_a(u, eco.alpha, stroke_width=3)
            curve.set_color(grey_for_level(t))
            self.play(Write(curve), run_time=0.4)
            drawn_a.add(curve)
        opt_a = drawn_a[-1]
        lower_a = VGroup(*drawn_a[:-1])
        self.play(FadeOut(lower_a), opt_a.animate.set_stroke(width=3.5), run_time=0.6)

        # Restore both agents (green dot already sits at the shared optimum)
        self.play(
            box.chrome_a.animate.set_opacity(1),
            box.chrome_b.animate.set_opacity(1),
            name_a.animate.set_opacity(1),
            name_b.animate.set_opacity(1),
            run_time=0.45,
        )
        self.wait(2)


class ExchangeBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("exchange")
        name_a, name_b = _pair_name(eco)
        box = EdgeworthBox(
            stage.total_x,
            stage.total_y,
            eco.agent_a.name,
            eco.agent_b.name,
            eco.good_x,
            eco.good_y,
            eco.agent_a.color,
            eco.agent_b.color,
        ).shift(DOWN * 0.2)

        # --- 1) Same ending frame as AutarkyBox: endowment + two autarky ICs ---
        u_a0 = utility(*stage.produce_a, eco.alpha)
        u_b0 = utility(*stage.produce_b, eco.alpha)
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
        ic_color = grey_for_level(1.0)
        ic_a0.set_color(ic_color)
        ic_b0.set_color(ic_color)
        eq = Dot(box.c2p(*stage.produce_a), color=DOT_COLOR, radius=0.1)

        self.play(
            FadeIn(name_a),
            FadeIn(name_b),
            FadeIn(box),
            FadeIn(ic_a0),
            FadeIn(ic_b0),
            FadeIn(eq),
        )
        self.wait(0.4)

        # --- 2) Thin brilliant-green contract curve (full diagonal) ---
        contract_thin = box.plot_contract(
            0.0, 1.0, color=CONTRACT_COLOR, stroke_width=1.5
        )
        self.play(Write(contract_thin), run_time=1.2)
        self.wait(0.3)

        # --- 3) Thicken only the lens segment (inside both endowment ICs) ---
        t_lo, t_hi = contract_lens_t_range(
            stage.produce_a, stage.total_x, stage.total_y, eco.alpha
        )
        contract_thick = box.plot_contract(
            t_lo, t_hi, color=CONTRACT_COLOR, stroke_width=5.5
        )
        self.play(Write(contract_thick), run_time=0.9)
        self.wait(0.35)

        # --- 4) Move green dot to trade; live ICs through the moving point ---
        ox, oy = stage.produce_a
        cx, cy = stage.consume_a
        progress = ValueTracker(0.0)

        def _bundle():
            t = progress.get_value()
            return (ox + t * (cx - ox), oy + t * (cy - oy))

        def _live_a():
            curve = box.plot_ic_a(
                utility(*_bundle(), eco.alpha), eco.alpha, stroke_width=3.5
            )
            return curve.set_color(ic_color)

        def _live_b():
            xa, ya = _bundle()
            u_b = utility(stage.total_x - xa, stage.total_y - ya, eco.alpha)
            curve = box.plot_ic_b(u_b, eco.alpha, stroke_width=3.5)
            return curve.set_color(ic_color)

        live_a = always_redraw(_live_a)
        live_b = always_redraw(_live_b)
        eq.add_updater(lambda m: m.move_to(box.c2p(*_bundle())))

        self.add(live_a, live_b)
        self.play(progress.animate.set_value(1.0), run_time=2.0)
        eq.clear_updaters()
        self.remove(live_a, live_b)

        ic_a1 = box.plot_ic_a(
            utility(*stage.consume_a, eco.alpha), eco.alpha, stroke_width=3.5
        )
        ic_b1 = box.plot_ic_b(
            utility(*stage.consume_b, eco.alpha), eco.alpha, stroke_width=3.5
        )
        ic_a1.set_color(ic_color)
        ic_b1.set_color(ic_color)
        eq.move_to(box.c2p(*stage.consume_a))
        self.add(ic_a1, ic_b1)
        self.wait(2)


class SpecializationBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("specialization")
        prev = eco.stage("exchange")
        name_a, name_b = _pair_name(eco)

        box_old = EdgeworthBox(
            prev.total_x,
            prev.total_y,
            eco.agent_a.name,
            eco.agent_b.name,
            eco.good_x,
            eco.good_y,
            eco.agent_a.color,
            eco.agent_b.color,
            width=4.2,
        ).shift(DOWN * 0.3)

        box_new = EdgeworthBox(
            stage.total_x,
            stage.total_y,
            eco.agent_a.name,
            eco.agent_b.name,
            eco.good_x,
            eco.good_y,
            eco.agent_a.color,
            eco.agent_b.color,
            width=5.5,
        ).shift(DOWN * 0.2)

        self.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box_old))
        self.play(Transform(box_old, box_new), run_time=1.5)
        self.remove(box_old)
        self.add(box_new)
        box = box_new

        omega = box.allocation_dot(stage.produce_a)
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        budget = box.budget_through(stage.produce_a, stage.price_x)
        ic_a1 = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b1 = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)

        self.play(FadeIn(omega))
        self.play(Write(budget))
        self.play(FadeIn(eq), Write(ic_a1), Write(ic_b1))
        self.wait(2)
