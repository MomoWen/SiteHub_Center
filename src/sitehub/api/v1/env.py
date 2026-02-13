from __future__ import annotations

from fastapi import APIRouter, Request, Response

from sitehub.services.env_service import build_env_report, render_pretty_json


router = APIRouter(prefix="/env", tags=["env"])


@router.get("/health")
async def env_health(request: Request) -> Response:
    settings = request.app.state.settings
    try:
        report = await build_env_report(settings)
    except Exception as exc:
        report = {
            "status": "error",
            "error": {
                "type": "env_health_error",
                "message": str(exc),
            },
        }
    return Response(content=render_pretty_json(report), media_type="application/json")
