#!/usr/bin/env python3
"""Check Ollama, Qdrant, and llama-server reachability using the same env vars as ingest / n8n.

Run from any machine that can reach the services (your laptop with .env, or ssh to the ai-server).
Exits 0 if all checks pass, non-zero otherwise.

Usage:
  python scripts/verify_stack.py
  python scripts/verify_stack.py --skip-llama
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx
from dotenv import load_dotenv


def ok(msg: str) -> None:
    print(f"OK  {msg}", flush=True)


def fail(msg: str) -> None:
    print(f"ERR {msg}", file=sys.stderr, flush=True)


def check_ollama(client: httpx.Client, base: str, model: str) -> bool:
    base = base.rstrip("/")
    try:
        r = client.get(f"{base}/api/tags", timeout=10.0)
        r.raise_for_status()
    except Exception as e:
        fail(f"Ollama GET {base}/api/tags: {e}")
        return False
    ok(f"Ollama reachable at {base}")
    try:
        r = client.post(
            f"{base}/api/embeddings",
            json={"model": model, "prompt": "ping"},
            timeout=120.0,
        )
        r.raise_for_status()
        data = r.json()
        emb = data.get("embedding")
        if not isinstance(emb, list) or len(emb) < 8:
            fail("Ollama embeddings response missing vector")
            return False
    except Exception as e:
        fail(f"Ollama POST /api/embeddings (model={model!r}): {e}")
        return False
    ok(f"Ollama embedding model {model!r} returns a vector (dim={len(emb)})")
    return True


def check_qdrant(client: httpx.Client, base: str) -> bool:
    base = base.rstrip("/")
    try:
        r = client.get(f"{base}/", timeout=10.0)
        r.raise_for_status()
        ok(f"Qdrant reachable at {base}")
    except Exception as e:
        fail(f"Qdrant GET {base}/: {e}")
        return False
    return True


def check_llama(client: httpx.Client, base: str) -> bool:
    base = base.rstrip("/")
    try:
        r = client.get(f"{base}/v1/models", timeout=10.0)
        r.raise_for_status()
        data = r.json()
        ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict)]
        ok(f"llama-server reachable at {base} ({len(ids)} model(s) in /v1/models)")
        if ids:
            print(f"    models: {', '.join(str(i) for i in ids[:8])}{'...' if len(ids) > 8 else ''}")
    except Exception as e:
        fail(f"llama-server GET {base}/v1/models: {e}")
        return False
    return True


def main() -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skip-llama", action="store_true", help="Do not check LLAMA_SERVER_URL")
    args = p.parse_args()

    ollama = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
    qdrant = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
    llama = os.environ.get("LLAMA_SERVER_URL", "http://127.0.0.1:8081")

    print("Using env (after .env):", flush=True)
    print(f"  OLLAMA_HOST={ollama}", flush=True)
    print(f"  OLLAMA_EMBED_MODEL={model}", flush=True)
    print(f"  QDRANT_URL={qdrant}", flush=True)
    print(f"  LLAMA_SERVER_URL={llama}", flush=True)
    print(flush=True)

    good = True
    with httpx.Client() as client:
        good = check_ollama(client, ollama, model) and good
        good = check_qdrant(client, qdrant) and good
        if not args.skip_llama:
            good = check_llama(client, llama) and good

    if good:
        print("\nAll checks passed. You can run:", flush=True)
        print("  python scripts/ingest.py ingest --client-id demo_client --input sample_data/demo_faq.txt", flush=True)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
