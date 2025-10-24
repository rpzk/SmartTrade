from fastapi.testclient import TestClient

from smarttrade.web.app import app


def test_ping():
    client = TestClient(app)
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
