"""Chunk text → Ollama embeddings → Qdrant upsert. Shared by scripts/ingest.py and KB admin GUI."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

DEFAULT_CHUNK_SIZE = 600
DEFAULT_CHUNK_OVERLAP = 80

SourceLabel = Literal["faq", "website", "manual"]


def collection_name(client_id: str) -> str:
    s = client_id.strip().lower()
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        raise ValueError("client_id becomes empty after sanitization")
    return s[:256]


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(lines)


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be in [0, size)")
    text = normalize_whitespace(text)
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = end - overlap
    return chunks


def point_id(client_id: str, index: int, text: str) -> str:
    payload = f"{client_id}\0{index}\0{text}".encode("utf-8")
    return str(uuid.UUID(hashlib.sha256(payload).hexdigest()[:32]))


def embed_one(client: httpx.Client, base: str, model: str, prompt: str) -> list[float]:
    r = client.post(
        f"{base.rstrip('/')}/api/embeddings",
        json={"model": model, "prompt": prompt},
        timeout=120.0,
    )
    r.raise_for_status()
    data = r.json()
    vec = data.get("embedding")
    if not isinstance(vec, list):
        raise RuntimeError("Ollama response missing embedding list")
    return vec


def ensure_collection(
    qc: QdrantClient,
    name: str,
    vector_size: int,
) -> None:
    exists = False
    try:
        qc.get_collection(name)
        exists = True
    except Exception:
        exists = False
    if exists:
        info = qc.get_collection(name)
        params = info.config.params
        vs = getattr(params.vectors, "size", None) if params and params.vectors else None
        if vs is not None and vs != vector_size:
            raise RuntimeError(
                f"Collection {name!r} has vector size {vs}, expected {vector_size}"
            )
        return
    qc.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
    )


def _qdrant_client() -> QdrantClient:
    qdrant_url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    api_key = os.environ.get("QDRANT_API_KEY") or None
    return QdrantClient(url=qdrant_url, api_key=api_key)


def _ollama_settings() -> tuple[str, str]:
    ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    embed_model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
    return ollama_host, embed_model


@dataclass
class IngestResult:
    collection: str
    points_upserted: int
    qdrant_url: str
    client_id: str


def ingest_text(
    client_id: str,
    text: str,
    *,
    source: SourceLabel = "faq",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IngestResult:
    """Chunk UTF-8 text, embed via Ollama, upsert into Qdrant. Uses QDRANT_*, OLLAMA_* from os.environ."""
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        raise ValueError("No chunks after processing; empty or whitespace-only text?")

    coll = collection_name(client_id)
    qc = _qdrant_client()
    qdrant_url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    ollama_host, embed_model = _ollama_settings()

    with httpx.Client() as http:
        first = embed_one(http, ollama_host, embed_model, chunks[0])
        dim = len(first)
        ensure_collection(qc, coll, dim)

        vectors: list[list[float]] = [first]
        for i in range(1, len(chunks)):
            vectors.append(embed_one(http, ollama_host, embed_model, chunks[i]))

        points: list[qm.PointStruct] = []
        for i, (t, vec) in enumerate(zip(chunks, vectors)):
            pid = point_id(client_id, i, t)
            points.append(
                qm.PointStruct(
                    id=pid,
                    vector=vec,
                    payload={
                        "text": t,
                        "source": source,
                        "client_id": client_id,
                        "chunk_index": i,
                    },
                )
            )

        qc.upsert(collection_name=coll, points=points, wait=True)

    return IngestResult(
        collection=coll,
        points_upserted=len(points),
        qdrant_url=qdrant_url,
        client_id=client_id,
    )


@dataclass
class SearchHit:
    score: float
    text: str
    payload: dict[str, Any]


def search_collection(
    client_id: str,
    query: str,
    *,
    limit: int = 5,
) -> list[SearchHit]:
    """Embed query and return top hits (same behavior as CLI search)."""
    coll = collection_name(client_id)
    qc = _qdrant_client()
    ollama_host, embed_model = _ollama_settings()

    with httpx.Client() as http:
        vec = embed_one(http, ollama_host, embed_model, query)

    resp = qc.query_points(
        collection_name=coll,
        query=vec,
        limit=limit,
        with_payload=True,
    )
    out: list[SearchHit] = []
    for p in resp.points:
        payload = dict(p.payload or {})
        text = str(payload.get("text", ""))
        score = float(p.score) if p.score is not None else 0.0
        out.append(SearchHit(score=score, text=text, payload=payload))
    return out


@dataclass
class CollectionInfoRow:
    name: str
    points_count: int | None
    vector_size: int | None


def list_collections_detail() -> list[CollectionInfoRow]:
    qc = _qdrant_client()
    cols = qc.get_collections().collections
    rows: list[CollectionInfoRow] = []
    for c in cols:
        name = c.name
        pc: int | None = None
        vs: int | None = None
        try:
            info = qc.get_collection(name)
            pc = getattr(info, "points_count", None)
            params = info.config.params
            vs = getattr(params.vectors, "size", None) if params and params.vectors else None
        except Exception:
            pass
        rows.append(CollectionInfoRow(name=name, points_count=pc, vector_size=vs))
    rows.sort(key=lambda r: r.name)
    return rows


def delete_collection(collection_name: str) -> None:
    """Delete a Qdrant collection by its exact name (sanitized collection slug)."""
    qc = _qdrant_client()
    qc.delete_collection(collection_name=collection_name)
