#!/usr/bin/env bash
# Run on the ai-server from the repository root after git clone or git pull.
# Creates .venv, installs Python deps, and seeds .env from .env.example if missing.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "Created .env from .env.example — edit URLs and model names for this host, then:"
  echo "  python scripts/verify_stack.py"
else
  echo ".env already present; skipped copy from .env.example"
  echo "Smoke test: python scripts/verify_stack.py"
fi
