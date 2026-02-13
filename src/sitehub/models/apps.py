from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import AnyUrl, BaseModel, Field, field_validator


class AppStatus(str, Enum):
    running = "running"
    stopped = "stopped"
    deploying = "deploying"
    error = "error"


class AppRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    port: int = Field(ge=8081, le=8090)
    path: str = Field(min_length=1, max_length=1024)
    git_repo: AnyUrl | None = None
    status: AppStatus = AppStatus.stopped
    sitehub_config: dict[str, Any] | None = None

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("path must not have leading or trailing whitespace")
        if "\\" in value:
            raise ValueError("path must use '/' as separator")
        if value.startswith("/"):
            raise ValueError("path must be relative, not absolute")
        parts = [p for p in value.split("/") if p not in ("", ".")]
        if not parts:
            raise ValueError("path must not be empty")
        if any(p == ".." for p in parts):
            raise ValueError("path must not contain '..'")
        return "/".join(parts)


class AppRecord(BaseModel):
    id: str
    name: str
    port: int
    path: str
    git_repo: str | None = None
    status: AppStatus
    sitehub_config: dict[str, Any] | None = None
    created: str | None = None
    updated: str | None = None
