from __future__ import annotations

import argparse
import shlex
from pathlib import Path

import yaml

from sitehub.config import load_settings
from sitehub.services.deploy_service import SyncEngine, NginxEngine
from sitehub.sitehub_yaml import SitehubYaml


def _parse_local_sitehub_yaml(source: Path) -> dict | None:
    yaml_path = source / "sitehub.yaml"
    if not yaml_path.exists():
        return None
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if data is None or not isinstance(data, dict):
        return None
    validated = SitehubYaml.model_validate(data)
    return validated.model_dump(mode="python", exclude_none=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--site", required=False)
    parser.add_argument("--port", required=False, type=int)
    parser.add_argument("--remote-root", required=False)
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    settings = load_settings()
    engine = SyncEngine(settings)
    nginx_engine = NginxEngine(settings)

    sitehub_config = _parse_local_sitehub_yaml(source)
    site_name = args.site or (sitehub_config.get("name") if sitehub_config else None)
    port = args.port or (sitehub_config.get("port") if sitehub_config else None)
    if not site_name or not port:
        raise SystemExit("site and port are required when sitehub.yaml is missing")
    external_port = sitehub_config.get("external_port") if sitehub_config else None

    remote_root = args.remote_root or settings.app_root_dir or "/vol1/1000/MyDocker/web-cluster/sites"
    remote_path = f"{remote_root.rstrip('/')}/{site_name}"

    rsync_cmd = engine.build_rsync_command(source, remote_path)
    print("SIMULATE_SYNC")
    print(" ".join(shlex.quote(arg) for arg in rsync_cmd))
    print("NGINX_PREVIEW")
    print(nginx_engine.render_config(site_name, int(port), external_port=external_port))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
