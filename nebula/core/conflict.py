"""Misunderstandings that can end in agreement or war, plus war and ceasefire.

Peace is never guaranteed: outcomes weigh relations, trust, reputation, evidence,
the hidden truth, remembered promises and a little uncertainty. Casualty figures
are fictional.
"""

import random

from nebula.core import stages
from nebula.core.intel import add_intel
from nebula.core.state import (RuleError, change_relation, change_reputation, change_trust, clamp,
                               foreign, gain, home, log, relation, spend)
from nebula.data.characters import AIR_CHIEFS, CIVILIANS, LEADERS
from nebula.data.countries import COUNTRIES

KINDS = {
    "aircraft": ("Radar lock over the frontier", "{foe} says your patrol locked weapons on its aircraft."),
    "intercept": ("A message read as a threat", "{foe} intercepted one of your signals and reads it as an attack order."),
    "border": ("Shots near a border post", "Gunfire near the frontier. {foe} says your side fired first."),
}
TRUTHS = {"accident": "It was an accident: a faulty system and a frightened crew.",
          "provocation": "Officers on their side staged it.",
          "third_party": "A third party forged the signals to set you against each other."}
# id: (label, cost, score bonus, hint)
CHOICES = {
    "investigate": ("Investigate", {"credits": 40, "fuel": 30}, 0, "Takes a day. Evidence helps, but can be wrong."),
    "negotiate": ("Negotiate", {}, 4, "Free. Works best with existing goodwill."),
    "envoy": ("Send an envoy", {"credits": 80}, 11, "A calm voice in the room. Success can create a promise."),
    "share": ("Share intelligence", {"research": 25}, 14, "Show your records."),
    "cooperate": ("Joint inquiry", {"credits": 60, "fuel": 40}, 19, "Needs a peace treaty or 35+ trust."),
    "military": ("Respond militarily", {"fuel": 60}, 0, "May end in a clash or full war."),
}
OUTCOMES = {"peace": "Resolved peacefully", "tension": "Diplomatic tension remains",
            "suspended": "Cooperation suspended", "confrontation": "Armed confrontation",
            "war": "War"}
WAR_BASE = 100


def _rng(state, *parts):
    return random.Random(f"{state['seed']}:{state['day']}:" + ":".join(map(str, parts)))


def _remember(state, text):
    state.setdefault("history", []).append({"day": state["day"], "text": text})


def open_incident(state) -> dict | None:
    return next((i for i in state.get("incidents", []) if i["status"] == "open"), None)


def active_promise(state, country) -> dict | None:
    return next((p for p in state.get("promises", []) if p["country"] == country
                 and not p["broken"] and p["until"] >= state["day"]), None)


def break_promise(state, country, how: str):
    promise = active_promise(state, country)
    if promise:
        promise["broken"] = True
        change_reputation(state, -6)
        change_trust(state, country, -12)
        _remember(state, f"Broke a promise to {COUNTRIES[country]['name']}: {how}")


def _reactions(state, country) -> list[dict]:
    value = relation(state, country)
    stance = "hostile" if value < -10 else "wary" if value < 25 else "friendly"
    theirs = {"hostile": "You expected us to believe this was nothing? We will not be slow to answer.",
              "wary": "Explain this, Commander. My government is not yet convinced either way.",
              "friendly": "I want this to be a mistake. Help me prove it before others decide."}[stance]
    military = {"hostile": "My crews are fuelled. I am waiting for the order.",
                "wary": "I have moved aircraft forward. That is caution, not intent.",
                "friendly": "I have told my pilots to hold. I cannot hold them forever."}[stance]
    past = [i for i in state.get("incidents", []) if i["country"] == country and i["status"] != "open"]
    if any(p["broken"] and p["country"] == country for p in state.get("promises", [])):
        theirs += " And we remember the promise you broke."
    elif past:
        theirs += f" We have not forgotten day {past[-1]['day']}."
    return [{"speaker": LEADERS[country], "text": theirs},
            {"speaker": AIR_CHIEFS[country], "text": military},
            {"speaker": AIR_CHIEFS[home(state)], "text": "Commander, whatever you choose, tell me before my pilots hear it elsewhere."},
            {"speaker": CIVILIANS[home(state)], "text": "People here are packing bags. Please do not guess."}]


def trigger(state, country: str, kind: str | None = None) -> dict | None:
    if open_incident(state) or country in state.get("wars", {}) or country == home(state):
        return None
    incidents = state.setdefault("incidents", [])
    rng = _rng(state, "incident", country, len(incidents))
    kind = kind or rng.choice(list(KINDS))
    title, text = KINDS[kind]
    incident = {"id": len(incidents) + 1, "kind": kind, "country": country, "day": state["day"],
                "deadline": state["day"] + 6, "status": "open", "title": title,
                "text": text.format(foe=COUNTRIES[country]["name"]),
                "truth": rng.choice(["accident", "accident", "provocation", "third_party"]),
                "evidence": None, "reactions": _reactions(state, country), "outcome": None}
    incidents.append(incident)
    _remember(state, f"Misunderstanding with {COUNTRIES[country]['name']}: {title}")
    return incident


def after_level(state, level: int, host: str):
    if level % 10 in (2, 6):
        others = foreign(state)
        trigger(state, host if host in others else _rng(state, "host", level).choice(others))


def blocked_reason(state, incident, choice) -> str | None:
    country = incident["country"]
    if choice == "investigate" and incident["evidence"]:
        return "Already investigated"
    if choice == "cooperate" and "peace" not in state["treaties"][country] and state["trust"][country] < 35:
        return "Needs a peace treaty or 35+ trust"
    return None


def respond(state, choice: str) -> str:
    incident = open_incident(state)
    if not incident or choice not in CHOICES:
        raise RuleError("There is no misunderstanding awaiting that response")
    reason = blocked_reason(state, incident, choice)
    if reason:
        raise RuleError(reason)
    country = incident["country"]
    spend(state, f"incident:{choice}", **CHOICES[choice][1])
    log(state, "player_decision", choice=choice, context="incident")
    if choice == "investigate":
        rng = _rng(state, "evidence", incident["id"])
        correct = rng.random() < 0.8
        finding = incident["truth"] if correct else rng.choice([t for t in TRUTHS if t != incident["truth"]])
        incident["evidence"] = {"finding": TRUTHS[finding], "kind": finding, "confidence": "probable, not certain"}
        return "Investigators reported. Weigh the evidence before you act."
    return _resolve(state, incident, choice)


def score(state, incident, choice) -> float:
    country = incident["country"]
    broken = sum(p["broken"] for p in state.get("promises", []) if p["country"] == country)
    evidence = incident["evidence"]
    bonus = CHOICES[choice][2] if choice in CHOICES else -10
    if evidence:
        bonus += 12 if evidence["kind"] == incident["truth"] else -4
    return (relation(state, country) * 0.35 + (state["trust"][country] - 45) * 0.5
            + (state["reputation"] - 50) * 0.3 + bonus - 12 * broken
            + {"accident": 3, "third_party": 4, "provocation": -12}[incident["truth"]])


def _resolve(state, incident, choice) -> str:
    country, name = incident["country"], COUNTRIES[incident["country"]]["name"]
    rng = _rng(state, "resolve", incident["id"], choice)
    if choice == "military":
        break_promise(state, country, "you answered with force")
        ratings = stages.air_ratings(state)
        proven = incident["truth"] == "provocation" and incident["evidence"] \
            and incident["evidence"]["kind"] == "provocation"
        strong = ratings[home(state)] >= ratings[country] * 0.5
        outcome = "confrontation" if proven and strong else \
            "war" if relation(state, country) < 25 else "confrontation"
    else:
        total = score(state, incident, choice) + rng.randint(-12, 12)
        outcome = ("peace" if total >= 6 else "tension" if total >= -8 else
                   "suspended" if total >= -20 else "confrontation" if total >= -30 else "war")
    effects = []
    if outcome == "peace":
        change_relation(state, country, 10, reason="incident_peace")
        change_trust(state, country, 10)
        change_reputation(state, 3)
        stages.strain(state, country, -15, "a misunderstanding was resolved")
        state["conflicts_avoided"] += 1
        effects.append("relations +10, trust +10, reputation +3")
        if choice in ("share", "cooperate"):
            add_intel(state, country, "aircraft", 0.35, "joint_inquiry")
            effects.append("they opened aircraft records")
        if choice in ("envoy", "cooperate"):
            state.setdefault("promises", []).append(
                {"country": country, "text": "No armed response or pressure along the shared frontier",
                 "until": state["day"] + 20, "broken": False})
            effects.append("you gave a 20-day restraint promise")
    elif outcome == "tension":
        change_relation(state, country, -6, reason="incident_tension")
        change_trust(state, country, -5)
        effects.append("relations -6, trust -5")
    elif outcome == "suspended":
        change_relation(state, country, -12, reason="incident_suspended")
        change_trust(state, country, -10)
        lost = [t for t in state["treaties"][country] if t != "peace"]
        state["treaties"][country] = [t for t in state["treaties"][country] if t == "peace"]
        stages.strain(state, country, 35, "cooperation suspended after an incident")
        effects.append("relations -12, trust -10, agreements suspended: " + (", ".join(lost) or "none held"))
    elif outcome == "confrontation":
        change_relation(state, country, -18, reason="confrontation")
        change_trust(state, country, -12)
        change_reputation(state, -3)
        stages.strain(state, country, 45, "an armed confrontation")
        dead = rng.randint(2, 9)
        losses = _lose(state, 0.1, 15, "confrontation")
        effects += [f"{dead} military dead", losses, "relations -18, trust -12"]
    else:
        effects += start_war(state, country, rng)
    incident.update(status="resolved", choice=choice, outcome=outcome, resolved_day=state["day"],
                    summary=f"{OUTCOMES[outcome]}: " + "; ".join(effects))
    _remember(state, f"{name} incident, answered by '{choice}': {OUTCOMES[outcome]}")
    log(state, "incident", country=country, choice=choice, outcome=outcome)
    return incident["summary"]


def _lose(state, share: float, damage: int, reason: str) -> str:
    lost = {k: int(state["resources"][k] * share) for k in ("credits", "materials", "fuel")}
    gain(state, f"{reason}:losses", **{k: -v for k, v in lost.items()})
    for plane in state["fleet"]:
        plane["condition"] = max(10, plane["condition"] - damage)
    return "lost " + ", ".join(f"{v} {k}" for k, v in lost.items()) + f"; every aircraft -{damage} condition"


def start_war(state, country: str, rng) -> list[str]:
    military, civilian = rng.randint(30, 90), rng.randint(10, 60)
    losses = _lose(state, 0.2, 10, "war")
    change_relation(state, country, min(-35, -55 - relation(state, country)), reason="war")
    change_trust(state, country, -25)
    change_reputation(state, -6)
    state["treaties"][country] = []
    treaty = state.get("joint", {}).get(country)
    if treaty and treaty["status"] in ("active", "restricted"):
        treaty["status"] = "withdrawn"
        state["fleet"] = [p for p in state["fleet"] if p.get("owner") != country]
        treaty["aircraft"], treaty["stability"] = [], 0
    state.setdefault("wars", {})[country] = {"since": state["day"], "military": military,
                                             "civilian": civilian, "victories": 0, "defeats": 0}
    log(state, "war", country=country, status="started")
    return [f"war declared: {military} military and {civilian} civilian dead", losses,
            "all agreements broken; two war missions opened"]


def war_level(country: str) -> int:
    return WAR_BASE + 1 + list(COUNTRIES).index(country)


def war_mission(state, level: int) -> dict:
    country = next((c for c in state.get("wars", {}) if war_level(c) == level), None)
    if not country:
        raise RuleError("That war mission is not available")
    war, c = state["wars"][country], COUNTRIES[country]
    first = war["victories"] == 0
    seconds, count = 60, 7
    return {
        "level": level, "chapter": 0, "stage": 0, "chapter_title": "War", "country": country,
        "title": f"War with {c['name']}: " + ("Hold the Line" if first else "Break the Offensive"),
        "type": "defence" if first else "interception", "type_label": "War mission",
        "story": ("Their first wave is inbound. Hold." if first else "Stop the offensive and force them to talk."),
        "location": c["capital"], "combat": True, "choices": [], "antagonist": None, "opponent": country,
        "difficulty": round(1.5 + c["military"] / 30, 2),
        "params": {"n": count, "m": 3, "s": seconds},
        "objectives": [f"Defend the installation for {seconds} seconds" if first
                       else f"Shoot down {count} intruders before 3 slip past"],
        "completion": "Two victories force a ceasefire. Three defeats end the war on their terms.",
        "rewards": {"credits": 60, "materials": 30, "research": 10, "fuel": 40},
        "requirements": {"min_condition": 30, "fuel": 20, "min_range": 0, "recommended": ["fighter", "interceptor"]},
        "diplomatic_consequence": "War results change casualties, reputation and the ceasefire.",
        "intel_consequence": "None.",
    }


def end_war(state, country: str, how: str):
    war = state["wars"].pop(country)
    state.setdefault("war_record", []).append({"country": country, **war, "ended": state["day"], "how": how})
    _remember(state, f"War with {COUNTRIES[country]['name']} ended: {how}")
    log(state, "war", country=country, status=how)


def war_result(state, country: str, success: bool):
    war = state["wars"][country]
    rng = _rng(state, "battle", country, war["victories"], war["defeats"])
    war["military"] += rng.randint(5, 25) if success else rng.randint(20, 60)
    if success:
        war["victories"] += 1
        gain(state, "war:reward", credits=60, materials=30, fuel=40)
        if war["victories"] >= 2:
            change_reputation(state, 2)
            end_war(state, country, "ceasefire after your victories")
    else:
        war["defeats"] += 1
        war["civilian"] += rng.randint(5, 30)
        _lose(state, 0.1, 10, "war")
        if war["defeats"] >= 3:
            gain(state, "war:reparations", credits=-int(state["resources"]["credits"] * 0.3))
            change_reputation(state, -5)
            end_war(state, country, "ceasefire on their terms, with reparations")


def ceasefire(state, country: str) -> str:
    war = state.get("wars", {}).get(country)
    if not war:
        raise RuleError("There is no war with that nation")
    spend(state, "war:ceasefire_talks", credits=min(100, state["resources"]["credits"]))
    total = (state["trust"][country] * 0.4 + (state["reputation"] - 50) * 0.5 + war["victories"] * 18
             - war["defeats"] * 4 + (state["day"] - war["since"]) * 2 + _rng(state, "truce", country).randint(-10, 10))
    log(state, "player_decision", choice="ceasefire", context="war")
    if total < 22:
        war["military"] += 8
        return f"{COUNTRIES[country]['name']} rejected the ceasefire. Fighting continues."
    change_relation(state, country, 12, reason="ceasefire")
    change_trust(state, country, 8)
    end_war(state, country, "negotiated ceasefire")
    return f"Ceasefire agreed with {COUNTRIES[country]['name']}. Trust must be rebuilt."


def daily(state):
    for war in state.get("wars", {}).values():
        gain(state, "war:attrition", credits=-20, fuel=-15)
        if (state["day"] - war["since"]) % 3 == 0:
            war["military"] += 6
            war["civilian"] += 2
    incident = open_incident(state)
    if incident and state["day"] > incident["deadline"]:
        _resolve(state, incident, "silence")
    elif not incident and len(state.get("completed", {})) >= 3:
        rng = _rng(state, "spontaneous")
        hostile = [c for c in foreign(state) if relation(state, c) <= -30]
        if hostile and rng.random() < 0.03:
            trigger(state, rng.choice(hostile))


def view(state) -> dict:
    incidents = []
    for i in state.get("incidents", []):
        shown = {k: v for k, v in i.items() if k != "truth"}
        if i["evidence"]:
            shown["evidence"] = {k: v for k, v in i["evidence"].items() if k != "kind"}
        if i["status"] == "open":
            shown["choices"] = [{"id": k, "label": v[0], "cost": v[1], "hint": v[3],
                                 "blocked": blocked_reason(state, i, k)} for k, v in CHOICES.items()]
        incidents.append(shown)
    return {"incidents": incidents,
            "wars": [{"country": c, "level": war_level(c), **w} for c, w in state.get("wars", {}).items()],
            "war_record": state.get("war_record", []), "promises": state.get("promises", [])}
