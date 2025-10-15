from fastapi.testclient import TestClient
import types

from services.api.main import app as ops


def test_registry_empty_ok(tmp_path, monkeypatch):
    # ensure no registry file present
    client = TestClient(ops)
    r = client.get("/registry")
    assert r.status_code == 200
    assert "entries" in r.json()


def test_verify_cid_mocks_head(monkeypatch):
    # monkeypatch httpx AsyncClient.head to return a fake 200
    import httpx

    class DummyResp:
        def __init__(self, status_code=200):
            self.status_code = status_code

    class DummyClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False
        async def head(self, url):
            return DummyResp(200)

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)
    client = TestClient(ops)
    r = client.get("/verify/cid/QmTest")
    assert r.status_code == 200
    body = r.json()
    assert body["cid"] == "QmTest"
    assert body["ok"] is True


def test_verify_polygon_offline(monkeypatch):
    import httpx

    class DummyResp:
        def __init__(self, status_code=200):
            self.status_code = status_code
        def json(self):
            return {"jsonrpc":"2.0","id":1,"result": {"status":"0x1"}}

    class DummyClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            return False
        async def post(self, url, json):
            return DummyResp(200)

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)
    client = TestClient(ops)
    r = client.get("/verify/polygon/0xabc")
    assert r.status_code == 200
    body = r.json()
    assert body["tx"] == "0xabc"
    assert body["result"]["status"] == "0x1"


def test_verify_xrpl_endpoint():
    client = TestClient(ops)
    r = client.get("/verify/xrpl/ABCD")
    assert r.status_code == 200
    assert "explorer" in r.json()


def test_registry_resolve_latest(monkeypatch, tmp_path):
    # Write a minimal registry file and point REGISTRY_PATH to it
    import os, json
    p = tmp_path / "test.ndjson"
    entry = {"time": 1, "cid": "QmX", "url": "http://localhost/ipfs/QmX/", "sha": "deadbeef"}
    p.write_text(json.dumps(entry) + "\n")
    monkeypatch.setenv("REGISTRY_PATH", str(p))

    # Mock httpx head to succeed
    import httpx
    class DummyResp:
        def __init__(self, status_code=200):
            self.status_code = status_code
    class DummyClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return False
        async def head(self, url): return DummyResp(200)
        async def post(self, url, json): return DummyResp(200)
    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = TestClient(ops)
    r = client.get("/registry/resolve")
    assert r.status_code == 200
    body = r.json()
    assert body["cid"] == "QmX"
    assert body["gateway"]["ok"] is True


def test_verify_xrpl_live_mock(monkeypatch):
    # Mock asyncio.create_subprocess_exec to simulate Node script output
    import asyncio as _asyncio

    class DummyProc:
        def __init__(self, rc=0, out=b'{"validated":true,"tx":"T123"}', err=b''):
            self.returncode = rc
            self._out = out
            self._err = err
        async def communicate(self):
            return self._out, self._err

    async def fake_create_subprocess_exec(*a, **k):
        return DummyProc()

    monkeypatch.setattr(_asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    client = TestClient(ops)
    r = client.get("/verify/xrpl/live/T123")
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is True
    assert body["tx"] == "T123"


def test_audit_pubkey_env(monkeypatch):
    monkeypatch.setenv("AUDIT_PUBKEY", "-----BEGIN PGP PUBLIC KEY BLOCK-----\nabc\n-----END PGP PUBLIC KEY BLOCK-----")
    client = TestClient(ops)
    r = client.get("/audit/pubkey")
    assert r.status_code == 200
    body = r.json()
    assert body["pubkey"].startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")


def test_post_aliases_and_swarm_attest(monkeypatch):
    client = TestClient(ops)
    # POST /registry/resolve should work without body fields
    r = client.post("/registry/resolve", json={})
    # It may 404 if empty registry; tolerate 200 or 404
    assert r.status_code in (200, 404)

    # POST /verify/xrpl/live requires tx
    r2 = client.post("/verify/xrpl/live", json={})
    assert r2.status_code == 400

    # /swarm/attest minimal quorum
    monkeypatch.setenv("AUDIT_PUBKEY", "x")
    r3 = client.post("/swarm/attest", json={"root": "deadbeef"})
    assert r3.status_code == 200
    body = r3.json()
    assert "quorum" in body
