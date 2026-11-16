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


def _make_box(
    eco,
    stage,
    *,
    agent_b_at_final: bool = True,
    b_labels_rotated: bool = False,
) -> EdgeworthBox:
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
        b_labels_rotated=b_labels_rotated,
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


def _play_dot_ic_move(
    scene: Scene,
    eco,
    box: EdgeworthBox,
    eq: Dot,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    run_time: float = 1.5,
    settle: bool = False,
    fade_out: tuple = (),
) -> tuple:
    """Move ``eq`` from ``start`` to ``end`` with live ICs always through the bundle.

    ``fade_out``: optional mobjects (e.g. a prior IC pair) removed during the
    move so the scene does not accumulate stale curves.

    Returns ``(ic_a, ic_b)`` static finals at ``end`` when ``settle``; otherwise
    leaves live ICs on the scene and returns ``(live_a, live_b, cursors)``.
    """
    u_a0 = utility(*start, eco.alpha)
    u_b0 = utility(box.total_x - start[0], box.total_y - start[1], eco.alpha)
    u_a1 = utility(*end, eco.alpha)
    u_b1 = utility(box.total_x - end[0], box.total_y - end[1], eco.alpha)
    # Grey scale over the path's utility range (handles u rising or falling).
    u_a_lo, u_a_hi = min(u_a0, u_a1), max(u_a0, u_a1)
    u_b_lo, u_b_hi = min(u_b0, u_b1), max(u_b0, u_b1)
    progress = ValueTracker(0.0)

    def _bundle():
        t = progress.get_value()
        return (
            start[0] + t * (end[0] - start[0]),
            start[1] + t * (end[1] - start[1]),
        )

    def _live_a():
        xa, ya = _bundle()
        u = max(utility(xa, ya, eco.alpha), EPS)
        curve = box.plot_ic_a(u, eco.alpha, stroke_width=3.5)
        return curve.set_stroke(color=grey_for_level(_utility_level(u, u_a_lo, u_a_hi)))

    def _live_b():
        xa, ya = _bundle()
        u = max(
            utility(box.total_x - xa, box.total_y - ya, eco.alpha),
            EPS,
        )
        curve = box.plot_ic_b(u, eco.alpha, stroke_width=3.5)
        return curve.set_stroke(color=grey_for_level(_utility_level(u, u_b_lo, u_b_hi)))

    live_a = always_redraw(_live_a)
    live_b = always_redraw(_live_b)
    cursors = always_redraw(lambda: box.cursor_ticks(*_bundle()))
    eq.clear_updaters()
    eq.add_updater(lambda m: m.move_to(box.c2p(*_bundle())))
    scene.add(live_a, live_b, cursors)
    scene.bring_to_front(live_a, live_b, eq, cursors)
    anims = [progress.animate.set_value(1.0)]
    anims.extend(FadeOut(m) for m in fade_out)
    scene.play(*anims, run_time=run_time)
    eq.clear_updaters()
    eq.move_to(box.c2p(*end))

    if not settle:
        return live_a, live_b, cursors

    ic_hi = grey_for_level(1.0)
    ic_a = box.plot_ic_a(u_a1, eco.alpha, stroke_width=3.5)
    ic_b = box.plot_ic_b(u_b1, eco.alpha, stroke_width=3.5)
    ic_a.set_stroke(color=ic_hi)
    ic_b.set_stroke(color=ic_hi)
    final_cursors = box.cursor_ticks(*end)
    scene.add(ic_a, ic_b, final_cursors)
    scene.bring_to_front(ic_a, ic_b, eq, final_cursors)
    scene.remove(live_a, live_b, cursors)
    return ic_a, ic_b


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
    retain_endowment_ics: bool = True,
) -> EdgeworthBox:
    """Shared Exchange/Specialization beat: endowment → contract → trade move.

    intro:
      - ``together``: fade in frame + endowment ICs + dot at once
      - ``sequential``: frame, then dot, then ICs
      - ``resume``: frame already on screen; start from dot + ICs
      - ``after_endowment``: frame + endowment ICs + dot already on screen;
        begin at the contract curve (``endowment_arts`` = (ic_a0, ic_b0, eq))

    The green dot always sits on a drawable IC pair: corner endowments are
    nudged inside the box (``_away_from_axes``) so Cobb–Douglas ICs exist.

    ``lens_utilities``: optional ``(u_a, u_b)`` floors for the thick contract
    segment (default: utilities at the endowment). Use autarky utilities on the
    specialization box so the highlight sits inside the autarky ICs.

    ``retain_endowment_ics``: if True (exchange), dim endowment ICs as a
    reference under the live/final pair. If False (specialization), fade them
    out when trade starts — another reference (autarky) is already on screen.
    """
    raw_endow = endowment_a if endowment_a is not None else stage.produce_a
    # Always a drawable interior point so the dot never floats without ICs.
    endow = _away_from_axes(raw_endow, stage.total_x, stage.total_y)
    u_a0 = utility(*endow, eco.alpha)
    u_b0 = utility(stage.total_x - endow[0], stage.total_y - endow[1], eco.alpha)
    ic_hi = grey_for_level(1.0)
    ic_a0 = ic_b0 = None

    if intro == "after_endowment":
        if endowment_arts is None:
            raise ValueError("endowment_arts required for intro='after_endowment'")
        ic_a0, ic_b0, eq = endowment_arts
    else:
        eq = Dot(box.c2p(*endow), color=DOT_COLOR, radius=0.1)
        ic_a0 = box.plot_ic_a(u_a0, eco.alpha, stroke_width=3.5)
        ic_b0 = box.plot_ic_b(u_b0, eco.alpha, stroke_width=3.5)
        ic_a0.set_stroke(color=ic_hi)
        ic_b0.set_stroke(color=ic_hi)

        if intro == "sequential":
            scene.play(FadeIn(name_a), FadeIn(name_b), FadeIn(box))
            scene.play(FadeIn(eq), FadeIn(ic_a0), FadeIn(ic_b0))
        elif intro == "resume":
            scene.play(FadeIn(eq), FadeIn(ic_a0), FadeIn(ic_b0))
        else:
            scene.play(
                FadeIn(name_a),
                FadeIn(name_b),
                FadeIn(box),
                FadeIn(eq),
                FadeIn(ic_a0),
                FadeIn(ic_b0),
            )
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
        endow, stage.total_x, stage.total_y, eco.alpha, **lens_kw
    )
    contract_thick = box.plot_contract(
        t_lo, t_hi, color=CONTRACT_COLOR, stroke_width=5.5
    )
    scene.play(Write(contract_thick), run_time=0.9)
    scene.wait(0.35)

    fade_out = ()
    if ic_a0 is not None:
        if retain_endowment_ics:
            scene.play(
                ic_a0.animate.set_stroke(opacity=ENDOWMENT_DIM_OPACITY),
                ic_b0.animate.set_stroke(opacity=ENDOWMENT_DIM_OPACITY),
                run_time=0.5,
            )
        else:
            fade_out = (ic_a0, ic_b0)

    ic_a1, ic_b1 = _play_dot_ic_move(
        scene,
        eco,
        box,
        eq,
        endow,
        stage.consume_a,
        run_time=2.0,
        settle=True,
        fade_out=fade_out,
    )
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
        # Near-corner start (true axes endowment is w=0); ICs stay on the dot.
        # Autarky is the only reference — drop endowment ICs when trade starts.
        _play_endowment_trade(
            self,
            eco,
            stage,
            box,
            name_a,
            name_b,
            endowment_a=stage.produce_a,
            intro="sequential",
            retain_endowment_ics=False,
            lens_utilities=(
                utility(*aut.consume_a, eco.alpha),
                utility(*aut.consume_b, eco.alpha),
            ),
        )
