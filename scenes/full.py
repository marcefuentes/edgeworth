"""Full narrative: autarky maps → autarky box → exchange → specialization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import Dot, FadeIn, FadeOut, ReplacementTransform, Scene

from data import get_economy
from geometry import utility
from scenes.boxes import (
    ENDOWMENT_DIM_OPACITY,
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
        box, ic_a, ic_b, autarky_a, autarky_b = self._exchange_box(
            eco, name_a, name_b, box, eq
        )
        box, autarky_a, autarky_b = self._grow_to_specialization(
            eco, box, name_a, name_b, ic_a, ic_b, autarky_a, autarky_b
        )
        self._specialization_box(eco, box, name_a, name_b, autarky_a, autarky_b)

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
        # Only Iván's name at the box open (Gonzalo joins when his ICs start).
        self.play(
            FadeOut(map_state["budget"]),
            FadeOut(map_state["cursors"]),
            FadeOut(axes),
            FadeIn(box),
            ReplacementTransform(ivan_name, name_b),
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
        """Same SW/unit/totals as autarky end-frame; keep the box and green dot.

        Do not FadeTransform the box into a fresh copy: after Iván's rotate-in the
        live tree can still differ from a new ``agent_b_at_final`` box, and Manim
        then cross-fades Gonzalo's teal axes toward Iván's yellow.
        """
        stage = eco.stage("exchange")
        box = box_old
        ic_hi = grey_for_level(1.0)
        u_a0 = utility(*stage.produce_a, eco.alpha)
        u_b0 = utility(*stage.produce_b, eco.alpha)
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
        ic_a0.set_stroke(color=ic_hi)
        ic_b0.set_stroke(color=ic_hi)

        keep = {name_a, name_b, box, eq_old}
        extras = [m for m in list(self.mobjects) if m not in keep]
        self.play(
            *[FadeOut(m) for m in extras],
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
        # Endowment ICs are the autarky optima (same bundles); kept dimmed as reference.
        return box, ic_a, ic_b, ic_a0, ic_b0

    def _grow_to_specialization(
        self, eco, box_old, name_a, name_b, ic_a, ic_b, autarky_a, autarky_b
    ):
        """Grow up/right from fixed SW; keep only dimmed autarky ICs (drop exchange)."""
        aut = eco.stage("autarky")
        stage = eco.stage("specialization")
        box_new = _make_box(eco, stage)
        ic_hi = grey_for_level(1.0)
        u_aut_a = utility(*aut.consume_a, eco.alpha)
        u_aut_b = utility(*aut.consume_b, eco.alpha)
        autarky_a_new = box_new.plot_ic_a(u_aut_a, eco.alpha, stroke_width=3.5)
        autarky_b_new = box_new.plot_ic_b(u_aut_b, eco.alpha, stroke_width=3.5)
        autarky_a_new.set_stroke(color=ic_hi, opacity=ENDOWMENT_DIM_OPACITY)
        autarky_b_new.set_stroke(color=ic_hi, opacity=ENDOWMENT_DIM_OPACITY)

        keep = {name_a, name_b, box_old, autarky_a, autarky_b}
        extras = [m for m in list(self.mobjects) if m not in keep]
        # Exchange finals fade with extras (no meaningful ICs at the u=0 corner).
        if extras:
            self.play(*[FadeOut(m) for m in extras], run_time=0.5)
        box_old.play_grow_to(
            self,
            box_new,
            morphs=((autarky_a, autarky_a_new), (autarky_b, autarky_b_new)),
            run_time=1.6,
        )
        return box_new, autarky_a_new, autarky_b_new

    def _specialization_box(self, eco, box, name_a, name_b, autarky_a, autarky_b):
        """Corner endowment + contract/trade; dimmed autarky ICs stay as reference.

        No endowment ICs: specialized production is on the axes (w=0).
        """
        stage = eco.stage("specialization")
        aut = eco.stage("autarky")
        endow = stage.produce_a
        eq = Dot(box.c2p(*endow), color=DOT_COLOR, radius=0.1)
        # autarky_a/b already on scene (dimmed) from the grow.
        self.play(FadeIn(eq), run_time=0.6)
        _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            endowment_a=endow,
            intro="after_corner",
            endowment_arts=eq,
            skip_endowment_ics=True,
            lens_utilities=(
                utility(*aut.consume_a, eco.alpha),
                utility(*aut.consume_b, eco.alpha),
            ),
        )
