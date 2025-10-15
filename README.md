<div align="center">

# ⚜ Trustiva AI + Proof Kernel

Secure, autonomous AI‑to‑blockchain pipeline that publishes, verifies, and anchors artifacts to IPFS and on‑chain registries.

[![CI](https://github.com/Trustiva7777/Trustiva-Ai-/actions/workflows/ci.yml/badge.svg)](https://github.com/Trustiva7777/Trustiva-Ai-/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-C7A340.svg)](./LICENSE)
![Docker Compose](https://img.shields.io/badge/Docker-Compose-000000.svg?logo=docker&logoColor=C7A340)
![Python](https://img.shields.io/badge/Python-3.12-000000.svg?logo=python&logoColor=C7A340)
![Node](https://img.shields.io/badge/Node-20.x-000000.svg?logo=node.js&logoColor=C7A340)
![Hardhat](https://img.shields.io/badge/Hardhat-2.22-000000.svg?logo=ethereum&logoColor=C7A340)
![Solidity](https://img.shields.io/badge/Solidity-0.8.20-000000.svg?logo=solidity&logoColor=C7A340)
[![Code Size](https://img.shields.io/github/languages/code-size/Trustiva7777/Trustiva-Ai-?color=C7A340&label=Code%20Size&logo=github)](https://github.com/Trustiva7777/Trustiva-Ai-)
[![Issues](https://img.shields.io/github/issues/Trustiva7777/Trustiva-Ai-?color=C7A340&label=Issues)](https://github.com/Trustiva7777/Trustiva-Ai-/issues)
[![PRs](https://img.shields.io/github/issues-pr/Trustiva7777/Trustiva-Ai-?color=C7A340&label=PRs)](https://github.com/Trustiva7777/Trustiva-Ai-/pulls)

<sub style="color:#888">Theme: Trustiva Classic — black with gold accents (#C7A340).</sub>

</div>

## 🌟 Mission

Deliver a production‑grade trust pipeline where AI‑generated evidence is:

- Published to IPFS with gateway verification
- Validated by an AI swarm quorum and Ops API
- Finalized on a ProofChain and registered in an AuditRegistry smart contract
- Verifiable via a browser UI with OpenPGP and live XRPL checks

Built for auditors, investors, and engineers who expect repeatability, tests, and clear guardrails.

---

## 🧭 Architecture (high level)

```mermaid
flowchart LR
  subgraph Client
    UI[Next.js Verify UI\nOpenPGP.js]
  end

  subgraph Ops
    API[FastAPI Ops API\n/verify /registry /swarm]
    SWARM[AI Swarm Orchestrator\nQuorum Attestation]
  end

  subgraph Data Plane
    IPFS[(IPFS\nPublish + Gateway Verify)]
    XRPL[(XRPL Live Verify)]
    QDR[Qdrant]
    RDS[(Redis Streams)]
  end

  subgraph Chain
    POI[ProofChain.sol\nFinalize(root)]
    REG[AuditRegistry.sol\nRegister if Final]
  end

  UI <--> API
  API <--> SWARM
  API --> IPFS
  API -. ws/bridge .-> XRPL
  SWARM --> API
  API --> POI --> REG
  API -. vectors .-> QDR
  API -. queues .-> RDS
```

Key repos paths:

- Ops API: `services/api/main.py`
- Swarm: `ai_swarm/orchestrator.py`
- Contracts: `contracts/ProofChain.sol`, `contracts/AuditRegistry.sol`
- Node scripts: `scripts/deploy-local.cjs`, `scripts/proof-submit.cjs`
- Web UI: `apps/web/app/registry/verify/page.jsx`
- Runbook: `docs/README_RUNBOOK.md`

---

## 🔧 Tech stack

- Backend: FastAPI (Pydantic v2), httpx; Redis, Qdrant
- AI: Swarm quorum orchestrator; Hugging Face Inference with OpenAI fallback
- Web: Next.js 14, React 18, OpenPGP.js verification
- Chain: Solidity 0.8.20, Hardhat 2.22, ethers v6, Ganache devnet
- IPFS: Publisher with HTTP API and gateway verification
- CI: GitHub Actions (Python tests, web build, contracts)

---

## ⚡ Quick start

1) Configure environment

```bash
cp .env.example .env
# Set tokens: HUGGING (or OPENAI_API_KEY), optional IPFS_* and chain keys
```

2) Start services

```bash
docker compose up -d
```

3) One‑shot pipeline (publish → attest → submit)

```bash
make up && make pipeline
```

4) Explore locally

- Ops API docs: http://localhost:9000/docs (orchestrator at 8000 if running)
- Web UI: http://localhost:3000/registry/verify

5) Contracts (local devnet)

```bash
HARDHAT_CONFIG=hardhat.config.cjs npx hardhat test --network localhost
```

---

## ✅ Status & guardrails

- CI badge above reflects `Trustiva7777/Trustiva-Ai-` main branch once pushed.
- No secrets in repo; use `.env` or GitHub Secrets. Never print token values.
- If IPFS returns CID but the gateway 404s, the publisher retries with backoff.
- Devnet: Ganache on 8545; scripts handle deploy+finalize+register.

---

## 👥 Contributors (senior team credits)

- Lead Blockchain Engineer — smart contracts, on‑chain finalization
- AI Systems Lead — swarm quorum, policy, attestations
- DevOps Architect — CI/CD, Docker Compose, IPFS pipeline
- Full‑Stack Engineer — Next.js verification UI, Ops endpoints
- Security & Compliance Engineer — guardrails, verification, audits

Featured Professional Credit

- Kevan Burns — Sovereign Infrastructure Architect
  - Senior Engineering Division (DevOps | Blockchain | AI Systems | Compliance)

For contributor guidelines and service details, see the Runbook.

---

## 📚 Documentation

- Runbook: `docs/README_RUNBOOK.md`
- Engineering Appraisal: `docs/Trustiva_1.0_Appraisal.md`
- CI Workflow: `.github/workflows/ci.yml`

---

> Palette: Trustiva Classic — black with gold (#C7A340). Provide names/titles to expand credits.
