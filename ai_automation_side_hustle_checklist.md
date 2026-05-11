# AI Automation Side Hustle - Master Checklist

## Phase 1 - Foundation (Do this once)

### Infrastructure
- [ ] Confirm llama-server reachable: **Gemma** at `172.88.88.245:8081` (automation); **Qwen** at `:8080` if needed
- [ ] Confirm Ollama embeddings working at `172.88.88.245:11434`
- [ ] Confirm Qdrant running (`6333` or `6336`)
- [ ] Confirm n8n can reach all services (no network issues)
- [ ] From a host with `.env`: `python scripts/verify_stack.py` → all OK

### Standardize Your Stack (important)
- [ ] Decide: one Qdrant collection per client
- [ ] Decide: one n8n workflow per client
- [ ] Create base prompt template (reusable)

### Base Prompt Template (create once)
- [ ] Write system prompt template
- [ ] Include:
  - business tone
  - no hallucination rule
  - escalation rule

## Phase 2 - AI Knowledge System (Qdrant)

### Qdrant Schema
- [ ] Define collection structure:
  - `id`
  - `vector`
  - `payload`:
    - `text`
    - `source` (faq / website / manual)
    - `client_id`

### Ingestion Script
- [x] Script to:
  - take raw FAQ text
  - chunk into pieces
  - generate embeddings (Ollama)
  - insert into Qdrant
  - (`scripts/ingest.py`; smoke: `python scripts/verify_stack.py` then `ingest ingest --client-id …`)

### Data Sources
For each client:
- [ ] Website content
- [ ] FAQs
- [ ] Pricing / services
- [ ] Operating hours
- [ ] Custom rules

## Phase 3 - n8n Automation Core

### Email Workflow (MVP)
- [x] IMAP Trigger (incoming mail) — repo: [workflows/rag-email-mvp.json](workflows/rag-email-mvp.json) or [workflows/rag-email-whatsapp-mvp.json](workflows/rag-email-whatsapp-mvp.json)
- [x] Extract message content
- [x] Send to embedding API
- [x] Query Qdrant
- [x] Build prompt (context + question)
- [x] Call llama-server
- [x] Send reply via SMTP

### WhatsApp Workflow (Meta Cloud API)
- [x] Provider: **WhatsApp Business Cloud** + n8n **WhatsApp Trigger** / **WhatsApp** send — repo: [workflows/rag-whatsapp-mvp.json](workflows/rag-whatsapp-mvp.json) or combined [workflows/rag-email-whatsapp-mvp.json](workflows/rag-email-whatsapp-mvp.json)
- [x] Webhook → n8n (one trigger **per Meta app** — see [docs/n8n-troubleshooting.md](docs/n8n-troubleshooting.md))
- [x] Same pipeline as email (embed → Qdrant → LLM)

### Logic Handling
- [x] Add fallback: "I'll forward this to a human" (fallback send branches in workflows)
- [ ] Add confidence check (optional later)
- [ ] Add logging (important for debugging) — see [docs/n8n-email-mvp-build.md](docs/n8n-email-mvp-build.md) §11

## Phase 4 - Productization

### Offer Setup
- [ ] Define packages:
  - Starter / Standard / Pro
- [ ] Define pricing (R500-R2000)
- [ ] Define setup fee

### Sales Assets
- [x] WhatsApp outreach message (stub in [sales/demo-pack.md](sales/demo-pack.md))
- [x] Demo script (what you show client)
- [x] 2-3 example responses

### Demo Environment
- [ ] Create demo client in Qdrant
- [ ] Preload sample business data ([sample_data/demo_faq.txt](sample_data/demo_faq.txt) + `scripts/ingest.py`)
- [ ] Test full flow end-to-end ([docs/n8n-runbook-import-test.md](docs/n8n-runbook-import-test.md))

## Phase 5 - First Client Acquisition

### Target Selection
- [ ] Pick 3-5 local businesses
- [ ] Prefer:
  - slow replies
  - lots of customer questions

### Outreach
- [ ] Send WhatsApp message
- [ ] Offer quick demo
- [ ] Keep it casual, not salesy

### Closing
- [ ] Offer discounted first month
- [ ] Get access to:
  - email OR WhatsApp
  - FAQs / info

## Phase 6 - Deployment Per Client

### Setup
- [ ] Create Qdrant collection (`client_name`)
- [ ] Run ingestion script
- [ ] Clone n8n workflow
- [ ] Insert client-specific config

### Testing
- [ ] Test 10-15 real questions
- [ ] Fix incorrect responses
- [ ] Adjust prompt if needed

### Go Live
- [ ] Enable auto-replies
- [ ] Monitor first 48 hours

## Phase 7 - Maintenance (Low Effort Mode)

### Weekly (optional)
- [ ] Review logs
- [ ] Add missing FAQs
- [ ] Improve responses

### Monthly
- [ ] Client check-in
- [ ] Minor improvements
- [ ] Upsell automation

## Bonus - Optimization Later (Don't do now)
- [ ] Confidence scoring
- [ ] Admin dashboard
- [ ] Multi-tenant system
- [ ] Self-service onboarding

## What matters most (don't skip these)
If you only do 5 things:
- [x] Build ingestion script
- [x] Build working n8n flow
- [ ] Create demo (run ingest + n8n manual test — see [docs/n8n-runbook-import-test.md](docs/n8n-runbook-import-test.md))
- [ ] Send outreach message
- [ ] Close 1 client
