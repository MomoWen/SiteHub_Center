#!/usr/bin/env bash
set -euo pipefail
PM="${1:-}"
shift || true
ARGS=("$@")
PREFER_CACHE="${prefer_cache:-true}"
PROXY_GATEWAY="${PROXY_GATEWAY:-http://10.8.8.80:7890}"
ALLOW_DIRECT="${ALLOW_DIRECT:-false}"
if [[ -z "${CACHE_SERVER:-}" ]]; then
  case "$PM" in
    pip) CACHE_SERVER="http://10.8.8.80:3141/root/pypi/+simple/" ;;
    npm|pnpm) CACHE_SERVER="http://10.8.8.80:4873/" ;;
    *) CACHE_SERVER="" ;;
  esac
fi
LOG_FILE="${PWD}/sitehub.log"
ts() { date +"%Y-%m-%dT%H:%M:%S%z"; }
log() { echo "$(ts) [$1] $2" >> "$LOG_FILE"; }
MODE=""
trap 'log "DEPENDENCY" "status=failed pm=${PM:-} mode=${MODE:-}";' ERR
if [[ -z "$PM" ]]; then
  echo "ERR package_manager required: pip|npm|pnpm" >&2
  exit 2
fi
log "DEPENDENCY" "status=begin pm=${PM}"
if [[ "$PREFER_CACHE" == "true" && -n "$CACHE_SERVER" ]]; then
  if curl -I -s --connect-timeout 2 "$CACHE_SERVER" | head -n1 | grep -E "HTTP/.* (200|302)" >/dev/null; then
    MODE="CACHE"
  else
    if curl -I -s --connect-timeout 2 "$PROXY_GATEWAY" | head -n1 | grep -E "HTTP/.* (200|302)" >/dev/null; then
      MODE="PROXY"
    else
      if [[ "$ALLOW_DIRECT" == "true" ]]; then
        MODE="DIRECT"
      else
        echo "ERR network unreachable: cache and proxy failed" >&2
        exit 3
      fi
    fi
  fi
else
  if curl -I -s --connect-timeout 2 "$PROXY_GATEWAY" | head -n1 | grep -E "HTTP/.* (200|302)" >/dev/null; then
    MODE="PROXY"
  else
    if [[ "$ALLOW_DIRECT" == "true" ]]; then
      MODE="DIRECT"
    else
      echo "ERR proxy unreachable" >&2
      exit 3
    fi
  fi
fi
if [[ -f "requirements.txt" ]]; then
  if grep -E -i "mirrors\.aliyun\.com|tsinghua\.edu\.cn" requirements.txt >/dev/null; then
    echo "ERR forbidden domestic mirror in requirements.txt" >&2
    exit 4
  fi
fi
for f in package.json package-lock.json pnpm-lock.yaml yarn.lock .npmrc .yarnrc .yarnrc.yml pnpm-workspace.yaml pyproject.toml poetry.lock setup.cfg pip.conf; do
  if [[ -f "$f" ]]; then
    if grep -E -i "mirrors\.aliyun\.com|tsinghua\.edu\.cn" "$f" >/dev/null; then
      echo "ERR forbidden domestic mirror in ${f}" >&2
      exit 4
    fi
  fi
done
if [[ "$MODE" == "CACHE" ]]; then
  log "DEPENDENCY" "Strategy: CACHE, Source: ${CACHE_SERVER}"
  case "$PM" in
    pip)
      pip install --index-url "${CACHE_SERVER}" --trusted-host 10.8.8.80 "${ARGS[@]}"
      ;;
    npm)
      npm config set registry "${CACHE_SERVER}" --location project
      npm install "${ARGS[@]}"
      ;;
    pnpm)
      pnpm config set registry "${CACHE_SERVER}"
      pnpm install "${ARGS[@]}"
      ;;
    *)
      echo "ERR unsupported package_manager: $PM" >&2
      exit 2
      ;;
  esac
elif [[ "$MODE" == "PROXY" ]]; then
  log "DEPENDENCY" "Strategy: PROXY, Source: https://official"
  export http_proxy="${PROXY_GATEWAY}"
  export https_proxy="${PROXY_GATEWAY}"
  export all_proxy="socks5://10.8.8.80:7891"
  case "$PM" in
    pip)
      pip install --index-url "https://pypi.org/simple" "${ARGS[@]}"
      ;;
    npm)
      npm config set registry "https://registry.npmjs.org" --location project
      npm install "${ARGS[@]}"
      ;;
    pnpm)
      pnpm config set registry "https://registry.npmjs.org"
      pnpm install "${ARGS[@]}"
      ;;
    *)
      echo "ERR unsupported package_manager: $PM" >&2
      exit 2
      ;;
  esac
else
  log "DEPENDENCY" "Strategy: DIRECT, Source: https://official"
  case "$PM" in
    pip)
      pip install --index-url "https://pypi.org/simple" "${ARGS[@]}"
      ;;
    npm)
      npm config set registry "https://registry.npmjs.org" --location project
      npm install "${ARGS[@]}"
      ;;
    pnpm)
      pnpm config set registry "https://registry.npmjs.org"
      pnpm install "${ARGS[@]}"
      ;;
    *)
      echo "ERR unsupported package_manager: $PM" >&2
      exit 2
      ;;
  esac
fi
log "DEPENDENCY" "status=success pm=${PM} mode=${MODE}"
