from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Request

from sitehub.config import Settings
from sitehub.models.apps import AppRecord, AppRegisterRequest


@dataclass(frozen=True)
class PocketBaseAuth:
    token: str | None = None
    admin_email: str | None = None
    admin_password: str | None = None


class PocketBaseError(RuntimeError):
    def __init__(self, status_code: int, message: str, payload: Any | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class PocketBaseClient:
    def __init__(self, *, base_url: str, auth: PocketBaseAuth | None = None, timeout_s: float = 10.0):
        self._base_url = base_url.rstrip("/")
        self._auth = auth or PocketBaseAuth()
        self._timeout_s = timeout_s

    @classmethod
    def from_settings(cls, settings: Settings) -> PocketBaseClient:
        auth = PocketBaseAuth(
            token=settings.pocketbase_token,
            admin_email=settings.pocketbase_admin_email,
            admin_password=settings.pocketbase_admin_password,
        )
        return cls(base_url=settings.pocketbase_url, auth=auth)

    async def create_app(self, payload: AppRegisterRequest) -> AppRecord:
        data = payload.model_dump(mode="json", exclude_none=True)
        result = await self._request(
            "POST",
            "/api/collections/apps/records",
            json=data,
        )
        return AppRecord.model_validate(result)

    async def _get_token(self, client: httpx.AsyncClient) -> str | None:
        if self._auth.token:
            return self._auth.token
        if not self._auth.admin_email or not self._auth.admin_password:
            return None
        resp = await client.post(
            f"{self._base_url}/api/admins/auth-with-password",
            json={"identity": self._auth.admin_email, "password": self._auth.admin_password},
        )
        if resp.status_code >= 400:
            raise PocketBaseError(resp.status_code, "PocketBase admin auth failed", resp.text)
        body = resp.json()
        token = body.get("token")
        if not isinstance(token, str) or not token:
            raise PocketBaseError(resp.status_code, "PocketBase admin auth token missing", body)
        return token

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            token = await self._get_token(client)
            headers = dict(kwargs.pop("headers", {}) or {})
            if token:
                headers["Authorization"] = f"Bearer {token}"
            resp = await client.request(method, f"{self._base_url}{path}", headers=headers, **kwargs)
            if resp.status_code >= 400:
                raise PocketBaseError(resp.status_code, "PocketBase request failed", resp.text)
            return resp.json()


def get_pocketbase_client(request: Request) -> PocketBaseClient:
    settings: Settings = request.app.state.settings
    return PocketBaseClient.from_settings(settings)
