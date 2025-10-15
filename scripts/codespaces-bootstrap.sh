#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODESPACE_VSCODE_FOLDER:-$PWD}"

# Prefer read-only HF token if present
HF_TOKEN="${HUGGINGREAD:-${HUGGING:-${HUGGINGWRITE:-}}}"

# If IPFS provided as JSON, extract parts
if [[ -n "${IPFS:-}" && "${IPFS}" =~ ^\{ ]]; then
  IPFS_API=$(jq -r '.API // empty' <<<"${IPFS}")
  IPFS_GATEWAY=$(jq -r '.GATEWAY // empty' <<<"${IPFS}")
  IPFS_AUTH=$(jq -r '.AUTH // empty' <<<"${IPFS}")
fi

ENV="$ROOT/.env"
touch "$ENV"
awk 'BEGIN{print ""}' >> "$ENV"  # newline
grep -q '^HUGGING=' "$ENV" || echo "HUGGING=${HF_TOKEN:-}" >> "$ENV"
grep -q '^HF_MODEL=' "$ENV" || echo "HF_MODEL=HuggingFaceH4/zephyr-7b-beta" >> "$ENV"
grep -q '^HF_API_BASE=' "$ENV" || echo "HF_API_BASE=https://api-inference.huggingface.co/models" >> "$ENV"
grep -q '^IPFS_API=' "$ENV" || echo "IPFS_API=${IPFS_API:-http://127.0.0.1:5201}" >> "$ENV"
grep -q '^IPFS_GATEWAY=' "$ENV" || echo "IPFS_GATEWAY=${IPFS_GATEWAY:-http://127.0.0.1:8082}" >> "$ENV"
if [[ -n "${IPFS_AUTH:-}" ]]; then
  grep -q '^IPFS_AUTH=' "$ENV" || echo "IPFS_AUTH=${IPFS_AUTH}" >> "$ENV"
fi

# Optional fallbacks
if [[ -n "${OPENAI:-}" ]]; then
  grep -q '^OPENAI_API_KEY=' "$ENV" || echo "OPENAI_API_KEY=${OPENAI}" >> "$ENV"
fi
if [[ -n "${POLYGON:-}" ]]; then
  grep -q '^POLYGON_RPC=' "$ENV" || echo "POLYGON_RPC=${POLYGON}" >> "$ENV"
fi

# Auditor public key (armored)
if [[ -n "${AUDIT_PUBKEY:-}" ]]; then
  grep -q '^AUDIT_PUBKEY=' "$ENV" || echo "AUDIT_PUBKEY=${AUDIT_PUBKEY}" >> "$ENV"
fi

echo "✅ .env refreshed from Codespaces secrets"
