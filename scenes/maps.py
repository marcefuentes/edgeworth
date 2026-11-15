"""Individual indifference-curve + budget-line maps (agent × stage)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import DOWN, Dot, UR, UP, FadeIn, Scene, Text, Write

from data import get_economy
from geometry import utility
from mobjects import BUDGET_COLOR, LabeledAxes, make_utility_label


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


def _stage_axis_max(stage) -> tuple[float, float]:
    return max(stage.total_x, 6.0), max(stage.total_y, 4.0)


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

        x_max, y_max = _stage_axis_max(stage)
        title = Text(
            f"{agent.name} — {stage.title}",
            font_size=34,
            color=agent.color,
        ).to_edge(UP)

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
        omega_lbl = Text("ω", font_size=26).next_to(omega_dot, DOWN, buff=0.12)

        consume_dot = Dot(axes.c2p(*consume), color=BUDGET_COLOR, radius=0.08)
        consume_lbl = Text("C", font_size=26, color=BUDGET_COLOR).next_to(
            consume_dot, UP, buff=0.12
        )

        util_lbl = make_utility_label(
            agent.name, consume, eco.alpha, agent.color
        ).to_corner(UR).shift(DOWN * 0.8)

        self.play(Write(title))
        self.play(FadeIn(axes))
        for curve in curves:
            self.play(Write(curve), run_time=0.6)

        self.play(FadeIn(omega_dot), Write(omega_lbl))

        if stage.price_x is not None:
            budget = axes.budget_line(produce, stage.price_x)
            price_lbl = Text(
                f"P({eco.good_x}) = {stage.price_x}",
                font_size=24,
                color=BUDGET_COLOR,
            ).next_to(title, DOWN, buff=0.2)
            self.play(Write(budget), FadeIn(price_lbl))
            self.play(FadeIn(consume_dot), Write(consume_lbl))
        else:
            note = Text("Autarquía: C = ω", font_size=24).to_edge(DOWN)
            self.play(Write(note))

        self.play(FadeIn(util_lbl))
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
