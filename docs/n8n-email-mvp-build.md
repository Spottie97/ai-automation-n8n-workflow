# n8n email MVP — implementation guide

**Importable workflows (same RAG stack: Ollama, Qdrant `points/query`, Gemma on **8081**):**

| File | Channels |
|------|----------|
| [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json) | Email only (IMAP → SMTP) |
| [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json) | WhatsApp only (Trigger → Cloud API send) |
| [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json) | **Both** in one workflow (two parallel chains so each run uses the correct parse/merge nodes) |

## Import into n8n

### Email (`rag-email-mvp.json`)

1. **Workflows → Import from File** and select [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json).
2. **Credentials:** open **IMAP Email Trigger** and **Send Reply Email** / **Send Fallback Email**; assign **IMAP** and **SMTP** (export has no credential IDs).
3. Set the **environment variables** below.

### WhatsApp (`rag-whatsapp-mvp.json`)

1. Import [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json).
2. **Credentials:** **WhatsApp Trigger** → **whatsAppTriggerApi**; **Send WhatsApp Reply** / **Send Fallback WhatsApp** → **whatsAppApi**. Configure per [n8n WhatsApp credentials](https://docs.n8n.io/integrations/builtin/credentials/whatsapp/).
3. **`WHATSAPP_PHONE_NUMBER_ID`:** set in n8n env (see table). The send nodes use it as `phoneNumberId`. If the node UI expects a dropdown, switch the field to **Expression** and keep the `={{ $env.WHATSAPP_PHONE_NUMBER_ID }}` form, or paste the numeric ID from Meta **WhatsApp → API Setup**.
4. **Trigger caveat:** Meta allows **one webhook per app**. Do not run two separate active workflows with **WhatsApp Trigger** on the same Facebook app.

### Email + WhatsApp (`rag-email-whatsapp-mvp.json`)

1. Import [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json).
2. Assign **IMAP**, **SMTP**, and **WhatsApp** credentials as above.
3. Use **Manual Test (Email)** or **Manual Test (WhatsApp)** to dry-run each branch.

### Environment variables (all workflows)

Set these so `$env.*` resolves in **HTTP Request** and **Code** nodes (n8n 1.x with env access enabled for Code):

| Variable | Purpose |
|----------|---------|
| `OLLAMA_HOST` | e.g. `http://172.88.88.245:11434` |
| `OLLAMA_EMBED_MODEL` | e.g. `nomic-embed-text:latest` |
| `QDRANT_URL` | e.g. `http://172.88.88.245:6333` |
| `LLAMA_SERVER_URL` | e.g. `http://172.88.88.245:8081` (Gemma) |
| `LLAMA_CHAT_MODEL` | e.g. `gemma4-e4b` |
| `CLIENT_ID` | Qdrant collection slug (default in code: `demo_client` if unset) |
| `SMTP_FROM` | From address for **emailSend** nodes (email workflows only) |
| `WHATSAPP_PHONE_NUMBER_ID` | Business phone number ID for **WhatsApp** send nodes (WhatsApp / combined workflows) |

**Test:** Step-by-step import and manual execution → **[n8n-runbook-import-test.md](n8n-runbook-import-test.md)**. Stack connectivity from CLI → `python scripts/verify_stack.py`. **Activate** only after a successful manual run. Problems → **[n8n-troubleshooting.md](n8n-troubleshooting.md)**.

Optional calendar / branded HTML: fork patterns from your **Farm Tours - Email Responder** workflow (Google Calendar + HTML template); this MVP keeps plain text and no calendar.

---

Step-by-step HTTP payloads and n8n expressions that match **[scripts/ingest.py](../scripts/ingest.py)**, **[scripts/reply_once.py](../scripts/reply_once.py)**, and **[.env.example](../.env.example)**. For the high-level node list, see **[n8n-email-mvp-outline.md](n8n-email-mvp-outline.md)**.

**Assumptions (ai-server):**

- Ollama embeddings: `OLLAMA_HOST` (e.g. `http://172.88.88.245:11434`)
- Qdrant REST: `QDRANT_URL` (e.g. `http://172.88.88.245:6333`)
- Chat (Gemma): `LLAMA_SERVER_URL` = **`http://172.88.88.245:8081`**, `LLAMA_CHAT_MODEL` = **`gemma4-e4b`** (confirm with `GET …/v1/models` on **8081**; **8080** is Qwen)

**Collection name** per client = same sanitization as the CLI: lowercase, non-alphanumeric → `_`, matches **`ingest_mod.collection_name()`** in Python. Example: `client_id` `demo_client` → collection `demo_client`.

---

## 1. Environment variables in n8n

Mirror `.env.example`:

| Variable | Example |
|----------|---------|
| `OLLAMA_HOST` | `http://172.88.88.245:11434` |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text:latest` |
| `QDRANT_URL` | `http://172.88.88.245:6333` |
| `QDRANT_API_KEY` | (optional) |
| `LLAMA_SERVER_URL` | `http://172.88.88.245:8081` |
| `LLAMA_CHAT_MODEL` | `gemma4-e4b` |
| `CLIENT_ID` | `demo_client` (must match ingest `--client-id` / collection name) |
| `SMTP_FROM` | Your verified sender address for SMTP |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Cloud “Phone number ID” (send nodes in WhatsApp / omnichannel workflows) |

Per workflow, **`CLIENT_ID`** selects the Qdrant collection (same sanitization as the Python CLI).

---

## 2. Ollama — create embedding

**HTTP Request** node:

- **Method:** POST  
- **URL:** `{{$env.OLLAMA_HOST}}/api/embeddings`  
- **Body content type:** JSON  
- **Body** (Expression on JSON fields):

```json
{
  "model": "={{ $env.OLLAMA_EMBED_MODEL }}",
  "prompt": "={{ $json.cleanedBody }}"
}
```

(`cleanedBody` = plain text from your **Set** / **Code** node after IMAP.)

**Pass the embedding to Qdrant:**

- n8n’s **HTTP Request** may put the JSON under **`body`**—inspect one run. Use `{{ $('Ollama Embeddings').item.json.body.embedding }}` **or** `{{ $('Ollama Embeddings').item.json.embedding }}`.
- **Code** node alternative: merge `embedding` + `cleanedBody` into one item for cleaner downstream wiring.

Ollama returns JSON: `{ "embedding": [ float, ... ] }` (768 dims for `nomic-embed-text`).

---

## 3. Qdrant — vector query (REST, tested shape)

**HTTP Request** node (after embedding node):

- **Method:** POST  
- **URL:** `{{$env.QDRANT_URL}}/collections/{{ $json.collection }}/points/query`  

Where **`collection`** is the sanitized client id (e.g. `demo_client`). You can set it in a prior **Set** node: `collection: "={{ $env.CLIENT_ID }}"` or a fixed string for one client.

- **Headers:** `Content-Type: application/json`  
- **Authentication:** if `QDRANT_API_KEY` is set, add header `api-key` (Qdrant) or whatever your deployment uses.  
- **Body (JSON)** — pass the embedding array from the previous step:

```json
{
  "query": "={{ $('Ollama Embeddings').item.json.embedding }}",
  "limit": 5,
  "with_payload": true
}
```

If **embedding** is missing, try `{{ $('Ollama Embeddings').item.json.body.embedding }}`. Replace `'Ollama Embeddings'` with your node name. For nested expression limits, use a **Code** node to build the Qdrant JSON body.

**Response shape:** `result.points[]` with `id`, `score`, `payload.text` (see ingest schema).

### If `points/query` returns 404 on older Qdrant

Try legacy search: `POST …/collections/{collection}/points/search` with body:

```json
{
  "vector": [ /* same 768 floats */ ],
  "limit": 5,
  "with_payload": true
}
```

Test with curl against your `QDRANT_URL` once; this project’s Qdrant accepts **`/points/query`** with top-level **`query`** = vector (verified against `172.88.88.245:6333`).

---

## 4. Build `context` string

**Code** node (JavaScript):

```javascript
const root = $input.first().json;
const body = root.body ?? root;
const res = body.result ?? body;
const points = res.points ?? [];
const sep = '\n\n---\n\n';
const parts = points
  .map((p) => (p.payload && p.payload.text) ? String(p.payload.text).trim() : '')
  .filter(Boolean);
return [{ json: { context: parts.join(sep), scores: points.map((p) => p.score) } }];
```

(Adjust path if your HTTP node returns the body without a `result` wrapper—some clients unwrap it to root `points`.)

---

## 5. Build chat messages

**Set** or **Code** node:

- **system**: long string from your filled **[prompts/system_template.md](../prompts/system_template.md)** (substitute `{{CLIENT_NAME}}`, etc., or store per-client in n8n **Credentials** / static data).
- **user**: include `context` + original customer text, same pattern as **[reply_once.py](../scripts/reply_once.py)**:

```text
Use only the following retrieved context to help answer the customer.

Context:
{{ $json.context }}

Customer question:
{{ $('Extract').item.json.cleanedBody }}
```

---

## 6. llama-server — chat completion

**HTTP Request:**

- **Method:** POST  
- **URL:** `{{$env.LLAMA_SERVER_URL}}/v1/chat/completions`  
- **Body (JSON):**

```json
{
  "model": "={{ $env.LLAMA_CHAT_MODEL }}",
  "messages": [
    { "role": "system", "content": "={{ $json.system }}" },
    { "role": "user", "content": "={{ $json.user }}" }
  ],
  "temperature": 0.3,
  "max_tokens": 1024
}
```

**Assistant text:** `{{ $json.choices[0].message.content }}` (double-check node output; may be under `body` depending on **Response Format** settings).

Use **max_tokens** high enough that models which emit hidden “thinking” still produce `content` (e.g. **1024**).

---

## 7. SMTP reply + fallbacks

- **Send Email** node: To = original sender; body = assistant text.
- **Error Trigger / Continue On Fail:** on failed HTTP nodes (Ollama, Qdrant, llama), send a short static message (same as **`FALLBACK_REPLY`** in `reply_once.py`):  
  *“Thanks for your message. I don't have enough information to answer that automatically — a team member will follow up with you shortly.”*
- **IF** node: if `context` is empty or Qdrant returns zero points → skip LLM, send fallback (and optionally log).

---

## 8. Optional — KB admin GUI (no terminal ingest)

Use the Streamlit app to paste/upload **.txt** or **.json** per client and upsert into Qdrant with the **same** rules as `scripts/ingest.py`. Setup: **[kb-admin.md](kb-admin.md)**; operator steps: **[kb-admin-user-guide.md](kb-admin-user-guide.md)** (`streamlit run apps/kb_admin/app.py`).

---

## 9. Optional — trigger CLI ingest from n8n

**Execute Command** (self-hosted only): run on the host where the repo and venv live:

```bash
cd "/path/to/Side Hustle" && . .venv/bin/activate && \
python scripts/ingest.py ingest --client-id "{{ $json.client_slug }}" --input "{{ $json.uploaded_txt_path }}" --source faq
```

Sanitize inputs; do **not** pass raw user text into the shell. Prefer **writing files** via a safe path or calling a small HTTP wrapper instead of shell if inputs are untrusted.

---

## 10. Local smoke test without n8n

```bash
cd "Side Hustle" && . .venv/bin/activate
cp .env.example .env   # then edit credentials
python scripts/reply_once.py --client-id demo_client --question "What are your hours?" --verbose
```

Requires **`demo_client`** collection populated: `python scripts/ingest.py ingest --client-id demo_client --input sample_data/demo_faq.txt`

**Reachability (same URLs as n8n):** `python scripts/verify_stack.py` from any host that can hit Ollama, Qdrant, and llama-server.

---

## 11. Execution logging (recommended)

Built-in MVP workflows do **not** persist runs outside n8n. Before production or client demos, add one of:

1. **n8n Execution Data** — Keep “Save execution progress” / execution retention per your compliance needs; use **Executions** list for debugging.
2. **Error Workflow** — Workflow settings → **Error workflow** → a small flow that posts to Slack/Discord/Email with execution URL and error message.
3. **Explicit log branch** — After **Build RAG Context** (or **Extract Reply Text**), add a **Code** node that shapes `{ execution_id: $execution.id, mode: $execution.mode, client_id: $json.collection, has_rag: $json.has_rag, channel_hint: ... }` and **HTTP Request** to your log endpoint, **Google Sheets** row, or DB API (choose one; keep PII minimal).
4. **Structured fields to log:** `CLIENT_ID` / collection, `has_rag`, `rag_hits`, channel (email vs WhatsApp), truncated question (`body` first ~200 chars), whether fallback branch ran (infer from which send node executed).

Troubleshooting and prompt locations: **[n8n-troubleshooting.md](n8n-troubleshooting.md)**. Import smoke test: **[n8n-runbook-import-test.md](n8n-runbook-import-test.md)**. KB ingest UI: **[kb-admin.md](kb-admin.md)**.
