"""Intelligence with explicit confidence. The API only ever sends redacted data."""

import random

from nebula.core.state import FOREIGN, RuleError, change_relation, change_trust, log, record, spend
from nebula.data.aircraft import AIRCRAFT
from nebula.data.countries import COUNTRIES
from nebula.data.geography import AIRBASES

SUBJECTS = ("strength", "weaknesses", "aircraft", "bases")
LEVELS = ((0.9, "confirmed"), (0.65, "probable"), (0.3, "rumour"), (0.0, "unknown"))


def label(confidence: float) -> str:
    return next(name for floor, name in LEVELS if confidence >= floor)


def add_intel(state, country: str, subject: str, amount: float, source: str):
    if "lens" in state["research"]:
        amount *= 1.25
    old = state["intel"][country].get(subject, 0.0)
    new = round(min(1.0, old + amount), 2)
    state["intel"][country][subject] = new
    if label(new) != label(old):
        record(state, "intel_discoveries", country=country, subject=subject,
               confidence=new, source=source)


def operate(state, country: str, subject: str, method: str) -> str:
    if country not in FOREIGN or subject not in SUBJECTS:
        raise RuleError("Unknown intelligence target")
    if state["intel"][country].get(subject, 0) >= 1:
        raise RuleError("Already fully confirmed")
    treaty = "intelligence" in state["treaties"][country]
    if method == "signals":
        spend(state, "intel:signals", credits=45)
        amount = 0.25
    elif method == "reconnaissance":
        spend(state, "intel:reconnaissance", fuel=60, credits=20)
        amount = 0.4
        if not treaty:
            change_relation(state, country, -3, reason="overflight")
            change_trust(state, country, -2)
    elif method == "exchange":
        if not treaty:
            raise RuleError("Needs an intelligence agreement")
        spend(state, "intel:exchange", research=10)
        amount = 0.55
    else:
        raise RuleError("Unknown method")
    add_intel(state, country, subject, amount, method)
    log(state, "intel_operation", country=country, subject=subject, method=method)
    return f"Intelligence updated: {label(state['intel'][country][subject])}."


def _estimate(value: int, confidence: float, key: str):
    level = label(confidence)
    if level == "unknown":
        return None
    if level == "confirmed":
        return str(value)
    spread = 22 if level == "rumour" else 9
    centre = value + random.Random(key).randint(-spread // 2, spread // 2)
    return f"{max(0, centre - spread)}–{min(100, centre + spread)}"


def report(state, country: str) -> dict:
    """What the player is allowed to know about a foreign nation."""
    known = state["intel"][country]
    c = COUNTRIES[country]
    out = {}
    for subject in SUBJECTS:
        conf = known.get(subject, 0.0)
        level = label(conf)
        value = None
        if subject == "strength":
            value = _estimate(c["military"], conf, country)
        elif level != "unknown":
            if subject == "weaknesses":
                value = c["weaknesses"] if conf >= 0.65 else c["weaknesses"][:1]
            elif subject == "aircraft":
                fleet = [a["name"] for a in AIRCRAFT.values() if a["country"] == country]
                value = fleet if conf >= 0.65 else fleet[:1]
            else:
                value = [b[1] for b in AIRBASES if b[2] == country]
        out[subject] = {"confidence": conf, "level": level, "value": value}
    return out


def tracks(state) -> list[dict]:
    """Aircraft movements visible this day, only where we have some intelligence."""
    result = []
    for country in FOREIGN:
        conf = max(state["intel"][country].get("aircraft", 0),
                   state["intel"][country].get("bases", 0))
        bases = [b for b in AIRBASES if b[2] == country]
        if conf < 0.3 or not bases:
            continue
        rng = random.Random(f"{state['seed']}:{state['day']}:{country}")
        origin = rng.choice(bases)
        target = rng.choice([b for b in AIRBASES if b[0] != origin[0]])
        result.append({"country": country, "from": origin[0], "to": target[0],
                       "confidence": conf, "level": label(conf)})
    return result
