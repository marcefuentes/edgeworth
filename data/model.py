"""Person-agnostic data model for Edgeworth-box economies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    name: str
    a_x: float  # max good-x if specialized
    a_y: float  # max good-y if specialized
    color: str


@dataclass(frozen=True)
class Stage:
    name: str  # "autarky" | "exchange" | "specialization"
    title: str
    total_x: float
    total_y: float
    produce_a: tuple[float, float]
    produce_b: tuple[float, float]
    consume_a: tuple[float, float]
    consume_b: tuple[float, float]
    price_x: float | None  # relative P(x) in terms of y; None in autarky

    @property
    def endowment_a(self) -> tuple[float, float]:
        return self.produce_a

    @property
    def trade_a(self) -> tuple[float, float]:
        return (
            self.consume_a[0] - self.produce_a[0],
            self.consume_a[1] - self.produce_a[1],
        )


@dataclass(frozen=True)
class Economy:
    id: str
    agent_a: Agent  # SW origin in Edgeworth box
    agent_b: Agent  # NE origin
    good_x: str
    good_y: str
    alpha: float
    stages: dict[str, Stage]

    def stage(self, key: str) -> Stage:
        return self.stages[key]

    def agent(self, key: str) -> Agent:
        if key == "a":
            return self.agent_a
        if key == "b":
            return self.agent_b
        raise KeyError(f"Unknown agent key: {key!r}")
