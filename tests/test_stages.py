import pytest
from fastapi.testclient import TestClient

from nebula import api
from nebula.core import commander, db, diplomacy, hangar, missions, stages, world
from nebula.core.state import RuleError, new_state
from nebula.data.treaty import DEFAULT

client = TestClient(api.app)


def staged(trust=60, relation=30, done=10):
    state = new_state("T", seed=1)
    state["completed"] = {str(n): "flown" for n in range(1, done + 1)}
    state["unlocked"] = done
    state["trust"]["zorvania"] = trust
    state["relations"]["lumeris|zorvania"] = relation
    return state


def signed(**changes):
    state = staged(trust=90, relation=70)
    stages.propose(state, 1, {**DEFAULT, **changes})
    assert state["joint"]["zorvania"]["status"] == "active"
    return state


def partner(state):
    return next(p for p in state["fleet"] if p.get("owner"))


def test_stage_ladder_follows_computed_rankings():
    assert stages.STAGE_OPPONENTS == commander.national_ranking()[::-1][1:]
    for n in range(1, 91, 10):
        assert missions.definition(n)["opponent"] == stages.STAGE_OPPONENTS[n // 10]
    assert missions.definition(95)["opponent"] is None
    state = new_state("T")
    # Joint air ranking starts at 10 and its order of foreign nations matches national order.
    assert stages.joint_rank(state) == 10
    assert [r["country"] for r in stages.air_ranking(state)] == commander.national_ranking()


def test_treaty_needs_all_ten_missions_and_gates_stage_two():
    with pytest.raises(RuleError):
        stages.propose(staged(done=9), 1, DEFAULT)
    state = staged()
    state["unlocked"] = 11
    with pytest.raises(RuleError):
        missions.check_level(state, 11)
    stages.postpone(state, 1)
    missions.check_level(state, 11)
    assert stages.joint_rank(state) == 10  # no treaty, no arbitrary promotion


def test_accept_counter_and_reject_are_different():
    fair = staged()
    stages.propose(fair, 1, DEFAULT)
    assert fair["talks"]["zorvania"]["outcome"] == "accept"

    middle = staged(trust=40, relation=0)
    before = len(middle["fleet"])
    stages.propose(middle, 1, DEFAULT)
    talks = middle["talks"]["zorvania"]
    assert talks["outcome"] == "counter" and len(middle["fleet"]) == before
    assert stages.burden("zorvania", talks["counter"]) <= stages.willingness(middle, "zorvania")
    assert len({line["speaker"] for line in talks["lines"]}) == 2
    stages.accept_counter(middle, 1)
    assert middle["joint"]["zorvania"]["terms"] == talks["counter"]

    greedy = staged(trust=30, relation=-10)
    worst = {k: v for k, v in DEFAULT.items()}
    worst.update(aircraft="40", command="lumeris", rules="all", intelligence="full",
                 bases="wide", supplies="large", withdrawal="none", duration="open", defence="none")
    stages.propose(greedy, 1, worst)
    assert greedy["talks"]["zorvania"]["outcome"] == "reject" and greedy["trust"]["zorvania"] < 30


def test_only_agreed_share_is_transferred_and_nation_stays_sovereign():
    for share, expected in (("20", 1), ("40", 2)):
        state = signed(aircraft=share)
        assert sum(p.get("owner") == "zorvania" for p in state["fleet"]) == expected
        assert stages.air_ratings(state)["zorvania"] > 0
    assert "zorvania" in commander.national_ranking()


def test_each_signed_stage_advances_exactly_one_place_at_any_share():
    for share in ("20", "40"):
        state = staged(trust=95, relation=80)
        for stage in range(1, 10):
            state["completed"] = {str(n): "flown" for n in range(1, stage * 10 + 1)}
            country = stages.STAGE_OPPONENTS[stage - 1]
            state["trust"][country], state["relations"]["|".join(sorted(("lumeris", country)))] = 100, 100
            before = stages.joint_rank(state)
            stages.propose(state, stage, {**DEFAULT, "aircraft": share})
            assert stages.joint_rank(state) == before - 1 == 10 - stage
            report = state["stage_reports"][str(stage)]
            assert (report["previous_rank"], report["new_rank"]) == (before, before - 1)
            ladder = [r["country"] for r in stages.air_ranking(state)]
            assert ladder.index("lumeris") + 1 == 10 - stage


def test_rank_never_changes_strength_or_national_ranking():
    small, large = signed(aircraft="20"), signed(aircraft="40")
    assert stages.joint_rank(small) == stages.joint_rank(large) == 9
    assert stages.air_ratings(small)["lumeris"] < stages.air_ratings(large)["lumeris"]
    expected = sum(stages.rating(stages.stats(p)) for p in large["fleet"])
    assert stages.air_ratings(large)["lumeris"] == round(expected)
    assert commander.national_ranking()[9] == "lumeris"


def test_failed_talks_and_purchases_do_not_advance_rank():
    countered = staged(trust=40, relation=0)
    stages.propose(countered, 1, DEFAULT)
    rejected = staged(trust=0, relation=-80)
    stages.propose(rejected, 1, {**DEFAULT, "command": "lumeris", "aircraft": "40", "withdrawal": "none"})
    assert rejected["talks"]["zorvania"]["outcome"] == "reject"
    rich = staged(done=9)
    rich["fleet"] += [dict(rich["fleet"][0], uid=100 + n) for n in range(8)]
    assert [stages.joint_rank(s) for s in (countered, rejected, rich)] == [10, 10, 10]
    stages.accept_counter(countered, 1)
    assert stages.joint_rank(countered) == 9


def test_postponed_then_signed_and_renewed_treaty_counts_once():
    state = staged(trust=95, relation=80)
    stages.postpone(state, 1)
    assert stages.joint_rank(state) == 10
    stages.propose(state, 1, {**DEFAULT, "duration": "60"})
    assert stages.joint_rank(state) == 9
    world.advance_day(state, 61)
    state["trust"]["zorvania"], state["relations"]["lumeris|zorvania"] = 95, 80
    stages.propose(state, 1, DEFAULT)
    assert stages.joint_rank(state) == 9


def test_old_save_reports_display_single_steps_without_being_rewritten():
    old = {"stage_reports": {str(n): {"stage": n, "day": n, "signed": True, "previous_rank": a, "new_rank": b}
                             for n, a, b in ((1, 10, 9), (2, 9, 8), (3, 8, 5))}}
    assert stages.joint_rank(old) == 7
    assert [r["new_rank"] for r in stages.reports(old).values()] == [9, 8, 7]
    assert old["stage_reports"]["3"]["new_rank"] == 5


def test_total_capability_is_conserved():
    before = sum(stages.air_ratings(new_state("T", seed=1)).values())
    state = signed(aircraft="40")
    assert abs(sum(stages.air_ratings(state).values()) - before) <= 2  # rounding


def test_breaking_rules_restricts_then_withdraws():
    state = signed()
    plane = partner(state)
    strike = {"type": "interception"}
    state["joint"]["zorvania"]["stability"] = 50
    stages.after_sortie(state, plane, strike, True)
    assert state["joint"]["zorvania"]["status"] == "restricted"
    with pytest.raises(RuleError):
        missions.check_aircraft(state, missions.definition(1), plane["uid"])
    diplomacy.send_aid(state, "zorvania")
    assert state["joint"]["zorvania"]["status"] == "active"
    stages.strain(state, "zorvania", 100, "test")
    assert state["joint"]["zorvania"]["status"] == "withdrawn"
    assert not any(p.get("owner") for p in state["fleet"])


def test_expiry_returns_aircraft_and_partner_planes_cannot_be_modified():
    state = signed(duration="60")
    with pytest.raises(RuleError):
        hangar.upgrade(state, partner(state)["uid"], "engine")
    world.advance_day(state, 61)
    assert state["joint"]["zorvania"]["status"] == "expired"
    assert not any(p.get("owner") for p in state["fleet"])


def test_api_negotiation_persists_and_reaches_analytics():
    game = client.post("/api/campaigns", json={"player": "T", "seed": 5}).json()
    with db.connect() as con:
        state = db.load(con, game["id"])
        state.update({k: v for k, v in staged(trust=95, relation=80).items()
                      if k in ("completed", "unlocked", "trust", "relations")})
        db.save(con, game["id"], state)
    url = f"/api/campaigns/{game['id']}"
    assert client.post(url + "/actions", json={"type": "joint_propose", "stage": 1,
                                               "terms": {"aircraft": "99"}}).status_code == 409
    done = client.post(url + "/actions", json={"type": "joint_propose", "stage": 1,
                                               "terms": {**DEFAULT, "aircraft": "40"}})
    assert done.status_code == 200
    saved = client.get(url).json()
    assert saved["joint"]["zorvania"]["status"] == "active" and saved["unlocked"] == 11
    data = client.get(url + "/analytics").json()
    assert data["joint_outcomes"] == {"accept": 1} and data["rank_history"][0]["new"] == 9
    assert data["treaties"][0]["aircraft"] == 2
