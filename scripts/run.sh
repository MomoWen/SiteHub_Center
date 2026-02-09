#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-${ROOT_DIR}/.venv/bin/python}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8085}"
export SITEHUB_ENV="${SITEHUB_ENV:-dev}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON}" -m uvicorn sitehub.main:app --host "${HOST}" --port "${PORT}"