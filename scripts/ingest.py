#!/usr/bin/env python3
"""Chunk text → Ollama embeddings → Qdrant upsert. One collection per client."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Repo root on path for `kb` package when running as scripts/ingest.py
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kb.ingest_pipeline import (  # noqa: E402
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    collection_name,
    embed_one,
    ingest_text,
    search_collection,
)


def cmd_ingest(args: argparse.Namespace) -> int:
    load_dotenv()
    path = Path(args.input)
    if not path.is_file():
        print(f"Input not found: {path}", file=sys.stderr)
        return 1

    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        result = ingest_text(
            args.client_id,
            raw,
            source=args.source,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(
        f"Upserted {result.points_upserted} points into collection "
        f"{result.collection!r} at {result.qdrant_url}"
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    load_dotenv()
    try:
        hits = search_collection(args.client_id, args.query, limit=args.limit)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1

    if not hits:
        print("No hits.")
        return 0

    for rank, h in enumerate(hits, start=1):
        preview = h.text.replace("\n", " ")[:200]
        print(f"{rank}. score={h.score:.4f}  {preview!r}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Ingest text into Qdrant (Ollama embeddings). "
            "Point IDs are UUIDs derived from SHA-256(client_id, index, text) "
            "so re-running ingest updates the same logical chunks."
        )
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="Chunk file, embed, upsert into Qdrant")
    pi.add_argument("--client-id", required=True, help="Logical client id (sanitized for collection name)")
    pi.add_argument("--input", required=True, help="Path to UTF-8 text file")
    pi.add_argument(
        "--source",
        default="faq",
        choices=("faq", "website", "manual"),
        help="Payload source label",
    )
    pi.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    pi.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    pi.set_defaults(func=cmd_ingest)

    ps = sub.add_parser("search", help="Embed a query and print top Qdrant hits")
    ps.add_argument("--client-id", required=True)
    ps.add_argument("--query", required=True)
    ps.add_argument("--limit", type=int, default=5)
    ps.set_defaults(func=cmd_search)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
