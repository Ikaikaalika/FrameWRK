#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

echo "[offline-eval] Running backend test suite"
PYTHONPATH=backend pytest -q

echo "[offline-eval] Building frontend for production"
npm --prefix frontend run build

echo "[offline-eval] Offline evaluation complete"
