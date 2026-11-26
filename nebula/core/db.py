"""SQLite persistence. All SQL for writes lives here to ease a PostgreSQL move."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HISTORY = {
    "mission_attempts": "level INTEGER, mission_type TEXT, country TEXT, mode TEXT, success INTEGER, "
                        "aircraft TEXT, kills INTEGER, shots INTEGER, hits INTEGER, "
                        "damage_taken INTEGER, duration REAL",
    "negotiations": "country TEXT, kind TEXT, success INTEGER, offer INTEGER",
    "relationship_history": "country_a TEXT, country_b TEXT, value INTEGER, delta INTEGER, reason TEXT",
    "resource_ledger": "resource TEXT, amount INTEGER, reason TEXT",
    "intel_discoveries": "country TEXT, subject TEXT, confidence REAL, source TEXT",
    "world_events": "category TEXT, title TEXT, countries TEXT, effects TEXT",
    "analytics_events": "event_type TEXT, detail TEXT",
}


def db_path() -> Path:
    return Path(os.environ.get("NEBULA_DB", Path(__file__).resolve().parents[2] / "saves" / "nebula.db"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def schema() -> str:
    parts = [
        "CREATE TABLE IF NOT EXISTS campaigns (id INTEGER PRIMARY KEY, player TEXT NOT NULL, "
        "state TEXT NOT NULL, created_at TEXT, updated_at TEXT);",
        "CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, campaign_id INTEGER NOT NULL "
        "REFERENCES campaigns(id), label TEXT, state TEXT NOT NULL, watermarks TEXT NOT NULL, created_at TEXT);",
        "CREATE TABLE IF NOT EXISTS sorties (id TEXT PRIMARY KEY, campaign_id INTEGER NOT NULL "
        "REFERENCES campaigns(id), level INTEGER, uid INTEGER, status TEXT, message TEXT, created_at TEXT);",
    ]
    for table, columns in HISTORY.items():
        parts.append(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY, campaign_id INTEGER "
                     f"NOT NULL REFERENCES campaigns(id), day INTEGER NOT NULL, {columns});")
        parts.append(f"CREATE INDEX IF NOT EXISTS ix_{table} ON {table}(campaign_id);")
    return "\n".join(parts)


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        con.executescript(schema())
        with con:
            yield con
    finally:
        con.close()


def _flush(con, campaign_id: int, state: dict):
    for table, row in state.pop("_records", []):
        if table not in HISTORY:
            raise ValueError(f"unknown table {table}")
        row = {"campaign_id": campaign_id,
               **{k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()}}
        con.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' * len(row))})",
                    list(row.values()))
    state["_records"] = []


def create_campaign(con, state: dict) -> int:
    cur = con.execute("INSERT INTO campaigns (player, state, created_at, updated_at) VALUES (?,?,?,?)",
                      (state["player"], "{}", _now(), _now()))
    save(con, cur.lastrowid, state)
    return cur.lastrowid


def save(con, campaign_id: int, state: dict):
    _flush(con, campaign_id, state)
    con.execute("UPDATE campaigns SET state=?, updated_at=? WHERE id=?",
                (json.dumps(state), _now(), campaign_id))


def load(con, campaign_id: int) -> dict:
    row = con.execute("SELECT state FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    if not row:
        raise KeyError(campaign_id)
    return json.loads(row["state"])


def list_campaigns(con) -> list[dict]:
    out = []
    for row in con.execute("SELECT id, player, state, updated_at FROM campaigns ORDER BY updated_at DESC, id DESC"):
        state = json.loads(row["state"])
        out.append({"id": row["id"], "player": row["player"], "updated_at": row["updated_at"],
                    "day": state["day"], "completed": len(state["completed"])})
    return out


def snapshot(con, campaign_id: int, label: str) -> int:
    state = load(con, campaign_id)
    marks = {t: con.execute(f"SELECT COALESCE(MAX(id),0) FROM {t} WHERE campaign_id=?",
                            (campaign_id,)).fetchone()[0] for t in HISTORY}
    return con.execute("INSERT INTO snapshots (campaign_id,label,state,watermarks,created_at) VALUES (?,?,?,?,?)",
                       (campaign_id, label, json.dumps(state), json.dumps(marks), _now())).lastrowid


def list_snapshots(con, campaign_id: int) -> list[dict]:
    return [dict(r) for r in con.execute(
        "SELECT id,label,created_at FROM snapshots WHERE campaign_id=? ORDER BY id DESC", (campaign_id,))]


def restore(con, snapshot_id: int) -> int:
    """Loading a snapshot forks a new campaign so analytics history stays truthful."""
    snap = con.execute("SELECT * FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
    if not snap:
        raise KeyError(snapshot_id)
    new_id = create_campaign(con, json.loads(snap["state"]))
    marks = json.loads(snap["watermarks"])
    for table, columns in HISTORY.items():
        names = "day," + ",".join(c.split()[0] for c in columns.split(", "))
        con.execute(f"INSERT INTO {table} (campaign_id,{names}) SELECT ?,{names} FROM {table} "
                    "WHERE campaign_id=? AND id<=?", (new_id, snap["campaign_id"], marks[table]))
    return new_id
