from __future__ import annotations

import asyncio

from sitehub.config import load_settings
from sitehub.services import deploy_service


async def main() -> None:
    settings = load_settings()
    cmd = "chmod -R 755 -- /vol1/1000/MyDocker/web-cluster/sites/p003-min-app-20260214g"
    rc, out, err = await deploy_service._run_ssh_command(settings, cmd, settings.ssh_connect_timeout_s)
    print(rc)
    print(out)
    print(err)


if __name__ == "__main__":
    asyncio.run(main())
