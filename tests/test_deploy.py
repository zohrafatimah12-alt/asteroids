import os
import importlib

from fastapi.testclient import TestClient


def test_cors_allows_only_listed_origin(monkeypatch):
    monkeypatch.setenv("NEBULA_CORS_ORIGINS", "https://nebula.vercel.app")
    from nebula import api
    importlib.reload(api)
    client = TestClient(api.app)
    ok = client.get("/api/world", headers={"Origin": "https://nebula.vercel.app"})
    assert ok.headers.get("access-control-allow-origin") == "https://nebula.vercel.app"
    other = client.get("/api/world", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers
    monkeypatch.delenv("NEBULA_CORS_ORIGINS")
    importlib.reload(api)


def test_combat_can_be_disabled_without_breaking_command(monkeypatch):
    from nebula import api
    importlib.reload(api)
    client = TestClient(api.app)
    cid = client.post("/api/campaigns", json={"player": "T", "seed": 2}).json()["id"]
    monkeypatch.setenv("NEBULA_ALLOW_COMBAT", "0")
    refused = client.post(f"/api/campaigns/{cid}/sorties", json={"level": 1, "uid": 1})
    assert refused.status_code == 409 and "Command a wing" in refused.json()["detail"]
    flown = client.post(f"/api/campaigns/{cid}/actions", json={"type": "delegate", "level": 1, "uid": 1})
    assert flown.status_code == 200
    monkeypatch.delenv("NEBULA_ALLOW_COMBAT")


def test_wsgi_entry_point_imports():
    from nebula.wsgi import application
    assert callable(application)


def test_healthz_answers_for_any_host_but_other_routes_still_check_hosts(monkeypatch):
    from nebula import api
    importlib.reload(api)
    client = TestClient(api.app)
    assert client.get("/healthz", headers={"host": "unknown.example"}).json() == {"status": "ok"}
    assert client.get("/healthz").status_code == 200
    assert client.get("/api/world", headers={"host": "unknown.example"}).status_code == 400
    monkeypatch.setenv("NEBULA_HOSTS", "my-app.ethiodeploy.example")
    importlib.reload(api)
    client = TestClient(api.app)
    assert client.get("/api/world", headers={"host": "my-app.ethiodeploy.example"}).status_code == 200
    monkeypatch.delenv("NEBULA_HOSTS")
    importlib.reload(api)


VERCEL = "https://nebulagame-seven.vercel.app"


def _fresh(monkeypatch, env=None):
    from nebula import api
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    importlib.reload(api)
    return api, TestClient(api.app)


def test_vercel_origin_gets_cors_headers_and_preflight_works(monkeypatch):
    api, client = _fresh(monkeypatch, {"NEBULA_HOSTS": "asteroids.ethiodeploy.app"})
    get = client.get("/api/world", headers={"Origin": VERCEL, "host": "asteroids.ethiodeploy.app"})
    assert get.status_code == 200 and get.headers["access-control-allow-origin"] == VERCEL
    pre = client.options("/api/campaigns", headers={
        "Origin": VERCEL, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type", "host": "asteroids.ethiodeploy.app"})
    assert pre.status_code == 200
    assert pre.headers["access-control-allow-origin"] == VERCEL
    assert "POST" in pre.headers["access-control-allow-methods"]
    monkeypatch.delenv("NEBULA_HOSTS")
    importlib.reload(api)


def test_error_responses_keep_cors_headers(monkeypatch):
    api, client = _fresh(monkeypatch)
    client = TestClient(api.app, raise_server_exceptions=False)
    cid = client.post("/api/campaigns", json={"player": "T", "seed": 2}).json()["id"]

    def broken(*args, **kwargs):
        raise RuntimeError("simulated fault")

    monkeypatch.setattr(api, "view", broken)
    boom = client.get(f"/api/campaigns/{cid}", headers={"Origin": VERCEL})
    assert boom.status_code == 500 and boom.headers["access-control-allow-origin"] == VERCEL
    monkeypatch.undo()
    missing = client.get("/api/campaigns/999", headers={"Origin": VERCEL})
    assert missing.status_code == 404 and missing.headers["access-control-allow-origin"] == VERCEL
    rude = client.get("/api/world", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in rude.headers
    importlib.reload(api)


def test_sortie_fails_clearly_without_a_screen_and_keeps_the_error(monkeypatch, tmp_path):
    from nebula import api
    importlib.reload(api)
    client = TestClient(api.app)
    cid = client.post("/api/campaigns", json={"player": "T", "seed": 2}).json()["id"]
    monkeypatch.setattr(api.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    no_screen = client.post(f"/api/campaigns/{cid}/sorties", json={"level": 1, "uid": 1})
    assert no_screen.status_code == 409 and "no screen" in no_screen.json()["detail"]
    monkeypatch.setenv("DISPLAY", ":0")

    class Crashed:
        def poll(self):
            return 1

    def crash(ticket):
        ticket.with_suffix(".log").write_text("boot\npygame.error: No video device\n")
        return Crashed()

    monkeypatch.setattr(api, "launch_combat", crash)
    sid = client.post(f"/api/campaigns/{cid}/sorties", json={"level": 1, "uid": 1}).json()["id"]
    status = client.get(f"/api/sorties/{sid}").json()
    assert status["status"] == "aborted" and "pygame.error: No video device" in status["message"]
    assert "closed without a result" not in status["message"]
    monkeypatch.undo()
    importlib.reload(api)


def test_leaving_before_the_mission_is_not_a_crash(monkeypatch):
    from nebula import api
    importlib.reload(api)
    client = TestClient(api.app)
    cid = client.post("/api/campaigns", json={"player": "T", "seed": 2}).json()["id"]
    monkeypatch.setenv("DISPLAY", ":0")

    class Left:
        def poll(self):
            return 0

    def leave(ticket):
        ticket.with_name(ticket.stem + ".left.json").write_text("{}")
        return Left()

    monkeypatch.setattr(api, "launch_combat", leave)
    sid = client.post(f"/api/campaigns/{cid}/sorties", json={"level": 1, "uid": 1}).json()["id"]
    assert client.get(f"/api/sorties/{sid}").json()["message"].startswith("You left the mission")
    importlib.reload(api)
