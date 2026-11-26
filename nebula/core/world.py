"""The living world: passing days, income and events that change state."""

import random

from nebula.core import stages
from nebula.core.hangar import finish_builds
from nebula.core.intel import add_intel
from nebula.core.state import (foreign, home, change_relation, change_trust, gain, record, relation)
from nebula.data.countries import COUNTRIES
from nebula.data.events import EVENTS


def daily_income(state) -> dict:
    trades = sum("trade" in t for t in state["treaties"].values())
    allies = sum("alliance" in t for t in state["treaties"].values())
    return {"credits": 25 + 18 * trades, "materials": 10 + 7 * trades,
            "fuel": 35 + 6 * trades, "research": 4 + 3 * allies}


def roll_event(state, rng: random.Random) -> dict | None:
    category, title, text, effects = rng.choice(EVENTS)
    a, b = rng.sample(foreign(state), 2)
    if category == "threat" and state["unlocked"] < 5:
        return None
    # Treaties and goodwill have teeth: friends do not stage incidents with each other.
    if effects.get("rel", 0) < 0 and relation(state, a, b) >= 45:
        return None
    names = {"a": COUNTRIES[a]["name"], "b": COUNTRIES[b]["name"], "home": COUNTRIES[home(state)]["name"]}
    event = {"day": state["day"], "category": category, "title": title.format(**names),
             "text": text.format(**names), "countries": [a, b] if "{b}" in title + text else [a]}
    if "rel" in effects:
        change_relation(state, a, effects["rel"], b=b, reason=f"event:{category}")
    if "trust" in effects and not (effects["trust"] < 0 and "alliance" in state["treaties"][a]):
        change_trust(state, a, effects["trust"])
    resources = {k: v for k, v in effects.items()
                 if k in ("credits", "materials", "fuel", "research")}
    if resources:
        gain(state, f"event:{category}", **resources)
    if "intel" in effects:
        add_intel(state, a, rng.choice(("strength", "aircraft", "bases")), 0.3, "intercept")
    if "threat" in effects:
        state["threat"] = min(100, state["threat"] + effects["threat"])
    if "weather" in effects:
        state["weather"] = effects["weather"]
    state["events"] = (state["events"] + [event])[-60:]
    record(state, "world_events", category=category, title=event["title"],
           countries=",".join(event["countries"]), effects=effects)
    return event


def advance_day(state, days: int = 1) -> list[dict]:
    new_events = []
    for _ in range(days):
        state["day"] += 1
        rng = random.Random(f"{state['seed']}:world:{state['day']}")
        state["weather"] = rng.choice(["clear", "clear", "cloud", "wind", "storm"])
        gain(state, "income:daily", **daily_income(state))
        finish_builds(state)
        stages.daily(state)
        from nebula.core import conflict
        conflict.daily(state)
        if rng.random() < 0.65:
            event = roll_event(state, rng)
            if event:
                new_events.append(event)
    return new_events
