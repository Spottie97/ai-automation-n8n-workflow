"""KB admin: manage Qdrant client collections without the terminal.

Run from repo root:
  streamlit run apps/kb_admin/app.py
Optional LAN:
  streamlit run apps/kb_admin/app.py --server.address 0.0.0.0 --server.port 8501
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kb.ingest_pipeline import (  # noqa: E402
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    SourceLabel,
    collection_name,
    delete_collection,
    ingest_text,
    list_collections_detail,
    search_collection,
)
from kb.upload_parse import maybe_parse_pasted_json, normalized_text_from_upload  # noqa: E402

st.set_page_config(page_title="KB Admin", page_icon="📚", layout="wide")

AUTH_KEY = "kb_admin_authed"


def _ensure_password() -> None:
    secret = os.environ.get("KB_ADMIN_PASSWORD", "").strip()
    if not secret:
        return
    if st.session_state.get(AUTH_KEY):
        return
    st.title("KB Admin")
    st.caption("Enter the operator password (set in `.env` as `KB_ADMIN_PASSWORD`).")
    pwd = st.text_input("Password", type="password", key="kb_pwd_field")
    if st.button("Unlock"):
        if pwd == secret:
            st.session_state[AUTH_KEY] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


def _test_connections() -> tuple[bool, list[str]]:
    lines: list[str] = []
    ok = True
    ollama = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    qdrant = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    llama = os.environ.get("LLAMA_SERVER_URL", "http://127.0.0.1:8081").rstrip("/")
    try:
        with httpx.Client() as c:
            r = c.get(f"{ollama}/api/tags", timeout=10.0)
            r.raise_for_status()
            lines.append(f"Ollama: OK ({ollama})")
    except Exception as e:
        ok = False
        lines.append(f"Ollama: FAIL — {e}")
    try:
        with httpx.Client() as c:
            r = c.get(f"{qdrant}/", timeout=10.0)
            r.raise_for_status()
            lines.append(f"Qdrant: OK ({qdrant})")
    except Exception as e:
        ok = False
        lines.append(f"Qdrant: FAIL — {e}")
    try:
        with httpx.Client() as c:
            r = c.get(f"{llama}/v1/models", timeout=10.0)
            r.raise_for_status()
            lines.append(f"llama-server: OK ({llama})")
    except Exception as e:
        ok = False
        lines.append(f"llama-server: FAIL — {e}")
    return ok, lines


def main() -> None:
    load_dotenv()
    _ensure_password()

    st.title("Knowledge base admin")
    st.caption(
        "Same ingestion rules as `scripts/ingest.py` and n8n `CLIENT_ID` "
        "(collection names are sanitized from client id)."
    )

    with st.sidebar:
        st.subheader("Environment")
        st.code(
            f"OLLAMA_HOST={os.environ.get('OLLAMA_HOST', '(unset)')}\n"
            f"QDRANT_URL={os.environ.get('QDRANT_URL', '(unset)')}",
            language="text",
        )
        if st.button("Test connections"):
            good, msgs = _test_connections()
            for m in msgs:
                if good:
                    st.success(m)
                else:
                    st.warning(m)

    tabs = st.tabs(["Collections", "Ingest", "Search", "Delete collection"])

    with tabs[0]:
        st.subheader("Qdrant collections")
        try:
            rows = list_collections_detail()
        except Exception as e:
            st.error(f"Could not list collections: {e}")
            rows = []
        if rows:
            data = [
                {
                    "collection_name": r.name,
                    "points": r.points_count if r.points_count is not None else "—",
                    "vector_size": r.vector_size if r.vector_size is not None else "—",
                }
                for r in rows
            ]
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No collections or Qdrant unreachable.")

    with tabs[1]:
        st.subheader("Ingest text into a client collection")
        client_id = st.text_input(
            "Client ID",
            value="demo_client",
            help="Logical id; sanitized to Qdrant collection name (same as n8n CLIENT_ID).",
        )
        try:
            preview = collection_name(client_id) if client_id.strip() else "—"
        except ValueError as e:
            preview = f"(invalid: {e})"
        st.caption(f"Qdrant collection name: **{preview}**")

        source: SourceLabel = st.selectbox(
            "Payload source label",
            options=("faq", "website", "manual"),
            format_func=lambda x: x,
        )
        c1, c2 = st.columns(2)
        with c1:
            chunk_size = st.number_input(
                "Chunk size",
                min_value=50,
                max_value=8000,
                value=DEFAULT_CHUNK_SIZE,
                step=50,
            )
        with c2:
            chunk_overlap = st.number_input(
                "Chunk overlap",
                min_value=0,
                max_value=chunk_size - 1,
                value=min(DEFAULT_CHUNK_OVERLAP, max(0, chunk_size - 1)),
                step=10,
            )

        uploaded = st.file_uploader(
            "Upload .txt or .json (optional)",
            type=["txt", "json"],
            help="Plain text as-is. JSON is flattened to text (see User guide).",
        )
        pasted = st.text_area(
            "Or paste UTF-8 text or JSON",
            height=220,
            placeholder="FAQ / markdown… or paste JSON starting with [ or {",
        )
        st.caption("Full walkthrough: **docs/kb-admin-user-guide.md** in this repo.")

        if st.button("Run ingest", type="primary"):
            raw: str | None = None
            if uploaded is not None:
                try:
                    raw = normalized_text_from_upload(uploaded.getvalue(), uploaded.name)
                except ValueError as e:
                    st.error(str(e))
                    raw = None
            elif pasted.strip():
                raw = maybe_parse_pasted_json(pasted)
            if not raw or not raw.strip():
                st.error("Provide a file upload or non-empty pasted text.")
            else:
                with st.spinner("Embedding and upserting…"):
                    try:
                        result = ingest_text(
                            client_id,
                            raw,
                            source=source,
                            chunk_size=int(chunk_size),
                            chunk_overlap=int(chunk_overlap),
                        )
                        st.success(
                            f"Upserted **{result.points_upserted}** points into "
                            f"`{result.collection}` at {result.qdrant_url}"
                        )
                    except Exception as e:
                        st.exception(e)

    with tabs[2]:
        st.subheader("Preview search")
        scid = st.text_input("Client ID", value="demo_client", key="search_client")
        q = st.text_input("Query", placeholder="e.g. dogs on patio")
        lim = st.number_input("Limit", min_value=1, max_value=50, value=5, key="search_lim")
        if st.button("Search", key="run_search"):
            if not q.strip():
                st.warning("Enter a query.")
            else:
                try:
                    hits = search_collection(scid, q.strip(), limit=int(lim))
                except Exception as e:
                    st.exception(e)
                else:
                    if not hits:
                        st.info("No hits.")
                    for i, h in enumerate(hits, start=1):
                        with st.expander(f"{i}. score={h.score:.4f}"):
                            st.text(h.text[:4000] if len(h.text) > 4000 else h.text)

    with tabs[3]:
        st.subheader("Delete a collection")
        st.warning("This removes **all** vectors for that collection. This cannot be undone.")
        try:
            names = [r.name for r in list_collections_detail()]
        except Exception as e:
            st.error(str(e))
            names = []
        target = st.selectbox("Collection to delete", options=names if names else ["(none)"], disabled=not names)
        confirm = st.text_input('Type **DELETE** to confirm', placeholder="DELETE")
        if st.button("Delete collection", type="primary", disabled=not names):
            if confirm != "DELETE":
                st.error('You must type exactly: DELETE')
            else:
                try:
                    delete_collection(target)
                    st.success(f"Deleted collection `{target}`.")
                except Exception as e:
                    st.exception(e)


if __name__ == "__main__":
    main()
