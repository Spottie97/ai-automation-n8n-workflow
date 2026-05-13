# KB admin behind Cloudflare Tunnel (HTTPS + Basic Auth)

Goal: **no open inbound ports** on the ai-server. **TLS** terminates at Cloudflare. **cloudflared** dials out. A **loopback-only Caddy** instance adds **HTTP Basic Auth** (username + password — you can use your email as the username), then proxies to **Streamlit on `127.0.0.1:8501`**.

This runbook matches **`kb.reinhardterasmus.info`** → tunnel → **`http://127.0.0.1:8089`** (Caddy) → Streamlit.

We are **not** using Cloudflare Access here; auth is **only** Basic Auth at Caddy plus optional **`KB_ADMIN_PASSWORD`** inside Streamlit.

## Architecture

```mermaid
flowchart LR
  user[Browser]
  edge[Cloudflare_Edge]
  tunnel[cloudflared_on_server]
  caddy[Caddy_127_0_0_1_8089_BasicAuth]
  streamlit[Streamlit_127_0_0_1_8501]

  user -->|HTTPS| edge
  edge --> tunnel
  tunnel -->|HTTP_loopback| caddy
  caddy --> streamlit
```

## Prerequisites

- DNS zone **reinhardterasmus.info** on Cloudflare.
- Repo on `ai-server` with working `.env` (`verify_stack.py` passes).
- Streamlit KB admin bound to **`127.0.0.1:8501`** only — [deploy/systemd/kb-admin.service.example](../deploy/systemd/kb-admin.service.example).
- Set **`KB_ADMIN_PASSWORD`** in `.env` for an in-app gate after Basic Auth (recommended).

## 0. Start order on the server

1. **`kb-admin.service`** — Streamlit on `127.0.0.1:8501`
2. **Caddy** — `127.0.0.1:8089` with Basic Auth → proxy to `8501` — [deploy/caddy/Caddyfile.example](../deploy/caddy/Caddyfile.example)
3. **`cloudflared`** — ingress hostname → `http://127.0.0.1:8089` — [deploy/cloudflared/config.yml.example](../deploy/cloudflared/config.yml.example)

## 1. Install cloudflared (Ubuntu server)

Use Cloudflare’s **APT** repo (works on Ubuntu LTS and current Debian-derived releases). Full options: [Install cloudflared](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/).

```bash
# 1) Cloudflare package signing key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# 2) APT source for cloudflared (needs distro codename, e.g. jammy, noble)
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(. /etc/os-release && echo "$VERSION_CODENAME") main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list

# 3) Install
sudo apt-get update
sudo apt-get install -y cloudflared

# 4) Confirm
cloudflared --version
```

If **`VERSION_CODENAME`** is empty on a minimal image, install `lsb-release` and use `$(lsb_release -cs)` instead, or set the codename manually (e.g. `noble` for Ubuntu 24.04, `jammy` for 22.04):

```bash
sudo apt-get install -y lsb-release
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install -y cloudflared
```

**Alternative (no APT):** download a `.deb` for your architecture from the [downloads page](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/) and run `sudo apt install ./cloudflared_*_amd64.deb` (adjust filename).

## 2. Authenticate and create a tunnel

```bash
cloudflared tunnel login
cloudflared tunnel create kb-admin
```

Save the **tunnel UUID** and **credentials JSON** path (often `~/.cloudflared/<UUID>.json`).

## 3. Public hostname (DNS)

```bash
cloudflared tunnel route dns kb-admin kb.reinhardterasmus.info
```

## 4. Install Caddy and Basic Auth

### 4a. Install Caddy (Debian / Ubuntu / Raspbian)

Official steps: [Install Caddy — Debian, Ubuntu, Raspbian](https://caddyserver.com/docs/install#debian-ubuntu-raspbian).

Stable release (copy-paste):

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
sudo chmod o+r /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
caddy version
```

The package enables a **`caddy`** systemd service and a default config. For this KB-admin setup you will either **stop/disable** the default `caddy` service and run a **separate** unit with only [deploy/caddy/Caddyfile.example](../deploy/caddy/Caddyfile.example) (see [deploy/systemd/caddy-kb-proxy.service.example](../deploy/systemd/caddy-kb-proxy.service.example)), or merge the loopback `127.0.0.1:8089` block into `/etc/caddy/Caddyfile` if you prefer one Caddy process. Read [Using the service](https://caddyserver.com/docs/running#using-the-service) so reloads match how you edit the file.

### 4b. Basic Auth in front of Streamlit

1. Generate a bcrypt hash for your password:

   ```bash
   caddy hash-password
   ```

2. Copy [deploy/caddy/Caddyfile.example](../deploy/caddy/Caddyfile.example) to the server (e.g. `/etc/caddy/kb-admin.Caddyfile`). Replace `your_username` with a short username **or** your email (some browsers handle `user@domain` in Basic Auth; if login fails, use a simple username).
3. Replace the `$2a$14$...` placeholder with the hash from step 1.
4. Run Caddy with that config (see [deploy/caddy/README.md](../deploy/caddy/README.md)). Optional dedicated unit: [deploy/systemd/caddy-kb-proxy.service.example](../deploy/systemd/caddy-kb-proxy.service.example).

**Do not** bind Caddy to `0.0.0.0` for this use case; keep **`127.0.0.1:8089`**.

## 5. Tunnel config

Copy [deploy/cloudflared/config.yml.example](../deploy/cloudflared/config.yml.example) to `~/.cloudflared/config.yml` (or `/etc/cloudflared/config.yml`), set `tunnel`, `credentials-file`, and confirm:

- **`hostname`:** `kb.reinhardterasmus.info`
- **`service`:** `http://127.0.0.1:8089` (Caddy — **not** Streamlit directly)

Test manually:

```bash
cloudflared tunnel run kb-admin
```

## 6. Run cloudflared as a service

Follow: [Run as a service · cloudflared](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/as-a-service/).

```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

Ensure the service reads your `config.yml` path per Cloudflare docs.

## 7. Verification

- On server: `ss -tlnp | grep -E '8501|8089'` — expect **`127.0.0.1:8501`** (Streamlit) and **`127.0.0.1:8089`** (Caddy), not `0.0.0.0` for public exposure.
- From the internet: open **`https://kb.reinhardterasmus.info`** — browser should prompt for **Basic Auth**, then Streamlit (and optionally `KB_ADMIN_PASSWORD` if set).

## 8. Optional: Cloudflare Access later

If you outgrow Basic Auth (team SSO, audit logs), you can add **Cloudflare Access** on the same hostname; then you may remove Caddy Basic Auth or keep defense-in-depth. Not required for the current plan.

## 9. n8n / Qdrant

This tunnel is **only** for the KB admin UI. **Do not** expose Qdrant REST to the public internet. n8n keeps using URLs reachable **from n8n** (often host LAN IP or Docker gateway), not necessarily this hostname.

## References

- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)
- [Caddy basic_auth](https://caddyserver.com/docs/caddyfile/directives/basic_auth)
- [kb-admin.md](kb-admin.md)
