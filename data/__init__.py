"""Economy registry."""

from __future__ import annotations

from data.gonzalo_ivan import ECONOMY as GONZALO_IVAN
from data.model import Economy

_ECONOMIES: dict[str, Economy] = {
    GONZALO_IVAN.id: GONZALO_IVAN,
}

DEFAULT_ECONOMY_ID = GONZALO_IVAN.id


def get_economy(economy_id: str | None = None) -> Economy:
    key = economy_id or DEFAULT_ECONOMY_ID
    try:
        return _ECONOMIES[key]
    except KeyError as exc:
        known = ", ".join(sorted(_ECONOMIES))
        raise KeyError(f"Unknown economy {key!r}. Known: {known}") from exc


def list_economies() -> list[str]:
    return sorted(_ECONOMIES)
