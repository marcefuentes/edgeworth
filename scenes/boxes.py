"""Edgeworth-box scenes for the three stages."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    DOWN,
    LEFT,
    FadeIn,
    Indicate,
    Scene,
    Transform,
    Write,
)

from data import get_economy
from geometry import utility
from mobjects import BUDGET_COLOR, EdgeworthBox
from style import mono, person_name


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


def _pair_name(eco):
    """Two names stacked upper-left (only non-axis text on box charts)."""
    a = person_name(eco.agent_a.name, color=eco.agent_a.color)
    b = mono(eco.agent_b.name, font_size=32, color=eco.agent_b.color)
    b.next_to(a, DOWN, aligned_edge=LEFT, buff=0.12)
    return a, b


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
        ).shift(DOWN * 0.2)

        omega = box.allocation_dot(stage.consume_a)
        ic_a = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)

        self.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box))
        self.play(FadeIn(omega))
        self.play(Write(ic_a), Write(ic_b))
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

        omega = box.allocation_dot(stage.produce_a)
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        budget = box.budget_through(stage.produce_a, stage.price_x)

        ic_a0 = box.plot_ic_a(utility(*stage.produce_a, eco.alpha), eco.alpha, stroke_width=2)
        ic_b0 = box.plot_ic_b(utility(*stage.produce_b, eco.alpha), eco.alpha, stroke_width=2)
        ic_a1 = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b1 = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)

        self.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box))
        self.play(FadeIn(omega), Write(ic_a0), Write(ic_b0))
        self.play(Write(budget))
        self.play(FadeIn(eq))
        self.play(Write(ic_a1), Write(ic_b1))
        self.play(Indicate(eq))
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
