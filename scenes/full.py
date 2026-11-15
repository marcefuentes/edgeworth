"""Full narrative: autarky → exchange → specialization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    DOWN,
    LEFT,
    FadeIn,
    FadeOut,
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
    a = person_name(eco.agent_a.name, color=eco.agent_a.color)
    b = mono(eco.agent_b.name, font_size=32, color=eco.agent_b.color)
    b.next_to(a, DOWN, aligned_edge=LEFT, buff=0.12)
    return a, b


class FullNarrative(Scene):
    def construct(self):
        eco = _economy()
        self._autarky(eco)
        self._exchange(eco)
        self._specialization(eco)

    def _autarky(self, eco):
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
        self.play(FadeIn(omega), Write(ic_a), Write(ic_b))
        self.wait(1.5)
        self.play(*[FadeOut(m) for m in self.mobjects])

    def _exchange(self, eco):
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
        ic_a = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)

        self.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box))
        self.play(FadeIn(omega), Write(budget))
        self.play(FadeIn(eq), Write(ic_a), Write(ic_b))
        self.wait(1.5)
        self.play(*[FadeOut(m) for m in self.mobjects])

    def _specialization(self, eco):
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
        self.play(Transform(box_old, box_new), run_time=1.2)
        self.remove(box_old)
        self.add(box_new)
        box = box_new

        omega = box.allocation_dot(stage.produce_a)
        eq = box.allocation_dot(stage.consume_a, color=BUDGET_COLOR)
        budget = box.budget_through(stage.produce_a, stage.price_x)
        ic_a = box.plot_ic_a(utility(*stage.consume_a, eco.alpha), eco.alpha)
        ic_b = box.plot_ic_b(utility(*stage.consume_b, eco.alpha), eco.alpha)

        self.play(FadeIn(omega), Write(budget))
        self.play(FadeIn(eq), Write(ic_a), Write(ic_b))
        self.wait(2)
