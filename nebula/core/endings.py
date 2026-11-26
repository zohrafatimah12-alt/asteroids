"""The three endings, decided by what the player actually did."""

from nebula.core.state import FOREIGN, RuleError, log, relation

ENDINGS = {
    "union": ("The Great Union", [
        "Ten air forces climb into one sky for the first time in Veyra's history.",
        "Drakorian steel, Aerovant wings, Frostaran ice and Lumeris light join into a single lattice.",
        "The Shard-Star strikes the shield. For nine hours, nobody on Veyra speaks.",
        "Then the sky clears, and Nebula rises over a world that chose each other.",
        "In Elowen, every public telescope is turned toward morning.",
    ]),
    "evacuation": ("The Last Evacuation", [
        "There are not enough ships. There were never going to be enough time or trust.",
        "The arks lift from the launch rails while volunteers stay to hold the corridor.",
        "Children press their faces to the ports and watch the mountains grow small.",
        "Veyra burns behind them. Nebula still lights their way.",
        "They carry ten flags, sewn together, into the dark.",
    ]),
    "last_star": ("The Last Star", [
        "The council ends without a signature.",
        "Each nation looks up alone.",
        "In Elowen, an astronomer records the sky one final time, carefully, for no one.",
        "The Shard-Star arrives on the day Lumeris predicted.",
        "Long after, Nebula keeps shining on the silence.",
    ]),
}


def cooperating(state) -> list[str]:
    return [c for c in FOREIGN if "alliance" in state["treaties"][c]
            or (relation(state, c) >= 40 and state["trust"][c] >= 60)]


def requirements(state) -> dict:
    partners = len(cooperating(state))
    settled = sum(v != "open" for v in state["disputes"].values())
    victories = len(state["completed"])
    supplies = state["resources"]["materials"] + state["resources"]["fuel"]
    sacrifices = state.get("sacrifices", 0)
    # Remembered sacrifices persuade hesitant nations: each lowers the partner bar (max 2).
    needed = 7 - min(2, sacrifices // 2)
    return {
        "union": [
            (f"Cooperating nations: {partners}/{needed}", partners >= needed),
            ("Shield Lattice III complete", "shield3" in state["research"]),
            (f"Reputation {state['reputation']}/65", state["reputation"] >= 65),
            (f"Territorial disputes settled: {settled}/2", settled >= 2),
            (f"Levels completed: {victories}/100", victories >= 100),
        ],
        "evacuation": [
            ("Ark Programme III complete", "ark3" in state["research"]),
            (f"Materials + fuel in reserve: {supplies}/600", supplies >= 600),
            (f"Levels completed: {victories}/100", victories >= 100),
        ],
    }


def conclude(state, plan: str) -> str:
    if state["ending"]:
        raise RuleError("This campaign has already ended")
    if "100" not in state["completed"]:
        raise RuleError("The final level has not been completed")
    checks = requirements(state)
    if plan not in checks:
        raise RuleError("Choose the shield or the evacuation")
    if all(ok for _, ok in checks[plan]):
        ending = plan
    elif all(ok for _, ok in checks["evacuation"]):
        ending = "evacuation"
    else:
        ending = "last_star"
    state["ending"] = ending
    log(state, "campaign_ending", plan=plan, ending=ending, partners=len(cooperating(state)),
        sacrifices=state.get("sacrifices", 0))
    return ending
