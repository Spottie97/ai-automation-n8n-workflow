#!/usr/bin/env python3
"""One-shot RAG reply: embed question → Qdrant → context + system prompt → llama-server chat."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Reuse ingest helpers (same venv / project root)
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import ingest as ingest_mod  # noqa: E402

FALLBACK_REPLY = (
    "Thanks for your message. I don't have enough information to answer that automatically — "
    "a team member will follow up with you shortly."
)


def repo_root() -> Path:
    return _SCRIPTS.parent


def load_system_prompt(
    path: Path,
    client_name: str,
    business_summary: str,
    tone_notes: str,
) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # Strip markdown title / front matter before "---" if using system_template.md
    if "---" in raw:
        raw = raw.split("---", 1)[-1].strip()
    return (
        raw.replace("{{CLIENT_NAME}}", client_name)
        .replace("{{BUSINESS_SUMMARY}}", business_summary)
        .replace("{{TONE_NOTES}}", tone_notes)
    )


def build_context(hits: list, separator: str) -> str:
    parts: list[str] = []
    for h in hits:
        payload = h.payload or {}
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return separator.join(parts)


def chat_complete(
    client: httpx.Client,
    base: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str | None:
    r = client.post(
        f"{base.rstrip('/')}/v1/chat/completions",
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=180.0,
    )
    r.raise_for_status()
    data = r.json()
    choices = data.get("choices") or []
    if not choices:
        return None
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "RAG reply once: Ollama embed → Qdrant query → llama-server chat. "
            f"On failure or no context, prints: {FALLBACK_REPLY!r}"
        )
    )
    parser.add_argument("--client-id", required=True, help="Qdrant collection (same sanitize rules as ingest)")
    parser.add_argument("--question", required=True, help="Customer question text")
    parser.add_argument(
        "--system-file",
        type=Path,
        default=None,
        help="System prompt file (default: prompts/system_template.md under repo root)",
    )
    parser.add_argument(
        "--client-name",
        default="Harborview Coffee Co. (demo)",
        help="Value for {{CLIENT_NAME}} in system template",
    )
    parser.add_argument(
        "--business-summary",
        default=(
            "Local café: hours, location, menu highlights, catering, dogs, Wi‑Fi, refunds. "
            "Details live in the retrieved snippets."
        ),
        help="Value for {{BUSINESS_SUMMARY}}",
    )
    parser.add_argument(
        "--tone-notes",
        default="Professional, warm, concise.",
        help="Value for {{TONE_NOTES}}",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Qdrant hits to include in context")
    parser.add_argument("--context-separator", default="\n\n---\n\n", help="Between retrieved chunks")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Chat completion max_tokens (raise if replies truncate; some reasoning models need 512+)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print retrieval scores to stderr",
    )
    args = parser.parse_args()

    load_dotenv(repo_root() / ".env")
    load_dotenv()

    system_path = args.system_file
    if system_path is None:
        system_path = repo_root() / "prompts" / "system_template.md"
    if not system_path.is_file():
        print(f"System prompt file not found: {system_path}", file=sys.stderr)
        print(FALLBACK_REPLY)
        return 0

    import os

    ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    embed_model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
    qdrant_url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    api_key = os.environ.get("QDRANT_API_KEY") or None
    llama_url = os.environ.get("LLAMA_SERVER_URL", "").rstrip("/")
    chat_model = os.environ.get("LLAMA_CHAT_MODEL", "gemma4-e4b")

    if not llama_url:
        print("LLAMA_SERVER_URL not set", file=sys.stderr)
        print(FALLBACK_REPLY)
        return 0

    try:
        system_prompt = load_system_prompt(
            system_path,
            args.client_name,
            args.business_summary,
            args.tone_notes,
        )
    except OSError as e:
        print(f"Failed to read system file: {e}", file=sys.stderr)
        print(FALLBACK_REPLY)
        return 0

    coll = ingest_mod.collection_name(args.client_id)
    qc = QdrantClient(url=qdrant_url, api_key=api_key)

    try:
        with httpx.Client() as http:
            vec = ingest_mod.embed_one(http, ollama_host, embed_model, args.question)

            resp = qc.query_points(
                collection_name=coll,
                query=vec,
                limit=args.top_k,
                with_payload=True,
            )
            hits = list(resp.points)

            if not hits:
                print("No Qdrant hits.", file=sys.stderr)
                print(FALLBACK_REPLY)
                return 0

            if args.verbose:
                for i, h in enumerate(hits, start=1):
                    print(f"[{i}] score={h.score:.4f}", file=sys.stderr)

            context = build_context(hits, args.context_separator)
            if not context.strip():
                print("Empty context from payloads.", file=sys.stderr)
                print(FALLBACK_REPLY)
                return 0

            user_content = (
                "Use only the following retrieved context to help answer the customer.\n\n"
                f"Context:\n{context}\n\n"
                f"Customer question:\n{args.question}\n"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]

            reply = chat_complete(
                http,
                llama_url,
                chat_model,
                messages,
                max_tokens=args.max_tokens,
            )

        if reply:
            print(reply)
            return 0
        print("Empty LLM response.", file=sys.stderr)
        print(FALLBACK_REPLY)
        return 0

    except httpx.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        print(FALLBACK_REPLY)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(FALLBACK_REPLY)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
