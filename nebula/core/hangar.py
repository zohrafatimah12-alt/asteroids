"""Air force management: servicing, upgrades, manufacturing and research."""

from nebula.core.state import HOME, RuleError, add_aircraft, find_plane, log, spend, stats
from nebula.data.aircraft import AIRCRAFT, UPGRADES

# id: (name, description, cost, prerequisite)
RESEARCH = {
    "lens": ("Deep-Sky Lens", "Better intelligence gain; reveals more about the threat.",
             {"research": 60, "materials": 80}, None),
    "airframe": ("Dawnspire Airframe", "Unlocks Lumeris' LX-9 Dawnspire.",
                 {"research": 160, "materials": 200, "credits": 300}, None),
    "shield1": ("Shield Lattice I", "Planetary shield: field theory.",
                {"research": 140, "materials": 120}, "lens"),
    "shield2": ("Shield Lattice II", "Planetary shield: orbital emitters.",
                {"research": 220, "materials": 300, "credits": 400}, "shield1"),
    "shield3": ("Shield Lattice III", "Planetary shield: full lattice.",
                {"research": 320, "materials": 450, "credits": 600}, "shield2"),
    "ark1": ("Ark Programme I", "Evacuation: life support.",
             {"research": 100, "materials": 160}, "lens"),
    "ark2": ("Ark Programme II", "Evacuation: hull yards.",
             {"research": 150, "materials": 350, "credits": 300}, "ark1"),
    "ark3": ("Ark Programme III", "Evacuation: launch fleet.",
             {"research": 200, "materials": 500, "credits": 500, "fuel": 400}, "ark2"),
}
PARTNERS = ("aerovant", "drakoria")  # allies who make big projects cheaper


def research_cost(state, project: str) -> dict:
    discount = sum(0.15 for c in PARTNERS if "alliance" in state["treaties"][c])
    return {k: round(v * (1 - discount)) for k, v in RESEARCH[project][2].items()}


def do_research(state, project: str) -> str:
    if project not in RESEARCH:
        raise RuleError("Unknown research project")
    name, _, _, needs = RESEARCH[project]
    if project in state["research"]:
        raise RuleError("Already researched")
    if needs and needs not in state["research"]:
        raise RuleError(f"Requires {RESEARCH[needs][0]} first")
    spend(state, f"research:{project}", **research_cost(state, project))
    state["research"].append(project)
    log(state, "research_completed", project=project)
    return f"{name} complete."


def service_cost(plane: dict) -> dict:
    full = stats(plane)
    damage = 100 - plane["condition"]
    return {
        "refuel": {"fuel": (100 - plane["fuel"]) // 2},
        "rearm": {"materials": (full["ammo"] - plane["ammo"] + 9) // 10},
        "repair": {"credits": damage, "materials": damage // 3},
    }


def service(state, uid: int, action: str) -> str:
    plane = find_plane(state, uid)
    costs = service_cost(plane)
    actions = list(costs) if action == "all" else [action]
    if any(a not in costs for a in actions):
        raise RuleError("Unknown service action")
    total: dict[str, int] = {}
    for a in actions:
        for k, v in costs[a].items():
            total[k] = total.get(k, 0) + v
    spend(state, f"maintenance:{action}", **total)
    for a in actions:
        if a == "refuel":
            plane["fuel"] = 100
        elif a == "rearm":
            plane["ammo"] = stats(plane)["ammo"]
        else:
            plane["condition"] = 100
    return "Aircraft serviced."


def upgrade_cost(tier: int) -> dict:
    return {"credits": 90 * (tier + 1), "research": 15 * (tier + 1)}


def upgrade(state, uid: int, key: str) -> str:
    plane = find_plane(state, uid)
    if plane.get("owner"):
        raise RuleError("Partner-owned aircraft cannot be modified under the treaty")
    if key not in UPGRADES:
        raise RuleError("Unknown upgrade")
    label, _, _, max_tier = UPGRADES[key]
    tier = plane["upgrades"].get(key, 0)
    if tier >= max_tier:
        raise RuleError("Upgrade already at maximum")
    spend(state, f"upgrade:{key}", **upgrade_cost(tier))
    plane["upgrades"][key] = tier + 1
    log(state, "aircraft_upgraded", aircraft=plane["type"], upgrade=key, tier=tier + 1)
    return f"{label} upgraded to tier {tier + 1}."


def availability(state, kind: str) -> str | None:
    """None when buildable, otherwise the reason it is locked."""
    spec = AIRCRAFT[kind]
    country = spec["country"]
    if country == HOME:
        if kind == "lm_dawn" and "airframe" not in state["research"]:
            return "Research the Dawnspire Airframe"
        return None
    treaties = state["treaties"][country]
    if "alliance" in treaties:
        return None
    if "trade" in treaties and spec["category"] in ("support", "reconnaissance", "heavy"):
        return None
    return "Needs an alliance (trade covers support, heavy and reconnaissance types)"


def build_cost(kind: str) -> dict:
    base = AIRCRAFT[kind]["cost"]
    return {"credits": base, "materials": base // 3}


def manufacture(state, kind: str) -> str:
    if kind not in AIRCRAFT:
        raise RuleError("Unknown aircraft")
    reason = availability(state, kind)
    if reason:
        raise RuleError(reason)
    if sum(not p.get("owner") for p in state["fleet"]) + len(state["builds"]) >= 12:
        raise RuleError("Hangars are full (12 airframes)")
    spend(state, f"manufacture:{kind}", **build_cost(kind))
    state["builds"].append({"type": kind, "ready_day": state["day"] + 2})
    log(state, "aircraft_ordered", aircraft=kind)
    return f"{AIRCRAFT[kind]['name']} ordered: ready in 2 days."


def finish_builds(state) -> None:
    for build in [b for b in state["builds"] if b["ready_day"] <= state["day"]]:
        add_aircraft(state, build["type"])
        state["builds"].remove(build)
