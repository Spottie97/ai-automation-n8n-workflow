# n8n RAG workflows — troubleshooting

See also **[n8n-email-mvp-build.md](n8n-email-mvp-build.md)** (import, env), runbook **[n8n-runbook-import-test.md](n8n-runbook-import-test.md)**, **[kb-admin.md](kb-admin.md)**, and **[kb-admin-user-guide.md](kb-admin-user-guide.md)** (browser ingest: text + JSON).

## Stack reachability (before blaming n8n)

From the same network as your n8n instance, copy [.env.example](../.env.example) to `.env`, adjust hosts, then:

```bash
python scripts/verify_stack.py
```

If embedding fails with **404** on `/api/embeddings`, the host on `OLLAMA_HOST` is probably **not Ollama** (wrong port or reverse proxy). Confirm with `GET {OLLAMA_HOST}/api/tags`.

## Qdrant response shape in Code nodes

The **Build RAG Context** nodes expect points on `result.points` or top-level `points` after the HTTP node. If you see empty context but Qdrant returned data, open the **Qdrant Query** execution output and adjust the one line that resolves `points` in the Code node (some proxies wrap the body).

## `$env` inside Code nodes

**Merge … + Embedding** and similar nodes read `$env.CLIENT_ID`, etc. If those are `undefined`, enable environment access for Code nodes in your n8n version/settings, or duplicate the needed values in a **Set** node (copy through `from_email` / `body` / `wa_from` explicitly so nothing is dropped).

## WhatsApp: one webhook per Meta app

Only **one** production **WhatsApp Trigger** can be registered per Facebook app. Symptoms: duplicate workflows fire, or webhook overwrites when switching test/production URL.

- Keep a **single** active workflow with a WhatsApp trigger per app (e.g. only [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json) **or** [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json), not both active).
- Deactivate the other when testing, or use a separate Meta app for dev.

## `WHATSAPP_PHONE_NUMBER_ID`

Used as **Sender Phone Number (ID)** on **WhatsApp Business Cloud** send nodes. Find it under Meta **WhatsApp → API Setup** (Phone number ID). If the n8n UI shows a dropdown only, switch the field to **Expression** and use `={{ $env.WHATSAPP_PHONE_NUMBER_ID }}` or paste the numeric ID.

## `recipientPhoneNumber`

Inbound `from` from the Cloud API is usually digits (country code, no `+`). The n8n node sanitizes numbers; if sends fail, confirm the format Meta expects for your region.

## IMAP / SMTP after import

Workflow JSON ships **without** credential IDs. Every import must **reassign** IMAP on the trigger and SMTP on **emailSend** nodes.

## Prompt edits (where to change tone)

System and user prompts live in the **Build LLM Request** Code nodes inside:

- [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json)
- [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json)
- [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json) — two nodes: **Build LLM Request (Email)** and **Build LLM Request (WhatsApp)**

Keep email vs WhatsApp wording in sync if you want identical behavior.
