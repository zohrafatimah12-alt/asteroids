"""Agreement status and history, shared by diplomacy, incidents and mission generation.

Trade, peace and alliance live in state["treaties"]; a joint defence agreement is
an active joint-command treaty with the mutual-defence term. All reads tolerate
saves made before the history log existed.
"""

from nebula.data.countries import COUNTRIES

LABELS = {"trade": "trade agreement", "peace": "peace treaty", "alliance": "military alliance",
          "joint_defence": "joint defence agreement", "intelligence": "intelligence agreement",
          "joint_command": "joint air-command treaty"}
PROTECTIVE = ("peace", "alliance", "joint_defence")
TRUCE_DAYS = 10


def current(state, country: str) -> dict:
    signed = state["treaties"].get(country, [])
    joint = state.get("joint", {}).get(country, {})
    return {"trade": "trade" in signed, "peace": "peace" in signed, "alliance": "alliance" in signed,
            "joint_defence": joint.get("status") == "active" and joint["terms"]["defence"] == "mutual"}


def protected(state, country: str) -> bool:
    """Bound to the player by peace, alliance or joint defence."""
    held = current(state, country)
    return any(held[k] for k in PROTECTIVE)


def stand_down(state, country: str) -> str | None:
    """Why this nation must not be cast as the enemy, from agreements then history."""
    if country in state.get("wars", {}):
        return None
    held = current(state, country)
    names = [LABELS[k] for k in PROTECTIVE if held[k]]
    if names:
        return "a " + " and a ".join(names)
    last = next((w for w in reversed(state.get("war_record", [])) if w["country"] == country), None)
    if last and "ceasefire" in last["how"] and state["day"] - last["ended"] <= TRUCE_DAYS:
        return "a recent ceasefire"
    return None


def record(state, country: str, agreement: str, status: str, reason: str):
    state.setdefault("agreement_log", []).append(
        {"day": state["day"], "country": country, "agreement": agreement, "status": status, "reason": reason})
    if status != "signed":
        state.setdefault("history", []).append(
            {"day": state["day"], "text": f"{COUNTRIES[country]['name']} {LABELS[agreement]} {status}: {reason}"})
