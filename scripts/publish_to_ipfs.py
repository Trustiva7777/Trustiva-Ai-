#!/usr/bin/env python3
import os, sys, json, subprocess, time, socket
from pathlib import Path


def _cli_available() -> bool:
    from shutil import which
    return which("ipfs") is not None


def _use_cli(path: str) -> str:
    return subprocess.check_output(["ipfs", "add", "-Qr", path], text=True).strip()


def _parse_ipfs_api_url() -> str:
    # IPFS_API can be like /ip4/127.0.0.1/tcp/5201 or a full http URL
    api = os.getenv("IPFS_API")
    if api and api.startswith("/ip4/") and "/tcp/" in api:
        host = api.split("/ip4/")[-1].split("/tcp/")[0]
        port = api.split("/tcp/")[-1].split("/")[0]
        return f"http://{host}:{port}"
    if api and api.startswith("http"):
        return api.rstrip("/")
    # default to dockerized mapping from scripts/run-ipfs-daemon.sh
    return "http://127.0.0.1:5201"


def _use_http_api(path: str) -> str:
    import requests
    from requests_toolbelt.multipart.encoder import MultipartEncoder

    base = _parse_ipfs_api_url()
    url = f"{base}/api/v0/add?recursive=true&wrap-with-directory=true&pin=true&quieter=true"

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    files = []
    if p.is_file():
        files.append(("file", (p.name, p.read_bytes(), "application/octet-stream")))
    else:
        root = p.resolve()
        for fp in root.rglob("*"):
            if fp.is_file():
                rel = fp.relative_to(root).as_posix()
                files.append(("file", (f"{rel}", fp.read_bytes(), "application/octet-stream")))

    enc = MultipartEncoder(fields=files)
    headers = {"Content-Type": enc.content_type}
    auth = os.getenv("IPFS_AUTH")
    if auth:
        headers["Authorization"] = auth

    # The IPFS API returns one JSON object per line; the final line is the root (when wrap-with-directory=true)
    resp = requests.post(url, data=enc, headers=headers, stream=True, timeout=120)
    resp.raise_for_status()
    root_cid = None
    last = None
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line.decode("utf-8"))
            last = obj
            # Root has empty Name when wrapped, but some versions set Name to ""
            if obj.get("Name", None) in ("", None):
                root_cid = obj.get("Hash")
        except Exception:
            continue
    if not root_cid and last:
        root_cid = last.get("Hash")
    if not root_cid:
        raise RuntimeError("Failed to parse root CID from IPFS API response")
    return root_cid


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: publish_to_ipfs.py <path>"}))
        sys.exit(1)
    path = sys.argv[1]
    try:
        if _cli_available():
            cid = _use_cli(path)
        else:
            cid = _use_http_api(path)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    gateway = os.getenv("IPFS_GATEWAY", "http://127.0.0.1:8082")
    out = {
        "cid": cid,
        "gateway": gateway,
        "path": path,
        "time": int(time.time()),
        "host": socket.gethostname(),
    }
    # Optionally write to <path>/publish.json when path is a directory
    try:
        p = Path(path)
        if p.exists() and p.is_dir():
            (p / "publish.json").write_text(json.dumps(out))
    except Exception:
        pass
    print(json.dumps(out))


if __name__ == "__main__":
    main()
