# Deploy on the ai-server

Use this when the stack (Ollama, Qdrant, llama-server) already runs on the same machine, or when this host can reach those services over the network. The repo is **code + workflows + CLI/GUI**; n8n itself is configured separately (import JSON, set environment variables).

## 1. Clone or update

SSH into the server, pick an install root (examples: `~/ai-automation-n8n-workflow` or `/srv/ai-automation-n8n-workflow`).

```bash
git clone https://github.com/Spottie97/ai-automation-n8n-workflow.git
cd ai-automation-n8n-workflow
git pull origin main   # later updates
```

## 2. Bootstrap Python environment

From the repo root:

```bash
chmod +x scripts/bootstrap_server.sh
./scripts/bootstrap_server.sh
```

This creates `.venv`, installs `requirements.txt`, and copies `.env.example` → `.env` if `.env` does not exist.

## 3. Configure `.env`

Edit `.env` on the server:

- If Ollama, Qdrant, and llama-server run **on this host**, use `http://127.0.0.1:…` with the correct ports (see `.env.example`).
- If any service is on another machine, use reachable hostnames or IPs **only** in this local file (never commit `.env`).

Lock down permissions:

```bash
chmod 600 .env
```

## 4. Smoke test

```bash
source .venv/bin/activate
python scripts/verify_stack.py
```

If something fails, fix URLs in `.env` or service health first; see [connectivity.md](connectivity.md).

## 5. Optional: demo ingest and one-shot reply

```bash
python scripts/ingest.py ingest --client-id demo_client --input sample_data/demo_faq.txt
python scripts/reply_once.py --client-id demo_client --question "What are your hours?" --verbose
```

## 6. KB admin UI

Manual run (LAN):

```bash
source .venv/bin/activate
streamlit run apps/kb_admin/app.py --server.address 0.0.0.0 --server.port 8501
```

Prefer **localhost + SSH tunnel** or a reverse proxy with TLS for anything beyond a trusted LAN. Long-running: copy [deploy/systemd/kb-admin.service.example](../deploy/systemd/kb-admin.service.example), replace every `REPO_ROOT` with your clone path, install under `systemd --user` or system-wide, then enable the unit. Details: [kb-admin.md](kb-admin.md).

## 7. n8n

This repository does not install n8n. On your n8n instance:

1. Set environment variables to match `.env` (`OLLAMA_HOST`, `OLLAMA_EMBED_MODEL`, `QDRANT_URL`, `LLAMA_SERVER_URL`, `LLAMA_CHAT_MODEL`, `CLIENT_ID`, email/WhatsApp vars as needed). n8n must reach the same URLs your `.env` uses (often `http://HOST:PORT` from the n8n container/host, not necessarily `127.0.0.1`).
2. Import workflow JSON from `workflows/` (see [n8n-email-mvp-build.md](n8n-email-mvp-build.md) and [n8n-runbook-import-test.md](n8n-runbook-import-test.md)).

## 8. Updates

```bash
cd /path/to/ai-automation-n8n-workflow
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_stack.py
```

Restart the KB admin systemd unit if you use it: `systemctl --user restart kb-admin.service`.

## 9. Security

- Do not copy the server’s real `.env` into the public GitHub repo.
- Keep API keys and SMTP secrets only in n8n Credentials / server `.env`.
- See [SECURITY.md](../SECURITY.md).
