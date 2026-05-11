# Stack connectivity (smoke checks)

Run from the same network as n8n/scripts. **AI stack host:** `172.88.88.245` (ai-server — Qdrant, models, etc. on one machine). Recorded **2026-05-11** against the checklist hosts unless noted.

## Qdrant on ai-server (Docker)

Two **separate** Qdrant processes; data is **not** shared between them.

| Container | Host port (REST API) | Notes |
|-----------|----------------------|--------|
| `qdrant` | **6333** | Default instance (e.g. collections used with Open WebUI / general KB). |
| `qdrant-farmtours` | **6336** | Maps host `6336` → container `6333`; host **6337** → container gRPC `6334`. Farm-tours–specific collections (e.g. `farm_tours_kb`). |

Smoke checks:

| URL | Result |
|-----|--------|
| `http://172.88.88.245:6333/collections` | OK — e.g. `open-webui_files`. |
| `http://172.88.88.245:6336/collections` | OK — e.g. `farm_tours_kb`. |

**This project** defaults to the main **`qdrant`** instance: set **`QDRANT_URL=http://172.88.88.245:6333`** (see `.env.example`). Use **`http://172.88.88.245:6336`** only if you want the separate **`qdrant-farmtours`** database instead (e.g. `farm_tours_kb`).

Client collections for the automation side hustle share the **6333** instance with other collections on that Qdrant (e.g. Open WebUI); isolation is **per collection**, not per container.

## Ollama (embeddings)

| Check | Result |
|-------|--------|
| `GET http://172.88.88.245:11434/api/tags` | OK — models include `nomic-embed-text:latest`. |
| `POST /api/embeddings` with `nomic-embed-text:latest` | OK — **vector dimension 768**. |

Default embed model: `nomic-embed-text:latest` (`OLLAMA_EMBED_MODEL`).

## llama-server (generation — systemd on ai-server)

Two **separate** llama-server instances (different ports):

| systemd unit | Model | Port | `LLAMA_SERVER_URL` |
|--------------|--------|------|--------------------|
| `llama-server-gemma4.service` | Gemma 4 E4B (`gemma4-e4b`) | **8081** | **Default for this project** |
| `llama-server.service` | Qwen3.5 4B (`qwen35-4b`) | **8080** | Use only if you want Qwen |

Smoke checks:

| URL | Expected |
|-----|----------|
| `GET http://172.88.88.245:8081/health` | `{"status":"ok"}` (Gemma) |
| `GET http://172.88.88.245:8081/v1/models` | `data[].id` **`gemma4-e4b`** |
| `GET http://172.88.88.245:8080/v1/models` | `data[].id` **`qwen35-4b`** |

**Base URL for automation / n8n:** `http://172.88.88.245:8081` (`LLAMA_SERVER_URL` in `.env.example`).

**Chat model id (Gemma on 8081):** **`gemma4-e4b`** — set `LLAMA_CHAT_MODEL` to whatever `GET {LLAMA_SERVER_URL}/v1/models` returns for the instance you use.

Use `POST {LLAMA_SERVER_URL}/v1/chat/completions` with the correct `model` id (not required for ingestion; ingest still uses Ollama embeddings).
