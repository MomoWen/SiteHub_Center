from __future__ import annotations

import asyncio
import re
import hashlib
import shlex
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Any

import yaml

from sitehub.config import Settings, load_settings
from sitehub.models.site_config import PortRangeError
from sitehub.sitehub_yaml import SitehubYaml

SSH_CONTROL_PERSIST_S = 60
SSH_MAX_ATTEMPTS = 2
SSH_RETRY_BACKOFF_S = 0.2
DEFAULT_EXCLUDES = (".git/", "__pycache__/", ".venv/", ".env", ".DS_Store")
DEFAULT_NGINX_CONF_DIR = "/etc/nginx/conf.d"
DEFAULT_NGINX_REMOTE_CONF_DIR = "/vol1/1000/MyDocker/nginx/conf.d"
DEFAULT_NGINX_SITE_ROOT = "/usr/share/nginx/sites"
LOG_FILE = Path(__file__).resolve().parents[3] / "sitehub.log"
LISTEN_PORT_RE = re.compile(r"listen\s+(?:[\d\.]+:|\[[a-fA-F\d:]+\]:)?(\d+)\b")


@dataclass(frozen=True)
class SyncResult:
    method: str
    stdout: str
    stderr: str


@dataclass(frozen=True)
class NginxUpdateResult:
    status: str
    message: str
    preview: str | None = None


class PortConflictError(RuntimeError):
    def __init__(self, conflict_conf: str) -> None:
        super().__init__(f"port_conflict: conflict_conf={conflict_conf}")
        self.conflict_conf = conflict_conf


def _ssh_target(settings: Settings) -> str | None:
    host = settings.env_host
    if not host:
        return None
    user = settings.ssh_user
    if user:
        return f"{user}@{host}"
    return host


def _ssh_control_path(settings: Settings) -> str:
    target = _ssh_target(settings) or "unknown"
    port = settings.ssh_port or 22
    digest = hashlib.sha1(f"{target}:{port}".encode("utf-8")).hexdigest()[:12]
    return f"/tmp/sitehub-ssh-{digest}"


def _ssh_base_args(settings: Settings) -> list[str]:
    args = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={int(settings.ssh_connect_timeout_s)}",
        "-o",
        "ConnectionAttempts=1",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "LogLevel=ERROR",
        "-o",
        "ControlMaster=auto",
        "-o",
        f"ControlPersist={SSH_CONTROL_PERSIST_S}s",
        "-o",
        f"ControlPath={_ssh_control_path(settings)}",
    ]
    if settings.ssh_private_key_path:
        args.extend(["-i", settings.ssh_private_key_path])
    if settings.ssh_port:
        args.extend(["-p", str(settings.ssh_port)])
    return args


async def _run_local_command(args: list[str], timeout_s: float) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    return proc.returncode or 0, stdout.decode(), stderr.decode()


async def _run_ssh_command(
    settings: Settings, command: str, timeout_s: float
) -> tuple[int, str, str]:
    target = _ssh_target(settings)
    if not target:
        return 255, "", "ssh_target_missing"
    _log_event("SSH", f"command={command}")
    args = _ssh_base_args(settings)
    for attempt in range(SSH_MAX_ATTEMPTS):
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
            rc = proc.returncode or 0
        except asyncio.TimeoutError:
            proc.kill()
            rc = 124
            stdout = b""
            stderr = b"ssh_timeout"
        if rc == 0:
            return rc, stdout.decode(), stderr.decode()
        if attempt < SSH_MAX_ATTEMPTS - 1:
            await asyncio.sleep(SSH_RETRY_BACKOFF_S * (attempt + 1))
            continue
        return rc, stdout.decode(), stderr.decode()
    return 255, "", "ssh_failed"


def _log_event(category: str, message: str) -> None:
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} [{category}] {message}\n")
    except Exception:
        pass


class SyncEngine:
    def __init__(
        self,
        settings: Settings,
        excludes: Iterable[str] | None = None,
        ssh_timeout_s: float | None = None,
    ) -> None:
        self.settings = settings
        self.excludes = tuple(excludes or DEFAULT_EXCLUDES)
        self.ssh_timeout_s = ssh_timeout_s or settings.ssh_connect_timeout_s

    def build_rsync_command(self, local_path: Path, remote_path: str) -> list[str]:
        ssh_args = _ssh_base_args(self.settings)
        ssh_command = " ".join(shlex.quote(arg) for arg in ssh_args)
        target = _ssh_target(self.settings)
        if not target:
            raise ValueError("ssh_target_missing")
        rsync_args = [
            "rsync",
            "-az",
            "--delete-delay",
            "--chmod=D755,F644",
        ]
        for item in self.excludes:
            rsync_args.append(f"--exclude={item}")
        rsync_args.extend(["-e", ssh_command])
        source = f"{local_path.as_posix().rstrip('/')}/"
        destination = f"{target}:{remote_path}"
        rsync_args.extend([source, destination])
        return rsync_args

    def build_scp_command(self, local_path: Path, remote_path: str) -> list[str]:
        target = _ssh_target(self.settings)
        if not target:
            raise ValueError("ssh_target_missing")
        scp_args = ["scp", "-r"]
        scp_args.extend(_ssh_base_args(self.settings)[1:])
        destination = f"{target}:{remote_path}"
        scp_args.extend([str(local_path), destination])
        return scp_args

    async def ensure_remote_absent(self, remote_path: str) -> None:
        command = f"test -e {shlex.quote(remote_path)} && echo exists || true"
        rc, stdout, _ = await _run_ssh_command(self.settings, command, self.ssh_timeout_s)
        if rc == 0 and stdout.strip() == "exists":
            raise FileExistsError(f"remote_path_exists: {remote_path}")
        if rc != 0:
            raise RuntimeError(f"remote_check_failed: {remote_path}")

    async def sync(self, local_path: Path, remote_path: str, timeout_s: float = 300.0) -> SyncResult:
        await self.ensure_remote_absent(remote_path)
        rsync_args = self.build_rsync_command(local_path, remote_path)
        rc, stdout, stderr = await _run_local_command(rsync_args, timeout_s)
        if rc == 0:
            return SyncResult(method="rsync", stdout=stdout, stderr=stderr)
        if "command not found" in stderr or rc == 127:
            return await self._fallback_scp(local_path, remote_path, timeout_s)
        raise RuntimeError(f"rsync_failed: {stderr.strip() or rc}")

    async def _fallback_scp(
        self, local_path: Path, remote_path: str, timeout_s: float
    ) -> SyncResult:
        parent = str(PurePosixPath(remote_path).parent)
        mkdir_cmd = f"mkdir -p {shlex.quote(parent)}"
        rc, _, stderr = await _run_ssh_command(self.settings, mkdir_cmd, self.ssh_timeout_s)
        if rc != 0:
            raise RuntimeError(f"remote_mkdir_failed: {stderr.strip() or rc}")
        with tempfile.TemporaryDirectory(prefix="sitehub-sync-") as tmp_dir:
            tmp_root = Path(tmp_dir) / local_path.name
            self._copy_with_excludes(local_path, tmp_root)
            scp_args = self.build_scp_command(tmp_root, remote_path)
            rc, stdout, stderr = await _run_local_command(scp_args, timeout_s)
            if rc != 0:
                raise RuntimeError(f"scp_failed: {stderr.strip() or rc}")
            await self.fix_remote_permissions(remote_path)
            return SyncResult(method="scp", stdout=stdout, stderr=stderr)

    async def fix_remote_permissions(self, remote_path: str) -> None:
        owner = self.settings.ssh_user or "MomoWen"
        owner_quoted = shlex.quote(owner)
        _log_event("NGINX", f"action=perm_fix status=begin path={remote_path} owner={owner}")
        owner_cmd = f"stat -c %U {shlex.quote(remote_path)}"
        mode_cmd = f"stat -c %a {shlex.quote(remote_path)}"
        rc_owner, stdout_owner, _ = await _run_ssh_command(
            self.settings, owner_cmd, self.ssh_timeout_s
        )
        rc_mode, stdout_mode, _ = await _run_ssh_command(
            self.settings, mode_cmd, self.ssh_timeout_s
        )
        if rc_owner == 0 and rc_mode == 0:
            if stdout_owner.strip() == owner and stdout_mode.strip() == "755":
                _log_event("NGINX", f"action=perm_fix status=success method=precheck path={remote_path}")
                return
        chmod_cmd = f"chmod -R 755 {shlex.quote(remote_path)}"
        _log_event("NGINX", f"action=perm_fix detail=chmod_cmd value={chmod_cmd}")
        rc, _, stderr = await _run_ssh_command(self.settings, chmod_cmd, self.ssh_timeout_s)
        if rc != 0:
            reason = stderr.strip() or rc
            rc_owner, stdout_owner, _ = await _run_ssh_command(
                self.settings, owner_cmd, self.ssh_timeout_s
            )
            rc_mode, stdout_mode, _ = await _run_ssh_command(
                self.settings, mode_cmd, self.ssh_timeout_s
            )
            if rc_owner == 0 and rc_mode == 0:
                if stdout_owner.strip() == owner and stdout_mode.strip() == "755":
                    _log_event(
                        "NGINX",
                        f"action=perm_fix status=success method=postcheck path={remote_path}",
                    )
                    return
            _log_event(
                "NGINX",
                f"action=perm_fix status=failed method=chmod path={remote_path} reason={reason}",
            )
            raise RuntimeError(f"permission_fix_failed: {reason}")

        rc, stdout, stderr = await _run_ssh_command(self.settings, owner_cmd, self.ssh_timeout_s)
        if rc != 0:
            raise RuntimeError(f"permission_owner_check_failed: {stderr.strip() or rc}")
        current_owner = stdout.strip()
        if current_owner != owner:
            chown_cmd = f"chown -R {owner_quoted} {shlex.quote(remote_path)}"
            sudo_chown = f"sudo -n {chown_cmd}"
            rc, _, sudo_err = await _run_ssh_command(self.settings, sudo_chown, self.ssh_timeout_s)
            if rc != 0:
                reason = sudo_err.strip() or rc
                _log_event(
                    "NGINX",
                    f"action=perm_fix status=failed method=sudo path={remote_path} reason={reason}",
                )
                raise RuntimeError(f"permission_fix_failed: {reason}")

        _log_event("NGINX", f"action=perm_fix status=success path={remote_path}")

    def _copy_with_excludes(self, source: Path, destination: Path) -> None:
        excludes = set(self.excludes)

        def ignore(path: str, names: list[str]) -> list[str]:
            return [name for name in names if name in excludes]

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            Path(source).expanduser().resolve(),
            destination,
            ignore=ignore,
            dirs_exist_ok=False,
        )

    async def read_remote_sitehub_yaml(self, remote_root: str) -> tuple[dict[str, Any] | None, str | None]:
        yaml_path = f"{remote_root.rstrip('/')}/sitehub.yaml"
        rc, stdout, stderr = await _run_ssh_command(
            self.settings, f"cat {shlex.quote(yaml_path)}", self.ssh_timeout_s
        )
        if rc != 0:
            return None, "sitehub_yaml_missing"
        data = yaml.safe_load(stdout)
        if data is None or not isinstance(data, dict):
            return None, "sitehub_yaml_invalid"
        try:
            validated = SitehubYaml.model_validate(data)
        except Exception:
            return None, "sitehub_yaml_invalid"
        return validated.model_dump(mode="python", exclude_none=True), None

    def render_nginx_config(
        self, name: str, port: int, mode: str = "proxy", external_port: int | None = None
    ) -> str:
        if external_port is not None:
            return (
                "server {\n"
                f"  listen {external_port};\n"
                "  server_name _;\n"
                f"  root {DEFAULT_NGINX_SITE_ROOT}/{name};\n"
                "  index index.html index.htm;\n"
                "  location / {\n"
                "    try_files $uri $uri/ =404;\n"
                "  }\n"
                "}\n"
            )
        if mode == "static":
            return (
                "server {\n"
                "  listen 80;\n"
                f"  server_name {name};\n"
                f"  root {DEFAULT_NGINX_SITE_ROOT}/{name};\n"
                "  index index.html;\n"
                "  location / {\n"
                "    try_files $uri $uri/ =404;\n"
                "  }\n"
                "}\n"
            )
        return (
            "server {\n"
            "  listen 80;\n"
            f"  server_name {name};\n"
            "  location / {\n"
            f"    proxy_pass http://127.0.0.1:{port};\n"
            "    proxy_set_header Host $host;\n"
            "    proxy_set_header X-Real-IP $remote_addr;\n"
            "    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            "  }\n"
            "}\n"
        )

    async def push_nginx_config(
        self,
        remote_root: str,
        config_text: str,
        name: str,
        use_sudo: bool = False,
    ) -> NginxUpdateResult:
        tmp_path = f"/tmp/sitehub-{name}.conf"
        dest_dir = self.settings.nginx_conf_dir or DEFAULT_NGINX_CONF_DIR
        dest_path = f"{dest_dir.rstrip('/')}/{name}.conf"
        write_cmd = f"cat > {shlex.quote(tmp_path)}"
        rc, _, stderr = await self._run_ssh_with_stdin(write_cmd, config_text)
        if rc != 0:
            return NginxUpdateResult(status="error", message=f"tmp_write_failed: {stderr}")
        script_path = f"{remote_root.rstrip('/')}/scripts/nginx-safe-update.sh"
        apply_cmd = (
            f"bash {shlex.quote(script_path)} --src {shlex.quote(tmp_path)} "
            f"--dest {shlex.quote(dest_path)}"
        )
        if use_sudo:
            apply_cmd = f"sudo -n {apply_cmd}"
        rc, stdout, stderr = await _run_ssh_command(self.settings, apply_cmd, self.ssh_timeout_s)
        if rc == 0:
            return NginxUpdateResult(status="ok", message=stdout.strip() or "nginx_updated")
        await self._backup_remote_config(dest_path, use_sudo)
        if use_sudo:
            return NginxUpdateResult(
                status="error",
                message=(
                    "nginx_update_failed: sudo -n failed or update error; "
                    "configure passwordless sudo for nginx-related commands"
                ),
            )
        return NginxUpdateResult(status="error", message=stderr.strip() or "nginx_update_failed")

    async def _backup_remote_config(self, dest_path: str, use_sudo: bool) -> None:
        timestamp = time.strftime("%Y%m%d%H%M%S")
        backup_path = f"{dest_path}.bak.{timestamp}"
        base_cmd = (
            f"if [ -f {shlex.quote(dest_path)} ]; then "
            f"cp -a {shlex.quote(dest_path)} {shlex.quote(backup_path)}; fi"
        )
        if use_sudo:
            base_cmd = f"sudo -n {base_cmd}"
        await _run_ssh_command(self.settings, base_cmd, self.ssh_timeout_s)

    async def _run_ssh_with_stdin(self, command: str, content: str) -> tuple[int, str, str]:
        target = _ssh_target(self.settings)
        if not target:
            return 255, "", "ssh_target_missing"
        _log_event("SSH", f"command={command}")
        args = _ssh_base_args(self.settings)
        proc = await asyncio.create_subprocess_exec(
            *args,
            target,
            "bash",
            "-lc",
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(content.encode())
        return proc.returncode or 0, stdout.decode(), stderr.decode()


class NginxEngine:
    def __init__(
        self,
        settings: Settings,
        remote_conf_dir: str | None = None,
        ssh_timeout_s: float | None = None,
    ) -> None:
        self.settings = settings
        self.remote_conf_dir = remote_conf_dir or DEFAULT_NGINX_REMOTE_CONF_DIR
        self.ssh_timeout_s = ssh_timeout_s or settings.ssh_connect_timeout_s

    def _extract_listen_ports(self, content: str) -> set[int]:
        ports: set[int] = set()
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for match in LISTEN_PORT_RE.finditer(stripped):
                try:
                    ports.add(int(match.group(1)))
                except ValueError:
                    continue
        return ports

    def _is_same_app_conf(self, conf_path: str, content: str, app_name: str) -> bool:
        conf_name = Path(conf_path).name
        if conf_name.startswith(app_name):
            return True
        return f"root {DEFAULT_NGINX_SITE_ROOT}/{app_name};" in content

    async def _list_conf_paths(self) -> list[str]:
        conf_dir = self.settings.nginx_conf_dir or DEFAULT_NGINX_CONF_DIR
        cmd = f"ls -1 {shlex.quote(conf_dir.rstrip('/'))}/*.conf 2>/dev/null || true"
        rc, stdout, _ = await _run_ssh_command(self.settings, cmd, self.ssh_timeout_s)
        if rc != 0 and not stdout.strip():
            return []
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    async def _read_conf(self, conf_path: str) -> str | None:
        cmd = f"cat {shlex.quote(conf_path)}"
        rc, stdout, _ = await _run_ssh_command(self.settings, cmd, self.ssh_timeout_s)
        if rc != 0:
            return None
        return stdout

    async def ensure_external_port_available(self, app_name: str, external_port: int) -> int:
        if not (8400 <= external_port <= 8500):
            raise PortRangeError("external_port_out_of_range: expected 8400-8500")
        conf_paths = await self._list_conf_paths()
        for conf_path in conf_paths:
            content = await self._read_conf(conf_path)
            if content is None:
                continue
            ports = self._extract_listen_ports(content)
            if external_port not in ports:
                continue
            if self._is_same_app_conf(conf_path, content, app_name):
                return external_port
            raise PortConflictError(Path(conf_path).name)
        return external_port

    def parse_sitehub_yaml(self, sitehub_path: Path) -> dict[str, Any]:
        data = yaml.safe_load(sitehub_path.read_text(encoding="utf-8"))
        if data is None or not isinstance(data, dict):
            raise ValueError("sitehub_yaml_invalid")
        validated = SitehubYaml.model_validate(data)
        return validated.model_dump(mode="python", exclude_none=True)

    def render_config(
        self, name: str, port: int, mode: str = "proxy", external_port: int | None = None
    ) -> str:
        if external_port is not None:
            return (
                "server {\n"
                f"  listen {external_port};\n"
                "  server_name _;\n"
                f"  root {DEFAULT_NGINX_SITE_ROOT}/{name};\n"
                "  index index.html index.htm;\n"
                "  location / {\n"
                "    try_files $uri $uri/ =404;\n"
                "  }\n"
                "}\n"
            )
        if mode == "static":
            return (
                "server {\n"
                "  listen 80;\n"
                f"  server_name {name};\n"
                f"  root {DEFAULT_NGINX_SITE_ROOT}/{name};\n"
                "  index index.html;\n"
                "  location / {\n"
                "    try_files $uri $uri/ =404;\n"
                "  }\n"
                "}\n"
            )
        return (
            "server {\n"
            "  listen 80;\n"
            f"  server_name {name};\n"
            "  location / {\n"
            f"    proxy_pass http://127.0.0.1:{port};\n"
            "    proxy_set_header Host $host;\n"
            "    proxy_set_header X-Real-IP $remote_addr;\n"
            "    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
            "  }\n"
            "}\n"
        )

    async def push_config(self, config_text: str, app_name: str) -> None:
        conf_path = f"{self.remote_conf_dir.rstrip('/')}/{app_name}.conf"
        command = f"cat > {shlex.quote(conf_path)}"
        rc, _, stderr = await self._run_ssh_with_stdin(command, config_text)
        if rc != 0:
            raise RuntimeError(f"nginx_conf_write_failed: {stderr.strip() or rc}")

    async def reload(self) -> None:
        test_cmd = "docker exec sitehub-nginx nginx -t"
        rc, _, stderr = await _run_ssh_command(self.settings, test_cmd, self.ssh_timeout_s)
        if rc != 0:
            raise RuntimeError(f"nginx_test_failed: {stderr.strip() or rc}")
        command = "docker exec sitehub-nginx nginx -s reload"
        rc, _, stderr = await _run_ssh_command(self.settings, command, self.ssh_timeout_s)
        if rc != 0:
            raise RuntimeError(f"nginx_reload_failed: {stderr.strip() or rc}")

    async def apply_from_sitehub(self, sitehub_path: Path) -> None:
        config = self.parse_sitehub_yaml(sitehub_path)
        name_value = config.get("name")
        name = str(name_value) if name_value is not None else "unknown"
        port_value = config.get("port")
        if isinstance(port_value, int):
            port = port_value
        elif isinstance(port_value, str):
            port = int(port_value)
        else:
            raise ValueError("port_invalid")
        mode_value = config.get("mode")
        mode = str(mode_value) if isinstance(mode_value, str) else "proxy"
        ext_value = config.get("external_port")
        assigned_port: int | None = None
        if isinstance(ext_value, int):
            assigned_port = await self.ensure_external_port_available(name, ext_value)
        elif isinstance(ext_value, str):
            assigned_port = await self.ensure_external_port_available(name, int(ext_value))
        conf_text = self.render_config(name, port, mode, assigned_port)
        await self.push_config(conf_text, name)
        await self.reload()

    async def _run_ssh_with_stdin(self, command: str, content: str) -> tuple[int, str, str]:
        target = _ssh_target(self.settings)
        if not target:
            return 255, "", "ssh_target_missing"
        _log_event("SSH", f"command={command}")
        args = _ssh_base_args(self.settings)
        proc = await asyncio.create_subprocess_exec(
            *args,
            target,
            "bash",
            "-lc",
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(content.encode())
        return proc.returncode or 0, stdout.decode(), stderr.decode()


def build_nginx_preview(name: str, port: int, external_port: int | None = None) -> str:
    engine = NginxEngine(load_settings())
    return engine.render_config(name, port, external_port=external_port)
