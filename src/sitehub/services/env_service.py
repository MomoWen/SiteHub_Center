from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sitehub.config import Settings


DEFAULT_PROBE_PATHS = (
    "/vol1/1000/",
    "/vol1/1000/MyDocker/web-cluster/sites",
)
DEFAULT_NGINX_CONF = "/etc/nginx/nginx.conf"
DEFAULT_NGINX_CONF_DIR = "/etc/nginx/conf.d"
SSH_WARNING_THRESHOLD_MS = 2000


def _ssh_target(settings: Settings) -> str | None:
    host = settings.env_host
    if not host:
        return None
    user = settings.ssh_user
    if user:
        return f"{user}@{host}"
    return host


def _ssh_base_args(settings: Settings) -> list[str]:
    args = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={int(settings.ssh_connect_timeout_s)}",
        "-o",
        "ConnectionAttempts=1",
    ]
    if settings.ssh_port:
        args.extend(["-p", str(settings.ssh_port)])
    return args


async def _run_ssh_command(
    settings: Settings, command: str, timeout_s: float
) -> tuple[int, str, str, float]:
    target = _ssh_target(settings)
    if not target:
        return 255, "", "ssh_target_missing", 0.0
    args = _ssh_base_args(settings)
    start = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        *args,
        target,
        "bash",
        "-lc",
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "ssh_timeout", time.monotonic() - start
    return proc.returncode or 0, stdout.decode(), stderr.decode(), time.monotonic() - start


async def measure_ssh_latency(settings: Settings) -> tuple[int | None, str | None]:
    rc, _, stderr, elapsed = await _run_ssh_command(settings, "true", settings.ssh_connect_timeout_s)
    if rc != 0:
        reason = stderr.strip() if stderr.strip() else "ssh_unreachable"
        return None, reason
    return int(elapsed * 1000), None


async def _probe_local_path(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "method": "local",
        "exists": False,
        "readable": False,
        "writable": False,
        "status": "missing",
        "reason": None,
    }
    try:
        if not path.exists():
            return result
        result["exists"] = True
        result["readable"] = os.access(path, os.R_OK)
        probe_path = path / ".sitehub_probe"
        try:
            probe_path.write_text("probe", encoding="utf-8")
            result["writable"] = True
        except PermissionError as exc:
            result["writable"] = False
            result["reason"] = str(exc)
        finally:
            if probe_path.exists():
                try:
                    probe_path.unlink()
                except OSError:
                    pass
        if not result["readable"] or not result["writable"]:
            result["status"] = "permission_denied"
        else:
            result["status"] = "ok"
        return result
    except PermissionError as exc:
        result["status"] = "permission_denied"
        result["reason"] = str(exc)
        return result
    except OSError as exc:
        result["status"] = "unreachable"
        result["reason"] = str(exc)
        return result


async def _probe_remote_path(settings: Settings, path: str, timeout_s: float) -> dict[str, Any]:
    probe_target = f"{path.rstrip('/')}/.sitehub_probe"
    command = (
        "set -e; "
        f"if [ ! -e '{path}' ]; then echo 'missing'; exit 0; fi; "
        f"r=0; w=0; [ -r '{path}' ] && r=1; "
        f"probe='{probe_target}'; "
        "trap 'rm -f \"$probe\"' EXIT; "
        "touch \"$probe\" >/dev/null 2>&1 && w=1 || w=0; "
        "echo \"exists r=$r w=$w\""
    )
    rc, stdout, stderr, _ = await _run_ssh_command(settings, command, timeout_s)
    result: dict[str, Any] = {
        "path": path,
        "method": "ssh",
        "exists": False,
        "readable": False,
        "writable": False,
        "status": "unreachable",
        "reason": None,
    }
    if rc != 0:
        if rc == 124 or stderr.strip() == "ssh_timeout":
            result["status"] = "timeout"
            result["reason"] = "ssh_timeout"
            return result
        result["reason"] = stderr.strip() or "ssh_unreachable"
        return result
    line = stdout.strip()
    if line == "missing":
        result["status"] = "missing"
        return result
    result["exists"] = True
    parts = dict(item.split("=", 1) for item in line.split() if "=" in item)
    result["readable"] = parts.get("r") == "1"
    result["writable"] = parts.get("w") == "1"
    if not result["readable"] or not result["writable"]:
        result["status"] = "permission_denied"
    else:
        result["status"] = "ok"
    return result


async def probe_path(settings: Settings, path: str) -> dict[str, Any]:
    local_path = Path(path)
    if local_path.exists():
        return await _probe_local_path(local_path)
    return await _probe_remote_path(settings, path, settings.env_probe_timeout_s)


def _disk_usage_from_local(path: Path) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


async def _disk_usage_from_remote(settings: Settings, path: str) -> dict[str, Any] | None:
    command = f"df -k '{path}' | tail -n 1"
    rc, stdout, stderr, _ = await _run_ssh_command(settings, command, settings.env_probe_timeout_s)
    if rc != 0:
        if rc == 124 or stderr.strip() == "ssh_timeout":
            return {"status": "timeout", "reason": "ssh_timeout"}
        return {"status": "unreachable", "reason": stderr.strip() or "ssh_unreachable"}
    parts = stdout.split()
    if len(parts) < 4:
        return {"status": "unreachable", "reason": "df_output_invalid"}
    total_kb = int(parts[1])
    used_kb = int(parts[2])
    free_kb = int(parts[3])
    return {
        "status": "ok",
        "total_bytes": total_kb * 1024,
        "used_bytes": used_kb * 1024,
        "free_bytes": free_kb * 1024,
    }


async def probe_disk_usage(settings: Settings, path: str) -> dict[str, Any]:
    local_path = Path(path)
    if local_path.exists():
        return {"status": "ok", **_disk_usage_from_local(local_path)}
    return await _disk_usage_from_remote(settings, path)


async def probe_nginx(settings: Settings) -> dict[str, Any]:
    conf_path = settings.nginx_conf_path or DEFAULT_NGINX_CONF
    conf_dir = settings.nginx_conf_dir or DEFAULT_NGINX_CONF_DIR
    local_conf = Path(conf_path)
    if local_conf.exists():
        return {
            "method": "local",
            "binary_path": shutil.which("nginx"),
            "config_path": conf_path,
            "config_dir": conf_dir,
            "config_readable": os.access(conf_path, os.R_OK),
            "config_writable": os.access(conf_path, os.W_OK),
            "dir_readable": os.access(conf_dir, os.R_OK),
            "dir_writable": os.access(conf_dir, os.W_OK),
        }
    command = (
        f"bin=$(command -v nginx || true); "
        "cr=0; cw=0; dr=0; dw=0; "
        f"[ -r '{conf_path}' ] && cr=1; [ -w '{conf_path}' ] && cw=1; "
        f"[ -r '{conf_dir}' ] && dr=1; [ -w '{conf_dir}' ] && dw=1; "
        "echo \"bin=$bin cr=$cr cw=$cw dr=$dr dw=$dw\""
    )
    rc, stdout, stderr, _ = await _run_ssh_command(settings, command, settings.env_probe_timeout_s)
    if rc != 0:
        status = "timeout" if rc == 124 or stderr.strip() == "ssh_timeout" else "unreachable"
        reason = "ssh_timeout" if status == "timeout" else (stderr.strip() or "ssh_unreachable")
        return {
            "method": "ssh",
            "binary_path": None,
            "config_path": conf_path,
            "config_dir": conf_dir,
            "status": status,
            "reason": reason,
        }
    parts = dict(item.split("=") for item in stdout.split() if "=" in item)
    return {
        "method": "ssh",
        "binary_path": parts.get("bin") or None,
        "config_path": conf_path,
        "config_dir": conf_dir,
        "config_readable": parts.get("cr") == "1",
        "config_writable": parts.get("cw") == "1",
        "dir_readable": parts.get("dr") == "1",
        "dir_writable": parts.get("dw") == "1",
    }


def backup_nginx_config(settings: Settings) -> dict[str, Any]:
    conf_path = Path(settings.nginx_conf_path or DEFAULT_NGINX_CONF)
    backup_dir = conf_path.parent
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    backup_path = backup_dir / f"{conf_path.name}.bak.{timestamp}"
    if not conf_path.exists():
        return {"status": "missing", "path": str(conf_path)}
    backup_path.write_bytes(conf_path.read_bytes())
    backups = sorted(backup_dir.glob(f"{conf_path.name}.bak.*"), key=lambda p: p.name)
    while len(backups) > 5:
        oldest = backups.pop(0)
        try:
            oldest.unlink()
        except OSError:
            break
    return {"status": "ok", "backup_path": str(backup_path)}


async def build_env_report(settings: Settings) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": {
            "host": settings.env_host,
            "ssh_user": settings.ssh_user,
            "ssh_port": settings.ssh_port,
        },
    }
    ssh_latency_ms, ssh_reason = await measure_ssh_latency(settings)
    warnings: list[str] = []
    if ssh_latency_ms is None and ssh_reason:
        warnings.append(f"ssh_unreachable: {ssh_reason}")
    elif ssh_latency_ms is not None and ssh_latency_ms > SSH_WARNING_THRESHOLD_MS:
        warnings.append("ssh_latency_high")
    report["ssh_latency_ms"] = ssh_latency_ms
    report["warnings"] = warnings

    probe_tasks = [probe_path(settings, path) for path in DEFAULT_PROBE_PATHS]
    path_results = await asyncio.gather(*probe_tasks)
    report["paths"] = path_results

    disk_target = DEFAULT_PROBE_PATHS[0]
    report["disk"] = await probe_disk_usage(settings, disk_target)
    report["nginx"] = await probe_nginx(settings)

    if any(item.get("status") not in ("ok", "missing") for item in path_results):
        report["status"] = "degraded"
    if warnings:
        report["status"] = "degraded"
    return report


def render_pretty_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
