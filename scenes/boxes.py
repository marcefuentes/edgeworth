"""Edgeworth-box scenes for the three stages."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UL,
    UP,
    FadeIn,
    FadeOut,
    Indicate,
    Scene,
    Text,
    Transform,
    VGroup,
    Write,
)

from data import get_economy
from geometry import utility
from mobjects import BUDGET_COLOR, EdgeworthBox, make_utility_label


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


class AutarkyBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("autarky")
        title = Text(stage.title, font_size=36).to_edge(UP)
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

        omega = box.allocation_dot(stage.consume_a)
        omega_lbl = Text("ω", font_size=28).next_to(omega, UP, buff=0.15)

        u_a = utility(*stage.consume_a, eco.alpha)
        u_b = utility(*stage.consume_b, eco.alpha)
        ic_a = box.plot_ic_a(u_a, eco.alpha)
        ic_b = box.plot_ic_b(u_b, eco.alpha)

        utils = VGroup(
            make_utility_label(
                eco.agent_a.name, stage.consume_a, eco.alpha, eco.agent_a.color
            ),
            make_utility_label(
                eco.agent_b.name, stage.consume_b, eco.alpha, eco.agent_b.color
            ),
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(UL).shift(DOWN * 0.9)

        note = Text(
            "Sin intercambio: cada uno consume lo que produce",
            font_size=24,
        ).to_edge(DOWN)

        self.play(Write(title))
        self.play(FadeIn(box))
        self.play(FadeIn(omega), Write(omega_lbl))
        self.play(Write(ic_a), Write(ic_b))
        self.play(FadeIn(utils), Write(note))
        self.wait(2)


class ExchangeBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("exchange")
        title = Text(stage.title, font_size=36).to_edge(UP)
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

        omega = box.allocation_dot(stage.produce_a)
        omega_lbl = Text("ω", font_size=28).next_to(omega, DOWN, buff=0.15)
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        eq_lbl = Text("E", font_size=28, color=BUDGET_COLOR).next_to(eq, UP, buff=0.15)

        budget = box.budget_through(stage.produce_a, stage.price_x)

        u_a0 = utility(*stage.produce_a, eco.alpha)
        u_b0 = utility(*stage.produce_b, eco.alpha)
        u_a1 = utility(*stage.consume_a, eco.alpha)
        u_b1 = utility(*stage.consume_b, eco.alpha)
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=2)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=2)
        ic_a1 = box.plot_ic_a(u_a1, eco.alpha)
        ic_b1 = box.plot_ic_b(u_b1, eco.alpha)

        trade = stage.trade_a
        trade_lbl = Text(
            f"Intercambian: {abs(trade[0]):.1f} {eco.good_x}, "
            f"{abs(trade[1]):.1f} {eco.good_y}",
            font_size=24,
        ).to_edge(DOWN)
        price_lbl = Text(
            f"P({eco.good_x}) = {stage.price_x}",
            font_size=24,
            color=BUDGET_COLOR,
        ).next_to(title, DOWN, buff=0.25)

        utils = VGroup(
            make_utility_label(
                eco.agent_a.name, stage.consume_a, eco.alpha, eco.agent_a.color
            ),
            make_utility_label(
                eco.agent_b.name, stage.consume_b, eco.alpha, eco.agent_b.color
            ),
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(UL).shift(DOWN * 0.9)

        self.play(Write(title), FadeIn(price_lbl))
        self.play(FadeIn(box))
        self.play(FadeIn(omega), Write(omega_lbl), Write(ic_a0), Write(ic_b0))
        self.play(Write(budget))
        self.play(FadeIn(eq), Write(eq_lbl))
        self.play(Write(ic_a1), Write(ic_b1))
        self.play(FadeIn(utils), Write(trade_lbl))
        self.play(Indicate(eq))
        self.wait(2)


class SpecializationBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("specialization")
        prev = eco.stage("exchange")
        title = Text(stage.title, font_size=34).to_edge(UP)

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

        size_note = Text(
            f"Caja {prev.total_x:.0f}×{prev.total_y:.0f} → "
            f"{stage.total_x:.0f}×{stage.total_y:.0f}",
            font_size=26,
        ).to_edge(DOWN)

        self.play(Write(title))
        self.play(FadeIn(box_old))
        self.play(Write(size_note))
        self.play(Transform(box_old, box_new), run_time=1.5)

        # After Transform, build overlays on the target geometry
        box = box_new
        self.remove(box_old)
        self.add(box)

        omega = box.allocation_dot(stage.produce_a)
        omega_lbl = Text("ω′", font_size=28).next_to(omega, RIGHT, buff=0.15)
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        eq_lbl = Text("E′", font_size=28, color=BUDGET_COLOR).next_to(eq, UP, buff=0.15)
        budget = box.budget_through(stage.produce_a, stage.price_x)

        u_a1 = utility(*stage.consume_a, eco.alpha)
        u_b1 = utility(*stage.consume_b, eco.alpha)
        ic_a1 = box.plot_ic_a(u_a1, eco.alpha)
        ic_b1 = box.plot_ic_b(u_b1, eco.alpha)

        utils = VGroup(
            make_utility_label(
                eco.agent_a.name, stage.consume_a, eco.alpha, eco.agent_a.color
            ),
            make_utility_label(
                eco.agent_b.name, stage.consume_b, eco.alpha, eco.agent_b.color
            ),
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(UL).shift(DOWN * 0.9)

        gains = Text(
            "Producción ampliada por especialización",
            font_size=24,
        ).to_edge(DOWN)

        self.play(FadeIn(omega), Write(omega_lbl))
        self.play(Write(budget))
        self.play(FadeIn(eq), Write(eq_lbl), Write(ic_a1), Write(ic_b1))
        self.play(FadeOut(size_note), FadeIn(utils), Write(gains))
        self.wait(2)
