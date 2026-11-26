"""Commander identity: opening philosophy, conversations, rankings, advice."""

from nebula.core.intel import add_intel
from nebula.core.state import (HOME, RuleError, change_relation, change_reputation, change_trust,
                               gain, log, spend, stats)
from nebula.data.characters import CHARACTERS, public
from nebula.data.countries import COUNTRIES
from nebula.data.messages import MESSAGES

# Philosophies never touch military rank or the first opponent.
PHILOSOPHIES = {
    "diplomacy": {
        "name": "Diplomacy First", "text": "Prioritise negotiation, alliances and peaceful solutions.",
        "reputation": 8, "trust": 4, "resources": {},
        "reactions": {"lu_dip": "At last, a commander who writes before launching.",
                      "lu_air": "Talk all you like. Keep my aircraft fuelled while you do.",
                      "vk_head": "Words are cheap when your sky is empty."},
        "advice": "You chose diplomacy first. Look for a message or treaty before a launch."},
    "defence": {
        "name": "Strategic Defence", "text": "Protect Lumeris and strengthen its defensive capabilities.",
        "reputation": 3, "trust": 2, "resources": {"materials": 60},
        "reactions": {"lu_army": "Hold what is ours. I can work with that.",
                      "lu_dip": "Defence is a language neighbours understand. Let us add others.",
                      "vk_head": "A wall is still a wall. We shall see how high."},
        "advice": "You chose strategic defence. A patrol before contact suits that."},
    "preparedness": {
        "name": "Military Preparedness", "text": "Prioritise military readiness and strategic strength.",
        "reputation": -2, "trust": -2, "resources": {"fuel": 80, "materials": 30},
        "reactions": {"lu_air": "Good. Ready crews live longer.",
                      "lu_pres": "Readiness, yes. Remember who it is meant to protect.",
                      "vk_head": "Now you speak a language Varkora respects."},
        "advice": "You chose preparedness. Keep every airframe fuelled, armed and repaired."},
}


def choose_philosophy(state, key: str) -> str:
    if key not in PHILOSOPHIES:
        raise RuleError("Unknown command philosophy")
    if state.get("philosophy"):
        raise RuleError("Your command philosophy is already on record")
    p = PHILOSOPHIES[key]
    state["philosophy"] = key
    change_reputation(state, p["reputation"])
    for country in state["trust"]:
        change_trust(state, country, p["trust"])
    gain(state, "philosophy:opening", **p["resources"])
    remember(state, f"Declared a command philosophy: {p['name']}")
    log(state, "player_decision", choice=key, context="philosophy")
    return f"On record: {p['name']}."


def remember(state, text: str):
    state.setdefault("history", []).append({"day": state["day"], "text": text})


def inbox(state) -> list[dict]:
    answered = state.get("replies", {})
    out = []
    for m in MESSAGES:
        if "after" in m:
            source, wanted = m["after"]
            if source not in answered or (wanted and answered[source] != wanted):
                continue
        if "level" in m and str(m["level"]) not in state["completed"]:
            continue
        chosen = next((r for r in m["replies"] if r["id"] == answered.get(m["id"])), None)
        out.append({"id": m["id"], "network": m["network"], "priority": m["priority"],
                    "subject": m["subject"], "body": m["body"], "sender": public(m["from"]),
                    "day": state.get("received", {}).get(m["id"], 1),
                    "answer": chosen and {"text": chosen["text"], "response": chosen["response"]},
                    "replies": [] if chosen else [{k: r[k] for k in ("id", "text", "cost")}
                                                  for r in m["replies"]]})
    return out


def deliver(state) -> None:
    """Stamp the day each message first arrives."""
    received = state.setdefault("received", {})
    for m in inbox(state):
        received.setdefault(m["id"], state["day"])


def reply(state, message_id: str, reply_id: str) -> str:
    entry = next((m for m in inbox(state) if m["id"] == message_id), None)
    if not entry or entry["answer"]:
        raise RuleError("That message is not awaiting a reply")
    message = next(m for m in MESSAGES if m["id"] == message_id)
    choice = next((r for r in message["replies"] if r["id"] == reply_id), None)
    if not choice:
        raise RuleError("Unknown reply")
    if choice["cost"]:
        spend(state, "communication:reply", **choice["cost"])
    sender = CHARACTERS[message["from"]]
    effects = choice["effects"]
    if sender["country"] != HOME:
        change_relation(state, sender["country"], effects.get("relation", 0), reason="message")
        change_trust(state, sender["country"], effects.get("trust", 0))
    elif "relation" in effects:  # home advisers acting on the first opponent
        change_relation(state, "zorvania", effects["relation"], reason="message")
    change_reputation(state, effects.get("reputation", 0))
    gain(state, "communication:outcome",
         **{k: v for k, v in effects.items() if k in ("materials", "research", "credits", "fuel")})
    if "intel" in effects:
        add_intel(state, "zorvania", "aircraft", effects["intel"], "intercept")
    state.setdefault("replies", {})[message_id] = reply_id
    remember(state, f"To {sender['name']}: \"{choice['text']}\"")
    log(state, "player_decision", choice=reply_id, context=f"message:{message_id}")
    return f"{sender['name']}: {choice['response']}"


def national_ranking() -> list[str]:
    """Order computed from each nation's military score, strongest first."""
    return sorted(COUNTRIES, key=lambda c: -COUNTRIES[c]["military"])


def air_power(state) -> int:
    """Rating of the aircraft Lumeris actually owns, weighted by condition."""
    return round(sum(sum(stats(p)[k] for k in ("speed", "agility", "armour", "radar")) / 4
                     * p["condition"] / 100 for p in state["fleet"]))


def advice(state) -> list[str]:
    """Uses only what the player can already see."""
    tips = []
    if state.get("philosophy"):
        tips.append(PHILOSOPHIES[state["philosophy"]]["advice"])
    unread = [m for m in inbox(state) if not m["answer"]]
    if unread:
        tips.insert(0, f"{len(unread)} message(s) await your reply. {unread[0]['sender']['name']} wrote: {unread[0]['subject']}.")
    if any(p["fuel"] < 40 or p["condition"] < 60 or p["ammo"] < 60 for p in state["fleet"]):
        tips.insert(0, "An aircraft is low on fuel, ammunition or condition. Service it before deployment.")
    if state["resources"]["fuel"] < 100:
        tips.append("Fuel reserves are low. Reconnaissance and refuelling both draw on them.")
    if not state["completed"]:
        if not state["intel"]["zorvania"]:
            tips.append("You know little about Zorvania. Analyse its signals before you commit.")
        tips.append("Open the Level 1 briefing when ready. Diplomacy may prevent losses.")
    return tips or ["No urgent concerns. Check the campaign for your next mission."]
