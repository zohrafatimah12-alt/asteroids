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
