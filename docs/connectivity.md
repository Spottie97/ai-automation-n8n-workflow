# Stack connectivity (smoke checks)

Run from a machine that can reach your Ollama, Qdrant, and llama-server URLs (same network as n8n/scripts if they are not on localhost). Replace `BASE` below with each service base URL from your `.env` (`OLLAMA_HOST`, `QDRANT_URL`, `LLAMA_SERVER_URL`).

## Qdrant

- List collections: `GET {QDRANT_URL}/collections`
- Expect HTTP 200 and a JSON payload listing collection names when the service is up.

## Ollama (embeddings)

- List models: `GET {OLLAMA_HOST}/api/tags`
- Confirm your embed model appears in the response (`OLLAMA_EMBED_MODEL`, e.g. `nomic-embed-text:latest`).
- Embeddings: `POST {OLLAMA_HOST}/api/embeddings` with your chosen model; vector dimension must match what your ingest pipeline expects (768 for common nomic-embed-text setups).

## llama-server (OpenAI-compatible generation)

- Health (if exposed): `GET {LLAMA_SERVER_URL}/health` — often `{"status":"ok"}` or similar.
- Models: `GET {LLAMA_SERVER_URL}/v1/models` — pick `LLAMA_CHAT_MODEL` from `data[].id`.

Chat: `POST {LLAMA_SERVER_URL}/v1/chat/completions` with the `model` id from `/v1/models`. Ingestion uses Ollama embeddings only; generation uses llama-server.

## Project helper

From the repo root with `.env` configured: `python scripts/verify_stack.py`.
