from __future__ import annotations

import asyncio
from pathlib import Path

from sitehub.config import load_settings
from sitehub.services import deploy_service


async def main() -> None:
    settings = load_settings()
    app_name = "p003-min-app-verify"
    local_path = Path("/home/momo/dev/projects/SiteHub_Center/tmp/p003-min-app-verify")
    remote_root = "/vol1/1000/MyDocker/web-cluster/sites"
    remote_path = f"{remote_root}/{app_name}"

    engine = deploy_service.SyncEngine(settings)
    await engine.sync(local_path, remote_path)

    nginx_engine = deploy_service.NginxEngine(settings)
    await nginx_engine.apply_from_sitehub(local_path / "sitehub.yaml")


if __name__ == "__main__":
    asyncio.run(main())
