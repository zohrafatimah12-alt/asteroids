"""Regenerate the data-derived docs: python -m docs.generate_docs"""

from pathlib import Path

from nebula.core.db import schema
from nebula.data.aircraft import ABILITIES, AIRCRAFT
from nebula.data.campaign import levels
from nebula.data.countries import COUNTRIES
from nebula.data.geography import AIRBASES, DISPUTES, STRATEGIC, TRADE_ROUTES, neighbours

HERE = Path(__file__).parent

INTRO = """# VEYRA World Bible

*Generated from `nebula/data`. Edit the data, then run `python -m docs.generate_docs`.*
All nations, people and technology here are original fiction.

## The sky
**Nebula** is the star Veyra orbits. The **Shard-Star** is a broken body from outside the system.
For most of the campaign its first fragments look like unrelated mysteries: warm glass older than
Veyra, a regular pulse, a trajectory hidden in a Zorvanian vault, and four centuries of Frostaran
sky logs. Together they show it will strike Veyra.

## History in brief
After an age of resource wars came the **Quiet Century**. Lumeris disarmed, others rearmed, and
old territorial claims were frozen, not solved. The campaign begins as that peace frays.
"""


def world() -> str:
    out = [INTRO, "## Nations"]
    for cid, c in COUNTRIES.items():
        out.append(f"""### {c['name']} (capital {c['capital']})
- **Colours:** {', '.join(c['colors'])}. **Flag emblem:** {c['emblem']}
- **Government:** {c['government']}
- **Geography:** {c['geography']}. **Cities:** {', '.join(c['cities'])}
- **Population / economy:** {c['population']}M / {c['economy']} of 100
- **Resources:** {', '.join(c['resources'])}
- **History:** {c['history']}
- **Culture:** {c['culture']}
- **Air force:** {c['airforce']} (military {c['military']}, technology {c['technology']})
- **Aircraft:** {', '.join(a['name'] + ' (' + a['category'] + ')' for a in AIRCRAFT.values() if a['country'] == cid)}
- **Strengths:** {', '.join(c['strengths'])}. **Weaknesses:** {', '.join(c['weaknesses'])}
- **Historic allies:** {', '.join(c['allies']) or 'none'}. **Historic enemies:** {', '.join(c['enemies']) or 'none'}. All others start near neutral and change in play.
- **Land borders:** {', '.join(neighbours(cid)) or 'none (island nation)'}
""")
    out.append("## Places\n" + "\n".join(f"- Airbase: {b[1]} ({b[2]}, {b[5]})" for b in AIRBASES))
    out.append("\n".join(f"- Disputed: {d[1]} ({d[2]} / {d[3]})" for d in DISPUTES))
    out.append("\n".join(f"- Strategic: {s[1]}. {s[4]}." for s in STRATEGIC))
    out.append("\n".join(f"- Trade route: {a} to {b}" for a, b in TRADE_ROUTES))
    out.append("## Aircraft abilities\n" + "\n".join(f"- `{k}`: {v}" for k, v in ABILITIES.items()))
    out.append("## Campaign (spoilers)")
    for m in levels():
        if m["level"] % 10 == 1:
            out.append(f"\n### Chapter {m['chapter']}: {m['chapter_title']}")
        out.append(f"{m['level']}. **{m['title']}** ({m['type']}): {m['story']}")
    return "\n".join(out) + "\n"


def database() -> str:
    return f"""# Database Schema

SQLite file at `saves/nebula.db` (override with `NEBULA_DB`). *Generated from `nebula/core/db.py`.*

- `campaigns`: current game state as one JSON document (the autosave).
- `snapshots`: manual saves. Loading one **forks a new campaign** and copies history up to that point, so analytics never mix abandoned timelines.
- `sorties`: the Pygame bridge; each result is applied once.
- History tables: append-only facts that analytics reads. Every row has `campaign_id` and in-game `day`.

Reference data (countries, aircraft, missions) lives in version-controlled Python under `nebula/data`, not in the database.

```sql
{schema()}
```

## PostgreSQL migration path
All writes are in `nebula/core/db.py`. A port needs: `INTEGER PRIMARY KEY` to identity columns, `?` to `%s` placeholders,
`executescript` to a migration tool, removal of `PRAGMA`, `datetime('now')` (in `api.py`) to `now()`, JSON text columns to `jsonb`,
and a SQLAlchemy engine for `pandas.read_sql_query`. This port has not been done or tested.
"""


if __name__ == "__main__":
    (HERE / "WORLD_BIBLE.md").write_text(world())
    (HERE / "DATABASE_SCHEMA.md").write_text(database())
