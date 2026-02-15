from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    env: str
    port: int
    pocketbase_url: str
    pocketbase_url_dev: str | None
    pocketbase_url_prod: str | None
    pocketbase_admin_email: str | None
    pocketbase_admin_password: str | None
    pocketbase_token: str | None
    app_root_dir: str | None
    apps_root_dev: str | None
    apps_root_prod: str | None
    env_host: str
    ssh_user: str | None
    ssh_port: int | None
    ssh_private_key_path: str | None
    ssh_connect_timeout_s: float
    env_probe_timeout_s: float
    nginx_conf_path: str | None
    nginx_conf_dir: str | None


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        return {}
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]
        data[key] = value
    return data


def _env_str(name: str, *, dotenv: Mapping[str, str]) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        value = dotenv.get(name)
    if value is None or value == "":
        return None
    return value


def _env_int(name: str, default: int, *, dotenv: Mapping[str, str]) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        value = dotenv.get(name)
    if value is None or value == "":
        return default
    return int(value)


def _env_int_optional(name: str, *, dotenv: Mapping[str, str]) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        value = dotenv.get(name)
    if value is None or value == "":
        return None
    return int(value)


def _env_float(name: str, default: float, *, dotenv: Mapping[str, str]) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        value = dotenv.get(name)
    if value is None or value == "":
        return default
    return float(value)


def _default_dotenv_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def load_settings() -> Settings:
    dotenv_path = os.getenv("SITEHUB_DOTENV_PATH")
    dotenv = _read_dotenv(Path(dotenv_path) if dotenv_path else _default_dotenv_path())
    env = _env_str("SITEHUB_ENV", dotenv=dotenv) or "dev"
    port = _env_int("PORT", 8085, dotenv=dotenv)
    pocketbase_url = _env_str("POCKETBASE_URL", dotenv=dotenv) or "http://localhost:8090"
    pocketbase_url_dev = _env_str("POCKETBASE_URL_DEV", dotenv=dotenv)
    pocketbase_url_prod = _env_str("POCKETBASE_URL_PROD", dotenv=dotenv)
    app_root_dir = _env_str("APP_ROOT_DIR", dotenv=dotenv)
    apps_root_dev = _env_str("SITEHUB_APPS_ROOT_DEV", dotenv=dotenv)
    apps_root_prod = _env_str("SITEHUB_APPS_ROOT_PROD", dotenv=dotenv)
    env_host = _env_str("SITEHUB_ENV_HOST", dotenv=dotenv) or "10.8.8.80"
    ssh_user = _env_str("SITEHUB_SSH_USER", dotenv=dotenv)
    ssh_port = _env_int_optional("SITEHUB_SSH_PORT", dotenv=dotenv)
    ssh_private_key_path = _env_str("SSH_PRIVATE_KEY_PATH", dotenv=dotenv)
    if ssh_private_key_path:
        ssh_private_key_path = str(Path(ssh_private_key_path).expanduser())
    ssh_connect_timeout_s = _env_float("SITEHUB_SSH_CONNECT_TIMEOUT", 2.0, dotenv=dotenv)
    env_probe_timeout_s = _env_float("SITEHUB_ENV_PROBE_TIMEOUT", 5.0, dotenv=dotenv)
    nginx_conf_path = _env_str("NGINX_CONF_PATH", dotenv=dotenv)
    nginx_conf_dir = _env_str("NGINX_CONF_DIR", dotenv=dotenv)
    effective_app_root_dir = app_root_dir
    if effective_app_root_dir is None:
        if env == "prod":
            effective_app_root_dir = apps_root_prod or "/vol1/1000/MyDocker/web-cluster/sites"
        else:
            effective_app_root_dir = apps_root_dev or str(
                Path(__file__).resolve().parents[2] / "sites"
            )
    effective_pocketbase_url = pocketbase_url
    if env == "prod" and pocketbase_url_prod:
        effective_pocketbase_url = pocketbase_url_prod
    if env != "prod" and pocketbase_url_dev:
        effective_pocketbase_url = pocketbase_url_dev
    return Settings(
        env=env,
        port=port,
        pocketbase_url=effective_pocketbase_url,
        pocketbase_url_dev=pocketbase_url_dev,
        pocketbase_url_prod=pocketbase_url_prod,
        pocketbase_admin_email=_env_str("POCKETBASE_ADMIN_EMAIL", dotenv=dotenv),
        pocketbase_admin_password=_env_str("POCKETBASE_ADMIN_PASSWORD", dotenv=dotenv),
        pocketbase_token=_env_str("POCKETBASE_TOKEN", dotenv=dotenv),
        app_root_dir=effective_app_root_dir,
        apps_root_dev=apps_root_dev,
        apps_root_prod=apps_root_prod,
        env_host=env_host,
        ssh_user=ssh_user,
        ssh_port=ssh_port,
        ssh_private_key_path=ssh_private_key_path,
        ssh_connect_timeout_s=ssh_connect_timeout_s,
        env_probe_timeout_s=env_probe_timeout_s,
        nginx_conf_path=nginx_conf_path,
        nginx_conf_dir=nginx_conf_dir,
    )
