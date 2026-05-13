# Caddy loopback proxy for KB admin

Used with **Cloudflare Tunnel**: the tunnel forwards to `http://127.0.0.1:8089`; Caddy adds **`basic_auth`** then proxies to Streamlit on `127.0.0.1:8501`.

- Template: [Caddyfile.example](Caddyfile.example)
- Full steps: [docs/cloudflare-tunnel-kb-admin.md](../../docs/cloudflare-tunnel-kb-admin.md)
- Install Caddy (Debian/Ubuntu): [caddyserver.com/docs/install#debian-ubuntu-raspbian](https://caddyserver.com/docs/install#debian-ubuntu-raspbian)

Do not commit a Caddyfile containing real password hashes to a public repo; keep production files only on the server.
