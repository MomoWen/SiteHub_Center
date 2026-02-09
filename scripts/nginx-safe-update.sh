#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/sitehub.log"
NGINX_BIN="${NGINX_BIN:-nginx}"

ts() { date +"%Y-%m-%dT%H:%M:%S%z"; }
log() { echo "$(ts) [$1] $2" >> "$LOG_FILE"; }

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/nginx-safe-update.sh --src <new.conf> --dest <live.conf> [--dry-run]

Options:
  --src PATH     Path to generated configuration file
  --dest PATH    Path to live configuration file to update
  --dry-run      Validate config without changing live configuration
USAGE
}

SRC=""
DEST=""
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --src)
      SRC="$2"
      shift 2
      ;;
    --dest)
      DEST="$2"
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

if [[ -z "$SRC" || -z "$DEST" ]]; then
  echo "ERR --src and --dest are required" >&2
  usage >&2
  exit 2
fi

if [[ ! -f "$SRC" ]]; then
  echo "ERR src not found: $SRC" >&2
  exit 2
fi

if [[ "$DRY_RUN" == "true" ]]; then
  log "NGINX" "action=dry_run status=begin src=${SRC}"
  "$NGINX_BIN" -t -c "$SRC"
  log "NGINX" "action=dry_run status=success src=${SRC}"
  echo "OK: dry-run validated: $SRC"
  exit 0
fi

if [[ ! -f "$DEST" ]]; then
  echo "ERR dest not found: $DEST" >&2
  exit 2
fi

backup="${DEST}.bak.$(date +"%Y%m%d%H%M%S")"
cp -a "$DEST" "$backup"
log "NGINX" "action=backup status=success dest=${DEST} backup=${backup}"

cp -a "$SRC" "$DEST"

if ! "$NGINX_BIN" -t; then
  cp -a "$backup" "$DEST"
  log "NGINX" "action=apply status=failed dest=${DEST} restored_from=${backup}"
  echo "ERR nginx -t failed; restored backup: $backup" >&2
  exit 3
fi

if ! "$NGINX_BIN" -s reload; then
  log "NGINX" "action=reload status=failed dest=${DEST}"
  echo "ERR nginx reload failed" >&2
  exit 4
fi

log "NGINX" "action=apply status=success dest=${DEST}"
echo "OK: applied config and reloaded nginx"
