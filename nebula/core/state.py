"""Game state: a plain JSON-serialisable dict plus small mutation helpers.

Every meaningful mutation goes through these helpers so that analytics records
are produced from real play. Records queue in state["_records"] until the
database layer flushes them.
"""

import random

from nebula.data.aircraft import AIRCRAFT, UPGRADES
from nebula.data.countries import COUNTRIES
from nebula.data.geography import DISPUTES

HOME = "lumeris"
FOREIGN = [c for c in COUNTRIES if c != HOME]
START_TRUST = {"aerovant": 52, "elyndra": 55, "varkhen": 22, "drakoria": 34, "thalmora": 45,
               "ostraven": 40, "zorvania": 28, "kryvos": 40, "frostara": 46}


class RuleError(ValueError):
    """An action the rules do not allow. The message is shown to the player."""


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def _base_relation(a: str, b: str) -> int:
    ca, cb = COUNTRIES[a], COUNTRIES[b]
    if b in ca["allies"] or a in cb["allies"]:
        return 55
    if b in ca["enemies"] or a in cb["enemies"]:
        return -50
    return random.Random(pair_key(a, b)).randint(-12, 18)


def new_state(player: str, seed: int | None = None) -> dict:
    relations = {pair_key(a, b): _base_relation(a, b)
                 for i, a in enumerate(COUNTRIES) for b in list(COUNTRIES)[i + 1:]}
    for other, value in {"aerovant": 20, "elyndra": 25, "thalmora": 10, "ostraven": 8,
                         "frostara": 6, "zorvania": -5, "kryvos": 4, "drakoria": -12,
                         "varkhen": -22}.items():
        relations[pair_key(HOME, other)] = value
    state = {
        "player": player, "seed": random.randrange(1 << 30) if seed is None else seed, "day": 1,
        "resources": {"credits": 600, "materials": 240, "fuel": 500, "research": 40},
        "reputation": 50, "relations": relations, "trust": dict(START_TRUST),
        "treaties": {c: [] for c in FOREIGN},
        "disputes": {d[0]: "open" for d in DISPUTES},
        "fleet": [], "next_uid": 1, "builds": [], "research": [],
        "intel": {c: {} for c in FOREIGN},
        "completed": {}, "unlocked": 1, "threat": 0, "weather": "clear",
        "events": [], "conflicts_avoided": 0, "ending": None, "_records": [],
    }
    for kind in ("lm_wren", "lm_lantern"):
        add_aircraft(state, kind)
    return state


def record(state: dict, table: str, **fields) -> None:
    state["_records"].append((table, {"day": state["day"], **fields}))


def log(state: dict, event_type: str, **detail) -> None:
    record(state, "analytics_events", event_type=event_type, detail=detail)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def relation(state: dict, a: str, b: str = HOME) -> int:
    return state["relations"][pair_key(a, b)]


def change_relation(state, a, delta, b=HOME, reason=""):
    if not delta or a == b:
        return
    key = pair_key(a, b)
    old = state["relations"][key]
    new = clamp(old + delta, -100, 100)
    state["relations"][key] = new
    record(state, "relationship_history", country_a=min(a, b), country_b=max(a, b),
           value=new, delta=new - old, reason=reason)


def change_trust(state, country, delta):
    if country != HOME:
        state["trust"][country] = clamp(state["trust"][country] + delta, 0, 100)


def change_reputation(state, delta):
    state["reputation"] = clamp(state["reputation"] + delta, 0, 100)


def gain(state, reason: str, **amounts):
    """Apply resource changes (negative values drain, floored at zero)."""
    for name, amount in amounts.items():
        old = state["resources"][name]
        state["resources"][name] = max(0, old + int(amount))
        delta = state["resources"][name] - old
        if delta:
            record(state, "resource_ledger", resource=name, amount=delta, reason=reason)


def spend(state, reason: str, **costs):
    short = [f"{v} {k}" for k, v in costs.items() if state["resources"][k] < v]
    if short:
        raise RuleError("Not enough resources: needs " + ", ".join(short))
    gain(state, reason, **{k: -v for k, v in costs.items()})


def add_aircraft(state, kind: str) -> dict:
    plane = {"uid": state["next_uid"], "type": kind, "condition": 100, "fuel": 100,
             "ammo": AIRCRAFT[kind]["ammo"], "upgrades": {}, "sorties": 0, "kills": 0}
    state["next_uid"] += 1
    state["fleet"].append(plane)
    return plane


def stats(plane: dict) -> dict:
    """Airframe stats with upgrades applied."""
    result = dict(AIRCRAFT[plane["type"]])
    for key, tier in plane["upgrades"].items():
        _, stat, bonus, _ = UPGRADES[key]
        result[stat] += bonus * tier
    return result


def find_plane(state, uid: int) -> dict:
    for plane in state["fleet"]:
        if plane["uid"] == uid:
            return plane
    raise RuleError("No such aircraft in your hangar")
