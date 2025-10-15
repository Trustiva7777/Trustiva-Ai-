# Contributing — Trustiva AI + Proof Kernel

We welcome contributions from internal teams and the community. This guide helps you get productive quickly and ensures quality and security remain high.

## Prerequisites

- Python ≥ 3.12
- Node ≥ 20
- Docker ≥ 24
- Git and an SSH key configured for GitHub

## Getting Started

1. Fork the repo (if external) or create a feature branch (if internal):
   - `feature/<short-summary>` or `fix/<short-summary>`
2. Create a local `.env` from `.env.example` and set necessary tokens
3. Start services and run tests:
   ```bash
   docker compose up -d
   pytest -q
   HARDHAT_CONFIG=hardhat.config.cjs npx hardhat test --network localhost
   ```

## Conventional Commits

Use Conventional Commits to keep history readable and automate releases:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `chore:` tooling, build, infra changes
- `refactor:` code change that neither fixes a bug nor adds a feature
- `test:` adding or updating tests

Example: `feat(api): add POST /swarm/attest alias`

## Branching & PRs

- Branch names: `feature/*`, `fix/*`, `docs/*`, `chore/*`
- Open a draft PR early; link any related issues
- Ensure PRs are small and focused; avoid mixed concerns

## Pre‑PR Checklist

- [ ] Unit tests pass: `pytest -q` and Hardhat tests
- [ ] No secrets or keys in diffs or logs
- [ ] Updated docs or runbook if behavior changes
- [ ] Lint (if enabled) and type checks (if enabled) are clean

## Code of Conduct

Please be respectful and considerate. Adopt a collaborative posture; we will add a CODE_OF_CONDUCT.md if the project accepts broader community contributions.

## CLA

If Trustiva requires a Contributor License Agreement for certain contributions, a bot or a maintainer will guide you through the process during PR review.

## Security Considerations

- Never embed secrets in code or tests
- Avoid printing tokens in logs
- Be mindful of dependency updates that alter license or security posture

## Review & Merge

- At least one maintainer approval is required
- Squash merges recommended to keep history clean
- CI must be green before merge
