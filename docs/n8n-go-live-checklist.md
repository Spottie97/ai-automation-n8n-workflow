# n8n go-live checklist (email, then WhatsApp)

Use after `python scripts/verify_stack.py` passes from the **n8n host** (or set URLs n8n can reach: Docker gateway, host IP, etc.).

## Shared prerequisites

- [ ] `demo_client` collection exists (ingest: `python scripts/ingest.py ingest --client-id demo_client --input sample_data/demo_faq.txt`).
- [ ] n8n environment variables match your stack (same semantics as `.env`):

| Variable | Notes |
|----------|--------|
| `OLLAMA_HOST` | Reachable from n8n |
| `OLLAMA_EMBED_MODEL` | e.g. `nomic-embed-text:latest` |
| `QDRANT_URL` | Reachable from n8n |
| `LLAMA_SERVER_URL` | OpenAI-compatible base, no `/v1` suffix |
| `LLAMA_CHAT_MODEL` | From `GET …/v1/models` |
| `CLIENT_ID` | e.g. `demo_client` for demos |

- [ ] `SMTP_FROM` set for email workflows.
- [ ] `WHATSAPP_PHONE_NUMBER_ID` set for WhatsApp / combined workflows.

## Phase A — Email MVP

- [ ] Import [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json).
- [ ] Assign **IMAP** and **SMTP** credentials on trigger and send nodes.
- [ ] Manual execution / test mailbox (see [n8n-runbook-import-test.md](n8n-runbook-import-test.md)).
- [ ] Send a real test message; confirm RAG reply or fallback.
- [ ] Optional: attach **Error workflow** or log branch ([n8n-email-mvp-build.md](n8n-email-mvp-build.md) §11).

## Phase B — WhatsApp (after email works)

- [ ] Import [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json) **or** use the WhatsApp branch in [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json).
- [ ] Configure WhatsApp Trigger + send credentials per [n8n WhatsApp docs](https://docs.n8n.io/integrations/builtin/credentials/whatsapp/).
- [ ] Remember: **one webhook per Meta app** — do not run two active WhatsApp triggers on the same app.
- [ ] Manual test message; confirm reply uses same `CLIENT_ID` / collection as email.

## Phase C — Combined (optional)

- [ ] Import [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json).
- [ ] Test **Manual Test (Email)** and **Manual Test (WhatsApp)** separately before activating triggers.

## Handoff per client

- [ ] New `CLIENT_ID` / sanitized collection name agreed.
- [ ] Ingest client FAQs (CLI or KB admin).
- [ ] Clone workflow; set client env + credentials.
- [ ] Escalation path and fallback copy approved.
- [ ] 48h monitoring after go-live.
