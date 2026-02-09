#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/sitehub.log"

ts() { date +"%Y-%m-%dT%H:%M:%S%z"; }
log() { echo "$(ts) [$1] $2" >> "$LOG_FILE"; }

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/deploy.sh [--source PATH] [--site-root PATH] [--keep N] [--dry-run]
  bash scripts/deploy.sh --rollback <timestamp> [--site-root PATH] [--dry-run]

Options:
  --source PATH      Source directory to deploy (default: repo root)
  --site-root PATH   Target directory containing releases/ and current (default: repo root)
  --keep N           Number of releases to keep (default: 5)
  --rollback TS      Switch current to releases/TS
  --dry-run          Print planned actions without changing filesystem
USAGE
}

SOURCE_DIR="$ROOT_DIR"
SITE_ROOT="$ROOT_DIR"
KEEP="5"
ROLLBACK_TS=""
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --site-root)
      SITE_ROOT="$2"
      shift 2
      ;;
    --keep)
      KEEP="$2"
      shift 2
      ;;
    --rollback)
      ROLLBACK_TS="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
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

if [[ ! "$KEEP" =~ ^[0-9]+$ ]] || [[ "$KEEP" -lt 1 ]]; then
  echo "ERR --keep must be a positive integer" >&2
  exit 2
fi

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "ERR source dir not found: $SOURCE_DIR" >&2
  exit 2
fi

if [[ ! -d "$SITE_ROOT" ]]; then
  echo "ERR site root not found: $SITE_ROOT" >&2
  exit 2
fi

require_file() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "ERR missing required path: $path" >&2
    exit 3
  fi
}

require_file "${SOURCE_DIR}/src"
require_file "${SOURCE_DIR}/src/sitehub/main.py"
require_file "${SOURCE_DIR}/scripts/run.sh"

atomic_symlink() {
  local target="$1"
  local link_path="$2"
  local tmp_link="${link_path}.tmp"
  rm -f "$tmp_link"
  ln -s "$target" "$tmp_link"
  mv -Tf "$tmp_link" "$link_path"
}

rollback() {
  local ts_id="$1"
  local release_dir="${SITE_ROOT}/releases/${ts_id}"
  if [[ ! -d "$release_dir" ]]; then
    echo "ERR release not found: ${release_dir}" >&2
    exit 4
  fi

  echo "Plan: switch current -> ${release_dir}"
  if [[ "$DRY_RUN" == "true" ]]; then
    exit 0
  fi

  atomic_symlink "$release_dir" "${SITE_ROOT}/current"
  log "DEPLOY" "action=rollback status=success release=${ts_id} site_root=${SITE_ROOT}"
}

deploy() {
  local ts_id
  ts_id="$(date +"%Y%m%d%H%M%S")"
  local release_dir="${SITE_ROOT}/releases/${ts_id}"

  echo "Plan: create release ${release_dir}"
  echo "Plan: copy source ${SOURCE_DIR} -> ${release_dir}"
  echo "Plan: switch current -> ${release_dir}"

  if [[ "$DRY_RUN" == "true" ]]; then
    exit 0
  fi

  mkdir -p "${SITE_ROOT}/releases"
  mkdir -p "$release_dir"

  (
    cd "$SOURCE_DIR"
    tar \
      --exclude=".git" \
      --exclude=".venv" \
      --exclude="releases" \
      --exclude="current" \
      --exclude="openspec" \
      --exclude=".trae" \
      --exclude="sitehub.log" \
      -cf - .
  ) | (cd "$release_dir" && tar -xf -)

  atomic_symlink "$release_dir" "${SITE_ROOT}/current"
  log "DEPLOY" "action=deploy status=success release=${ts_id} site_root=${SITE_ROOT} source=${SOURCE_DIR}"

  local releases
  releases="$(ls -1 "${SITE_ROOT}/releases" | sort)"
  local count
  count="$(echo "$releases" | sed '/^$/d' | wc -l | tr -d ' ')"
  if [[ "$count" -le "$KEEP" ]]; then
    exit 0
  fi

  local to_delete
  to_delete="$(echo "$releases" | head -n "$(($count - $KEEP))")"
  while read -r rel; do
    [[ -z "$rel" ]] && continue
    rm -rf "${SITE_ROOT}/releases/${rel}"
    log "DEPLOY" "action=cleanup status=success release=${rel} site_root=${SITE_ROOT}"
  done <<< "$to_delete"
}

if [[ -n "$ROLLBACK_TS" ]]; then
  rollback "$ROLLBACK_TS"
else
  deploy
fi
