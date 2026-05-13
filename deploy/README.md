# Deploy artifacts (ai-server)

| Path | Purpose |
|------|---------|
| [cloudflared/config.yml.example](cloudflared/config.yml.example) | Tunnel → `http://127.0.0.1:8089` for **kb.reinhardterasmus.info** |
| [caddy/Caddyfile.example](caddy/Caddyfile.example) | Loopback Basic Auth → Streamlit `127.0.0.1:8501` |
| [systemd/kb-admin.service.example](systemd/kb-admin.service.example) | Streamlit user unit |
| [systemd/caddy-kb-proxy.service.example](systemd/caddy-kb-proxy.service.example) | Optional Caddy system unit |

**Order:** `kb-admin` (8501) → Caddy (8089) → `cloudflared`.

Full procedure: [docs/cloudflare-tunnel-kb-admin.md](../docs/cloudflare-tunnel-kb-admin.md) and [docs/deploy-ai-server.md](../docs/deploy-ai-server.md).
