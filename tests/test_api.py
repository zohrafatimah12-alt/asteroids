import json

from fastapi.testclient import TestClient

from nebula import api

client = TestClient(api.app)


def new_campaign():
    return client.post("/api/campaigns", json={"player": "Tester", "seed": 5}).json()


def act(cid, **body):
    return client.post(f"/api/campaigns/{cid}/actions", json=body)


def test_world_levels_and_static():
    assert len(client.get("/api/world").json()["map"]["shapes"]) == 10
    assert len(client.get("/api/levels").json()) == 100
    assert "NEBULA" in client.get("/").text


def test_state_hides_secrets():
    game = new_campaign()
    assert game["countries"]["varkhen"]["military"] is None
    assert game["countries"]["varkhen"]["weaknesses"] is None
    assert "seed" not in game and "intel" not in game


def test_actions_errors_and_analytics():
    cid = new_campaign()["id"]
    empty = client.get(f"/api/campaigns/{cid}/analytics").json()
    assert empty["mission_success_rate"] is None and empty["aircraft"] == []
    assert act(cid, type="nonsense").status_code == 422
    assert act(cid, type="treaty", country="aerovant", kind="alliance").status_code == 409
    assert act(cid, type="treaty", country="aerovant", kind="peace").status_code == 200
    assert act(cid, type="delegate", level=1, uid=1).status_code == 200
    assert client.get("/api/campaigns/999").status_code == 404
    data = client.get(f"/api/campaigns/{cid}/analytics").json()
    assert data["attempts"] == 1 and data["negotiations"] == 1
    assert data["by_mode"] == {"command": 1}
    assert data["aircraft"][0]["aircraft"] == "lm_wren"
    assert data["resources"]


def test_snapshot_restore_forks_history():
    cid = new_campaign()["id"]
    act(cid, type="aid", country="aerovant")
    sid = client.post(f"/api/campaigns/{cid}/snapshots", json={"label": "before"}).json()["id"]
    act(cid, type="delegate", level=1, uid=1)
    restored = client.post(f"/api/snapshots/{sid}/restore", json={}).json()
    assert restored["id"] != cid and restored["completed"] == {}
    assert client.get(f"/api/campaigns/{restored['id']}/analytics").json()["attempts"] == 0
    assert client.get(f"/api/campaigns/{cid}/analytics").json()["attempts"] == 1


def test_sortie_bridge_applies_result_once(monkeypatch):
    class Finished:
        def poll(self):
            return 0

    def fake_launch(ticket):
        from nebula.combat.sim import Sim, autopilot
        sim = Sim(json.loads(ticket.read_text()))
        while sim.outcome is None:
            sim.step(autopilot(sim), 1 / 30)
        ticket.with_name(ticket.stem + ".result.json").write_text(json.dumps(sim.result()))
        return Finished()

    monkeypatch.setattr(api, "launch_combat", fake_launch)
    cid = new_campaign()["id"]
    sid = client.post(f"/api/campaigns/{cid}/sorties", json={"level": 1, "uid": 1, "mode": "desktop"}).json()["id"]
    assert client.get(f"/api/sorties/{sid}").json()["status"] == "complete"
    client.get(f"/api/sorties/{sid}")
    data = client.get(f"/api/campaigns/{cid}/analytics").json()
    assert data["attempts"] == 1 and data["by_mode"] == {"flown": 1}
    assert client.get(f"/api/campaigns/{cid}").json()["unlocked"] == 2
