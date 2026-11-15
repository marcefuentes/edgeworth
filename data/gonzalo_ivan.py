"""Gonzalo–Iván economy (first pair from the Trade spreadsheet)."""

from data.model import Agent, Economy, Stage

GONZALO = Agent(name="Gonzalo", a_x=4.0, a_y=6.0, color="#2A9D8F")
IVAN = Agent(name="Iván", a_x=8.0, a_y=2.0, color="#E9C46A")

ECONOMY = Economy(
    id="gonzalo_ivan",
    agent_a=GONZALO,
    agent_b=IVAN,
    good_x="Truchas",
    good_y="Manzanas",
    alpha=0.5,
    stages={
        "autarky": Stage(
            name="autarky",
            title="(1) Autarquía",
            total_x=6.0,
            total_y=4.0,
            produce_a=(2.0, 3.0),
            produce_b=(4.0, 1.0),
            consume_a=(2.0, 3.0),
            consume_b=(4.0, 1.0),
            price_x=None,
        ),
        "exchange": Stage(
            name="exchange",
            title="(2) Intercambio",
            total_x=6.0,
            total_y=4.0,
            produce_a=(2.0, 3.0),
            produce_b=(4.0, 1.0),
            consume_a=(3.3, 2.2),
            consume_b=(2.7, 1.8),
            price_x=0.64,
        ),
        "specialization": Stage(
            name="specialization",
            title="(3) Especialización + intercambio",
            total_x=8.0,
            total_y=6.0,
            produce_a=(0.0, 6.0),
            produce_b=(8.0, 0.0),
            consume_a=(4.3, 3.2),
            consume_b=(3.7, 2.8),
            price_x=0.66,
        ),
    },
)
