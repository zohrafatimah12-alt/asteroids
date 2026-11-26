"""Treaties, pressure, aid and territorial negotiation."""

import random

from nebula.core import agreements, stages
from nebula.core.state import (RuleError, foreign, home, change_relation, change_reputation,
                               change_trust, gain, log, record, relation, spend)
from nebula.data.countries import COUNTRIES
from nebula.data.geography import DISPUTES

# kind: (label, score needed, prerequisite treaty)
TREATIES = {
    "peace": ("Peace treaty", 20, None),
    "trade": ("Trade agreement", 34, None),
    "intelligence": ("Intelligence agreement", 55, "peace"),
    "alliance": ("Military alliance", 72, "peace"),
}


def score(state, country: str, sweetener: int = 0) -> float:
    return (relation(state, country) + 0.6 * state["trust"][country]
            + 0.4 * (state["reputation"] - 50) + sweetener / 10)


def outlook(state, country: str, kind: str) -> str:
    margin = score(state, country) - TREATIES[kind][1]
    return "likely" if margin >= 6 else "uncertain" if margin >= -6 else "unlikely"


def _noise(state, *parts) -> int:
    return random.Random(f"{state['seed']}:{state['day']}:{':'.join(parts)}").randint(-5, 5)


def _check_country(state, country: str):
    if country not in foreign(state):
        raise RuleError("Choose a foreign nation")


def propose(state, country: str, kind: str, sweetener: int = 0) -> tuple[bool, str]:
    _check_country(state, country)
    if country in state.get("wars", {}):
        raise RuleError("You are at war. Only a ceasefire can be negotiated.")
    if kind not in TREATIES:
        raise RuleError("Unknown treaty")
    label, needed, prerequisite = TREATIES[kind]
    if country == stages.current_rival(state):
        raise RuleError(f"{COUNTRIES[country]['name']} is your current opponent. "
                        "Finish all ten missions of this stage before signing any treaty.")
    if kind in state["treaties"][country]:
        raise RuleError("That agreement is already in force")
    if prerequisite and prerequisite not in state["treaties"][country]:
        raise RuleError(f"Requires a {TREATIES[prerequisite][0].lower()} first")
    if sweetener:
        spend(state, "diplomacy:offer", credits=sweetener)
    accepted = score(state, country, sweetener) + _noise(state, country, kind) >= needed
    record(state, "negotiations", country=country, kind=kind, success=int(accepted),
           offer=sweetener)
    name = COUNTRIES[country]["name"]
    if not accepted:
        change_trust(state, country, -2)
        return False, f"{name} declined the {label.lower()}. Build trust or improve relations."
    state["treaties"][country].append(kind)
    agreements.record(state, country, kind, "signed", "negotiated")
    change_relation(state, country, 8, reason=f"treaty:{kind}")
    change_trust(state, country, 6)
    change_reputation(state, 2)
    if kind == "alliance":
        # Alliances are noticed by the ally's enemies.
        for rival in foreign(state):
            if rival != country and relation(state, rival, country) <= -40:
                change_relation(state, rival, -5, reason="rival_alliance")
    log(state, "treaty_signed", country=country, treaty=kind)
    return True, f"{name} signed the {label.lower()}."


def send_aid(state, country: str) -> str:
    _check_country(state, country)
    if country in state.get("wars", {}):
        raise RuleError("Aid cannot cross an active front")
    spend(state, "diplomacy:aid", credits=80, materials=20)
    change_relation(state, country, 6, reason="aid")
    change_trust(state, country, 5)
    change_reputation(state, 1)
    stages.strain(state, country, -10, "you sent aid")
    log(state, "aid_sent", country=country)
    return f"Aid delivered to {COUNTRIES[country]['name']}."


def pressure(state, country: str) -> tuple[bool, str]:
    _check_country(state, country)
    backing = sum("alliance" in t for t in state["treaties"].values())
    success = (state["reputation"] + backing * 12 + _noise(state, country, "pressure") * 3
               >= COUNTRIES[country]["military"])
    change_relation(state, country, -9, reason="pressure")
    change_trust(state, country, -8)
    from nebula.core import conflict
    conflict.break_promise(state, country, "you applied pressure")
    stages.strain(state, country, 35, "you applied pressure to a treaty partner")
    record(state, "negotiations", country=country, kind="pressure", success=int(success), offer=0)
    if success:
        gain(state, "diplomacy:concession", credits=110)
        return True, "They conceded economic terms. Trust has suffered."
    change_reputation(state, -3)
    return False, "The pressure failed and your reputation suffered."


# approach: (label, score needed from each foreign claimant, credit cost, reputation reward)
APPROACHES = {
    "shared": ("Shared stewardship", 30, 100, 5),
    "arbitrate": ("Neutral arbitration", 22, 160, 3),
    "concede": ("Concede our claim", -20, 0, 4),
}


def negotiate_dispute(state, dispute_id: str, approach: str) -> tuple[bool, str]:
    match = next((d for d in DISPUTES if d[0] == dispute_id), None)
    if not match or approach not in APPROACHES:
        raise RuleError("Unknown dispute or approach")
    _, name, a, b, _, _ = match
    if state["disputes"][dispute_id] != "open":
        raise RuleError("That dispute is already settled")
    if approach == "concede" and home(state) not in (a, b):
        raise RuleError("You have no claim here to concede")
    _, needed, cost, reputation = APPROACHES[approach]
    spend(state, "diplomacy:territory", credits=cost)
    parties = [c for c in (a, b) if c != home(state)]
    success = all(score(state, c) + _noise(state, c, dispute_id) >= needed for c in parties)
    for c in parties:
        record(state, "negotiations", country=c, kind=f"territory:{approach}",
               success=int(success), offer=cost)
    if not success:
        for c in parties:
            change_trust(state, c, -3)
        return False, f"Talks over {name} collapsed. A claimant does not trust you enough."
    state["disputes"][dispute_id] = approach
    state["conflicts_avoided"] += 1
    change_reputation(state, reputation)
    for c in parties:
        change_relation(state, c, 12, reason="territory")
        change_trust(state, c, 8)
    if len(parties) == 2:
        change_relation(state, a, 18, b=b, reason="mediation")
    log(state, "conflict_avoided", source="territory", dispute=dispute_id)
    return True, f"{name} settled: {APPROACHES[approach][0].lower()}."
