"""Knowledge-base ingestion shared by CLI and KB admin GUI."""

from kb.ingest_pipeline import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    collection_name,
    delete_collection,
    ingest_text,
    list_collections_detail,
    search_collection,
)
from kb.upload_parse import maybe_parse_pasted_json, normalized_text_from_upload

__all__ = [
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_CHUNK_SIZE",
    "collection_name",
    "delete_collection",
    "ingest_text",
    "list_collections_detail",
    "maybe_parse_pasted_json",
    "normalized_text_from_upload",
    "search_collection",
]
