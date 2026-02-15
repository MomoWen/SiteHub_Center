from __future__ import annotations

import asyncio
from pathlib import Path

from sitehub.config import load_settings
from sitehub.services import deploy_service


async def main() -> None:
    settings = load_settings()
    app_name = "p003-min-app-20260214h"
    local_path = Path("/home/momo/dev/projects/SiteHub_Center/tmp/p003-min-app-20260214h")
    remote_root = "/vol1/1000/MyDocker/web-cluster/sites"
    remote_path = f"{remote_root}/{app_name}"

    engine = deploy_service.SyncEngine(settings)
    await engine.sync(local_path, remote_path)

    nginx_engine = deploy_service.NginxEngine(settings)
    await nginx_engine.apply_from_sitehub(local_path / "sitehub.yaml")

    command = (
        f"cd '{remote_path}' && "
        f"PORT=8498 APP_DIR='{remote_path}' "
        f"nohup python3 app.py >/tmp/sitehub-{app_name}.log 2>&1 &"
    )
    await deploy_service._run_ssh_command(settings, command, settings.ssh_connect_timeout_s)


if __name__ == "__main__":
    asyncio.run(main())
