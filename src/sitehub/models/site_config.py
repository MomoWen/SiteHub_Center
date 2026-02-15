from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PortRangeError(ValueError):
    pass


class SiteConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    port: int
    mode: Literal["proxy", "static"] = "proxy"
    external_port: int | None = Field(default=None)

    @field_validator("external_port")
    @classmethod
    def _validate_external_port(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if 8400 <= value <= 8500:
            return value
        raise PortRangeError("external_port_out_of_range: expected 8400-8500")
