# Database Schema

SQLite file at `saves/nebula.db` (override with `NEBULA_DB`). *Generated from `nebula/core/db.py`.*

- `campaigns`: current game state as one JSON document (the autosave).
- `snapshots`: manual saves. Loading one **forks a new campaign** and copies history up to that point, so analytics never mix abandoned timelines.
- `sorties`: the Pygame bridge; each result is applied once.
- History tables: append-only facts that analytics reads. Every row has `campaign_id` and in-game `day`.

Reference data (countries, aircraft, missions) lives in version-controlled Python under `nebula/data`, not in the database.

```sql
CREATE TABLE IF NOT EXISTS campaigns (id INTEGER PRIMARY KEY, player TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), label TEXT, state TEXT NOT NULL, watermarks TEXT NOT NULL, created_at TEXT);
CREATE TABLE IF NOT EXISTS sorties (id TEXT PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), level INTEGER, uid INTEGER, status TEXT, message TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS mission_attempts (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, level INTEGER, mission_type TEXT, country TEXT, mode TEXT, success INTEGER, aircraft TEXT, kills INTEGER, shots INTEGER, hits INTEGER, damage_taken INTEGER, duration REAL);
CREATE INDEX IF NOT EXISTS ix_mission_attempts ON mission_attempts(campaign_id);
CREATE TABLE IF NOT EXISTS negotiations (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, country TEXT, kind TEXT, success INTEGER, offer INTEGER);
CREATE INDEX IF NOT EXISTS ix_negotiations ON negotiations(campaign_id);
CREATE TABLE IF NOT EXISTS relationship_history (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, country_a TEXT, country_b TEXT, value INTEGER, delta INTEGER, reason TEXT);
CREATE INDEX IF NOT EXISTS ix_relationship_history ON relationship_history(campaign_id);
CREATE TABLE IF NOT EXISTS resource_ledger (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, resource TEXT, amount INTEGER, reason TEXT);
CREATE INDEX IF NOT EXISTS ix_resource_ledger ON resource_ledger(campaign_id);
CREATE TABLE IF NOT EXISTS intel_discoveries (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, country TEXT, subject TEXT, confidence REAL, source TEXT);
CREATE INDEX IF NOT EXISTS ix_intel_discoveries ON intel_discoveries(campaign_id);
CREATE TABLE IF NOT EXISTS world_events (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, category TEXT, title TEXT, countries TEXT, effects TEXT);
CREATE INDEX IF NOT EXISTS ix_world_events ON world_events(campaign_id);
CREATE TABLE IF NOT EXISTS analytics_events (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, event_type TEXT, detail TEXT);
CREATE INDEX IF NOT EXISTS ix_analytics_events ON analytics_events(campaign_id);
```

## PostgreSQL migration path
All writes are in `nebula/core/db.py`. A port needs: `INTEGER PRIMARY KEY` to identity columns, `?` to `%s` placeholders,
`executescript` to a migration tool, removal of `PRAGMA`, `datetime('now')` (in `api.py`) to `now()`, JSON text columns to `jsonb`,
and a SQLAlchemy engine for `pandas.read_sql_query`. This port has not been done or tested.
