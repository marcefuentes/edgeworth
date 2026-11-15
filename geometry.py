"""Analytic geometry for Cobb–Douglas ICs, budgets, and Edgeworth transforms."""

from __future__ import annotations

import math

EPS = 1e-9


def utility(x: float, y: float, alpha: float) -> float:
    if x <= 0 or y <= 0:
        return 0.0
    return (x**alpha) * (y ** (1.0 - alpha))


def ic_y(x: float, u: float, alpha: float) -> float:
    """Indifference curve: y such that u = x^α y^(1-α)."""
    if x <= EPS or u <= EPS:
        return math.inf
    return (u / (x**alpha)) ** (1.0 / (1.0 - alpha))


def ic_x(y: float, u: float, alpha: float) -> float:
    if y <= EPS or u <= EPS:
        return math.inf
    return (u / (y ** (1.0 - alpha))) ** (1.0 / alpha)


def budget_y(x: float, endowment: tuple[float, float], price_x: float) -> float:
    """Budget: p·x + y = p·ωx + ωy  ⇒  y = m - p·x."""
    m = price_x * endowment[0] + endowment[1]
    return m - price_x * x


def budget_intercepts(
    endowment: tuple[float, float], price_x: float
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return (x-intercept point, y-intercept point) of the budget line."""
    m = price_x * endowment[0] + endowment[1]
    x_int = m / price_x if price_x > EPS else math.inf
    return (x_int, 0.0), (0.0, m)


def flip_to_a(
    bundle_b: tuple[float, float], total_x: float, total_y: float
) -> tuple[float, float]:
    """Express agent B's bundle in agent A's (SW) coordinates."""
    return (total_x - bundle_b[0], total_y - bundle_b[1])


def clip_domain_for_ic(
    u: float,
    alpha: float,
    x_max: float,
    y_max: float,
    n: int = 80,
) -> list[tuple[float, float]]:
    """Sample IC points that lie inside [0, x_max] × [0, y_max]."""
    if u <= EPS:
        return []
    x_at_ymax = ic_x(y_max, u, alpha)
    lo = max(EPS, x_at_ymax if math.isfinite(x_at_ymax) else EPS)
    lo = min(lo, x_max)
    while lo < x_max and ic_y(lo, u, alpha) > y_max * 1.001:
        lo *= 1.05
    hi = x_max
    while hi > lo and ic_y(hi, u, alpha) <= EPS:
        hi *= 0.95
    if hi <= lo:
        return []
    xs = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    pts: list[tuple[float, float]] = []
    for x in xs:
        y = ic_y(x, u, alpha)
        if EPS < y <= y_max * 1.001 and EPS < x <= x_max * 1.001:
            pts.append((x, min(y, y_max)))
    return pts
