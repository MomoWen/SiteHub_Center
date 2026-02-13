import os
from pathlib import Path

from sitehub.config import load_settings


def test_env_overrides_dotenv(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "\n".join(
            [
                "SITEHUB_ENV=dev",
                "PORT=8888",
                "POCKETBASE_URL=http://dotenv:8090",
                "APP_ROOT_DIR=/dotenv/root",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["SITEHUB_DOTENV_PATH"] = str(dotenv)
    env["PORT"] = "9999"
    env["POCKETBASE_URL"] = "http://env:8090"
    env["APP_ROOT_DIR"] = "/env/root"

    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    try:
        settings = load_settings()
    finally:
        os.environ.clear()
        os.environ.update(old)

    assert settings.port == 9999
    assert settings.pocketbase_url == "http://env:8090"
    assert settings.app_root_dir == "/env/root"


def test_dotenv_used_when_env_missing(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("PORT=7777\nPOCKETBASE_URL=http://dotenv:8090\n", encoding="utf-8")

    env = os.environ.copy()
    env["SITEHUB_DOTENV_PATH"] = str(dotenv)
    env.pop("PORT", None)
    env.pop("POCKETBASE_URL", None)

    old = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    try:
        settings = load_settings()
    finally:
        os.environ.clear()
        os.environ.update(old)

    assert settings.port == 7777
    assert settings.pocketbase_url == "http://dotenv:8090"
