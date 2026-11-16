"""Edgeworth-box scenes for the three stages."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from manim import (
    Dot,
    FadeIn,
    FadeOut,
    ReplacementTransform,
    Scene,
    ValueTracker,
    VGroup,
    VMobject,
    Write,
    always_redraw,
)

from data import get_economy
from geometry import EPS, contract_lens_t_range, utility
from layout import chart_size, pin_sw
from mobjects import CONTRACT_COLOR, EdgeworthBox
from style import (
    DOT_COLOR,
    IC_LEVEL_FACTORS,
    grey_for_level,
    person_name,
    person_name_stacked,
)

DIM_OPACITY = 0.22
ENDOWMENT_DIM_OPACITY = 0.45


def _economy():
    return get_economy(os.environ.get("ECONOMY"))


def _pair_name(eco):
    """Two names stacked upper-left (only non-axis text on box charts)."""
    a = person_name(eco.agent_a.name, color=eco.agent_a.color)
    b = person_name_stacked(
        eco.agent_b.name, color=eco.agent_b.color, under=a
    )
    return a, b


def _make_box(eco, stage, *, agent_b_at_final: bool = True) -> EdgeworthBox:
    """Edgeworth box with shared unit scale and fixed SW origin."""
    width, height = chart_size(stage.total_x, stage.total_y)
    box = EdgeworthBox(
        stage.total_x,
        stage.total_y,
        eco.agent_a.name,
        eco.agent_b.name,
        eco.good_x,
        eco.good_y,
        eco.agent_a.color,
        eco.agent_b.color,
        width=width,
        height=height,
        agent_b_at_final=agent_b_at_final,
    )
    return pin_sw(box, box.c2p(0, 0))


def _ic_levels(u_opt: float) -> list[float]:
    return [u_opt * f for f in IC_LEVEL_FACTORS]


def _away_from_axes(
    bundle_a: tuple[float, float],
    total_x: float,
    total_y: float,
    eps: float = 0.25,
) -> tuple[float, float]:
    """Nudge a corner endowment inside the box so CD ICs are drawable."""
    x, y = bundle_a
    return (
        min(max(x, eps), total_x - eps),
        min(max(y, eps), total_y - eps),
    )


def _utility_level(u: float, u0: float, u1: float) -> float:
    if u1 <= u0 + 1e-9:
        return 1.0
    return max(0.0, min(1.0, (u - u0) / (u1 - u0)))


def _play_endowment_trade(
    scene: Scene,
    eco,
    stage,
    box: EdgeworthBox,
    name_a,
    name_b,
    *,
    endowment_a: tuple[float, float] | None = None,
    intro: str = "together",
    endowment_arts: tuple | None = None,
    lens_utilities: tuple[float, float] | None = None,
    skip_endowment_ics: bool = False,
) -> EdgeworthBox:
    """Shared Exchange/Specialization beat: endowment → contract → trade move.

    intro:
      - ``together``: fade in frame + endowment ICs + dot at once
      - ``sequential``: frame, then dot, then ICs
      - ``resume``: frame already on screen; start from dot + ICs
      - ``after_endowment``: frame + endowment ICs + dot already on screen;
        begin at the contract curve (``endowment_arts`` = (ic_a0, ic_b0, eq))
      - ``after_corner``: frame + reference ICs already on screen; only the
        corner dot is new (``endowment_arts`` = eq). Use with
        ``skip_endowment_ics=True`` (specialization: u=0 at the corner).

    ``lens_utilities``: optional ``(u_a, u_b)`` floors for the thick contract
    segment (default: utilities at the endowment). Use autarky utilities on the
    specialization box so the highlight sits inside the autarky ICs.

    ``skip_endowment_ics``: do not draw or dim endowment ICs (corner u=0 has
    no meaningful IC). Live ICs grow from empty as the dot leaves the corner.
    """
    endow = endowment_a if endowment_a is not None else stage.produce_a
    endow_ic = _away_from_axes(endow, stage.total_x, stage.total_y)
    if skip_endowment_ics:
        # True corner endowment has w=0; grey-scale live ICs from 0 → final.
        u_a0 = 0.0
        u_b0 = 0.0
    else:
        u_a0 = utility(*endow_ic, eco.alpha)
        u_b0 = utility(
            stage.total_x - endow_ic[0], stage.total_y - endow_ic[1], eco.alpha
        )
    u_a1 = utility(*stage.consume_a, eco.alpha)
    u_b1 = utility(*stage.consume_b, eco.alpha)
    ic_hi = grey_for_level(1.0)
    ic_a0 = ic_b0 = None

    if intro == "after_corner":
        if endowment_arts is None:
            raise ValueError("endowment_arts (eq) required for intro='after_corner'")
        eq = endowment_arts
    elif intro == "after_endowment":
        if endowment_arts is None:
            raise ValueError("endowment_arts required for intro='after_endowment'")
        ic_a0, ic_b0, eq = endowment_arts
    else:
        eq = Dot(box.c2p(*endow), color=DOT_COLOR, radius=0.1)
        if not skip_endowment_ics:
            ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
            ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
            ic_a0.set_stroke(color=ic_hi)
            ic_b0.set_stroke(color=ic_hi)

        if intro == "sequential":
            scene.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box))
            scene.play(FadeIn(eq))
            if ic_a0 is not None:
                scene.play(Write(ic_a0), Write(ic_b0), run_time=0.9)
        elif intro == "resume":
            scene.play(FadeIn(eq))
            if ic_a0 is not None:
                scene.play(Write(ic_a0), Write(ic_b0), run_time=0.9)
        else:
            anims = [FadeIn(name_a), FadeIn(name_b), FadeIn(box), FadeIn(eq)]
            if ic_a0 is not None:
                anims.extend([FadeIn(ic_a0), FadeIn(ic_b0)])
            scene.play(*anims)
        scene.wait(0.4)

    contract_thin = box.plot_contract(
        0.0, 1.0, color=CONTRACT_COLOR, stroke_width=1.5
    )
    scene.play(Write(contract_thin), run_time=1.2)
    scene.wait(0.3)

    lens_kw = {}
    if lens_utilities is not None:
        lens_kw["u_a0"], lens_kw["u_b0"] = lens_utilities
    t_lo, t_hi = contract_lens_t_range(
        endow_ic, stage.total_x, stage.total_y, eco.alpha, **lens_kw
    )
    contract_thick = box.plot_contract(
        t_lo, t_hi, color=CONTRACT_COLOR, stroke_width=5.5
    )
    scene.play(Write(contract_thick), run_time=0.9)
    scene.wait(0.35)

    ox, oy = endow
    cx, cy = stage.consume_a
    progress = ValueTracker(0.0)

    def _bundle():
        t = progress.get_value()
        return (ox + t * (cx - ox), oy + t * (cy - oy))

    def _live_a():
        xa, ya = _bundle()
        u = utility(xa, ya, eco.alpha)
        if u <= EPS:
            if skip_endowment_ics:
                return VMobject()
            # Interior endowment: hold a drawable stroke until the move starts.
            u_plot = u_a0
        else:
            u_plot = u
        curve = box.plot_ic_a(u_plot, eco.alpha, stroke_width=3.5)
        return curve.set_stroke(color=grey_for_level(_utility_level(u, u_a0, u_a1)))

    def _live_b():
        xa, ya = _bundle()
        u = utility(stage.total_x - xa, stage.total_y - ya, eco.alpha)
        if u <= EPS:
            if skip_endowment_ics:
                return VMobject()
            u_plot = u_b0
        else:
            u_plot = u
        curve = box.plot_ic_b(u_plot, eco.alpha, stroke_width=3.5)
        return curve.set_stroke(color=grey_for_level(_utility_level(u, u_b0, u_b1)))

    live_a = always_redraw(_live_a)
    live_b = always_redraw(_live_b)
    cursors = always_redraw(lambda: box.cursor_ticks(*_bundle()))
    eq.add_updater(lambda m: m.move_to(box.c2p(*_bundle())))

    if ic_a0 is not None:
        scene.play(
            ic_a0.animate.set_stroke(opacity=ENDOWMENT_DIM_OPACITY),
            ic_b0.animate.set_stroke(opacity=ENDOWMENT_DIM_OPACITY),
            run_time=0.5,
        )
    scene.add(live_a, live_b, cursors)
    scene.play(progress.animate.set_value(1.0), run_time=2.0)
    eq.clear_updaters()
    scene.remove(live_a, live_b, cursors)

    ic_a1 = box.plot_ic_a(u_a1, eco.alpha, stroke_width=3.5)
    ic_b1 = box.plot_ic_b(u_b1, eco.alpha, stroke_width=3.5)
    ic_a1.set_stroke(color=ic_hi)
    ic_b1.set_stroke(color=ic_hi)
    final_cursors = box.cursor_ticks(*stage.consume_a)
    eq.move_to(box.c2p(*stage.consume_a))
    scene.add(ic_a1, ic_b1, final_cursors)
    scene.wait(2)
    return box, ic_a1, ic_b1


def _play_autarky_box(
    scene: Scene,
    eco,
    stage,
    box: EdgeworthBox,
    name_a,
    name_b,
    *,
    intro: str = "together",
    existing_dot=None,
    existing_ic=None,
) -> tuple:
    """Iván SW chart → rotate into NE corner → Gonzalo ICs → shared optimum.

    Returns ``(eq, ic_a, ic_b)`` at the final shared endowment frame.
    """
    # Dot starts on Iván's SW chart at his optimum; 180° rotation lands it
    # on the final Edgeworth allocation (consume_a).
    if existing_dot is None:
        eq = Dot(box.c2p(*stage.consume_b), color=DOT_COLOR, radius=0.1)
    else:
        eq = existing_dot
        eq.move_to(box.c2p(*stage.consume_b))

    if intro == "together":
        # Iván-only open; Gonzalo's name arrives with his focus beat.
        scene.play(FadeIn(name_b), FadeIn(box))

    u_b = utility(*stage.consume_b, eco.alpha)
    u_a = utility(*stage.consume_a, eco.alpha)

    # Focus Iván: dim Gonzalo's chrome; Iván's name already on screen alone
    focus = [
        box.chrome_a.animate.set_opacity(DIM_OPACITY),
        box.chrome_b.animate.set_opacity(1),
        name_b.animate.set_opacity(1),
    ]
    if existing_dot is None:
        focus.append(FadeIn(eq))
    scene.play(*focus, run_time=0.5)
    scene.wait(0.4)

    if existing_ic is not None:
        # Map already left the optimum IC; snap to SW box geometry, skip the sweep.
        opt_b = box.plot_ic_b_sw(u_b, eco.alpha, stroke_width=3.5)
        opt_b.set_stroke(color=grey_for_level(1.0))
        scene.play(ReplacementTransform(existing_ic, opt_b), run_time=0.45)
    else:
        # --- Iván ICs on his SW chart, then keep only the optimum ---
        levels_b = _ic_levels(u_b)
        drawn_b = VGroup()
        for u in levels_b:
            t = (u - levels_b[0]) / (levels_b[-1] - levels_b[0])
            curve = box.plot_ic_b_sw(u, eco.alpha, stroke_width=3)
            curve.set_stroke(color=grey_for_level(t))
            scene.play(Write(curve), run_time=0.4)
            drawn_b.add(curve)
        opt_b = drawn_b[-1]
        lower_b = VGroup(*drawn_b[:-1])
        scene.play(FadeOut(lower_b), opt_b.animate.set_stroke(width=3.5), run_time=0.6)

    # Rotate Iván's axes + optimum IC + dot into the NE Edgeworth corner
    box.play_rotate_b_into_box(scene, eq, opt_b, run_time=2.5)
    eq.move_to(box.c2p(*stage.consume_a))
    # Snap IC to exact Edgeworth geometry after the rotate.
    final_b = box.plot_ic_b(u_b, eco.alpha, stroke_width=3.5)
    final_b.set_stroke(color=opt_b.get_stroke_color())
    scene.remove(opt_b)
    scene.add(final_b)
    opt_b = final_b

    # Focus Gonzalo: dim Iván; bring Gonzalo's name in for the first time
    scene.play(
        box.chrome_b.animate.set_opacity(DIM_OPACITY),
        name_b.animate.set_opacity(DIM_OPACITY),
        box.chrome_a.animate.set_opacity(1),
        FadeIn(name_a),
        run_time=0.5,
    )

    # --- Gonzalo (agent A): ICs up to optimum, then keep only that curve ---
    levels_a = _ic_levels(u_a)
    drawn_a = VGroup()
    for u in levels_a:
        t = (u - levels_a[0]) / (levels_a[-1] - levels_a[0])
        curve = box.plot_ic_a(u, eco.alpha, stroke_width=3)
        curve.set_stroke(color=grey_for_level(t))
        scene.play(Write(curve), run_time=0.4)
        drawn_a.add(curve)
    opt_a = drawn_a[-1]
    lower_a = VGroup(*drawn_a[:-1])
    scene.play(FadeOut(lower_a), opt_a.animate.set_stroke(width=3.5), run_time=0.6)

    # Restore both agents (green dot already sits at the shared optimum)
    scene.play(
        box.chrome_a.animate.set_opacity(1),
        box.chrome_b.animate.set_opacity(1),
        name_a.animate.set_opacity(1),
        name_b.animate.set_opacity(1),
        run_time=0.45,
    )
    scene.wait(2)
    return eq, opt_a, opt_b


class AutarkyBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("autarky")
        name_a, name_b = _pair_name(eco)
        box = _make_box(eco, stage, agent_b_at_final=False)
        _play_autarky_box(self, eco, stage, box, name_a, name_b)


class ExchangeBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("exchange")
        name_a, name_b = _pair_name(eco)
        box = _make_box(eco, stage)
        _play_endowment_trade(self, eco, stage, box, name_a, name_b)


class SpecializationBox(Scene):
    def construct(self):
        eco = _economy()
        stage = eco.stage("specialization")
        aut = eco.stage("autarky")
        name_a, name_b = _pair_name(eco)
        box = _make_box(eco, stage)
        # Dimmed autarky ICs as a welfare reference on the larger box.
        ic_hi = grey_for_level(1.0)
        autarky_a = box.plot_ic_a(
            utility(*aut.consume_a, eco.alpha), eco.alpha, stroke_width=3.5
        )
        autarky_b = box.plot_ic_b(
            utility(*aut.consume_b, eco.alpha), eco.alpha, stroke_width=3.5
        )
        autarky_a.set_stroke(color=ic_hi, opacity=ENDOWMENT_DIM_OPACITY)
        autarky_b.set_stroke(color=ic_hi, opacity=ENDOWMENT_DIM_OPACITY)
        self.add(autarky_a, autarky_b)
        # Corner dot only (w=0 — no endowment ICs); thick contract inside autarky ICs.
        _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            endowment_a=stage.produce_a,
            intro="sequential",
            skip_endowment_ics=True,
            lens_utilities=(
                utility(*aut.consume_a, eco.alpha),
                utility(*aut.consume_b, eco.alpha),
            ),
        )
