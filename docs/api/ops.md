# Ops API Reference

This page documents key Ops API endpoints and selected Python interfaces.

## Endpoints

- `/registry/resolve` — Resolve registry entries (GET/POST)
- `/verify/xrpl/live` — XRPL live verification bridge (GET/POST)
- `/swarm/attest` — Request a Level‑7 swarm attestation (POST)
- `/audit/pubkey` — Get the OpenPGP public key (GET)

## Usage examples

Base URL (local): `http://127.0.0.1:9000` (or `http://localhost:9000`).

### Swarm attestation — POST /swarm/attest

- curl

```bash
BASE=http://127.0.0.1:9000
curl -sS -X POST "$BASE/swarm/attest" \
  -H 'Content-Type: application/json' \
  -d '{"root":"0xabc123...","cid":"bafybeigd..."}' | jq .
```

- Python (requests)

```python
import requests
BASE = "http://127.0.0.1:9000"
resp = requests.post(f"{BASE}/swarm/attest", json={
    "root": "0xabc123...",
    "cid": "bafybeigd..."
})
print(resp.json())  # {"root":..., "cid":..., "votes": [...], "quorum": 0.73}
```

### Resolve latest (or specific) bundle — GET/POST /registry/resolve

- GET with query

```bash
BASE=http://127.0.0.1:9000
# Latest
curl -sS "$BASE/registry/resolve" | jq .
# Specific CID
curl -sS "$BASE/registry/resolve?cid=bafybeigd..." | jq .
```

- POST with JSON body

```bash
BASE=http://127.0.0.1:9000
curl -sS -X POST "$BASE/registry/resolve" \
  -H 'Content-Type: application/json' \
  -d '{"cid":"bafybeigd..."}' | jq .
```

- Python (requests)

```python
import requests
BASE = "http://127.0.0.1:9000"
r = requests.get(f"{BASE}/registry/resolve", params={"cid": "bafybeigd..."})
bundle = r.json()
print(bundle["gateway"], bundle.get("polygon"), bundle.get("xrpl"))
```

### XRPL live verification — GET/POST /verify/xrpl/live

- GET

```bash
BASE=http://127.0.0.1:9000
TX=<XRPL_TX_HASH>
curl -sS "$BASE/verify/xrpl/live/$TX?wait=true" | jq .
```

- POST

```bash
BASE=http://127.0.0.1:9000
TX=<XRPL_TX_HASH>
curl -sS -X POST "$BASE/verify/xrpl/live" \
  -H 'Content-Type: application/json' \
  -d "{\"tx\":\"$TX\",\"wait\":true}" | jq .
```

- Python (requests)

```python
import requests
BASE = "http://127.0.0.1:9000"
TX = "<XRPL_TX_HASH>"
r = requests.post(f"{BASE}/verify/xrpl/live", json={"tx": TX, "wait": True})
print(r.json())  # Example: {"validated": true, "tx": "...", ...}
```

### Audit public key — GET /audit/pubkey

- curl

```bash
BASE=http://127.0.0.1:9000
curl -sS "$BASE/audit/pubkey" | jq .  # {"pubkey": "-----BEGIN PGP PUBLIC KEY BLOCK-----..."}
```

- Python (requests)

```python
import requests
BASE = "http://127.0.0.1:9000"
print(requests.get(f"{BASE}/audit/pubkey").json())
```

## Python Interfaces

::: services.api.main
    handler: python
    options:
      show_root_heading: true
      show_source: false
