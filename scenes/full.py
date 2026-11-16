"""Full narrative: autarky maps → autarky box → exchange → specialization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import DOWN, Dot, FadeIn, FadeOut, FadeTransform, Scene

from data import get_economy
from geometry import utility
from mobjects import EdgeworthBox
from scenes.boxes import _pair_name, _play_autarky_box, _play_endowment_trade
from scenes.maps import _PersonStageMap
from style import DOT_COLOR, grey_for_level


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


class FullNarrative(_PersonStageMap):
    """Autarky maps, Iván's rotate-in box, then exchange and specialization.

    Section transitions keep something on screen (crossfade / grow) — no black gaps.
    """

    def construct(self):
        eco = _economy()
        self._autarky_maps(eco)
        name_a, name_b = self._autarky_box(eco)
        box = self._exchange_box(eco, name_a, name_b)
        box = self._grow_to_specialization(eco, box, name_a, name_b)
        self._specialization_box(eco, box, name_a, name_b)

    def _autarky_maps(self, eco):
        stage = eco.stage("autarky")
        for i, (key, produce) in enumerate(
            (
                ("a", stage.produce_a),
                ("b", stage.produce_b),
            )
        ):
            agent = eco.agent(key)
            intro = "crossfade" if i > 0 else "together"
            self._construct_autarky(eco, agent, stage, produce, intro=intro)

    def _autarky_box(self, eco):
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
        outgoing = list(self.mobjects)
        self.play(
            *[FadeOut(m) for m in outgoing],
            FadeIn(name_a),
            FadeIn(name_b),
            FadeIn(box),
            run_time=0.8,
        )
        _play_autarky_box(self, eco, stage, box, name_a, name_b, intro="resume")
        return name_a, name_b

    def _exchange_box(self, eco, name_a, name_b):
        """Fresh exchange geometry; crossfade from autarky end-frame (names stay)."""
        stage = eco.stage("exchange")
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
        ic_hi = grey_for_level(1.0)
        u_a0 = utility(*stage.produce_a, eco.alpha)
        u_b0 = utility(*stage.produce_b, eco.alpha)
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
        ic_a0.set_stroke(color=ic_hi)
        ic_b0.set_stroke(color=ic_hi)
        eq = Dot(box.c2p(*stage.produce_a), color=DOT_COLOR, radius=0.1)

        keep = {name_a, name_b}
        outgoing = [m for m in list(self.mobjects) if m not in keep]
        self.play(
            *[FadeOut(m) for m in outgoing],
            FadeIn(box),
            FadeIn(ic_a0),
            FadeIn(ic_b0),
            FadeIn(eq),
            run_time=0.8,
        )
        _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            intro="after_endowment",
            endowment_arts=(ic_a0, ic_b0, eq),
        )
        return box

    def _grow_to_specialization(self, eco, box_old, name_a, name_b):
        """Morph exchange box into the larger specialization box; names stay up."""
        stage = eco.stage("specialization")
        box_new = EdgeworthBox(
            stage.total_x,
            stage.total_y,
            eco.agent_a.name,
            eco.agent_b.name,
            eco.good_x,
            eco.good_y,
            eco.agent_a.color,
            eco.agent_b.color,
        ).shift(DOWN * 0.2)
        keep = {name_a, name_b, box_old}
        extras = [m for m in list(self.mobjects) if m not in keep]
        self.play(
            *[FadeOut(m) for m in extras],
            FadeTransform(box_old, box_new),
            run_time=1.5,
        )
        return box_new

    def _specialization_box(self, eco, box, name_a, name_b):
        stage = eco.stage("specialization")
        _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            endowment_a=stage.produce_a,
            intro="resume",
        )
