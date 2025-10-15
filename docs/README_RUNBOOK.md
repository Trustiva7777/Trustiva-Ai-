# Trustiva Proof Chain — Developer Runbook

This runbook describes how to boot the Trustiva kernel locally and run the full end-to-end proof pipeline: publish → verify → hash → swarm attest → on-chain finalize + register.

## Quick start

```bash
make up && make pipeline
```

What this does:
- Starts Docker services (ops, swarm, redis, qdrant, chain)
- Waits for Ops API health
- Publishes the `dist/` folder to IPFS and verifies the gateway
- Computes the bundle hash and requests a Level-7 swarm attestation
- Finalizes the root and registers the CID on the local devnet

## Environment

These environment variables can be provided via `.env` or your shell and are consumed by the services and scripts.

| Variable | Default | Purpose |
| --- | --- | --- |
| IPFS_API | http://127.0.0.1:5201 | Kubo API address for IPFS helper scripts |
| IPFS_GATEWAY | http://127.0.0.1:8082 | Gateway base URL for HEAD checks and links |
| HUGGING | – | Hugging Face token (if using HF inference) |
| HF_MODEL | – | HF model id (e.g. bigscience/bloomz-560m) |
| OPENAI_API_KEY | – | OpenAI fallback API key |
| OPENAI_MODEL | gpt-4o-mini | OpenAI model name fallback |
| XRPL_NET | testnet | XRPL explorer net for links (testnet/mainnet) |
| POLYGON_RPC | https://polygon-rpc.com | JSON-RPC endpoint for Polygon verify |
| AUDIT_PUBKEY | – | Armored OpenPGP public key for signature verification UI |
| SWARM_AUTOSUBMIT | false | If true, swarm will auto-submit on quorum |
| SWARM_QUORUM | 0.67 | Quorum threshold for autosubmit |
| OPS_API_URL | http://ops:9000 | Internal URL the swarm uses to reach ops |

## Architecture (services)

- ops — FastAPI orchestrator (registry resolver, XRPL verify, auditing endpoints, `/swarm/attest`)
- swarm — Level-7 AI quorum engine (ProofAgent, AuditAgent, XRPLAgent, GovernanceAgent)
- chain — Local EVM chain for development (Ganache in docker-compose)
- redis — Pub/sub + caching for queues and agent comms
- qdrant — Vector store for semantic search/logs (optional)

## Workflow (end-to-end)

1. Publish
   - `scripts/publish_to_ipfs.py` adds the `dist/` directory to IPFS and writes `dist/publish.json` containing { cid, gateway, path, time }.
2. Verify
   - Ops API HEAD-checks the IPFS gateway for the published CID.
3. Hash
   - `scripts/hash_directory.py` computes a deterministic SHA-256 over `dist/` → `dist/audit-bundle.json.sha256`.
4. Swarm attest
   - POST `/swarm/attest` aggregates votes from Proof/Audit/XRPL/Governance agents and returns a quorum score.
5. Finalize + register
   - Runner finalizes the root on `ProofChain` and registers the CID on `AuditRegistry` (gated by `isFinal(root)`).

## Useful commands

- Start services and wait for Ops API
  ```bash
  make up
  ```
- Run the full loop
  ```bash
  make pipeline
  ```
- Tear down containers
  ```bash
  make down
  ```
- Python tests
  ```bash
  pytest -q
  ```
- Contracts
  ```bash
  HARDHAT_CONFIG=hardhat.config.cjs npx hardhat compile
  HARDHAT_CONFIG=hardhat.config.cjs npx hardhat test --network localhost
  ```
- Web build
  ```bash
  npm run -s build --prefix apps/web
  ```

## Notes

- The Makefile normalizes the root hash to a 0x-prefixed 32-byte hex before calling contracts.
- Ops API exposes both GET and POST variants for key endpoints, so workflow tools can always POST JSON.
- To enable autosubmit at the swarm layer, set `SWARM_AUTOSUBMIT=true` (and ensure a submit hook is in place) — the Makefile already provides `proof-submit` if you prefer external orchestration.