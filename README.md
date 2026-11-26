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

## Your first mission
1. **Start campaign**, enter a name and watch the written introduction (no voices; skippable, but you must choose a command philosophy).
2. In the command centre, follow **Commander training**. Answer messages in the **Inbox**.
3. Open **Mission briefing**: read the Zorvania dossier and **What should I do?**
4. Press **LAUNCH MISSION** (Pygame window; Enter to take off). The debrief opens when you finish.

To avoid combat, build goodwill with Zorvania (for example, choose Diplomacy First, fund the hotline and answer its follow-up) until **Resolve peacefully** unlocks.

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
- **Stages:** each ten-level stage faces the next nation up the military ranking. Finishing one opens **Joint Command**, where that nation, still independent, can accept, counter or reject a treaty. You may postpone it and continue.
- **Two rankings:** national military strength comes from fixed national data. The joint air-force competitive rank rises exactly one place for each completed stage with a signed treaty. Actual joint strength is calculated separately from the aircraft under each command and is shown beside it.
- **Treaty care:** flying partner aircraft outside the agreed rules, returning them badly damaged or pressuring the partner lowers stability. Partners can ground or withdraw their aircraft.
- **Endings:** the Great Union, the Last Evacuation or the Last Star, decided after level 100. The final screen lists each requirement.

## Documentation
[World bible](docs/WORLD_BIBLE.md) (spoilers) · [Architecture](docs/ARCHITECTURE.md) · [Database](docs/DATABASE_SCHEMA.md) ·
[API](docs/API_DOCUMENTATION.md) · [Roadmap and limitations](docs/DEVELOPMENT_ROADMAP.md) ·
[Development log](docs/DEVELOPMENT_LOG.md) · [Contributing](docs/CONTRIBUTING.md)
