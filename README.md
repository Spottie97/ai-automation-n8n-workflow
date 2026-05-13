# ai-automation-n8n-workflow

Small RAG pipeline that turns a client's FAQs into auto-replies on email and WhatsApp, using Ollama (embeddings), Qdrant (vectors), llama-server (chat), and n8n (orchestration).

**Start here:** [docs/README.md](docs/README.md) — operator guide with step-by-step setup, ingest, n8n import, smoke test, and go-live, linking to focused runbooks for each step.

## Quick links

- Environment template: [.env.example](.env.example)
- CLI ingest: [scripts/ingest.py](scripts/ingest.py)
- One-shot RAG reply: [scripts/reply_once.py](scripts/reply_once.py)
- Stack smoke test: [scripts/verify_stack.py](scripts/verify_stack.py)
- KB admin (Streamlit): [apps/kb_admin/app.py](apps/kb_admin/app.py)
- n8n workflows: [workflows/](workflows/)
- Master checklist: [ai_automation_side_hustle_checklist.md](ai_automation_side_hustle_checklist.md)
- Sales / demo pack: [sales/demo-pack.md](sales/demo-pack.md)
- Security notes: [SECURITY.md](SECURITY.md)
