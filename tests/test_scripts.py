import os
import subprocess
from pathlib import Path

import pytest


def run_script(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True, env=env)


def test_deploy_dry_run_does_not_modify_filesystem(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    proc = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "deploy.sh"),
            "--source",
            str(repo_root),
            "--site-root",
            str(tmp_path),
            "--dry-run",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_path / "releases").exists()
    assert not (tmp_path / "current").exists()


def test_deploy_rollback_dry_run_does_not_switch_current(tmp_path: Path) -> None:
    (tmp_path / "releases" / "20260101010101").mkdir(parents=True)
    repo_root = Path(__file__).resolve().parents[1]
    proc = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "deploy.sh"),
            "--site-root",
            str(tmp_path),
            "--rollback",
            "20260101010101",
            "--dry-run",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert not (tmp_path / "current").exists()


def test_provision_site_allocates_port_and_writes_env(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    proc = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "provision-site.sh"),
            "--site",
            "demo-site",
            "--sites-base",
            str(tmp_path),
            "--no-venv",
        ]
    )
    assert proc.returncode == 0, proc.stderr

    env_file = tmp_path / "demo-site" / "sitehub.env"
    assert env_file.exists()

    env_text = env_file.read_text(encoding="utf-8")
    port_line = [line for line in env_text.splitlines() if line.startswith("PORT=")][0]
    port = int(port_line.split("=", 1)[1])
    assert 8085 <= port <= 8095

    proc2 = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "provision-site.sh"),
            "--site",
            "demo-site",
            "--sites-base",
            str(tmp_path),
            "--no-venv",
        ]
    )
    assert proc2.returncode == 0, proc2.stderr
    env_text2 = env_file.read_text(encoding="utf-8")
    assert env_text2 == env_text


def test_provision_site_rejects_port_out_of_range(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    proc = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "provision-site.sh"),
            "--site",
            "demo-site",
            "--sites-base",
            str(tmp_path),
            "--port",
            "9000",
            "--no-venv",
        ]
    )
    assert proc.returncode != 0


def test_nginx_safe_update_backup_and_apply(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    nginx_stub = tmp_path / "nginx"
    nginx_stub.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"$1\" == \"-t\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"$1\" == \"-s\" && \"$2\" == \"reload\" ]]; then\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    os.chmod(nginx_stub, 0o755)

    src = tmp_path / "new.conf"
    dest = tmp_path / "live.conf"
    src.write_text("worker_processes 1;\nerror_log stderr;\n", encoding="utf-8")
    dest.write_text("worker_processes 1;\nerror_log stderr;\n", encoding="utf-8")

    env = os.environ.copy()
    env["NGINX_BIN"] = str(nginx_stub)

    proc = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "nginx-safe-update.sh"),
            "--src",
            str(src),
            "--dest",
            str(dest),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr

    backups = list(tmp_path.glob("live.conf.bak.*"))
    assert backups


def test_nginx_safe_update_dry_run_does_not_touch_dest(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    nginx_stub = tmp_path / "nginx"
    nginx_stub.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "exit 0\n",
        encoding="utf-8",
    )
    os.chmod(nginx_stub, 0o755)

    src = tmp_path / "new.conf"
    dest = tmp_path / "live.conf"
    src.write_text("worker_processes 1;\nerror_log stderr;\n", encoding="utf-8")
    dest.write_text("old\n", encoding="utf-8")

    env = os.environ.copy()
    env["NGINX_BIN"] = str(nginx_stub)

    proc = run_script(
        [
            "bash",
            str(repo_root / "scripts" / "nginx-safe-update.sh"),
            "--src",
            str(src),
            "--dest",
            str(dest),
            "--dry-run",
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert dest.read_text(encoding="utf-8") == "old\n"
