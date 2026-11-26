# API

Base URL `http://127.0.0.1:8000`. Interactive reference while the server runs: `/docs`.
Errors are `{"detail": ...}`: **404** unknown id, **409** a game rule forbids it, **422** invalid request.

| Method and path | Purpose |
|---|---|
| GET `/api/world` | Map geometry, treaties, upgrades, abilities |
| GET `/api/levels` | All 100 level definitions |
| GET, POST `/api/campaigns` | List; create with `{"player": "name", "seed": 5}` (seed optional) |
| GET `/api/campaigns/{id}` | Full redacted game view |
| GET `/api/campaigns/{id}/missions/{level}` | Briefing, peaceful option, wing odds |
| POST `/api/campaigns/{id}/actions` | Perform an action; returns `{message, state}` |
| GET `/api/campaigns/{id}/analytics` | Metrics from recorded play |
| GET, POST `/api/campaigns/{id}/snapshots` | List; save with `{"label": "..."}` |
| POST `/api/snapshots/{id}/restore` | Fork a campaign from a snapshot |
| POST `/api/campaigns/{id}/sorties` | `{level, uid}`; opens the combat window |
| GET `/api/sorties/{id}` | `flying`, `complete`, `aborted` or `void` |

## Actions
Body: `{"type": ..., plus the fields below}`

| type | fields |
|---|---|
| `treaty` | country, kind (peace, trade, intelligence, alliance), offer (credits, optional) |
| `aid`, `pressure` | country |
| `dispute` | subject (dispute id), kind (shared, arbitrate, concede) |
| `intel` | country, subject (strength, weaknesses, aircraft, bases), kind (signals, reconnaissance, exchange) |
| `service` | uid, kind (refuel, rearm, repair, all) |
| `upgrade` | uid, kind (engine, controls, plating, sensors, tanks, magazine) |
| `manufacture` | kind (aircraft id) |
| `research` | kind (project id) |
| `decide` | level, kind (choice id) |
| `delegate` | level, uid |
| `peaceful` | level |
| `wait` | none |
| `joint_propose` | stage (1–9), terms (every key in `/api/world` `terms`) |
| `joint_counter`, `joint_postpone` | stage |
| `ending` | kind (union, evacuation) |

`joint_propose`, `treaty`, `aid`, `pressure`, `dispute` and `intel` each take one day. A rejected negotiation is still a 200: it happened, and it is recorded.
