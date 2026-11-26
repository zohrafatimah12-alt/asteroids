"""Analytics: SQL extracts -> Pandas metrics. Read-only; never touches gameplay.

Every number is computed from recorded play. With no data a metric is None or
empty rather than a placeholder.
"""

import json

import pandas as pd

from nebula.core import db


def _frame(con, table: str, campaign_id: int) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM {table} WHERE campaign_id = ? ORDER BY id",
                             con, params=(campaign_id,))


def _rate(series: pd.Series):
    return None if series.empty else round(float(series.mean()) * 100, 1)


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records"))


def metrics(con, campaign_id: int) -> dict:
    attempts = _frame(con, "mission_attempts", campaign_id)
    talks = _frame(con, "negotiations", campaign_id)
    ledger = _frame(con, "resource_ledger", campaign_id)
    relations = _frame(con, "relationship_history", campaign_id)
    events = _frame(con, "analytics_events", campaign_id)
    state = db.load(con, campaign_id)

    by_type = (attempts.groupby("mission_type")["success"].agg(attempts="count", rate="mean")
               .reset_index() if not attempts.empty else pd.DataFrame())
    if not by_type.empty:
        by_type["rate"] = (by_type["rate"] * 100).round(1)

    aircraft = pd.DataFrame()
    flown = attempts.dropna(subset=["aircraft"]) if not attempts.empty else attempts
    if not flown.empty:
        aircraft = flown.groupby("aircraft").agg(
            sorties=("success", "count"), success_rate=("success", "mean"), kills=("kills", "sum"),
            shots=("shots", "sum"), hits=("hits", "sum"), avg_damage=("damage_taken", "mean")).reset_index()
        aircraft["success_rate"] = (aircraft["success_rate"] * 100).round(1)
        aircraft["accuracy"] = (aircraft["hits"] / aircraft["shots"].where(aircraft["shots"] > 0) * 100).round(1)
        aircraft["avg_damage"] = aircraft["avg_damage"].round(1)

    resources = []
    if not ledger.empty:
        ledger["flow"] = ledger["amount"].map(lambda v: "earned" if v > 0 else "spent")
        table = ledger.pivot_table(index="resource", columns="flow", values="amount",
                                   aggfunc="sum", fill_value=0)
        for name, row in table.iterrows():
            resources.append({"resource": name, "earned": int(row.get("earned", 0)),
                              "spent": int(-row.get("spent", 0))})
    spending = []
    if not ledger.empty and (ledger["amount"] < 0).any():
        out = ledger[ledger["amount"] < 0].copy()
        out["category"] = out["reason"].str.split(":").str[0]
        grouped = out.groupby("category")["amount"].sum().abs().sort_values(ascending=False)
        spending = [{"category": k, "total": int(v)} for k, v in grouped.items()]

    wins = int(attempts["success"].sum()) if not attempts.empty else 0
    spent_credits = next((r["spent"] for r in resources if r["resource"] == "credits"), 0)

    trend = []
    if not relations.empty:
        mine = relations[(relations["country_a"] == "lumeris") | (relations["country_b"] == "lumeris")].copy()
        if not mine.empty:
            mine["country"] = mine["country_a"].where(mine["country_a"] != "lumeris", mine["country_b"])
            trend = _records(mine.groupby(["country", "day"], as_index=False)["value"].last())

    decisions = []
    if not events.empty:
        picks = events[events["event_type"] == "decision_choice"]
        if not picks.empty:
            parsed = pd.DataFrame([json.loads(d) for d in picks["detail"]])
            decisions = _records(parsed.groupby(["type", "choice"]).size().reset_index(name="count"))

    modes = attempts["mode"].value_counts().to_dict() if not attempts.empty else {}
    return {
        "attempts": len(attempts),
        "mission_success_rate": _rate(attempts["success"]),
        "flown_success_rate": _rate(attempts.loc[attempts["mode"] == "flown", "success"]),
        "by_mode": modes,
        "by_type": _records(by_type),
        "aircraft": _records(aircraft),
        "negotiations": len(talks),
        "diplomacy_success_rate": _rate(talks["success"]),
        "conflicts_avoided": state["conflicts_avoided"],
        "resources": resources,
        "spending": spending,
        "credits_per_success": round(spent_credits / wins, 1) if wins else None,
        "campaign": {"completed": len(state["completed"]), "total": 100, "day": state["day"]},
        "decisions": decisions,
        "relationship_trend": trend,
    }


def export_csv(campaign_id: int, folder) -> list[str]:
    """Dump raw history tables for notebooks or BI tools."""
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    with db.connect() as con:
        for table in db.HISTORY:
            path = folder / f"{table}.csv"
            _frame(con, table, campaign_id).to_csv(path, index=False)
            written.append(str(path))
    return written


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Analyse a NEBULA campaign")
    parser.add_argument("campaign_id", type=int)
    parser.add_argument("--export", type=Path, help="folder for CSV export")
    args = parser.parse_args()
    with db.connect() as connection:
        print(json.dumps(metrics(connection, args.campaign_id), indent=2))
    if args.export:
        export_csv(args.campaign_id, args.export)
