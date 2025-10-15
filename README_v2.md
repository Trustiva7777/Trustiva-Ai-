<div align="center">

# ⚜ Trustiva AI + Proof Kernel

Autonomous AI‑to‑blockchain trust infrastructure.

[![CI](https://github.com/Trustiva7777/Trustiva-Ai-/actions/workflows/ci.yml/badge.svg)](https://github.com/Trustiva7777/Trustiva-Ai-/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-C7A340.svg)](./LICENSE)
[![Docs](https://img.shields.io/badge/Docs-/docs-000000.svg?logo=readthedocs&logoColor=C7A340)](./docs)
![Docker Compose](https://img.shields.io/badge/Docker-Compose-000000.svg?logo=docker&logoColor=C7A340)
![Python](https://img.shields.io/badge/Python-3.12-000000.svg?logo=python&logoColor=C7A340)
![Node](https://img.shields.io/badge/Node-20.x-000000.svg?logo=node.js&logoColor=C7A340)
![Hardhat](https://img.shields.io/badge/Hardhat-2.22-000000.svg?logo=ethereum&logoColor=C7A340)
![Solidity](https://img.shields.io/badge/Solidity-0.8.20-000000.svg?logo=solidity&logoColor=C7A340)
[![Code Size](https://img.shields.io/github/languages/code-size/Trustiva7777/Trustiva-Ai-?color=C7A340&label=Code%20Size&logo=github)](https://github.com/Trustiva7777/Trustiva-Ai-)
[![Issues](https://img.shields.io/github/issues/Trustiva7777/Trustiva-Ai-?color=C7A340&label=Issues)](https://github.com/Trustiva7777/Trustiva-Ai-/issues)
[![PRs](https://img.shields.io/github/issues-pr/Trustiva7777/Trustiva-Ai-?color=C7A340&label=PRs)](https://github.com/Trustiva7777/Trustiva-Ai-/pulls)
[![Status](https://img.shields.io/badge/Status-Alpha-C7A340.svg)](#)

<sub style="color:#888">Theme: Trustiva Classic — black with gold accents (#C7A340).</sub>

</div>

## Table of Contents

1. Overview
2. Mission & Vision
3. Architecture
4. Core Features
5. Technology Stack
6. System Workflow
7. Smart Contracts
8. AI Swarm
9. Ops API
10. Web Verification UI
11. Jurisdictional Compliance
12. Installation
13. Development
14. Testing
15. Environment Variables
16. Deployment
17. Security
18. Governance & DAO Extensions
19. Roadmap
20. Contributing
21. Credits
22. License

---

## 1. Overview

Trustiva AI + Proof Kernel is a sovereign‑grade audit engine that fuses AI‑generated intelligence with blockchain verification. It provides a reproducible, cryptographically verifiable trust loop — from data creation, to AI validation, to immutable proof anchoring.

---

## 2. Mission & Vision

- AI as a compliance instrument
- Provable truth across jurisdictional contexts

---

## 3. Architecture

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

| Layer   | Component                  | Description                        |
| ------- | -------------------------- | ---------------------------------- |
| Client  | UI / CLI                   | Publishes and verifies bundles     |
| API     | Ops (FastAPI)              | Policy engine, jurisdiction gating |
| AI      | Swarm Orchestrator         | Quorum-based validation            |
| Chain   | ProofChain + AuditRegistry | Smart contracts                    |
| Storage | IPFS / XRPL / Polygon      | Distributed persistence            |

---

## 4. Core Features

- ✅ End-to-end proof pipeline — IPFS → AI → Smart Contract
- 🧩 Modular architecture — ops, swarm, chain as independent services
- 🧠 AI Quorum validation — Level‑7 swarm consensus
- 🛡️ Jurisdictional compliance — policy YAML enforcement (planned)
- 🧾 Proof-of-Integrity registry — cryptographic finalization on-chain
- 🔍 Open verification — UI & public audit endpoints

---

## 5. Technology Stack

| Domain           | Tech                                |
| ---------------- | ----------------------------------- |
| AI Orchestration | Python 3.12, FastAPI, Redis, Qdrant |
| Smart Contracts  | Solidity 0.8.x, Hardhat, Ethers v6  |
| Web Interface    | Next.js 14, React, Tailwind         |
| Storage          | IPFS, Pinata, XRPL                  |
| DevOps           | Docker, Makefile, GitHub Actions CI |
| Testing          | Pytest, Hardhat Mocha, Vitest       |
| Security         | OpenPGP, Chainlink VRF-ready        |

---

## 6. System Workflow

1. Publish artifacts to IPFS.
2. Compute SHA256 → Keccak root.
3. Swarm attests quorum.
4. ProofChain finalizes hash.
5. AuditRegistry registers CID + root.
6. UI verifies via OpenPGP + XRPL live check.

---

## 7. Smart Contracts

| Contract          | Description            | Key Methods                 |
| ----------------- | ---------------------- | --------------------------- |
| ProofChain.sol    | Finalization guard     | `finalize(root)`            |
| AuditRegistry.sol | Registers proof bundle | `registerBundle(root, cid)` |

Short snippet:

```solidity
require(poi.isFinal(root), "Not finalized");
emit BundleRegistered(root, cid);
```

---

## 8. AI Swarm

- ProofAgent — verifies CID integrity
- AuditAgent — validates signers
- XRPLAgent — confirms XRPL anchoring
- GovernanceAgent — checks jurisdiction rules
- Quorum logic and optional auto-submit (`SWARM_AUTOSUBMIT`, `SWARM_QUORUM`)

---

## 9. Ops API

Endpoints (GET/POST):

- `/health`
- `/ops/policy`
- `/registry/resolve`
- `/swarm/attest`
- `/verify/xrpl/live`

Sample:

```bash
curl -s -X POST http://localhost:9000/swarm/attest \
  -H "content-type: application/json" \
  -d '{"root":"0x..","cid":"Qm.."}' | jq .
```

---

## 10. Web Verification UI

- Next.js verification UI with OpenPGP signature check
- CID ↔ XRPL cross-check visualization
- Path: `apps/web/app/registry/verify/page.jsx`

---

## 11. Jurisdictional Compliance

| Region | Restriction               | Flag        |
| ------ | ------------------------- | ----------- |
| EU/UK  | Retail promo disallowed   | GDPR=on     |
| US     | Full access               | GDPR=off    |
| UAE/KSA| Require Shariah audit     | travel_rule |

---

## 12. Installation

```bash
make up
make pipeline
```

---

## 13. Development

```bash
docker compose up ops swarm chain
pytest -q
```

---

## 14. Testing

```bash
pytest -q
HARDHAT_CONFIG=hardhat.config.cjs npx hardhat test --network localhost
```

---

## 15. Environment Variables

| Name               | Default                            | Description         |
| ------------------ | ---------------------------------- | ------------------- |
| REGION             | US                                 | Jurisdiction        |
| SWARM_AUTOSUBMIT   | false                              | Auto finalization   |
| OPS_API_URL        | http://ops:9000                    | Internal API route  |
| AUDIT_PUBKEY       | —                                  | Audit key reference |

---

## 16. Deployment

- Docker Compose orchestration
- GitHub Actions CI/CD
- Optional IPFS publish

---

## 17. Security

- .gitignore protections for data/* and build artifacts
- GPG key storage recommendations
- Never put secrets in build context or logs

---

## 18. Governance & DAO Extensions

- DAO proof approval (planned)
- Tokenized compliance credits (planned)
- Vault agents (planned)

---

## 19. Roadmap

| Phase | Focus                  | ETA      |
| ----- | ---------------------- | -------- |
| v1.1  | Autosubmit logic       | Nov 2025 |
| v1.2  | Governance + Analytics | Dec 2025 |
| v1.3  | DAO integration        | Q1 2026  |

---

## 20. Contributing

- Branch policy: feature/*, fix/*
- Conventional commits
- PR checks: lint, test, docs

---

## 21. Credits

- Kevan Burns — Sovereign Infrastructure Architect
- Trustiva Engineering Division
- AI Swarm Maintainers (Level‑7)

---

## 22. License

MIT — see [`LICENSE`](./LICENSE).
