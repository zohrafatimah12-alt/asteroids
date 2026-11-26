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
