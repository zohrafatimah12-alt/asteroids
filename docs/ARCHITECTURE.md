# Architecture

```
browser (nebula/web: HTML, CSS, JavaScript modules, SVG map)
   | JSON over http://127.0.0.1
nebula/api.py (FastAPI: validation, redaction, sortie bridge)
   |-- nebula/core      rules on a JSON-serialisable state dict
   |-- nebula/core/db   SQLite persistence and history records
   |-- nebula/analytics read-only SQL + Pandas
   '-- subprocess: python -m nebula.combat --ticket file.json
            sim.py (headless) <- app.py (Pygame render, input, audio)
nebula/data   countries, geography, aircraft, campaign, events
repo root     original Asteroids game; CircleShape and Shot are reused by combat
```

## Decisions
- **Plain JavaScript instead of React/Vite.** The development environment had no Linux Node.js, and the game needs no build step. The API boundary allows a React client later.
- **Rules only on the server.** The browser renders state and sends actions. Unconfirmed intelligence is redacted before it leaves the server.
- **Data-driven campaign.** Each level is one line (title, type, story). Difficulty, rewards, requirements and consequences come from `core/missions.py`.
- **Map consistency by construction.** Countries are rings of shared vertices; borders are the shared edges. Both neighbours get identical polylines.
- **Headless simulation.** `sim.py` takes `Controls` and a time step, so tests and the autopilot run the real game logic without a window.

## Combat bridge
1. `POST .../sorties` validates the aircraft and writes a ticket (mission, aircraft stats, weather, seed).
2. A subprocess flies it (fixed argument list, no shell).
3. It atomically writes `<id>.result.json`.
4. The browser polls `GET /api/sorties/{id}`; the server applies the result once. No result means nothing changes.

## Reuse from Asteroids
| Original | In NEBULA |
|---|---|
| `CircleShape` and `collides_with` | Base of aircraft and fragments |
| `Shot` | Base of cannon rounds and missiles (movement, off-screen removal) |
| `Player` rotation convention, cooldown shooting | Flight model, now with momentum and throttle |
| `Asteroid.split` | Re-implemented in `Fragment` for falling Shard-Star debris |
| Delta-time loop, sprite groups, edge spawning | `app.py` and `sim.py` |

## Security
Local single-player only. The server binds to 127.0.0.1 and checks the Host header; there is no authentication, so do not expose it to a network. User text is escaped in the browser, SQL values are parameterised, and no secrets are used. A local user could forge a sortie result file.
