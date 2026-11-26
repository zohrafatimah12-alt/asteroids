import pytest

from nebula.core import diplomacy, endings, hangar, intel, missions, world
from nebula.core.state import FOREIGN, RuleError, new_state


def strategist(state):
    """Plays all 100 levels through the public rules, investing in diplomacy."""
    def attempt(fn, *args):
        try:
            return fn(state, *args)
        except RuleError:
            return None

    for level in range(1, 101):
        for _ in range(60):
            if str(level) in state["completed"]:
                break
            mission = missions.definition(level)
            if mission["combat"]:
                if (missions.peaceful_option(state, mission) or {}).get("available"):
                    missions.resolve_peacefully(state, level)
                    continue
                for plane in sorted(state["fleet"], key=lambda p: -missions.success_chance(state, mission, p)):
                    attempt(hangar.service, plane["uid"], "all")
                    for _ in range(3):
                        if plane["upgrades"].get("tanks", 0) < 3 and \
                                missions.stats(plane)["range"] < mission["requirements"]["min_range"]:
                            attempt(hangar.upgrade, plane["uid"], "tanks")
                    if attempt(missions.delegate, level, plane["uid"]):
                        break
                else:
                    world.advance_day(state)
            else:
                for choice in ("sacrifice", "honest", "incentive", "invest", "joint", "analyse", "home", "frugal"):
                    result = attempt(missions.decide, level, choice)
                    if result and result[0]:
                        break
                else:
                    world.advance_day(state, 2)
        assert str(level) in state["completed"], f"stuck at level {level}: {state['resources']}"
        for project in hangar.RESEARCH:
            if project.startswith(("lens", "shield", "airframe")):
                attempt(hangar.do_research, project)
        if "airframe" in state["research"] and not any(p["type"] == "lm_dawn" for p in state["fleet"]) \
                and not state["builds"]:
            attempt(hangar.manufacture, "lm_dawn")
        if level % 2 == 0:
            target = min((c for c in FOREIGN if "alliance" not in state["treaties"][c]),
                         key=lambda c: -diplomacy.score(state, c), default=None)
            if target:
                for kind in ("peace", "trade", "intelligence", "alliance"):
                    if kind not in state["treaties"][target]:
                        if diplomacy.outlook(state, target, kind) == "unlikely":
                            attempt(diplomacy.send_aid, target)
                        else:
                            attempt(diplomacy.propose, target, kind)
                        break
        for dispute, status in list(state["disputes"].items()):
            if status == "open" and level % 9 == 0:
                attempt(diplomacy.negotiate_dispute, dispute, "arbitrate")
    return state


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_full_campaign_is_completable_and_union_reachable(seed):
    state = strategist(new_state("Bot", seed=seed))
    assert len(state["completed"]) == 100
    unmet = [text for text, ok in endings.requirements(state)["union"] if not ok]
    assert endings.conclude(state, "union") == "union", unmet


def finished(**changes):
    state = new_state("T", seed=1)
    state["completed"] = {str(n): "flown" for n in range(1, 101)}
    state.update(changes)
    return state


def test_endings_depend_on_play():
    assert endings.conclude(finished(), "union") == "last_star"
    assert endings.conclude(finished(research=["lens", "ark1", "ark2", "ark3"]), "union") == "evacuation"


def test_ending_needs_final_level():
    with pytest.raises(RuleError):
        endings.conclude(new_state("T"), "union")


def test_intel_is_redacted_until_learned():
    state = new_state("T", seed=1)
    assert intel.report(state, "varkhen")["strength"]["value"] is None
    intel.add_intel(state, "varkhen", "strength", 0.4, "test")
    assert "–" in intel.report(state, "varkhen")["strength"]["value"]
    intel.add_intel(state, "varkhen", "strength", 0.6, "test")
    assert intel.report(state, "varkhen")["strength"]["value"] == "94"


def test_rules_reject_invalid_actions():
    state = new_state("T", seed=1)
    with pytest.raises(RuleError):
        diplomacy.propose(state, "aerovant", "alliance")  # needs peace first
    with pytest.raises(RuleError):
        hangar.manufacture(state, "vk_fang")  # no alliance
    with pytest.raises(RuleError):
        missions.decide(state, 4, "honest")  # locked level
    state["resources"]["credits"] = 0
    with pytest.raises(RuleError):
        diplomacy.send_aid(state, "aerovant")
    assert state["resources"]["materials"] == 240  # failed spend changes nothing


def test_events_change_state_and_are_recorded():
    state = new_state("T", seed=3)
    state["_records"] = []
    world.advance_day(state, 20)
    assert state["events"]
    assert any(table == "world_events" for table, _ in state["_records"])
