# Security

## KB admin on the public internet

If you expose the Streamlit KB admin via **Cloudflare Tunnel**:

- Prefer **HTTPS at the edge** (Cloudflare) and **HTTP only on loopback** behind the tunnel.
- Put **HTTP Basic Auth** (e.g. Caddy on `127.0.0.1:8089`) in front of Streamlit; point the tunnel at that port, not at Qdrant or Ollama.
- Keep Streamlit on **`127.0.0.1:8501`** only; set **`KB_ADMIN_PASSWORD`** in `.env` as defense in depth.
- Do **not** publish Qdrant’s REST port to the internet without strong `api-key`, allowlists, and the same tunnel discipline.

See [docs/cloudflare-tunnel-kb-admin.md](docs/cloudflare-tunnel-kb-admin.md) and [deploy/README.md](deploy/README.md).

## Reporting

If you discover a security vulnerability, please open a **private** report via GitHub **Security Advisories** for this repository (or contact the maintainers directly). Do not post exploit details in public issues.

## For contributors and operators

- **Never commit `.env`** or files containing real API keys, SMTP passwords, or production hostnames you need to keep private. `.env` is gitignored; use `.env.example` as a template with placeholders only.
- **Rotate** any credential that was ever committed or shared, even briefly.
- If sensitive data was pushed to git, remove it from **history** (e.g. `git filter-repo` or BFG Repo-Cleaner), then rotate secrets; rewriting history requires coordinating with anyone who cloned the repo.
- Prefer **n8n Credentials** and environment variables injected at runtime over hardcoding secrets in workflow JSON or docs.

## Optional checks before push

- `git grep` for internal IPs, keys, or tokens you recognize.
- Tools like [gitleaks](https://github.com/gitleaks/gitleaks) or [trufflehog](https://github.com/trufflesecurity/trufflehog) can help scan for accidental leaks.
