# SECURITY POLICY — Trustiva AI + Proof Kernel

Theme: Trustiva Classic (black/gold #C7A340)

## Responsible Disclosure

We take security seriously. If you discover a vulnerability:

- Email: security@trustiva.example (replace with your security inbox)
- PGP: Provide your public key in the email for encrypted follow‑up
- Please include steps to reproduce, impact, and any PoC details
- We aim to acknowledge within 72 hours and provide an ETA for remediation

Do not publicly disclose vulnerabilities before we confirm a fix window.

## Scope

- In scope: This repository and its deployable artifacts (Ops API, Swarm, Web UI, contracts, scripts)
- Out of scope: Third‑party services (GitHub, Docker Hub, cloud providers)

## Key Management & Secrets

- SSH: Use per‑device ed25519 keys; do not re‑use keys across environments
- GPG/PGP: Store audit keys securely; do not commit armored keys in repo
- Environment Secrets: Use `.env` locally and GitHub Actions Secrets in CI; never commit tokens or keys
- Token Handling: Never echo secrets in logs; use masked output in CI

## Dependency Security

- Enable Dependabot for GitHub‑hosted dependencies
- Node: `npm audit` during CI; review and patch high‑severity findings
- Python: `pip-audit` in CI for vulnerabilities
- Contracts: Pin compiler versions; audit third‑party libraries before use

## CI Guardrails

- CI must not print secret values; redact sensitive logs
- Publishing steps should treat `publish.json` and artifacts as untrusted inputs
- IPFS publish: Verify gateway availability, and handle propagation delays with retry/backoff

## Reporting Format

Provide:

- Affected component(s)
- Version/commit hash
- Reproduction steps
- Expected vs actual behavior
- Impact assessment and severity

## Coordinated Disclosure Timeline (target)

- Triage: within 72 hours
- Fix plan: within 7 days for high‑severity issues
- Patch release: within 30 days depending on complexity

## Contact & PGP

- security@trustiva.example
- PGP public key: (to be published)
