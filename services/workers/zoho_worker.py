import time, json, traceback
from pathlib import Path
from services.zoho_client import ZohoClient

PENDING = Path("queue/pending")
DONE = Path("queue/done")
FAILED = Path("queue/failed")
for d in (PENDING, DONE, FAILED):
    d.mkdir(parents=True, exist_ok=True)

zc = ZohoClient()


def handle(job):
    typ = job["type"]
    data = job["data"]
    if typ == "send_mail":
        res = zc.mail_send(
            to=data["to"], subject=data["subject"],
            text=data.get("text"), html=data.get("html"),
            cc=data.get("cc"), bcc=data.get("bcc")
        )
        return {"status": "sent", "resp": res}
    if typ == "upsert_contact":
        res = zc.bigin_upsert_contact(**data)
        return {"status": "ok", "contact": res}
    raise ValueError(f"unknown job type: {typ}")


def main():
    while True:
        for path in sorted(PENDING.glob("*.json")):
            try:
                job = json.loads(path.read_text())
                res = handle(job)
                (DONE / f"{path.stem}.done.json").write_text(json.dumps(res))
                path.unlink(missing_ok=True)
            except Exception as e:
                (FAILED / f"{path.stem}.err.txt").write_text(f"{e}\n\n{traceback.format_exc()}")
                path.unlink(missing_ok=True)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
