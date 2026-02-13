from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError


class SitehubYaml(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    port: int


def load_sitehub_yaml(file_path: Path) -> dict[str, Any]:
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("sitehub.yaml must be a YAML mapping")
    try:
        validated = SitehubYaml.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    return validated.model_dump(mode="python")
