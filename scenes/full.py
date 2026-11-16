"""Full narrative: autarky maps → autarky box → exchange → specialization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import Dot, FadeIn, FadeOut, FadeTransform, ReplacementTransform, Scene

from data import get_economy
from geometry import utility
from scenes.boxes import (
    _away_from_axes,
    _make_box,
    _pair_name,
    _play_autarky_box,
    _play_endowment_trade,
)
from scenes.maps import _PersonStageMap
from style import DOT_COLOR, grey_for_level


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


class FullNarrative(_PersonStageMap):
    """Autarky maps, Iván's rotate-in box, then exchange and specialization.

    Charts share a fixed SW origin; section transitions morph instead of cutting to black.
    """

    def construct(self):
        eco = _economy()
        map_state = self._autarky_maps(eco)
        name_a, name_b, box, eq = self._autarky_box_from_map(eco, map_state)
        box, ic_a, ic_b = self._exchange_box(eco, name_a, name_b, box, eq)
        box, ic_a, ic_b = self._grow_to_specialization(
            eco, box, name_a, name_b, ic_a, ic_b
        )
        self._specialization_box(eco, box, name_a, name_b, ic_a, ic_b)

    def _autarky_maps(self, eco):
        return self._construct_paired_autarky_maps(eco)

    def _autarky_box_from_map(self, eco, map_state):
        """Crossfade map → box with fixed SW/unit so shared ticks stay put (no shrink)."""
        stage = eco.stage("autarky")
        name_a, name_b = _pair_name(eco)
        box = _make_box(eco, stage, agent_b_at_final=False)

        axes = map_state["axes"]
        ivan_name = map_state["name"]
        dot = map_state["dot"]
        target = box.c2p(*stage.consume_b)

        # Opacity crossfade (not FadeTransform): ticks at 2/4/6 keep screen
        # positions under the shared CHART_UNIT. Keep Iván's optimum IC + green
        # dot; only the map chrome extras and axes span beyond the box go away.
        self.play(
            FadeOut(map_state["budget"]),
            FadeOut(map_state["cursors"]),
            FadeOut(map_state["w"]),
            FadeOut(axes),
            FadeIn(box),
            ReplacementTransform(ivan_name, name_b),
            FadeIn(name_a),
            dot.animate.move_to(target),
            run_time=1.4,
        )
        _play_autarky_box(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            intro="resume",
            existing_dot=dot,
            existing_ic=map_state["ic"],
        )
        return name_a, name_b, box, dot

    def _exchange_box(self, eco, name_a, name_b, box_old, eq_old):
        """Same SW/unit/totals as autarky end-frame; morph box, keep the green dot."""
        stage = eco.stage("exchange")
        box = _make_box(eco, stage)
        ic_hi = grey_for_level(1.0)
        u_a0 = utility(*stage.produce_a, eco.alpha)
        u_b0 = utility(*stage.produce_b, eco.alpha)
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
        ic_a0.set_stroke(color=ic_hi)
        ic_b0.set_stroke(color=ic_hi)

        keep = {name_a, name_b, box_old, eq_old}
        extras = [m for m in list(self.mobjects) if m not in keep]
        self.play(
            *[FadeOut(m) for m in extras],
            FadeTransform(box_old, box),
            FadeIn(ic_a0),
            FadeIn(ic_b0),
            run_time=0.9,
        )
        eq_old.move_to(box.c2p(*stage.produce_a))
        _, ic_a, ic_b = _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            intro="after_endowment",
            endowment_arts=(ic_a0, ic_b0, eq_old),
        )
        return box, ic_a, ic_b

    def _grow_to_specialization(self, eco, box_old, name_a, name_b, ic_a, ic_b):
        """Grow up/right from fixed SW; keep final ICs — A extends, B moves with NE."""
        ex = eco.stage("exchange")
        stage = eco.stage("specialization")
        box_new = _make_box(eco, stage)
        ic_hi = grey_for_level(1.0)
        u_a = utility(*ex.consume_a, eco.alpha)
        u_b = utility(*ex.consume_b, eco.alpha)
        ic_a_new = box_new.plot_ic_a(u_a, eco.alpha, stroke_width=3.5)
        ic_b_new = box_new.plot_ic_b(u_b, eco.alpha, stroke_width=3.5)
        ic_a_new.set_stroke(color=ic_hi)
        ic_b_new.set_stroke(color=ic_hi)

        keep = {name_a, name_b, box_old, ic_a, ic_b}
        extras = [m for m in list(self.mobjects) if m not in keep]
        if extras:
            self.play(*[FadeOut(m) for m in extras], run_time=0.5)
        box_old.play_grow_to(
            self,
            box_new,
            morphs=((ic_a, ic_a_new), (ic_b, ic_b_new)),
            run_time=1.6,
        )
        return box_new, ic_a_new, ic_b_new

    def _specialization_box(self, eco, box, name_a, name_b, ic_a, ic_b):
        """Land grown exchange ICs on the specialized endowment, then trade."""
        stage = eco.stage("specialization")
        endow = stage.produce_a
        endow_ic = _away_from_axes(endow, stage.total_x, stage.total_y)
        ic_hi = grey_for_level(1.0)
        u_a0 = utility(*endow_ic, eco.alpha)
        u_b0 = utility(
            stage.total_x - endow_ic[0], stage.total_y - endow_ic[1], eco.alpha
        )
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
        ic_a0.set_stroke(color=ic_hi)
        ic_b0.set_stroke(color=ic_hi)
        eq = Dot(box.c2p(*endow), color=DOT_COLOR, radius=0.1)
        self.play(
            ReplacementTransform(ic_a, ic_a0),
            ReplacementTransform(ic_b, ic_b0),
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
            endowment_a=endow,
            intro="after_endowment",
            endowment_arts=(ic_a0, ic_b0, eq),
        )
