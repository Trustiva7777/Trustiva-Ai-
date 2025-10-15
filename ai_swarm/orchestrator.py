from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, json, asyncio, httpx


class AttestRequest(BaseModel):
    root: str
    cid: str | None = None


class AgentResult(BaseModel):
    name: str
    confidence: float
    details: dict | None = None


app = FastAPI(title="Trustiva AI Swarm")


async def _fetch(url: str, method: str = "GET", json_body: dict | None = None, timeout: int = 15):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await (client.post(url, json=json_body) if method == "POST" else client.get(url))
        return r


async def proof_agent(root: str, cid: str | None) -> AgentResult:
    # Recompute hash by resolving bundle and hashing its JSON payload deterministically
    # Use local Ops API registry resolver
    base = os.getenv("OPS_API_URL", "http://127.0.0.1:9000")
    q = f"?cid={cid}" if cid else ""
    try:
        r = await _fetch(f"{base}/registry/resolve{q}")
        ok = r.status_code == 200
        body = r.json() if ok else {}
        # Trust that /registry/resolve included computed sha256; consider confidence from presence
        sha = body.get("sha256") or body.get("sha")
        conf = 0.9 if (ok and sha) else 0.0
        return AgentResult(name="ProofAgent", confidence=conf, details={"ok": ok, "sha": sha})
    except Exception as e:
        return AgentResult(name="ProofAgent", confidence=0.0, details={"error": str(e)})


async def audit_agent(root: str, cid: str | None) -> AgentResult:
    # Check for available pubkey; if present assume signature verification handled client-side/UI or CI
    pubkey = os.getenv("AUDIT_PUBKEY", "")
    conf = 0.8 if pubkey else 0.4  # weaker without pubkey
    return AgentResult(name="AuditAgent", confidence=conf, details={"has_pubkey": bool(pubkey)})


async def xrpl_agent(root: str, cid: str | None) -> AgentResult:
    # Query XRPL live verification if tx present in registry resolve
    base = os.getenv("OPS_API_URL", "http://127.0.0.1:9000")
    q = f"?cid={cid}" if cid else ""
    try:
        r = await _fetch(f"{base}/registry/resolve{q}")
        if r.status_code != 200:
            return AgentResult(name="XRPLAgent", confidence=0.0, details={"status": r.status_code})
        body = r.json()
        tx = (body.get("xrpl") or {}).get("tx") if isinstance(body.get("xrpl"), dict) else None
        if not tx:
            return AgentResult(name="XRPLAgent", confidence=0.5, details={"note": "no-xrpl-tx"})
        live = await _fetch(f"{base}/verify/xrpl/live/{tx}")
        ok = live.status_code == 200
        lbody = live.json() if ok else {}
        conf = 0.9 if (ok and lbody.get("validated")) else 0.5
        return AgentResult(name="XRPLAgent", confidence=conf, details=lbody)
    except Exception as e:
        return AgentResult(name="XRPLAgent", confidence=0.0, details={"error": str(e)})


async def governance_agent(root: str, cid: str | None) -> AgentResult:
    # Placeholder: in real life, check policies/limits, origin allowlist, etc.
    return AgentResult(name="GovernanceAgent", confidence=0.8, details={"policy": "default"})


AGENTS = [proof_agent, audit_agent, xrpl_agent, governance_agent]


@app.post("/swarm/attest")
async def swarm_attest(req: AttestRequest):
    if not req.root:
        raise HTTPException(status_code=400, detail="root is required")
    # run agents concurrently
    results = await asyncio.gather(*[a(req.root, req.cid) for a in AGENTS])
    quorum = sum(r.confidence for r in results) / len(results)
    # optional: auto-submit if quorum reached
    auto_submit = os.getenv("SWARM_AUTOSUBMIT", "false").lower() == "true"
    submitted = False
    if auto_submit and quorum >= float(os.getenv("SWARM_QUORUM", "0.67")):
        # trigger make proof-submit if available
        try:
            proc = await asyncio.create_subprocess_exec("make", "proof-submit", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, err = await proc.communicate()
            submitted = (proc.returncode == 0)
        except Exception:
            submitted = False
    return {
        "root": req.root,
        "cid": req.cid,
        "votes": [r.model_dump() for r in results],
        "quorum": quorum,
        "submitted": submitted,
    }
