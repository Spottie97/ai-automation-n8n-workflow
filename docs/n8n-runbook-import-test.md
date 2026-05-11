# Runbook — import workflows and manual test

Use this after **[docs/n8n-email-mvp-build.md](n8n-email-mvp-build.md)** for a repeatable smoke test.

## 0. Prerequisites

1. **Services:** Run `python scripts/verify_stack.py` from a machine that reaches Ollama, Qdrant, and llama-server (same URLs n8n will use).
2. **Knowledge base:** Ingest demo data (from repo root, with `.env` pointing at your stack):

   ```bash
   python scripts/ingest.py ingest --client-id demo_client --input sample_data/demo_faq.txt
   ```

   Or use the **[KB admin GUI](kb-admin.md)** (`streamlit run apps/kb_admin/app.py`) — same pipeline as the CLI.

3. **n8n variables:** In n8n, set `OLLAMA_HOST`, `OLLAMA_EMBED_MODEL`, `QDRANT_URL`, `LLAMA_SERVER_URL`, `LLAMA_CHAT_MODEL`, `CLIENT_ID` (`demo_client`), plus `SMTP_FROM` / `WHATSAPP_PHONE_NUMBER_ID` as needed.

## 1. Choose workflow file

| Goal | Import |
|------|--------|
| Email only | [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json) |
| WhatsApp only | [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json) |
| Email + WhatsApp | [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json) |

Do **not** activate **two** workflows that each register a **WhatsApp Trigger** on the **same** Meta app (see [n8n-troubleshooting.md](n8n-troubleshooting.md)).

## 2. Import and credentials

1. **Workflows → Import from File** → select the JSON.
2. Open each **Email** / **WhatsApp** / **IMAP** / **SMTP** node with **Credentials** → assign your production or test credential (exports do not embed credential IDs).

## 3. Manual test execution

1. Open the workflow → **Execute workflow** (or use **Manual Test Trigger** / **Manual Test (Email)** / **Manual Test (WhatsApp)**).
2. **Expected path (RAG hit):** Parse → Ollama → Merge → Qdrant → Build RAG Context with `has_rag: true` → LLM → channel send.
3. **Fallback path:** Temporarily point `CLIENT_ID` at an empty collection or ask off-topic question → **Send Fallback** branch should run (no LLM or short-circuit per workflow design).

## 4. Email-specific checks

- **Send** nodes: `SMTP_FROM` must be allowed by your SMTP provider.
- Reply goes to mock `customer@example.com` until you change **Mock Inbox Email** or use real IMAP.

## 5. WhatsApp-specific checks

- **`WHATSAPP_PHONE_NUMBER_ID`** must match the sender number in Meta.
- Mock branch uses a fake `27123456789`-style `from`; real trigger supplies live `from`.

## 6. Post-test

- Review execution log in n8n for each node’s input/output.
- When satisfied, **Activate** workflow.
- Add external **execution logging** if required (see **Execution logging** in [n8n-email-mvp-build.md](n8n-email-mvp-build.md)).
