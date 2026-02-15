import os
from pathlib import Path

from fastapi.testclient import TestClient

from sitehub.main import create_app
from sitehub.models.apps import AppRecord, AppRegisterRequest, AppStatus
from sitehub.pocketbase import get_pocketbase_client


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


def test_apps_register() -> None:
    class DummyPocketBase:
        async def create_app(self, payload: AppRegisterRequest) -> AppRecord:
            return AppRecord(
                id="rec_test",
                name=payload.name,
                port=payload.port,
                path=payload.path,
                git_repo=str(payload.git_repo) if payload.git_repo else None,
                status=payload.status,
                sitehub_config=payload.sitehub_config,
                created="2026-02-13 00:00:00.000Z",
                updated="2026-02-13 00:00:00.000Z",
            )

    app = create_app()
    app.dependency_overrides[get_pocketbase_client] = lambda: DummyPocketBase()
    with TestClient(app) as client:
        resp = client.post(
            "/apps/register",
            json={
                "name": "MyBookmark",
                "port": 8081,
                "path": "apps/MyBookmark",
                "git_repo": "https://github.com/example/MyBookmark",
                "status": "running",
                "sitehub_config": {"foo": "bar"},
            },
        )
    assert resp.status_code == 201
    assert resp.json()["name"] == "MyBookmark"
    assert resp.json()["port"] == 8081
    assert resp.json()["path"] == "apps/MyBookmark"
    assert resp.json()["status"] == AppStatus.running.value


def test_apps_register_rejects_absolute_path() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.post(
            "/apps/register",
            json={"name": "MyBookmark", "port": 8081, "path": "/vol1/1000/apps/MyBookmark"},
        )
    assert resp.status_code == 422


def test_apps_register_parses_sitehub_yaml(tmp_path: Path) -> None:
    class DummyPocketBase:
        async def create_app(self, payload: AppRegisterRequest) -> AppRecord:
            return AppRecord(
                id="rec_test",
                name=payload.name,
                port=payload.port,
                path=payload.path,
                git_repo=str(payload.git_repo) if payload.git_repo else None,
                status=payload.status,
                sitehub_config=payload.sitehub_config,
                created="2026-02-13 00:00:00.000Z",
                updated="2026-02-13 00:00:00.000Z",
            )

    (tmp_path / "apps" / "MyBookmark").mkdir(parents=True)
    (tmp_path / "apps" / "MyBookmark" / "sitehub.yaml").write_text("name: MyBookmark\nport: 8081\n", encoding="utf-8")

    env = os.environ.copy()
    env["APP_ROOT_DIR"] = str(tmp_path)
    env["SITEHUB_ENV"] = "dev"

    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    try:
        app = create_app()
    finally:
        os.environ.clear()
        os.environ.update(old)

    app.dependency_overrides[get_pocketbase_client] = lambda: DummyPocketBase()
    with TestClient(app) as client:
        resp = client.post(
            "/apps/register",
            json={"name": "MyBookmark", "port": 8081, "path": "apps/MyBookmark", "status": "running"},
        )
    assert resp.status_code == 201
    assert resp.json()["sitehub_config"] == {"name": "MyBookmark", "port": 8081, "mode": "proxy"}


def test_apps_register_rejects_sitehub_yaml_missing_required_fields(tmp_path: Path) -> None:
    class DummyPocketBase:
        async def create_app(self, payload: AppRegisterRequest) -> AppRecord:
            raise RuntimeError("should not be called")

    (tmp_path / "apps" / "MyBookmark").mkdir(parents=True)
    (tmp_path / "apps" / "MyBookmark" / "sitehub.yaml").write_text("name: MyBookmark\n", encoding="utf-8")

    env = os.environ.copy()
    env["APP_ROOT_DIR"] = str(tmp_path)
    env["SITEHUB_ENV"] = "dev"

    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    try:
        app = create_app()
    finally:
        os.environ.clear()
        os.environ.update(old)

    app.dependency_overrides[get_pocketbase_client] = lambda: DummyPocketBase()
    with TestClient(app) as client:
        resp = client.post(
            "/apps/register",
            json={"name": "MyBookmark", "port": 8081, "path": "apps/MyBookmark", "status": "running"},
        )
    assert resp.status_code == 422
