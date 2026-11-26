import pytest
from fastapi.testclient import TestClient

from nebula import api
from nebula.core import commander, conflict, diplomacy, missions, stages, world
from nebula.core.state import RuleError, new_state
from nebula.data.countries import COUNTRIES

client = TestClient(api.app)


def tense(trust, relation_value, seed=1):
    state = new_state("T", seed=seed)
    state["trust"]["zorvania"] = trust
    state["relations"]["lumeris|zorvania"] = relation_value
    conflict.trigger(state, "zorvania")
    return state


def outcomes(trust, relation_value, choice):
    found = set()
    for seed in range(60):
        state = tense(trust, relation_value, seed)
        conflict.respond(state, choice)
        found.add(state["incidents"][0]["outcome"])
    return found


def test_negotiation_depends_on_relationship_and_is_not_guaranteed():
    assert outcomes(95, 70, "envoy") == {"peace"}
    assert len(outcomes(42, -5, "negotiate")) >= 3
    poor = outcomes(5, -70, "negotiate")
    assert "peace" not in poor and "war" in poor


def test_war_has_consequences_and_playable_missions():
    state = tense(30, -20)
    state["treaties"]["zorvania"] = ["peace", "trade"]
    credits, trust = state["resources"]["credits"], state["trust"]["zorvania"]
    conflict.respond(state, "military")
    war = state["wars"]["zorvania"]
    assert war["military"] > 0 and war["civilian"] > 0
    assert state["resources"]["credits"] < credits and state["trust"]["zorvania"] < trust
    assert state["treaties"]["zorvania"] == []
    with pytest.raises(RuleError):
        diplomacy.send_aid(state, "zorvania")
    level = conflict.war_level("zorvania")
    assert missions.mission_for(state, level)["combat"]
    for _ in range(2):
        missions.apply_combat(state, level, 1, {"success": True, "damage_taken": 0})
    assert "zorvania" not in state["wars"] and state["war_record"]
    assert state["completed"] == {} and state["unlocked"] == 1
    with pytest.raises(RuleError):
        missions.mission_for(state, level)


def test_truth_stays_hidden_and_broken_promises_are_remembered():
    state = tense(95, 70)
    assert "truth" not in conflict.view(state)["incidents"][0]
    conflict.respond(state, "investigate")
    assert "kind" not in conflict.view(state)["incidents"][0]["evidence"]
    conflict.respond(state, "envoy")
    assert conflict.active_promise(state, "zorvania")
    diplomacy.pressure(state, "zorvania")
    assert state["promises"][0]["broken"]
    assert "promise you broke" in conflict.trigger(state, "zorvania")["reactions"][0]["text"]


def test_ignoring_has_an_outcome_and_levels_trigger_incidents():
    state = tense(40, 0)
    world.advance_day(state, 8)
    assert state["incidents"][0]["choice"] == "silence"
    fresh = new_state("T", seed=2)
    conflict.after_level(fresh, 2, "zorvania")
    assert commander.next_objective(fresh) == "Respond to the misunderstanding"


def test_war_mission_briefing_and_pygame_ticket_over_api(monkeypatch):
    from nebula.combat.sim import Sim
    from nebula.core import db

    class Running:
        def poll(self):
            return 0

    tickets = []
    monkeypatch.setattr(api, "launch_combat", lambda path: tickets.append(path) or Running())
    cid = client.post("/api/campaigns", json={"player": "T", "seed": 3}).json()["id"]
    with db.connect() as con:
        state = db.load(con, cid)
        state.update(_records=[], trust={**state["trust"], "zorvania": 10})
        conflict.trigger(state, "zorvania")
        state["relations"]["lumeris|zorvania"] = -50
        conflict.respond(state, "military")
        db.save(con, cid, state)
    level = conflict.war_level("zorvania")
    url = f"/api/campaigns/{cid}"
    assert client.get(url + f"/missions/{level}").json()["type_label"] == "War mission"
    assert client.post(url + "/sorties", json={"level": level, "uid": 1}).status_code == 201
    import json
    assert Sim(json.loads(tickets[0].read_text())).mission["level"] == level


@pytest.mark.parametrize("nation", sorted(COUNTRIES))
def test_every_nation_can_start_and_play(nation):
    game = client.post("/api/campaigns", json={"player": "T", "nation": nation, "seed": 3}).json()
    assert game["home"] == nation and nation not in game["trust"] and len(game["fleet"]) == 2
    assert game["joint_rank"] == game["start_rank"] == stages.national_order().index(nation) + 1
    levels = client.get(f"/api/levels?home={nation}").json()
    assert len(levels) == 100 and all(m["opponent"] != nation for m in levels)
    url = f"/api/campaigns/{game['id']}"
    assert client.get(url + "/missions/1").status_code == 200
    for body in ({"type": "reply", "subject": "welcome", "kind": "crews"},
                 {"type": "delegate", "level": 1, "uid": 1}):
        response = client.post(url + "/actions", json=body)
        assert response.status_code == 200, response.text
    assert client.get(url + "/analytics").status_code == 200


def test_bad_nation_rejected_and_old_save_defaults_to_lumeris():
    assert client.post("/api/campaigns", json={"player": "T", "nation": "nowhere"}).status_code == 409
    old = new_state("T", seed=1)
    del old["home"]
    assert stages.joint_rank(old) == 10 and commander.next_objective(old).startswith("Level 1")
