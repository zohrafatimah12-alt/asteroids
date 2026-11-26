"""Campaign rules: level definitions, requirements, resolution and consequences."""

import random

from nebula.core import stages
from nebula.core.intel import add_intel
from nebula.core.state import (FOREIGN, HOME, RuleError, change_relation, change_reputation,
                               change_trust, find_plane, gain, log, record, relation, spend, stats)
from nebula.core.world import advance_day
from nebula.data.campaign import levels
from nebula.data.countries import COUNTRIES

# type: (label, objective template, recommended airframe categories)
TYPES = {
    "interception": ("Interception", "Shoot down {n} intruders before {m} slip past", ["interceptor", "fighter"]),
    "escort": ("Escort", "Keep the transport alive until it crosses the sector", ["fighter", "support"]),
    "reconnaissance": ("Reconnaissance", "Scan {n} survey sites", ["reconnaissance"]),
    "defence": ("Defence", "Defend the installation for {s} seconds", ["fighter", "interceptor"]),
    "rescue": ("Rescue", "Reach the beacon, hold for pickup, then return to base point", ["support", "fighter"]),
    "strike": ("Strategic attack", "Destroy {n} ground emplacements", ["bomber", "heavy"]),
    "airbase": ("Airbase protection", "Protect the airbase for {s} seconds", ["interceptor", "heavy"]),
    "investigation": ("Investigation", "Scan {n} anomalies and survive any ambush", ["reconnaissance", "fighter"]),
    "emergency": ("Emergency response", "Destroy {n} falling fragments before the ground is lost", ["fighter", "heavy"]),
    "battle": ("Major battle", "Defeat {n} hostiles including their ace", ["fighter", "heavy", "bomber"]),
    "diplomacy": ("Diplomacy", "Choose how to negotiate", []),
    "intelligence": ("Intelligence", "Choose how to obtain the truth", []),
    "economy": ("Economic decision", "Decide how resources are committed", []),
    "research": ("Research", "Decide how the science is pursued", []),
}
STRATEGIC_TYPES = ("diplomacy", "intelligence", "economy", "research")

# In stages 1-9 these combat types are fought against the stage's ranked opponent,
# so enough goodwill with that nation can end them without a shot. Level 1 does too.
OPPOSED_TYPES = ("interception", "strike", "battle")
THREAT_STAGES = {5: 10, 9: 18, 20: 24, 29: 28, 47: 38, 55: 50, 57: 58, 71: 68, 74: 78,
                 77: 84, 78: 86, 95: 94, 100: 100}


def _choice(key, label, text, cost=None, **effects):
    return {"id": key, "label": label, "text": text, "cost": cost or {}, "effects": effects}


# Effects: trust, relation, reputation, intel, research, credits, materials, needs (min score)
CHOICES = {
    "diplomacy": [
        _choice("honest", "Speak openly", "Share what Lumeris knows. Works when they already trust you a little.",
                needs=36, trust=9, relation=8, reputation=3),
        _choice("incentive", "Offer a partnership package", "Pay for joint projects. Reliable but expensive.",
                {"credits": 120, "materials": 30}, trust=6, relation=7, reputation=1),
        _choice("firm", "Bargain hard", "Gain material terms at the cost of goodwill.",
                needs=18, trust=-6, relation=-4, materials=90, credits=90),
    ],
    "intelligence": [
        _choice("trade", "Trade information", "Give up some research notes for theirs.",
                {"research": 20}, intel=0.6, trust=5, relation=3),
        _choice("analyse", "Patient analysis", "Slow, lawful and cheap.",
                {"credits": 50}, intel=0.35, reputation=2),
        _choice("covert", "Covert acquisition", "Best intelligence. They may never forgive it.",
                {"credits": 90}, intel=0.9, trust=-12, relation=-8, reputation=-3),
    ],
    "economy": [
        _choice("invest", "Invest in shared infrastructure", "Costs now, builds lasting trust.",
                {"credits": 150, "materials": 40}, trust=10, relation=8, reputation=4, research=30),
        _choice("sacrifice", "Sacrifice Lumeris' own reserves", "A deep sacrifice every nation will remember.",
                {"credits": 220, "fuel": 120}, trust=14, relation=10, reputation=8, sacrifice=1),
        _choice("frugal", "Protect the treasury", "Keep your reserves. Partners notice.",
                trust=-5, credits=100),
    ],
    "research": [
        _choice("joint", "Open joint research", "Publish everything and work together.",
                {"credits": 80}, trust=8, relation=6, reputation=3, research=50),
        _choice("home", "Keep it in Lumeris", "Larger gain for you, less goodwill.",
                {"materials": 40}, trust=-4, research=80),
        _choice("data", "Prioritise observation data", "Learn about their capabilities while you work.",
                {"credits": 60}, intel=0.35, research=35),
    ],
}


def definition(level: int) -> dict:
    if not 1 <= level <= 100:
        raise RuleError("There is no such level")
    m = levels()[level - 1]
    kind, country = m["type"], m["country"]
    c = COUNTRIES[country]
    difficulty = round(1 + (level - 1) * 7 / 99 + (0.4 if kind == "battle" else 0), 2)
    params = {"n": 3, "m": 4, "s": 45 + level // 4}
    if kind == "interception":
        params["n"] = 5 + level // 12
        params["m"] = max(2, params["n"] // 3 + 1)
    elif kind == "battle":
        params["n"] = 8 + level // 10
    elif kind == "emergency":
        params["n"] = 10 + level // 8
    elif kind in ("reconnaissance", "investigation", "strike"):
        params["n"] = 3 + level // 40
    label, objective, categories = TYPES[kind]
    stage = m["chapter"]
    opponent = country if stage <= 9 else None
    antagonist = opponent if level == 1 or kind in OPPOSED_TYPES else None
    # Stage 1 is fought over Lumeris' own south-eastern corridor.
    place = COUNTRIES[HOME] if stage == 1 else c
    locations = [place["capital"], *place["cities"][1:]]
    combat = kind not in STRATEGIC_TYPES
    reward = {"credits": 90 + 3 * level, "materials": 40 + level, "research": 12 + level // 2,
              "fuel": 50 + level // 2}
    host = c["name"]
    return {
        **m, "type_label": label, "combat": combat, "difficulty": difficulty, "params": params,
        "location": locations[(level - 1) % len(locations)],
        "objectives": [objective.format(**params)],
        "completion": "Meet the objective with your aircraft intact" if combat
                      else "Choose an approach that succeeds",
        "rewards": reward, "stage": stage, "opponent": opponent, "antagonist": antagonist,
        "requirements": ({"min_condition": 35, "fuel": 25, "min_range": 30 + level // 5,
                          "recommended": categories} if combat else {}),
        "diplomatic_consequence": ("Success raises trust at home and morale across Veyra."
                                   if country == HOME else
                                   f"Success raises {host}'s trust; failure lowers it."),
        "intel_consequence": ("Reveals observations about the falling object."
                              if level in THREAT_STAGES else
                              "No strategic intelligence expected." if country == HOME else
                              f"Success adds intelligence on {host}."),
        "choices": [] if combat else CHOICES[kind],
    }


def peaceful_option(state, mission) -> dict | None:
    foe = mission["antagonist"]
    if not foe:
        return None
    available = "peace" in state["treaties"][foe] or (relation(state, foe) >= 15 and state["trust"][foe] >= 45)
    return {"country": foe, "available": available,
            "requirement": f"A peace treaty with {COUNTRIES[foe]['name']}, or relations 15+ and trust 45+"}


def check_level(state, level: int):
    if state["ending"]:
        raise RuleError("This campaign has ended")
    stages.check_unlocked(state, level)
    if level > state["unlocked"]:
        raise RuleError("Complete the previous level first")


def check_aircraft(state, mission, uid: int) -> dict:
    plane = find_plane(state, uid)
    need = mission["requirements"]
    if stages.grounded(state, plane):
        raise RuleError("Its nation has restricted this aircraft. Repair the treaty first.")
    if plane["condition"] < need["min_condition"]:
        raise RuleError("Aircraft needs repair before it can fly this mission")
    if plane["fuel"] < need["fuel"]:
        raise RuleError("Aircraft needs refuelling")
    if plane["ammo"] <= 0:
        raise RuleError("Aircraft needs rearming")
    if stats(plane)["range"] < need["min_range"] - stages.range_relief(state):
        raise RuleError(f"Range too short: needs {need['min_range']}. Upgrade tanks or use another aircraft.")
    return plane


def _complete(state, mission, success: bool, mode: str, scale: float = 1.0):
    level, country = mission["level"], mission["country"]
    first = str(level) not in state["completed"]
    if success:
        share = scale if first else 0.25  # replays pay a little, to prevent soft locks
        gain(state, "mission:reward", **{k: v * share for k, v in mission["rewards"].items()})
        if first:
            state["completed"][str(level)] = mode
            state["unlocked"] = min(100, max(state["unlocked"], level + 1))
            if country == HOME or (mission["antagonist"] == country and mode != "peaceful"):
                # Beating a rival's aircraft earns standing at home, not their affection.
                change_reputation(state, 1)
            else:
                change_trust(state, country, 3)
                change_relation(state, country, 2, reason="mission")
            if country != HOME:
                subject = ("strength", "weaknesses", "aircraft", "bases")[level % 4]
                add_intel(state, country, subject, 0.3, "mission")
            if level in THREAT_STAGES:
                state["threat"] = max(state["threat"], THREAT_STAGES[level])
    elif country != HOME:
        change_trust(state, country, -2)
    log(state, "campaign_progress", level=level, success=success, mode=mode,
        completed=len(state["completed"]))


def _attempt(state, mission, mode, success, aircraft=None, **perf):
    record(state, "mission_attempts", level=mission["level"], mission_type=mission["type"],
           country=mission["country"], mode=mode, success=int(success), aircraft=aircraft,
           kills=perf.get("kills", 0), shots=perf.get("shots", 0), hits=perf.get("hits", 0),
           damage_taken=perf.get("damage_taken", 0), duration=perf.get("duration", 0.0))


def apply_combat(state, level: int, uid: int, result: dict, mode: str = "flown") -> str:
    """Apply a sortie outcome to aircraft, resources and the campaign."""
    mission = definition(level)
    check_level(state, level)
    plane = find_plane(state, uid)
    success = bool(result["success"])
    damage = max(0, min(100, int(result.get("damage_taken", 0))))
    # Ground crews always recover the airframe, so a defeat cannot soft lock the game.
    plane["condition"] = max(10, plane["condition"] - damage)
    plane["fuel"] = max(0, plane["fuel"] - max(10, min(60, int(result.get("fuel_used", 25)))))
    plane["ammo"] = max(0, plane["ammo"] - max(0, int(result.get("ammo_used", 0))))
    plane["sorties"] += 1
    plane["kills"] += int(result.get("kills", 0))
    _attempt(state, mission, mode, success, plane["type"],
             **{k: v for k, v in result.items() if k != "success"})
    _complete(state, mission, success, mode)
    stages.after_sortie(state, plane, mission, success)
    state.pop("tactics", None)  # preparations last for one sortie
    advance_day(state)
    return "Mission accomplished." if success else "Mission failed. Repair, rearm and try again."


# id: (label, cost, plain-language benefit, risk)
TACTICS = {
    "patrol": ("Defensive patrol", {"fuel": 40},
               "Picket aircraft widen your radar by a quarter on the next sortie.",
               "Spends fuel even if you never launch."),
    "support": ("Request allied support", {"credits": 60},
                "An Aerovant wingman joins your next sortie. Needs Aerovant trust 52+.",
                "Costs credits and a little Aerovant goodwill. The wingman can be shot down."),
}


def prepare(state, key: str) -> str:
    if key not in TACTICS:
        raise RuleError("Unknown preparation")
    if key in state.get("tactics", []):
        raise RuleError("Already arranged for the next sortie")
    if key == "support" and state["trust"]["aerovant"] < 52:
        raise RuleError("Aerovant does not trust you enough yet")
    label, cost, _, _ = TACTICS[key]
    spend(state, f"tactics:{key}", **cost)
    if key == "support":
        change_relation(state, "aerovant", -2, reason="support_request")
    state.setdefault("tactics", []).append(key)
    log(state, "player_decision", choice=key, context="tactics")
    return f"{label} arranged for the next flown sortie."


def debrief(before: dict, after: dict, level: int, result: dict | None = None) -> dict:
    """What changed, computed by comparing real state before and after a mission."""
    mission = definition(level)
    attempt = next((row for table, row in reversed(after["_records"])
                    if table == "mission_attempts"), {})
    delta = lambda a, b: {k: b[k] - a[k] for k in a if b[k] != a[k]}
    intel_gained = [f"{COUNTRIES[c]['name']}: {s}" for c, known in after["intel"].items()
                    for s, v in known.items() if v > before["intel"][c].get(s, 0)]
    result = result or {}
    return {
        "level": level, "title": mission["title"], "success": bool(attempt.get("success")),
        "mode": attempt.get("mode"), "objectives": mission["objectives"],
        # None means not simulated for this mode, which the UI states rather than inventing.
        "enemy_lost": result.get("kills"), "wingman_lost": result.get("wingman_lost"),
        "ammo_used": result.get("ammo_used"), "fuel_used": result.get("fuel_used"),
        "damage": result.get("damage_taken"),
        "resources": delta(before["resources"], after["resources"]),
        "trust": delta(before["trust"], after["trust"]),
        "reputation": after["reputation"] - before["reputation"],
        "intel": intel_gained,
        "unlocked": after["unlocked"] if after["unlocked"] > before["unlocked"] else None,
    }


def success_chance(state, mission, plane) -> float:
    s = stats(plane)
    power = (s["speed"] + s["agility"] + s["armour"] + s["radar"]) / 4
    power += 6 * (s["category"] in mission["requirements"]["recommended"])
    allies = sum("alliance" in t for t in state["treaties"].values())
    chance = 0.62 + (power - 40 - 4.2 * mission["difficulty"]) / 70 + 0.025 * allies
    return round(max(0.15, min(0.95, chance * (0.5 + plane["condition"] / 200))), 2)


def delegate(state, level: int, uid: int) -> str:
    """Command a wing leader to fly the sortie: an odds-based, clearly-labelled simulation."""
    mission = definition(level)
    check_level(state, level)
    if not mission["combat"]:
        raise RuleError("This is a strategic mission")
    plane = check_aircraft(state, mission, uid)
    rng = random.Random(f"{state['seed']}:{state['day']}:{level}:{uid}")
    success = rng.random() < success_chance(state, mission, plane)
    result = {"success": success, "damage_taken": rng.randint(5, 30) + (0 if success else 25),
              "fuel_used": 25, "ammo_used": min(plane["ammo"], 70), "kills": 0}
    return "Command sortie: " + apply_combat(state, level, uid, result, mode="command")


def resolve_peacefully(state, level: int) -> str:
    mission = definition(level)
    check_level(state, level)
    option = peaceful_option(state, mission)
    if not option or not option["available"]:
        raise RuleError("No peaceful resolution is available for this mission")
    foe, first = option["country"], str(level) not in state["completed"]
    _attempt(state, mission, "peaceful", True)
    _complete(state, mission, True, "peaceful")
    if first:
        state["conflicts_avoided"] += 1
        change_reputation(state, 4)
        change_relation(state, foe, 7, reason="peaceful_resolution")
        change_trust(state, foe, 6)
        log(state, "conflict_avoided", source="mission", level=level)
    advance_day(state)
    return "Resolved without a shot. Veyra took notice."


def decide(state, level: int, choice_id: str) -> tuple[bool, str]:
    mission = definition(level)
    check_level(state, level)
    choice = next((c for c in mission["choices"] if c["id"] == choice_id), None)
    if not choice:
        raise RuleError("That is not an option here")
    if choice["cost"]:
        spend(state, f"decision:{mission['type']}", **choice["cost"])
    effects, country = choice["effects"], mission["country"]
    first = str(level) not in state["completed"]
    # At home the audience is the Council, whose confidence follows your reputation.
    standing = state["reputation"] if country == HOME else (
        state["trust"][country] + 0.4 * relation(state, country) + 0.3 * (state["reputation"] - 50))
    success = standing >= effects.get("needs", -999)
    _attempt(state, mission, "decision", success)
    record(state, "negotiations" if mission["type"] == "diplomacy" else "analytics_events",
           **({"country": country, "kind": f"mission:{choice_id}", "success": int(success), "offer": 0}
              if mission["type"] == "diplomacy" else
              {"event_type": "player_decision", "detail": {"level": level, "choice": choice_id}}))
    log(state, "decision_choice", type=mission["type"], choice=choice_id, success=success)
    if success and first:
        change_reputation(state, effects.get("reputation", 0))
        if country != HOME:
            change_trust(state, country, effects.get("trust", 0))
            change_relation(state, country, effects.get("relation", 0), reason="decision")
            if "intel" in effects:
                for subject in ("strength", "weaknesses", "aircraft"):
                    add_intel(state, country, subject, effects["intel"] * 0.6, "mission")
        gain(state, "decision:outcome", **{k: effects[k] for k in ("research", "credits", "materials") if k in effects})
        if effects.get("sacrifice"):
            state["sacrifices"] = state.get("sacrifices", 0) + 1
        if mission["type"] == "diplomacy":
            state["conflicts_avoided"] += 1
    elif not success:
        change_trust(state, country, -2)
    _complete(state, mission, success, "decision")
    advance_day(state)
    return success, (f"{choice['label']}: it worked." if success else
                     f"{choice['label']}: not enough trust yet. Try another approach.")
