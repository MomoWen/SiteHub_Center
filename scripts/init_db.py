#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import httpx


def _str_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    return value


def _select_pocketbase_url(env: str) -> str:
    base = os.getenv("POCKETBASE_URL", "http://localhost:8090")
    if env == "prod":
        return _str_env("POCKETBASE_URL_PROD") or base
    return _str_env("POCKETBASE_URL_DEV") or base


def _get_token(client: httpx.Client, base_url: str) -> str | None:
    token = _str_env("POCKETBASE_TOKEN")
    if token:
        return token
    email = _str_env("POCKETBASE_ADMIN_EMAIL")
    password = _str_env("POCKETBASE_ADMIN_PASSWORD")
    if not email or not password:
        return None
    resp = client.post(
        f"{base_url}/api/admins/auth-with-password",
        json={"identity": email, "password": password},
    )
    resp.raise_for_status()
    data = resp.json()
    t = data.get("token")
    if not isinstance(t, str) or not t:
        raise RuntimeError("PocketBase admin auth token missing")
    return t


def _ensure_apps_collection(client: httpx.Client, base_url: str, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(f"{base_url}/api/collections", headers=headers)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items") if isinstance(data, dict) else None
    if isinstance(items, list) and any(isinstance(it, dict) and it.get("name") == "apps" for it in items):
        return

    payload: dict[str, Any] = {
        "name": "apps",
        "type": "base",
        "schema": [
            {"name": "name", "type": "text", "required": True, "unique": True, "options": {}},
            {"name": "port", "type": "number", "required": True, "unique": True, "options": {}},
            {"name": "path", "type": "text", "required": True, "unique": False, "options": {}},
            {"name": "git_repo", "type": "text", "required": False, "unique": False, "options": {}},
            {
                "name": "status",
                "type": "select",
                "required": True,
                "unique": False,
                "options": {"maxSelect": 1, "values": ["running", "stopped", "deploying", "error"]},
            },
            {"name": "sitehub_config", "type": "json", "required": False, "unique": False, "options": {}},
        ],
    }
    create = client.post(f"{base_url}/api/collections", headers=headers, json=payload)
    create.raise_for_status()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="init_db.py")
    parser.add_argument("--env", default=os.getenv("SITEHUB_ENV", "dev"))
    parser.add_argument("--ensure-apps", action="store_true")
    args = parser.parse_args(argv)

    base_url = _select_pocketbase_url(args.env).rstrip("/")
    with httpx.Client(timeout=10.0) as client:
        health = client.get(f"{base_url}/api/health")
        health.raise_for_status()
        token = _get_token(client, base_url)
        if args.ensure_apps:
            if not token:
                raise RuntimeError("Missing POCKETBASE_TOKEN or POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD")
            _ensure_apps_collection(client, base_url, token)
    sys.stdout.write("ok\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
