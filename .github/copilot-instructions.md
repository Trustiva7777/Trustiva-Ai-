# AI Ops Playbook — Trustiva

## Mission

- Own the entire code + build + publish loop.
- Keep the app compiling, tests green, site published to Trustiva IPFS, and optional on-chain anchoring/minting ready.
- Use Hugging Face Inference by default; fall back to OpenAI if HF isn’t configured.
- Never leak secrets. Never block on interactive prompts.

---

## Environment & Secrets

### Required (set in `.env` or GitHub Codespaces/Repo Secrets)

```
# IPFS / Trustiva node
IPFS_API=/ip4/127.0.0.1/tcp/5201
IPFS_GATEWAY=http://127.0.0.1:8082
# Optional auth header: "Basic <base64>" or a token your publisher expects
IPFS_AUTH=

# Hugging Face
HUGGING=hf_************************
HF_MODEL=bigscience/bloomz-560m  # example; change as needed

# OpenAI fallback (optional)
OPENAI_API_KEY=sk-***********************
OPENAI_MODEL=gpt-4o-mini          # optional; pick any deployed model

# Polygon (optional on-chain step)
POLYGON_RPC=https://polygon-rpc.com
POLYGON_PRIVATE_KEY=0x...
POLYGON_CHAIN_ID=137
```

AI behavior:

- If `HUGGING` and `HF_MODEL` are set → use HF Inference API.
- Else if `OPENAI_API_KEY` is set → use OpenAI fallback.
- Else → skip generation features, continue build/publish.

---

## Daily Loop (what the AI runs)

1. Install & test

```bash
npm ci
npm test --silent
```

2. Build

```bash
npm run build
```

3. Ensure IPFS daemon

- If a daemon is already listening on 5201/8082, reuse it.
- Else run:

```bash
bash scripts/run-ipfs-daemon.sh || true
```

4. Publish to Trustiva IPFS

- Dev/preview API:

```bash
curl -sS "http://localhost:3000/api/publish?path=dist" | jq .
```

- Or direct helper:

```bash
python3 scripts/publish_to_ipfs.py dist | tee publish.result.json
```

- Success criteria:
  - Receive a root CID.
  - Verify gateway serves: `curl -I "$IPFS_GATEWAY/ipfs/<CID>/"` returns 200.

5. Write/verify `dist/publish.json`

- Must contain: `cid`, `gateway`, `path`, `time`, `host`.

6. (Optional) On-chain step

```bash
# XRPL (testnet) anchor example
# export XRPL_NET=testnet XRPL_SEED=sn_...
# node scripts/xrpl-anchor-cid.js <CID>

# Polygon mint/anchor example
node scripts/mint-token.mjs --note "ipfs://<CID>" --send
```

7. Certificates (on demand)

```bash
python3 scripts/issue_certificate.py "Jane Doe" rTESTADDRESS | jq .
# If XRPL env provided and --anchor used, attach tx hash in output.
```

---

## HF Inference Usage (default)

Node/TS helper shape:

```ts
// hf_generate.ts
import fetch from "node-fetch";

export async function hfGenerate(prompt: string) {
  const { HUGGING, HF_MODEL, OPENAI_API_KEY, OPENAI_MODEL } = process.env;

  // HF primary
  if (HUGGING && HF_MODEL) {
    const res = await fetch(`https://api-inference.huggingface.co/models/${HF_MODEL}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${HUGGING}`, "Content-Type": "application/json" },
      body: JSON.stringify({ inputs: prompt })
    });
    if (res.ok) return await res.json();
  }

  // OpenAI fallback
  if (OPENAI_API_KEY) {
    const model = OPENAI_MODEL || "gpt-4o-mini";
    const r = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${OPENAI_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages: [{ role: "user", content: prompt }] })
    });
    if (!r.ok) throw new Error(`OpenAI error: ${r.status}`);
    return await r.json();
  }

  // Neither configured
  return { error: "No inference backend configured" };
}
```

---

## Local Inference Option

- Extend docker-compose with TGI or vLLM service.
- Add env switch: `HF_BACKEND=local|hf|openai`.
- In `hf_generate.ts`, route based on `HF_BACKEND` to local `http://tgi:8080/generate` (or vLLM endpoint).

---

## GitHub Actions (CI)

- Use a two-job pipeline (build-and-publish → anchor-or-mint). Ensure secrets exist before enabling on-chain job.
- Post the gateway preview and CID in the job summary.

---

## VS Code Tasks (one-click)

- Hardhat: Compile — hardhat compile
- Hardhat: Deploy (polygon) — read `POLYGON_*` env
- Generate vouchers/QR — `scripts/generate_vouchers_and_qr.ts`
- Publish to Trustiva IPFS — calls `publish_to_ipfs.py dist`
- Run backend (FastAPI) if present

---

## Guardrails for the AI

- Never print token values in logs or commit them.
- If IPFS shows repo.lock errors: detect running PID, reuse; do not kill user processes.
- If publish returns CID but gateway 404s, wait and retry.
- Open a PR for structural changes; commit small fixes to a feature branch.

---

## PR Acceptance Checklist

- `npm ci && npm test` pass
- `npm run build` pass
- `/api/publish?path=dist` returns CID; `dist/publish.json` written
- Gateway serves `index.html` at `/ipfs/<CID>/`
- (If enabled) On-chain step logs tx hash with CID reference
- No secrets in diff; `.env` untouched

---

## Optional Connectors

- Twilio inbound webhooks (SMS/voice) → task queue
- SendGrid/Gmail outbound + inbound parsing → ticketing
- Zoho: Bigin/CRM basic OAuth & lead ingest
- Redis Streams for event bus; Qdrant for vector search
- LangGraph nodes: `ads`, `analytics`, `seo_programmatic`, `affiliate_qr`, `human_approval`
