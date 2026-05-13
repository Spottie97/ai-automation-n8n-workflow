# Demo pack — AI inbox assistant (Phase 4)

Use with **Harborview Coffee Co.** demo data: [sample_data/demo_faq.txt](../sample_data/demo_faq.txt). One-shot stack + ingest + RAG smoke: **`./scripts/verify_demo_rag.sh`** (from repo root, `.env` + `.venv`). Ingest via CLI or **[KB admin GUI](../docs/kb-admin.md)** — remote KB admin after tunnel: **`https://kb.reinhardterasmus.info`** (Basic Auth + optional `KB_ADMIN_PASSWORD`). n8n: **[n8n-go-live-checklist.md](../docs/n8n-go-live-checklist.md)** and [n8n-runbook-import-test.md](../docs/n8n-runbook-import-test.md). Workflows: [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json), [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json), [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json).

---

## Client onboarding (per customer)

- [ ] **Collection / client id** — agree sanitized `CLIENT_ID` (matches Qdrant collection).
- [ ] **Source material** — FAQs, hours, pricing, policies (txt/json or paste in KB admin).
- [ ] **Ingest** — CLI or KB admin; spot-check search hits for top 10 questions.
- [ ] **Prompt** — fill [prompts/system_template.md](../prompts/system_template.md) tone + escalation rules.
- [ ] **n8n** — clone workflow; IMAP/SMTP or WhatsApp credentials; env vars from n8n’s network view ([n8n-go-live-checklist.md](../docs/n8n-go-live-checklist.md)).
- [ ] **Go-live** — dry run, then activate; monitor 48h ([ai_automation_side_hustle_checklist.md](../ai_automation_side_hustle_checklist.md)).

---

## Execution logging (before client demos)

See [docs/n8n-email-mvp-build.md](../docs/n8n-email-mvp-build.md) §11 — add an error workflow, external webhook, or sheet row so you can review `has_rag` and fallbacks without replaying the whole inbox.

---

## Packages (stub — set your ZAR)

| Tier | What’s included | Monthly (indicative) | Setup (once) |
|------|-----------------|----------------------|--------------|
| **Starter** | Email auto-replies from your FAQs + 1 small site scrape; weekly log review | R500–R800 | R1k–R2k |
| **Standard** | Starter + n8n tweaks + 2 ingestion updates/mo + escalation templates | R900–R1400 | R2k–R3k |
| **Pro** | Standard + second channel (e.g. WhatsApp) roadmap + priority tuning | R1500–R2000 | R3k+ |

Adjust numbers to your market; keep setup fee separate so onboarding covers ingestion + first workflow clone.

---

## WhatsApp outreach (casual)

> Hi [Name] — quick one. I help small shops answer repetitive customer questions (hours, pricing, “do you do X?”) automatically over email, using their own FAQs so it doesn’t invent stuff.  
> If you’re curious I can show you a 5‑min demo on a fake café inbox. No pressure — reply **demo** if you want a time.

---

## Demo script (what you show)

1. **The problem:** “Same questions eat your morning.”
2. **The stack:** FAQs → vectors (Qdrant) → short RAG reply (Gemma on your server); you stay in control.
3. **Live or recorded:** Run `./scripts/verify_demo_rag.sh` **or** `reply_once.py` with `demo_client` **or** the imported n8n workflow (Manual trigger) — ask: *hours*, *dogs on patio*, *catering lead time*. Optionally show KB admin at `https://kb.reinhardterasmus.info` after tunnel + Caddy are up.
4. **Safety:** No answer if nothing in KB; polite handoff line (same as automation fallback).
5. **Next step:** “I’d ingest your real FAQs + wire your mailbox when you’re ready.”

---

## Example assistant replies (Harborview-style)

These illustrate tone and grounding; real outputs come from your model + retrieved chunks.

**Q:** *Are dogs allowed?*  
**A:** *Dogs are welcome on the patio on a leash, but not inside the café. If you need an indoor seat, let us know and we’ll suggest options.*

**Q:** *How long for catering?*  
**A:** *We need at least **5 business days** for coffee catering (roughly 10–80 people). Reply with your date, headcount, and any dietary needs and we’ll put together a quote.*

**Q:** *What’s your Wi‑Fi password?*  
**A:** *Guest Wi‑Fi details are posted at the counter and change monthly — ask a barista if you have trouble connecting.*

---

## Checklist pointer

- [x] Demo data: [sample_data/demo_faq.txt](../sample_data/demo_faq.txt)  
- [x] Workflow JSON: [workflows/rag-email-mvp.json](../workflows/rag-email-mvp.json), [workflows/rag-whatsapp-mvp.json](../workflows/rag-whatsapp-mvp.json), [workflows/rag-email-whatsapp-mvp.json](../workflows/rag-email-whatsapp-mvp.json)  
- [ ] Stack + demo RAG: `./scripts/verify_demo_rag.sh` (on a host that reaches Ollama/Qdrant/llama-server)  
- [ ] KB admin HTTPS: `https://kb.reinhardterasmus.info` (Caddy Basic Auth + tunnel — [docs/cloudflare-tunnel-kb-admin.md](../docs/cloudflare-tunnel-kb-admin.md))  
- [ ] n8n: [docs/n8n-go-live-checklist.md](../docs/n8n-go-live-checklist.md) + [docs/n8n-runbook-import-test.md](../docs/n8n-runbook-import-test.md)

When n8n email/WhatsApp MVP is live, repeat the same questions against the real workflow and compare.
