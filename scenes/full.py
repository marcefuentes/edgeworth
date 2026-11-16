"""Full narrative: autarky maps → autarky box → exchange → specialization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import FadeIn, FadeOut, ReplacementTransform, Scene

from data import get_economy
from geometry import utility
from scenes.boxes import (
    ENDOWMENT_DIM_OPACITY,
    _make_box,
    _pair_name,
    _play_autarky_box,
    _play_dot_ic_move,
    _play_endowment_trade,
)
from scenes.maps import _PersonStageMap
from style import grey_for_level


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


class FullNarrative(_PersonStageMap):
    """Autarky maps, Iván's rotate-in box, then exchange and specialization.

    Charts share a fixed SW origin; section transitions morph instead of cutting to black.
    """

    def construct(self):
        eco = _economy()
        map_state = self._autarky_maps(eco)
        name_a, name_b, box, eq, cursors = self._autarky_box_from_map(eco, map_state)
        box, ic_a, ic_b, autarky_a, autarky_b, eq, cursors = self._exchange_box(
            eco, name_a, name_b, box, eq, cursors
        )
        box, autarky_a, autarky_b, eq, ic_a, ic_b, cursors = self._grow_to_specialization(
            eco, box, name_a, name_b, ic_a, ic_b, autarky_a, autarky_b, eq, cursors
        )
        self._specialization_box(
            eco, box, name_a, name_b, autarky_a, autarky_b, eq, ic_a, ic_b, cursors
        )

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

        # Shrink map axes about SW to the autarky box (8×6 → 6×4), like the
        # inverse of exchange→specialization grow. Shared ticks at 2/4/6 stay put.
        # Morph Iván's optimum IC with the shrink; keep the green dot; only his name.
        u_b = utility(*stage.consume_b, eco.alpha)
        ic_box = box.plot_ic_b_sw(u_b, eco.alpha, stroke_width=3.5)
        ic_box.set_stroke(color=grey_for_level(1.0))
        # Pin ticks (and the dot) to the pre-shrink screen point for this bundle.
        # always_redraw via axes.c2p drifts while NumberLines shorten; shared
        # goods 2/4/6 stay put, so static ticks stay aligned with the dot.
        bx, by = stage.consume_b
        dot_pt = axes.c2p(bx, by)
        self.remove(map_state["cursors"])
        shrink_cursors = axes.cursor_ticks(bx, by, axes.color)
        self.add(shrink_cursors)
        dot.move_to(dot_pt)
        self.bring_to_front(shrink_cursors, dot)
        axes.play_shrink_to(
            self,
            stage.total_x,
            stage.total_y,
            extra_anims=(
                FadeOut(map_state["budget"]),
                ReplacementTransform(ivan_name, name_b),
                ReplacementTransform(map_state["ic"], ic_box),
            ),
            run_time=1.4,
        )
        # Crossfade to the open box — hand ticks off in the same beat so they
        # never drop between the shrunk map and Iván's SW chart.
        box_cursors = box.cursor_ticks_sw(*stage.consume_b)
        self.play(
            FadeOut(axes),
            FadeIn(box),
            ReplacementTransform(shrink_cursors, box_cursors),
            dot.animate.move_to(target),
            run_time=0.45,
        )
        box.chrome_a.set_opacity(0)
        self.bring_to_front(box_cursors, dot)
        _, _, _, cursors = _play_autarky_box(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            intro="resume",
            existing_dot=dot,
            existing_ic=ic_box,
            existing_cursors=box_cursors,
        )
        return name_a, name_b, box, dot, cursors

    def _exchange_box(self, eco, name_a, name_b, box_old, eq_old, cursors):
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

        keep = {name_a, name_b, box, eq_old, cursors}
        extras = [m for m in list(self.mobjects) if m not in keep]
        endow_cursors = box.cursor_ticks(*stage.produce_a)
        # Same green dot + ticks move to the exchange endowment (never fade).
        self.play(
            *[FadeOut(m) for m in extras],
            FadeIn(ic_a0),
            FadeIn(ic_b0),
            eq_old.animate.move_to(box.c2p(*stage.produce_a)),
            ReplacementTransform(cursors, endow_cursors),
            run_time=0.9,
        )
        self.bring_to_front(endow_cursors, eq_old)
        _, ic_a, ic_b, trade_cursors = _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            intro="after_endowment",
            endowment_arts=(ic_a0, ic_b0, eq_old),
            existing_cursors=endow_cursors,
        )
        # Endowment ICs are the autarky optima (same bundles); kept dimmed as reference.
        return box, ic_a, ic_b, ic_a0, ic_b0, eq_old, trade_cursors

    def _grow_to_specialization(
        self, eco, box_old, name_a, name_b, ic_a, ic_b, autarky_a, autarky_b, eq, cursors
    ):
        """Grow up/right from fixed SW; keep ICs and cursor ticks through the green dot."""
        aut = eco.stage("autarky")
        ex = eco.stage("exchange")
        stage = eco.stage("specialization")
        # Keep Iván's upside-down NE titles/numbers after the autarky rotate-in.
        box_new = _make_box(eco, stage, b_labels_rotated=True)
        ic_hi = grey_for_level(1.0)
        u_aut_a = utility(*aut.consume_a, eco.alpha)
        u_aut_b = utility(*aut.consume_b, eco.alpha)
        autarky_a_new = box_new.plot_ic_a(u_aut_a, eco.alpha, stroke_width=3.5)
        autarky_b_new = box_new.plot_ic_b(u_aut_b, eco.alpha, stroke_width=3.5)
        autarky_a_new.set_stroke(color=ic_hi, opacity=ENDOWMENT_DIM_OPACITY)
        autarky_b_new.set_stroke(color=ic_hi, opacity=ENDOWMENT_DIM_OPACITY)

        # Exchange finals stay attached to the dot; remorph onto the larger box.
        ox, oy = ex.consume_a
        u_ex_a = utility(ox, oy, eco.alpha)
        u_ex_b = utility(stage.total_x - ox, stage.total_y - oy, eco.alpha)
        ic_ex_a = box_new.plot_ic_a(u_ex_a, eco.alpha, stroke_width=3.5)
        ic_ex_b = box_new.plot_ic_b(u_ex_b, eco.alpha, stroke_width=3.5)
        ic_ex_a.set_stroke(color=ic_hi)
        ic_ex_b.set_stroke(color=ic_hi)
        new_cursors = box_new.cursor_ticks(ox, oy)

        keep = {name_a, name_b, box_old, autarky_a, autarky_b, eq, ic_a, ic_b, cursors}
        extras = [m for m in list(self.mobjects) if m not in keep]
        if extras:
            self.play(*[FadeOut(m) for m in extras], run_time=0.5)
        box_old.play_grow_to(
            self,
            box_new,
            morphs=(
                (autarky_a, autarky_a_new),
                (autarky_b, autarky_b_new),
                (ic_a, ic_ex_a),
                (ic_b, ic_ex_b),
                (cursors, new_cursors),
            ),
            run_time=1.6,
        )
        eq.move_to(box_new.c2p(ox, oy))
        self.bring_to_front(new_cursors, eq)
        return box_new, autarky_a_new, autarky_b_new, eq, ic_ex_a, ic_ex_b, new_cursors

    def _specialization_box(
        self, eco, box, name_a, name_b, autarky_a, autarky_b, eq, ic_a, ic_b, cursors
    ):
        """Specialize to the NW corner → contract → trade.

        Live ICs accompany the move to the true corner (w=0) and vanish on
        arrival. They reappear when the allocation leaves the corner toward the
        contract. Dimmed autarky ICs stay as the only reference.
        """
        stage = eco.stage("specialization")
        aut = eco.stage("autarky")
        ex = eco.stage("exchange")
        start = ex.consume_a
        corner = stage.produce_a

        # Live-move to the true specialized corner; ICs shrink away and vanish.
        # Old static ticks fade as live ticks take over with the green dot.
        _play_dot_ic_move(
            self,
            eco,
            box,
            eq,
            start,
            corner,
            run_time=1.2,
            vanish_ics=True,
            fade_out=(ic_a, ic_b, cursors),
        )

        # Contract while parked at the corner (no endowment ICs); trade grows them.
        _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            endowment_a=corner,
            intro="after_corner",
            endowment_arts=eq,
            skip_endowment_ics=True,
            lens_utilities=(
                utility(*aut.consume_a, eco.alpha),
                utility(*aut.consume_b, eco.alpha),
            ),
        )
        # Extra beat on the final specialization optimum before the movie ends.
        self.wait(2)
