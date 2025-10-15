# Trustiva MCP + n8n Agentic Playbook

A modular control system that lets the Trustiva orchestrator (FastAPI + LangGraph) coordinate AI agents, data pipelines, and smart-contract operations through n8n and MCP nodes — all tied to IPFS and optional XRPL/Polygon anchoring.

---

## 1) Architecture Overview

- Orchestrator: FastAPI service with LangGraph nodes (marketing, webmaster, support, compliance)
- MCP agent layer: logical agents mapped to LangGraph nodes and/or microservices
- n8n pipelines: ingest, generate, publish, anchor, notify
- Connectors:
  - IPFS: API :5201, gateway :8082 (dockerized fallback), script `scripts/publish_to_ipfs.py`
  - LLMs: Hugging Face (primary), OpenAI (fallback)
  - Zoho Ops: `services/api/main.py` + `services/workers/zoho_worker.py`
  - XRPL/Polygon: optional anchoring/minting scripts
- CI/Tasks: Makefile targets, VS Code tasks, GitHub Actions CI

Reference services and scripts in this repo:
- `services/orchestrator/main.py` (core orchestrator)
- `scripts/run-ipfs-daemon.sh` (daemon or dockerized fallback)
- `scripts/publish_to_ipfs.py` (CLI or HTTP API)
- `scripts/mint-token.mjs` (Polygon mint stub)

---

## 2) n8n Pipeline Design

Typical modules:

- Triggers:
  - Webhook → `POST /swarm/run` (or call orchestrator directly)
  - Cron → scheduled publish + anchor
  - CI event → on push
- Actions:
  - Publish to IPFS → HTTP request to orchestrator `/swarm/run` with task "publish"
  - XRPL Anchor → call `node scripts/xrpl-anchor-cid.mjs <CID>` (stubbed)
  - Generate Content → HTTP request to orchestrator `/swarm/run` with task "content"
  - Zoho mail/contact → Ops API endpoints
- Function nodes:
  - Transform payloads, pick `cid` from responses, map variables across nodes
- Notifications:
  - Slack/Discord/email summarizing CID, anchor tx, and links

---

## 3) MCP Agent Routing

- Agents are modeled as LangGraph nodes in the orchestrator:
  - Marketing → LLM copy generation
  - Webmaster → IPFS publish and site build
  - Compliance → anchoring and notarization (XRPL/Polygon)
  - Support → Zoho ticket and email
- n8n triggers call these via REST to `/swarm/run` with a `task` and `params`.

---

## 4) Runbook

- Environment (.env):
  - HUGGING / HF_MODEL or OPENAI_* for LLMs
  - IPFS_API (http://127.0.0.1:5201), IPFS_GATEWAY (http://127.0.0.1:8082)
  - ZOHO_* for Ops API/worker
- Makefile targets:
  - `make run-ipfs` → ensure IPFS daemon (dockerized fallback ok)
  - `make run` → start orchestrator (port 8000)
  - `make publish` → publish `dist/` to IPFS; writes `dist/publish.json`
  - `make verify` → HEAD + content check via gateway
  - `make smoke` → end-to-end health → publish → verify
  - `make run-ops`, `make run-worker` → Ops API and worker
- VS Code tasks mirror the same flows for one-click runs.

---

## 5) Security & Observability

- Secrets: use `.env` locally; GitHub/Codespaces secrets in CI
- Token refresh: Zoho handled by `services/zoho_client.py`
- Immutable audit: IPFS CID + optional XRPL anchor transaction
- Logging: FastAPI + file queue for Ops; extend to OTEL if needed

---

## 6) Optional Multichain Extensions

- XRPL: anchor CID via script; record tx hash alongside publish.json
- Polygon: mint/anchor via `scripts/mint-token.mjs`; store note `ipfs://<CID>`
- Registry: maintain `trustiva-registry.json` to log CID, anchor tx, mint tx, and commit SHA

---

## 7) n8n Flow (import sketch)

- HTTP Request (orchestrator publish) → Function (extract `cid`) → HTTP Request (XRPL anchor) → Slack (notify)
- Alternate triggers: Webhook → Generate Content → Publish → Notify

---

## 8) Quick commands

- Run locally:
  - `make run-ipfs && make run`
- Publish + verify:
  - `make publish && make verify`
- Full smoke:
  - `make smoke`

---

## 9) Next steps

- Add pytest smoke for /health and mocked publish
- Enable HF or OpenAI creds for LLM content
- Fill XRPL anchor implementation; decide on production gateway
- Wire a real n8n flow JSON with environment variables mapping to `.env`

---

## 10) M3 — Sovereign Chain Operations

Goal: On publish, anchor CID to XRPL with memos and mint a soulbound ERC-721 on Polygon with tokenURI=ipfs://CID, then log to registry and notify.

Environment:

```
# Polygon
POLYGON_RPC=https://polygon-rpc.com
POLYGON_PRIVATE_KEY=0x...
MINT_CONTRACT=0xYourSoulboundNFT

# XRPL (testnet default)
XRPL_NET=testnet
XRPL_SEED=sn_...
```

Scripts:
- scripts/xrpl-anchor-cid.mjs <CID> [sha256] → submits Payment with trustiva memo; returns tx_hash + explorer URL.
- scripts/mint-token.mjs --contract=<addr> --note=ipfs://<CID> --send → calls safeMint(to, tokenURI); parses tokenId.
- scripts/registry-update.mjs --cid=<CID> --xrpl=<tx> --polygon=<tx> [--url=<gateway-url>] → appends NDJSON entry.

Workflow:
1. Publish dist → CID.
2. Verify gateway.
3. Anchor on XRPL.
4. Mint on Polygon.
5. Update registry (trustiva-registry.ndjson).
6. Notify via Slack + Zoho.

Notes:
- If seeds/keys missing, scripts run in dry-run mode and exit safely.
- Soulbound enforcement is contract-level; ensure your contract rejects transfers.
