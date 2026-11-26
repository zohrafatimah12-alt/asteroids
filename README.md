# NEBULA

A strategy and air-combat game set on VEYRA, a planet orbiting the star Nebula. You command
Lumeris, the weakest of ten nations, through a 100-level campaign of diplomacy, intelligence,
air-force management and Pygame combat, while the world learns that something is coming.

NEBULA grew out of a Boot.dev Python **Asteroids** project, which is still here and still runs.

## Install
Needs [uv](https://docs.astral.sh/uv/) (Python 3.13 is fetched automatically). No Node.js or build step.

```bash
uv sync
```

## Play
```bash
uv run python -m nebula
```
Open http://127.0.0.1:8000. Options: `--port 8001`, `--no-browser`.

Combat opens a Pygame window **on the machine running the server** (on WSL this needs WSLg).
If you cannot open a window, use **Command a wing**: an odds-based simulation, recorded separately in analytics.

| Combat key | Action |
|---|---|
| W / S | Throttle |
| A / D | Turn |
| Space | Guns |
| F | Missile (needs a detected target ahead) |
| Q | Aircraft ability |
| P / Esc | Pause / abort (an abort counts as failure) |

Practice any combat level without saving anything:
```bash
uv run python -m nebula.combat --level 12 --aircraft fr_skua
```

The original game:
```bash
uv run main.py
```

## Test
```bash
uv run pytest
```

## Analytics from the command line
```bash
uv run python -m nebula.analytics.pipeline 1 --export saves/export
```
`1` is the campaign id. This prints the metrics and writes the history tables as CSV.

## How a campaign works
- **Time:** diplomacy and intelligence actions, missions and "Advance day" move the calendar. Each day pays income and may trigger a world event.
- **Diplomacy:** peace, then intelligence or alliance; trade any time. Some combat levels can be settled peacefully.
- **Intelligence:** unknown, rumour, probable, confirmed. Only confirmed values are exact.
- **Air force:** fuel, ammunition and repairs cost resources; later missions need more range. Failed missions can be retried.
- **Endings:** the Great Union, the Last Evacuation or the Last Star, decided after level 100. The final screen lists each requirement.

## Documentation
[World bible](docs/WORLD_BIBLE.md) (spoilers) · [Architecture](docs/ARCHITECTURE.md) · [Database](docs/DATABASE_SCHEMA.md) ·
[API](docs/API_DOCUMENTATION.md) · [Roadmap and limitations](docs/DEVELOPMENT_ROADMAP.md) ·
[Development log](docs/DEVELOPMENT_LOG.md) · [Contributing](docs/CONTRIBUTING.md)
