#!/usr/bin/env bash
set -euo pipefail

echo "🔎 /health"
curl -sS http://127.0.0.1:8000/health | jq .

echo "📦 publish"
RES=$(curl -sS -X POST http://127.0.0.1:8000/swarm/run \
  -H 'Content-Type: application/json' \
  -d '{"task":"publish","params":{"path":"dist"}}')
echo "$RES" | jq .
CID=$(echo "$RES" | jq -r .cid)

echo "✅ verify $CID"
curl -sS -I "http://127.0.0.1:8082/ipfs/$CID/" | head -n1
curl -sS "http://127.0.0.1:8082/ipfs/$CID/index.html" | head -n 5
