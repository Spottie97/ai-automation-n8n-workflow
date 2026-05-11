"""Convert uploaded file bytes to a single UTF-8 string for `ingest_text`. Supports .txt and .json."""

from __future__ import annotations

import json
from typing import Any


def _piece_from_mapping(obj: dict[str, Any]) -> str | None:
    """Extract one text blob from a JSON object (FAQ row, article, etc.)."""
    if not isinstance(obj, dict):
        return None
    for key in ("text", "content", "body", "markdown"):
        v = obj.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    q = obj.get("question") or obj.get("q") or obj.get("title")
    a = obj.get("answer") or obj.get("a") or obj.get("summary")
    parts = []
    if isinstance(q, str) and q.strip():
        parts.append(q.strip())
    if isinstance(a, str) and a.strip():
        parts.append(a.strip())
    if parts:
        return "\n\n".join(parts)
    return None


def _flatten_json_value(value: Any) -> list[str]:
    """Turn arbitrary JSON into a list of text segments (later joined)."""
    out: list[str] = []
    if value is None:
        return out
    if isinstance(value, str):
        if value.strip():
            out.append(value.strip())
        return out
    if isinstance(value, (int, float, bool)):
        out.append(str(value))
        return out
    if isinstance(value, list):
        for item in value:
            out.extend(_flatten_json_value(item))
        return out
    if isinstance(value, dict):
        for key in ("chunks", "items", "documents", "entries", "faqs", "pages", "articles"):
            if key in value:
                out.extend(_flatten_json_value(value[key]))
                return out
        piece = _piece_from_mapping(value)
        if piece:
            out.append(piece)
        else:
            for v in value.values():
                if isinstance(v, (list, dict)):
                    out.extend(_flatten_json_value(v))
                elif isinstance(v, str) and v.strip():
                    out.append(v.strip())
        return out
    return out


def json_payload_to_text(raw_json: str) -> str:
    """
    Parse JSON and merge into one document string for chunking.

    Supported shapes (non-exhaustive):
    - A single string
    - Array of strings
    - Array of objects with text/content/body or question+answer
    - Object with chunks | items | documents | entries | faqs | pages | articles → array
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
    parts = _flatten_json_value(data)
    if not parts:
        raise ValueError("JSON parsed but no text fields were found (expected strings or objects with text/content/body or question/answer).")
    merged = "\n\n---\n\n".join(parts)
    if not merged.strip():
        raise ValueError("JSON produced only empty text after flattening.")
    return merged


def normalized_text_from_upload(data: bytes, filename: str) -> str:
    """
    Decode upload. If filename ends with .json, flatten JSON to text; otherwise raw UTF-8 text.
    """
    name = (filename or "").strip().lower()
    text = data.decode("utf-8", errors="replace")
    if name.endswith(".json"):
        return json_payload_to_text(text)
    return text


def maybe_parse_pasted_json(text: str) -> str:
    """
    If the pasted string looks like JSON (starts with { or [), try to flatten it;
    on failure or if not JSON-shaped, return original text.
    """
    stripped = text.lstrip()
    if not stripped or stripped[0] not in "[{":
        return text
    try:
        return json_payload_to_text(text)
    except ValueError:
        return text
