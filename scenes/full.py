"""Full narrative: autarky → exchange → specialization."""

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


class FullNarrative(Scene):
    def construct(self):
        eco = _economy()
        header = Text(
            f"{eco.agent_a.name} y {eco.agent_b.name}",
            font_size=40,
        )
        subtitle = Text(
            f"{eco.good_x} y {eco.good_y}",
            font_size=28,
        ).next_to(header, DOWN)
        self.play(Write(header), FadeIn(subtitle))
        self.wait(1)
        self.play(FadeOut(header), FadeOut(subtitle))

        self._autarky(eco)
        self._exchange(eco)
        self._specialization(eco)

    def _autarky(self, eco):
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
        ic_a = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)
        utils = VGroup(
            make_utility_label(
                eco.agent_a.name, stage.consume_a, eco.alpha, eco.agent_a.color
            ),
            make_utility_label(
                eco.agent_b.name, stage.consume_b, eco.alpha, eco.agent_b.color
            ),
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(UL).shift(DOWN * 0.9)
        note = Text("Sin intercambio", font_size=24).to_edge(DOWN)

        self.play(Write(title), FadeIn(box))
        self.play(FadeIn(omega), Write(omega_lbl), Write(ic_a), Write(ic_b))
        self.play(FadeIn(utils), Write(note))
        self.wait(1.5)
        self.play(*[FadeOut(m) for m in self.mobjects])

    def _exchange(self, eco):
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
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        eq_lbl = Text("E", font_size=28, color=BUDGET_COLOR).next_to(eq, UP, buff=0.15)
        budget = box.budget_through(stage.produce_a, stage.price_x)
        ic_a = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)
        trade = stage.trade_a
        note = Text(
            f"Intercambian {abs(trade[0]):.1f} {eco.good_x}, "
            f"{abs(trade[1]):.1f} {eco.good_y}",
            font_size=24,
        ).to_edge(DOWN)

        self.play(Write(title), FadeIn(box))
        self.play(FadeIn(omega), Write(budget))
        self.play(FadeIn(eq), Write(eq_lbl), Write(ic_a), Write(ic_b), Write(note))
        self.wait(1.5)
        self.play(*[FadeOut(m) for m in self.mobjects])

    def _specialization(self, eco):
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

        self.play(Write(title), FadeIn(box_old))
        self.play(Transform(box_old, box_new), run_time=1.2)
        self.remove(box_old)
        self.add(box_new)
        box = box_new

        omega = box.allocation_dot(stage.produce_a)
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        eq_lbl = Text("E′", font_size=28, color=BUDGET_COLOR).next_to(eq, UP, buff=0.15)
        budget = box.budget_through(stage.produce_a, stage.price_x)
        ic_a = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)
        utils = VGroup(
            make_utility_label(
                eco.agent_a.name, stage.consume_a, eco.alpha, eco.agent_a.color
            ),
            make_utility_label(
                eco.agent_b.name, stage.consume_b, eco.alpha, eco.agent_b.color
            ),
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(UL).shift(DOWN * 0.9)
        note = Text(
            f"Caja {stage.total_x:.0f}×{stage.total_y:.0f} tras especialización",
            font_size=24,
        ).to_edge(DOWN)

        self.play(FadeIn(omega), Write(budget))
        self.play(
            FadeIn(eq),
            Write(eq_lbl),
            Write(ic_a),
            Write(ic_b),
            FadeIn(utils),
            Write(note),
        )
        self.wait(2)
