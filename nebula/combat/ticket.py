"""The contract between the strategy layer and the Pygame combat engine."""

from nebula.core.state import add_aircraft, new_state, stats
from nebula.core.missions import definition


def build_ticket(state: dict, mission: dict, plane: dict) -> dict:
    return {
        "mission": {k: mission[k] for k in ("level", "title", "type", "type_label", "story", "location",
                                            "objectives", "difficulty", "params", "country")},
        "plane": {**stats(plane), "condition": plane["condition"], "ammo_now": plane["ammo"],
                  "fuel_now": plane["fuel"]},
        "weather": state["weather"],
        "wingman": any("alliance" in t for t in state["treaties"].values()),
        "seed": state["seed"] + state["day"] * 101 + mission["level"],
    }


def practice_ticket(level: int, aircraft: str = "lm_wren") -> dict:
    state = new_state("Practice", seed=level)
    return build_ticket(state, definition(level), add_aircraft(state, aircraft))
