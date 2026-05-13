#!/usr/bin/env bash
# Smoke test: stack → ingest demo_client → one RAG reply. Run from repo root with .env configured.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "error: create .venv first (see scripts/bootstrap_server.sh or docs/deploy-ai-server.md)" >&2
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "== verify_stack =="
python scripts/verify_stack.py

echo "== ingest demo_client =="
python scripts/ingest.py ingest --client-id demo_client --input sample_data/demo_faq.txt

echo "== reply_once =="
python scripts/reply_once.py --client-id demo_client --question "What are your hours?" --verbose

echo "OK demo RAG path complete."
