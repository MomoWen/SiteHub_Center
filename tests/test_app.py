from fastapi.testclient import TestClient

from sitehub.main import create_app


def test_healthz() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readyz() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
