from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from fastapi import Request

from sitehub.config import Settings
from sitehub.models.apps import AppRecord, AppRegisterRequest
from sitehub.pocketbase import PocketBaseClient, PocketBaseError, get_pocketbase_client
from sitehub.sitehub_yaml import load_sitehub_yaml


router = APIRouter(prefix="/apps", tags=["apps"])


@router.post("/register", response_model=AppRecord, status_code=201)
async def register_app(
    request: Request,
    payload: AppRegisterRequest,
    pocketbase: PocketBaseClient = Depends(get_pocketbase_client),
) -> AppRecord:
    settings: Settings = request.app.state.settings
    sitehub_config = payload.sitehub_config
    if sitehub_config is None and settings.app_root_dir:
        app_dir = Path(settings.app_root_dir) / payload.path
        sitehub_yaml_path = app_dir / "sitehub.yaml"
        if sitehub_yaml_path.exists() and sitehub_yaml_path.is_file():
            try:
                sitehub_config = load_sitehub_yaml(sitehub_yaml_path)
            except ValueError as exc:
                raise HTTPException(
                    status_code=422,
                    detail={"error": {"type": "invalid_sitehub_yaml", "message": str(exc)}},
                ) from exc
    payload = payload.model_copy(update={"sitehub_config": sitehub_config})
    try:
        return await pocketbase.create_app(payload)
    except PocketBaseError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": {"type": "pocketbase_error", "message": str(exc), "details": exc.payload}},
        ) from exc
