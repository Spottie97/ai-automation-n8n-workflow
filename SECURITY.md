# Security

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
