import pytest

from nebula.core import agreements, conflict, diplomacy, missions, stages, world
from nebula.core.state import RuleError, new_state
from nebula.data.treaty import DEFAULT

ZV = "zorvania"


def campaign(trust=40, relation=0, treaties=(), seed=1):
    state = new_state("T", seed=seed)
    state["_records"] = []
    state["trust"][ZV] = trust
    state["relations"]["lumeris|zorvania"] = relation
    state["treaties"][ZV] = list(treaties)
    return state


def blocked(state, choice="military"):
    return conflict.blocked_reason(state, conflict.open_incident(state), choice)


def test_agreements_are_tracked_separately():
    state = campaign(treaties=["trade"])
    assert agreements.current(state, ZV) == {"trade": True, "peace": False, "alliance": False, "joint_defence": False}
    assert not agreements.protected(state, ZV)
    for defence, expected in (("mutual", True), ("none", False)):
        state["joint"] = {ZV: {"status": "active", "terms": {**DEFAULT, "defence": defence}}}
        assert agreements.current(state, ZV)["joint_defence"] is expected


def test_partners_are_never_random_enemies():
    for seed in range(40):
        state = campaign(relation=-60, treaties=["peace"], seed=seed)
        for country in state["treaties"]:
            state["relations"]["|".join(sorted(("lumeris", country)))] = -60
            state["treaties"][country] = ["alliance"]
        conflict.after_level(state, 2, "lumeris")  # no foreign host: random pick
        state["completed"] = {"1": "x", "2": "x", "3": "x"}
        world.advance_day(state, 20)
        assert not state.get("incidents")


def test_mission_generation_respects_agreements_and_history():
    hostile = campaign()
    assert missions.mission_for(hostile, 1)["antagonist"] == ZV
    for treaty in ("peace", "alliance"):
        state = campaign(treaties=[treaty])
        for level in (1, 10):
            mission = missions.mission_for(state, level)
            assert mission["antagonist"] is None and mission["opponent"] is None
            assert "not your enemy" in mission["story"] and mission["combat"]
            assert missions.peaceful_option(state, mission)["available"]
    truce = campaign()
    truce["war_record"] = [{"country": ZV, "how": "negotiated ceasefire", "ended": 1}]
    assert missions.mission_for(truce, 1)["antagonist"] is None
    truce["day"] = 30
    assert missions.mission_for(truce, 1)["antagonist"] == ZV


def test_ally_requires_investigation_and_negotiation_before_force():
    stalled = 0
    for seed in range(60):
        state = campaign(trust=5, relation=-70, treaties=["peace", "trade"], seed=seed)
        conflict.trigger(state, ZV)
        assert blocked(state)
        conflict.respond(state, "negotiate")
        assert ZV not in state.get("wars", {})
        if not conflict.open_incident(state):
            continue
        stalled += 1
        assert blocked(state)  # talks failed, but not yet investigated
        conflict.respond(state, "investigate")
        assert not blocked(state)
        conflict.respond(state, "military")
    assert stalled


def test_silence_and_one_failed_talk_cannot_start_war():
    for seed in range(60):
        for treaties in ([], ["alliance"]):
            state = campaign(trust=0, relation=-90, treaties=treaties, seed=seed)
            conflict.trigger(state, ZV)
            world.advance_day(state, 10)
            assert not state.get("wars")


def test_war_records_its_cause_and_broken_agreements():
    state = campaign(relation=-20, treaties=["trade"])
    conflict.trigger(state, ZV)
    conflict.respond(state, "military")
    assert state["wars"][ZV]["cause"].startswith("explicit player decision")
    entry = next(e for e in state["agreement_log"] if e["agreement"] == "trade")
    assert entry["status"] == "broken" and "explicit player decision" in entry["reason"]


def test_second_failed_talk_can_escalate_with_a_reason():
    causes = set()
    for seed in range(80):
        state = campaign(trust=0, relation=-90, seed=seed)
        conflict.trigger(state, ZV)
        for _ in range(2):
            if conflict.open_incident(state):
                conflict.respond(state, "negotiate")
        causes |= {w["cause"].split(":")[0] for w in state.get("wars", {}).values()}
    assert causes and causes <= {"failed negotiations", "confirmed betrayal", "treaty violation"}


def test_suspended_joint_treaty_records_reason_and_lowers_relation():
    state = campaign(trust=90, relation=70)
    state["completed"] = {str(n): "x" for n in range(1, 11)}
    stages.propose(state, 1, DEFAULT)
    state["joint"][ZV]["stability"] = 40
    before = state["relations"]["lumeris|zorvania"]
    diplomacy.stages.strain(state, ZV, 30, "outside agreed rules")
    assert state["relations"]["lumeris|zorvania"] == before - 6
    log = [(e["agreement"], e["status"], e["reason"]) for e in state["agreement_log"]]
    assert ("joint_defence", "suspended", "outside agreed rules") in log
    stages.strain(state, ZV, 100, "betrayal")
    assert state["relations"]["lumeris|zorvania"] == before - 18
    assert state["agreement_log"][-1]["status"] == "broken"


def test_old_save_without_new_fields_still_works():
    state = campaign()
    conflict.trigger(state, ZV)
    for key in ("allied", "failed_talks"):
        del state["incidents"][0][key]
    conflict.respond(state, "negotiate")
    assert not agreements.protected(state, ZV)


def test_campaign_list_shows_partners_and_keeps_finished_titles():
    state = campaign()
    assert missions.campaign_for(state)[0]["opponent"] == ZV
    state["treaties"][ZV] = ["peace"]
    levels = missions.campaign_for(state)
    assert all(m["opponent"] is None and m["ally"] == ZV for m in levels[:10])
    assert levels[0]["title"].startswith("Unmarked Raiders") and levels[10]["opponent"] == "thalmora"
    state["completed"]["1"] = "flown"
    assert missions.campaign_for(state)[0]["title"] == "First Watch"


@pytest.mark.parametrize("nation, foe", [("kryvos", "lumeris"), ("lumeris", "zorvania")])
def test_no_treaty_with_the_current_opponent_until_its_stage_is_done(nation, foe):
    state = new_state("T", seed=1, nation=nation)
    key = "|".join(sorted((nation, foe)))
    state["trust"][foe], state["relations"][key] = 100, 90
    assert stages.current_rival(state) == foe
    for kind in diplomacy.TREATIES:
        with pytest.raises(RuleError, match="current opponent"):
            diplomacy.propose(state, foe, kind)
    assert state["treaties"][foe] == []
    mission = missions.mission_for(state, 1)
    assert "peace treaty" not in missions.peaceful_option(state, mission)["requirement"]
    state["completed"] = {str(n): "x" for n in range(1, 11)}
    assert stages.current_rival(state) != foe
    assert diplomacy.propose(state, foe, "peace")[0]


def test_allies_can_never_fight_whatever_happens():
    for seed in range(60):
        state = campaign(trust=0, relation=-90, treaties=["peace", "alliance", "trade"], seed=seed)
        conflict.trigger(state, ZV)
        for choice in ("negotiate", "investigate", "negotiate"):
            if conflict.open_incident(state):
                assert blocked(state)
                conflict.respond(state, choice)
        world.advance_day(state, 12)
        assert not state.get("wars")
        assert "alliance" in state["treaties"][ZV]
        assert all(i["outcome"] != "confrontation" for i in state["incidents"])


def test_joint_defence_partner_is_an_ally_even_when_restricted():
    state = campaign()
    state["joint"] = {ZV: {"status": "restricted", "terms": {**DEFAULT, "defence": "mutual"}}}
    conflict.trigger(state, ZV)
    assert "ally" in blocked(state)
    with pytest.raises(RuleError):
        conflict.start_war(state, ZV, None, "test")


def test_formally_ending_the_alliance_has_costs_and_lifts_the_block():
    state = campaign(trust=90, relation=70)
    state["completed"] = {str(n): "x" for n in range(1, 11)}
    diplomacy.propose(state, ZV, "peace")
    state["treaties"][ZV].append("alliance")
    stages.propose(state, 1, DEFAULT)
    assert agreements.is_ally(state, ZV) and any(p.get("owner") == ZV for p in state["fleet"])
    rank, trust = stages.joint_rank(state), state["trust"][ZV]
    diplomacy.end_alliance(state, ZV)
    assert not agreements.is_ally(state, ZV) and state["trust"][ZV] == trust - 15
    assert not any(p.get("owner") == ZV for p in state["fleet"]) and stages.joint_rank(state) == rank
    assert "peace" in state["treaties"][ZV]
    assert any(e["reason"] == "formally ended by you" for e in state["agreement_log"])
    with pytest.raises(RuleError):
        diplomacy.end_alliance(state, ZV)
    conflict.trigger(state, ZV)
    assert "formally end" not in (blocked(state) or "")
