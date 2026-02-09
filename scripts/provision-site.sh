#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/sitehub.log"

ts() { date +"%Y-%m-%dT%H:%M:%S%z"; }
log() { echo "$(ts) [$1] $2" >> "$LOG_FILE"; }

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/provision-site.sh --site <name> [--port <8085-8095>] [--sites-base <path>] [--no-venv]

Options:
  --site NAME        Site identifier (directory name)
  --port PORT        Explicit port in 8085-8095 (optional)
  --sites-base PATH  Base directory (default: /vol1/1000/MyDocker/web-cluster/sites)
  --no-venv          Skip virtualenv initialization
USAGE
}

SITE_NAME=""
EXPLICIT_PORT=""
SITES_BASE="/vol1/1000/MyDocker/web-cluster/sites"
INIT_VENV="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --site)
      SITE_NAME="$2"
      shift 2
      ;;
    --port)
      EXPLICIT_PORT="$2"
      shift 2
      ;;
    --sites-base)
      SITES_BASE="$2"
      shift 2
      ;;
    --no-venv)
      INIT_VENV="false"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERR unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$SITE_NAME" ]]; then
  echo "ERR --site is required" >&2
  usage >&2
  exit 2
fi

if [[ ! "$SITE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*$ ]]; then
  echo "ERR invalid site name: $SITE_NAME" >&2
  exit 2
fi

site_dir="${SITES_BASE}/${SITE_NAME}"
env_file="${site_dir}/sitehub.env"
venv_dir="${site_dir}/.venv"

mkdir -p "$site_dir"

read_existing_port() {
  if [[ -f "$env_file" ]]; then
    local value
    value="$(grep -E '^PORT=' "$env_file" | head -n1 | cut -d= -f2- || true)"
    if [[ -n "$value" ]]; then
      echo "$value"
      return 0
    fi
  fi
  return 1
}

PYTHON_BIN="${PYTHON_BIN:-python3}"

port_available() {
  local port="$1"
  "$PYTHON_BIN" - "$port" <<'PY'
import socket
import sys

p = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", p))
except OSError:
    sys.exit(1)
finally:
    s.close()
sys.exit(0)
PY
}

validate_port_range() {
  local port="$1"
  if [[ ! "$port" =~ ^[0-9]+$ ]]; then
    return 1
  fi
  if [[ "$port" -lt 8085 || "$port" -gt 8095 ]]; then
    return 1
  fi
  return 0
}

selected_port=""

if [[ -n "$EXPLICIT_PORT" ]]; then
  if ! validate_port_range "$EXPLICIT_PORT"; then
    echo "ERR --port must be within 8085-8095" >&2
    exit 2
  fi
  if ! port_available "$EXPLICIT_PORT"; then
    echo "ERR port already in use: $EXPLICIT_PORT" >&2
    exit 3
  fi
  selected_port="$EXPLICIT_PORT"
else
  if existing="$(read_existing_port || true)"; then
    if validate_port_range "$existing"; then
      selected_port="$existing"
    fi
  fi

  if [[ -z "$selected_port" ]]; then
    for p in $(seq 8085 8095); do
      if port_available "$p"; then
        selected_port="$p"
        break
      fi
    done
  fi

  if [[ -z "$selected_port" ]]; then
    echo "ERR no available ports in range 8085-8095" >&2
    exit 3
  fi
fi

{
  echo "SITE_NAME=${SITE_NAME}"
  echo "PORT=${selected_port}"
} > "$env_file"

if [[ "$INIT_VENV" == "true" ]]; then
  if [[ -d "$venv_dir" ]]; then
    echo "OK: venv already exists: $venv_dir"
  else
    "$PYTHON_BIN" -m venv "$venv_dir"
    echo "OK: created venv: $venv_dir"
  fi
fi

echo "OK: provisioned site_dir=${site_dir} port=${selected_port}"
log "PROVISION" "status=success site=${SITE_NAME} site_dir=${site_dir} port=${selected_port}"
