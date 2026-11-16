# Edgeworth (Manim)

Animated Edgeworth boxes and indifference-curve maps for two-agent exchange economies.

Default economy: **Gonzalo–Iván** (truchas & manzanas), three stages:

1. Autarquía
2. Intercambio
3. Especialización + intercambio

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Render

From the project root (so `data` / `geometry` / `mobjects` import):

```bash
source .venv/bin/activate

# Edgeworth boxes
manim -pql scenes/boxes.py AutarkyBox
manim -pql scenes/boxes.py ExchangeBox
manim -pql scenes/boxes.py SpecializationBox

# Individual IC + budget maps (2 agents × 3 stages)
manim -pql scenes/maps.py AgentAAutarkyMap
manim -pql scenes/maps.py AgentAExchangeMap
manim -pql scenes/maps.py AgentASpecializationMap
manim -pql scenes/maps.py AgentBAutarkyMap
manim -pql scenes/maps.py AgentBExchangeMap
manim -pql scenes/maps.py AgentBSpecializationMap
manim -pql scenes/maps.py AutarkyMaps

# Full narrative: autarky maps → autarky box → exchange → specialization
manim -pql scenes/full.py FullNarrative
```

Use `-pqh` for higher quality. Preview flag `-p` opens the video when done.

## Other pairs

Scenes read `ECONOMY` (default `gonzalo_ivan`). Add a module under `data/` that builds an `Economy`, register it in `data/__init__.py`, then:

```bash
ECONOMY=other_id manim -pql scenes/boxes.py ExchangeBox
```

No scene code changes are needed if the new pair uses the same three-stage shape.
