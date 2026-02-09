from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str
    port: int


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def load_settings() -> Settings:
    env = os.getenv("SITEHUB_ENV", "dev")
    port = _int_env("PORT", 8085)
    return Settings(env=env, port=port)
