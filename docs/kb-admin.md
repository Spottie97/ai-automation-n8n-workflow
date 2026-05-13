# KB admin GUI

Browser UI to **list Qdrant collections**, **ingest** pasted or uploaded **plain text (.txt) or structured JSON (.json)** (same pipeline as [`scripts/ingest.py`](../scripts/ingest.py)), **search** preview, and **delete** collections—without using the terminal.

**Operator walkthrough:** [kb-admin-user-guide.md](kb-admin-user-guide.md)

## Setup

From the repo root, with the same `.env` as CLI ingest (Ollama + Qdrant):

```bash
cd "Side Hustle"
source .venv/bin/activate
pip install -r requirements.txt
streamlit run apps/kb_admin/app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`).

**LAN / tunnel** (bind all interfaces):

```bash
streamlit run apps/kb_admin/app.py --server.address 0.0.0.0 --server.port 8501
```

Prefer **HTTPS and a reverse proxy** (Caddy, nginx) with **Basic Auth** or SSO when exposing beyond a trusted network. The in-app password is a light gate only.

Full clone/update steps for a dedicated machine: **[deploy-ai-server.md](deploy-ai-server.md)**.

## Deploy on the inference host (recommended)

Run the GUI on the **same machine** that hosts Ollama and Qdrant (lowest latency, simplest firewall story). Benefits:

- Reuse the existing **`.env`** (`OLLAMA_HOST`, `QDRANT_URL` as `http://127.0.0.1:…` or your LAN URL — whatever already works for `verify_stack.py`).
- No need to punch firewall holes for Qdrant/Ollama from your laptop into the admin UI path.
- Ingest and search hit the same vectors n8n uses.

**1. Install once**

```bash
cd /path/to/Side\ Hustle   # your repo clone on the server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # if needed; edit for this host
```

**2. Run manually (quick test)**

```bash
source .venv/bin/activate
streamlit run apps/kb_admin/app.py --server.address 0.0.0.0 --server.port 8501
```

Then open `http://YOUR_HOST:8501` from a browser on your LAN, **or** do not bind `0.0.0.0` and use only SSH port forward (below).

**3. Reach it safely**

Pick **one** pattern:

| Pattern | When to use |
|--------|-------------|
| **SSH local forward** | You alone, temporary: `ssh -L 8501:127.0.0.1:8501 user@your-server` then run Streamlit on the server with `--server.address 127.0.0.1` (default) — no public port. |
| **Tailscale / VPN** | You trust the mesh; bind `127.0.0.1` or LAN IP; optional `KB_ADMIN_PASSWORD`. |
| **Cloudflare Tunnel** | HTTPS at **`https://kb.reinhardterasmus.info`** without inbound ports; **Caddy Basic Auth** on loopback then Streamlit — see **[cloudflare-tunnel-kb-admin.md](cloudflare-tunnel-kb-admin.md)**; set strong `KB_ADMIN_PASSWORD`. |

Do **not** rely on Streamlit’s password alone for anything internet-facing—add **TLS + Access/Basic Auth** at the tunnel or reverse proxy.

**4. Keep it running (optional `systemd` user unit)**

Example: run as your user, bind localhost only, tunnel or reverse-proxy in front.

```ini
[Unit]
Description=Side Hustle KB admin (Streamlit)
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/Side Hustle
EnvironmentFile=/path/to/Side Hustle/.env
ExecStart=/path/to/Side Hustle/.venv/bin/streamlit run apps/kb_admin/app.py --server.address 127.0.0.1 --server.port 8501
Restart=on-failure

[Install]
WantedBy=default.target
```

Adjust paths, then `systemctl --user daemon-reload && systemctl --user enable --now kb-admin.service` (or install as a system unit if you prefer).

**5. checklist**

- [ ] `KB_ADMIN_PASSWORD` set if the URL is shared beyond you.
- [ ] Tunnel or proxy terminates **HTTPS** and applies **Access / Basic Auth** where possible.
- [ ] Firewall: only expose **8501** on LAN if you must; prefer **localhost + SSH or tunnel**.

## Environment variables

Same as ingestion ([`.env.example`](../.env.example)):

| Variable | Purpose |
|----------|---------|
| `OLLAMA_HOST` | Ollama base URL |
| `OLLAMA_EMBED_MODEL` | Embedding model id |
| `QDRANT_URL` | Qdrant REST URL |
| `QDRANT_API_KEY` | Optional |
| `LLAMA_SERVER_URL` | Optional; used only by sidebar “Test connections” |
| `KB_ADMIN_PASSWORD` | If set (non-empty), unlock screen before any Qdrant/Ollama use |

Do not commit real passwords. Use a long random `KB_ADMIN_PASSWORD` if you expose the app.

## Behavior

- **Client ID** is sanitized to the Qdrant collection name the same way as n8n `CLIENT_ID` and the CLI (see [`kb/ingest_pipeline.py`](../kb/ingest_pipeline.py) `collection_name()`).
- **Ingest** accepts **.txt** (raw UTF-8) or **.json** (flattened to text per [kb/upload_parse.py](../kb/upload_parse.py)); pastes that start with `[` or `{` are treated as JSON. Chunking and embeddings match `python scripts/ingest.py ingest …`.
- **Delete** requires typing exactly `DELETE` and picking a collection.

## n8n

After ingesting in the GUI, set n8n **`CLIENT_ID`** to the same logical client id (e.g. `demo_client`). See [n8n-email-mvp-build.md](n8n-email-mvp-build.md) and [n8n-runbook-import-test.md](n8n-runbook-import-test.md).

## Code layout

- Shared logic: [`kb/ingest_pipeline.py`](../kb/ingest_pipeline.py)
- Upload / JSON flattening: [`kb/upload_parse.py`](../kb/upload_parse.py)
- CLI wrapper: [`scripts/ingest.py`](../scripts/ingest.py)
- App: [`apps/kb_admin/app.py`](../apps/kb_admin/app.py)
- User guide: [kb-admin-user-guide.md](kb-admin-user-guide.md)
