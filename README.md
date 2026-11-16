# Edgeworth (Manim)

Animated full-narrative Edgeworth boxes and indifference-curve maps for two-agent exchange economies.

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

# Writes media/videos/1080p60/edgeworth.mp4 (YouTube-grade)
manim -pqh scenes/full.py FullNarrative
```

Preview flag `-p` opens the video when done. Use `-ql` / `-qm` for faster drafts.

## Other pairs

`FullNarrative` reads `ECONOMY` (default `gonzalo_ivan`). Add a module under `data/` that builds an `Economy`, register it in `data/__init__.py`, then:

```bash
ECONOMY=other_id manim -pql scenes/full.py FullNarrative
```

No scene code changes are needed if the new pair uses the same three-stage shape.
