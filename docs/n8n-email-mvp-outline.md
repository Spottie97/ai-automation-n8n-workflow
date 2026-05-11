# n8n email MVP — node outline (next sprint)

**Workflow files:** [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json) (email), [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json) (WhatsApp), [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json) (both). Import + manual test runbook → [n8n-runbook-import-test.md](n8n-runbook-import-test.md). Troubleshooting → [n8n-troubleshooting.md](n8n-troubleshooting.md).

**Implementation detail:** HTTP bodies, Qdrant paths, and n8n expressions → **[n8n-email-mvp-build.md](n8n-email-mvp-build.md)**.

- **Email path:** **IMAP Trigger → extract body → embed → Qdrant retrieve → build prompt → llama-server → SMTP reply**.
- **WhatsApp path:** **WhatsApp Trigger → parse text-only messages → same RAG chain → WhatsApp Business send** (see `rag-whatsapp-mvp.json` or the WhatsApp branch in `rag-email-whatsapp-mvp.json`).

## 1. IMAP Email Trigger

- Node: **Email Trigger (IMAP)**.
- Connect to the client’s inbox (or a dedicated support address).
- Trigger on: new messages in INBOX (optionally filter on subject / sender later).

## 2. Extract content

- Node: **Set** (or **Code**) to normalize:
  - `from`, `subject`, `textBody` / `htmlBody` (prefer plain text; strip HTML if needed).
  - `messageId`, `references` for threading (optional for MVP).
- Truncate very long bodies (e.g. first 4–8k chars) to control embedding cost.

## 3. Embedding (Ollama)

- Node: **HTTP Request** (POST).
- URL: `{{$env.OLLAMA_HOST}}/api/embeddings`
- Body (JSON): `{ "model": "{{$env.OLLAMA_EMBED_MODEL}}", "prompt": "{{ $json.cleanedBody }}" }`
- Extract `embedding` array for the next step.

*Alternative:* run the same contract from a small **helper workflow** or **sub-workflow** if you reuse it for WhatsApp later.

## 4. Qdrant vector search

- Node: **HTTP Request** (POST) to Qdrant REST API **search** / **query** endpoint for the client’s collection (one collection per client; name = sanitized `client_id`).
  - Path shape (verify against your Qdrant version): e.g. `POST /collections/{collection}/points/search` with `vector`, `limit`, `with_payload: true`.
- Map results to a single string **`context`**: concatenate top‑`k` payloads’ `text` fields with clear separators (e.g. `---`).

## 5. Build chat messages

- Node: **Set** or **Code**:
  - **System**: content from your filled-in `prompts/system_template.md` (business summary + rules).
  - **User**: include `context` block + customer email body as the question.
- Keep total tokens under your llama-server budget.

## 6. llama-server (OpenAI-compatible)

- Node: **HTTP Request** (POST).
- URL: `{{$env.LLAMA_SERVER_URL}}/v1/chat/completions`
- Headers: `Content-Type: application/json`; add `Authorization: Bearer ...` only if you enabled API keys.
- Body (example): use `{{$env.LLAMA_CHAT_MODEL}}` — e.g. **`gemma4-e4b`** (verify with `GET /v1/models` on your `LLAMA_SERVER_URL`).

```json
{
  "model": "gemma4-e4b",
  "messages": [
    {"role": "system", "content": "..." },
    {"role": "user", "content": "..." }
  ],
  "temperature": 0.3,
  "max_tokens": 512
}
```

- Parse `choices[0].message.content` as **`replyText`**.

## 7. SMTP reply

- Node: **Send Email** or **SMTP**:
  - To: original sender.
  - Subject: `Re: {{ subject }}` (respect threading headers if you add them later).
  - Body: **`replyText`**.
- **Important for MVP:** decide policy on **auto-reply to all** vs **only first message in thread**; consider a **static BCC** to yourself for monitoring.

## 8. Logging & fallback

- **Error handling:** on failures (IMAP, HTTP, empty Qdrant hits), send a safe fallback: *“Thanks — we’ll have someone follow up shortly.”* and log the error payload to a file, DB, or Telegram/Slack **Error Workflow**.
- **Confidence (later):** optional branch if top score &lt; threshold → skip LLM, send escalation message (checklist “optional later”).

## Environment variables (n8n)

Mirror `.env.example`:

- `OLLAMA_HOST`, `OLLAMA_EMBED_MODEL`
- `QDRANT_URL` (+ `QDRANT_API_KEY` if used) — e.g. **`http://127.0.0.1:6333`**; use another host/port if you run a second Qdrant instance
- `LLAMA_SERVER_URL` (e.g. **`http://127.0.0.1:8081`**), `LLAMA_CHAT_MODEL` (e.g. `gemma4-e4b`)
- Per-execution **client config**: collection name / `client_id`, SMTP and IMAP credentials (prefer **Credentials** store, not plaintext in nodes).

## Order of build

1. Manual **HTTP** tests for embeddings + Qdrant search (same as `scripts/ingest.py`).
2. llama-server **chat** test with a hard-coded system + user message.
3. Stitch **IMAP → … → SMTP** with a single test mailbox.
4. Add logging and fallback paths before enabling for a real client.
