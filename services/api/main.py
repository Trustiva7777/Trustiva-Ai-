from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr
from pathlib import Path
import json, time, uuid, os
import httpx
import asyncio, subprocess, sys

QUEUE_DIR = Path("queue/pending")
DONE_DIR = Path("queue/done")
FAIL_DIR = Path("queue/failed")
for d in (QUEUE_DIR, DONE_DIR, FAIL_DIR):
    d.mkdir(parents=True, exist_ok=True)


class EmailJob(BaseModel):
    to: EmailStr
    subject: str
    text: str | None = None
    html: str | None = None
    cc: list[EmailStr] | None = None
    bcc: list[EmailStr] | None = None


class BiginUpsertJob(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] | None = None


app = FastAPI(title="Trustiva Ops API")


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": time.time()}


@app.post("/ops/zoho/send_mail")
def send_mail(job: EmailJob):
    job_id = f"mail-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    payload = {"type": "send_mail", "job_id": job_id, "data": job.dict()}
    (QUEUE_DIR / f"{job_id}.json").write_text(json.dumps(payload))
    return {"queued": True, "job_id": job_id}


@app.post("/ops/zoho/upsert_contact")
def upsert_contact(job: BiginUpsertJob):
    job_id = f"bigin-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    payload = {"type": "upsert_contact", "job_id": job_id, "data": job.dict()}
    (QUEUE_DIR / f"{job_id}.json").write_text(json.dumps(payload))
    return {"queued": True, "job_id": job_id}


@app.post("/events/zoho")
async def zoho_events(req: Request):
    body = await req.body()
    job_id = f"webhook-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    (DONE_DIR / f"{job_id}.http").write_bytes(body)
    return {"ok": True}


def _registry_path() -> Path:
    return Path(os.getenv("REGISTRY_PATH", "trustiva-registry.ndjson"))


# Swarm attest proxy (kernel nervous system)
class AttestIn(BaseModel):
    root: str
    cid: str | None = None


@app.post("/swarm/attest")
async def swarm_attest(body: AttestIn):
    # Route to local ai_swarm if imported; otherwise return basic quorum calc using xrpl + audit checks
    try:
        from ai_swarm.orchestrator import AGENTS  # type: ignore
        import asyncio as _asyncio
        results = await _asyncio.gather(*[a(body.root, body.cid) for a in AGENTS])
        quorum = sum(getattr(r, 'confidence', 0.0) for r in results) / len(results)
        return {
            "root": body.root,
            "cid": body.cid,
            "votes": [getattr(r, 'model_dump', lambda: dict(r))() if hasattr(r, 'model_dump') else dict(r.__dict__) for r in results],
            "quorum": quorum,
        }
    except Exception:
        # Minimal fallback: XRPL live weight + audit pubkey presence
        xr = await verify_xrpl_live_post({"tx": "", "wait": False})
        has_pubkey = bool(os.getenv("AUDIT_PUBKEY", ""))
        votes = [
            {"name": "XRPLAgent", "confidence": 0.6 if xr.get("validated") else 0.4, "details": xr},
            {"name": "AuditAgent", "confidence": 0.8 if has_pubkey else 0.4, "details": {"has_pubkey": has_pubkey}},
        ]
        quorum = sum(v["confidence"] for v in votes) / len(votes)
        return {"root": body.root, "cid": body.cid, "votes": votes, "quorum": quorum}


@app.get("/registry")
def get_registry(limit: int = 100):
    path = _registry_path()
    if not path.exists():
        return {"entries": []}
    lines = path.read_text().strip().splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except Exception:
            continue
    return {"entries": entries}


@app.get("/verify/cid/{cid}")
async def verify_cid(cid: str):
    gateway = os.getenv("IPFS_GATEWAY", "http://127.0.0.1:8082")
    url = f"{gateway}/ipfs/{cid}/"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.head(url)
        return {"cid": cid, "status": r.status_code, "ok": r.status_code == 200, "url": url}


@app.get("/verify/polygon/{tx_hash}")
async def verify_polygon(tx_hash: str):
    rpc = os.getenv("POLYGON_RPC", "https://polygon-rpc.com")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(rpc, json={
            "jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_hash]
        })
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="RPC error")
        data = r.json()
        return {"tx": tx_hash, "result": data.get("result")}


@app.get("/verify/xrpl/{tx_hash}")
async def verify_xrpl(tx_hash: str):
    # For now, return an explorer link; future: call XRPL websocket/JSON-RPC.
    net = os.getenv("XRPL_NET", "testnet")
    explorer = (
        f"https://livenet.xrpl.org/transactions/{tx_hash}" if net == "mainnet" else f"https://testnet.xrpl.org/transactions/{tx_hash}"
    )
    return {"tx": tx_hash, "explorer": explorer}


@app.get("/verify/xrpl/live/{tx_hash}")
async def verify_xrpl_live(tx_hash: str, wait: bool = False):
    """Calls the Node script to check XRPL tx validation, optionally waiting."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", "scripts/xrpl-verify-live.mjs", tx_hash, *( ["--wait"] if wait else [] ),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        if proc.returncode == 0:
            return json.loads(out.decode("utf-8") or "{}")
        return {"error": (err or out).decode("utf-8"), "tx": tx_hash}
    except Exception as e:
        return {"error": str(e), "tx": tx_hash}


@app.get("/audit/pubkey")
def audit_pubkey():
    key = os.getenv("AUDIT_PUBKEY", "")
    return {"pubkey": key}


@app.get("/registry/resolve")
async def registry_resolve(cid: str | None = None):
    # Pick latest entry if cid not provided
    reg = get_registry(limit=1000)["entries"]
    entry = None
    if cid:
        for e in reversed(reg):
            if e.get("cid") == cid:
                entry = e
                break
    else:
        entry = (reg or [None])[-1]
    if not entry:
        raise HTTPException(status_code=404, detail="CID not found in registry")

    # Gateway check
    gw_url = entry.get("url") or f"{os.getenv('IPFS_GATEWAY','http://127.0.0.1:8082')}/ipfs/{entry.get('cid')}/"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            head = await client.head(gw_url)
            gw = {"url": gw_url, "status": head.status_code, "ok": head.status_code == 200}
        except Exception:
            gw = {"url": gw_url, "status": None, "ok": False}

    # Polygon receipt (best-effort)
    poly = None
    txp = entry.get("polygon")
    if isinstance(txp, dict):
        txh = txp.get("tx") or txp.get("hash")
    else:
        txh = txp
    if txh:
        try:
            poly = await verify_polygon(txh)
        except Exception:
            poly = {"tx": txh}

    # XRPL link
    xr = None
    xv = entry.get("xrpl")
    if isinstance(xv, dict):
        xtx = xv.get("tx") or xv.get("tx_hash")
    else:
        xtx = xv
    if xtx:
        xr = await verify_xrpl(xtx)

    bundle = {
        "cid": entry.get("cid"),
        "time": entry.get("time"),
        "url": gw_url,
        "sha256": entry.get("sha") or entry.get("sha256"),
        "gateway": gw,
        "polygon": poly,
        "xrpl": xr,
        "entry": entry,
    }
    return bundle


# Kernel POST aliases for universal call shapes
@app.post("/registry/resolve")
async def registry_resolve_post(body: dict):
    return await registry_resolve(cid=body.get("cid"))


@app.post("/verify/xrpl/live")
async def verify_xrpl_live_post(body: dict):
    tx = body.get("tx")
    if not isinstance(tx, str) or not tx:
        raise HTTPException(status_code=400, detail="tx is required")
    return await verify_xrpl_live(tx_hash=tx, wait=bool(body.get("wait")))
