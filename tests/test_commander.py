import pytest
from fastapi.testclient import TestClient

from nebula import api
from nebula.combat.sim import Sim
from nebula.combat.ticket import build_ticket
from nebula.core import commander, missions
from nebula.core.state import RuleError, new_state

client = TestClient(api.app)


def test_ranks_come_from_data():
    order = commander.national_ranking()
    assert order[9] == "lumeris" and order[8] == "zorvania"
    assert missions.definition(1)["antagonist"] == "zorvania"


@pytest.mark.parametrize("key", list(commander.PHILOSOPHIES))
def test_philosophy_is_permanent_and_keeps_rank(key):
    state = new_state("T", seed=1)
    before = commander.national_ranking()
    commander.choose_philosophy(state, key)
    assert commander.national_ranking() == before and state["history"]
    with pytest.raises(RuleError):
        commander.choose_philosophy(state, "defence")


def test_replies_diverge_and_open_different_followups():
    outcomes = {}
    for choice in ("talk", "firm", "gift"):
        state = new_state("T", seed=1)
        commander.reply(state, "envoy", choice)
        ids = {m["id"] for m in commander.inbox(state)}
        assert f"envoy_{choice}" in ids and len([i for i in ids if i.startswith("envoy_")]) == 1
        outcomes[choice] = (state["relations"]["lumeris|zorvania"], state["trust"]["zorvania"],
                            state["resources"]["credits"])
        with pytest.raises(RuleError):
            commander.reply(state, "envoy", choice)
    assert len(set(outcomes.values())) == 3


def test_diplomacy_can_open_a_peaceful_level_one():
    state = new_state("T", seed=1)
    mission = missions.definition(1)
    assert not missions.peaceful_option(state, mission)["available"]
    commander.choose_philosophy(state, "diplomacy")
    commander.reply(state, "envoy", "gift")
    commander.reply(state, "envoy_gift", "good")
    assert missions.peaceful_option(state, mission)["available"]


def test_tactics_change_the_real_ticket():
    state = new_state("T", seed=1)
    plain = Sim(build_ticket(state, missions.definition(1), state["fleet"][0]))
    missions.prepare(state, "patrol")
    missions.prepare(state, "support")
    ready = Sim(build_ticket(state, missions.definition(1), state["fleet"][0]))
    assert ready.radar > plain.radar and ready.wingman and not plain.wingman


def test_api_debrief_persists_and_hides_private_motives():
    game = client.post("/api/campaigns", json={"player": "T", "seed": 5}).json()
    url = f"/api/campaigns/{game['id']}"
    assert client.post(url + "/actions", json={"type": "philosophy", "kind": "defence"}).status_code == 200
    client.post(url + "/actions", json={"type": "delegate", "level": 1, "uid": 1})
    saved = client.get(url).json()
    assert saved["philosophy"] == "defence" and saved["last_debrief"]["level"] == 1
    assert saved["last_debrief"]["mode"] == "command" and saved["last_debrief"]["enemy_lost"] is None
    assert "private" not in client.get("/api/world").text
