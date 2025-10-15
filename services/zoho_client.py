import os, time, requests

DC = os.getenv("ZOHO_DC", "com")
ACCOUNTS = f"https://accounts.zoho.{DC}/oauth/v2/token"
MAIL_API = f"https://mail.zoho.{DC}/api"
BIGIN_API = f"https://www.zohoapis.{DC}/bigin/v2"

CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
REFRESH = os.environ.get("ZOHO_REFRESH_TOKEN", "")
MAIL_ACCOUNT = os.environ.get("ZOHO_MAIL_ACCOUNT_ID", "")

_cache = {"tok": None, "exp": 0}

def zoho_token():
    now = time.time()
    if _cache["tok"] and now < _cache["exp"] - 30:
        return _cache["tok"]
    r = requests.post(ACCOUNTS, data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }, timeout=20)
    r.raise_for_status()
    tok = r.json()["access_token"]
    _cache.update(tok=tok, exp=now+3300)
    return tok

def mail_list(folder_id, limit=25):
    tok = zoho_token()
    url = f"{MAIL_API}/accounts/{MAIL_ACCOUNT}/messages"
    r = requests.get(url, params={"folderId": folder_id, "limit": limit},
                     headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
    r.raise_for_status()
    return r.json()

def mail_send(to_addr, subject, html):
    tok = zoho_token()
    url = f"{MAIL_API}/accounts/{MAIL_ACCOUNT}/messages"
    payload = {"toAddress": to_addr, "subject": subject, "content": html}
    r = requests.post(url, json=payload, headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
    r.raise_for_status()
    return r.json()

def bigin_upsert_contact(email, first_name=None, last_name=None):
    tok = zoho_token()
    s = requests.get(f"{BIGIN_API}/Contacts/search", params={"email": email},
                     headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
    if s.status_code == 200 and s.json().get("data"):
        return s.json()["data"][0]
    body = {"data":[{"Email": email, "First_Name": first_name, "Last_Name": last_name or email.split('@')[0]}]}
    c = requests.post(f"{BIGIN_API}/Contacts", json=body, headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
    c.raise_for_status()
    return c.json()["data"][0]


class ZohoClient:
    def __init__(self,
                 client_id: str | None = None,
                 client_secret: str | None = None,
                 refresh_token: str | None = None,
                 dc: str | None = None,
                 mail_account: str | None = None):
        self.client_id = client_id or os.environ.get("ZOHO_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("ZOHO_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("ZOHO_REFRESH_TOKEN", "")
        self.dc = dc or os.getenv("ZOHO_DC", "com")
        self.mail_account = mail_account or os.environ.get("ZOHO_MAIL_ACCOUNT_ID", "")
        self.ACCOUNTS = f"https://accounts.zoho.{self.dc}/oauth/v2/token"
        self.MAIL_API = f"https://mail.zoho.{self.dc}/api"
        self.BIGIN_API = f"https://www.zohoapis.{self.dc}/bigin/v2"
        self._tok = None
        self._exp = 0

    def _token(self) -> str:
        now = time.time()
        if self._tok and now < self._exp - 30:
            return self._tok
        r = requests.post(self.ACCOUNTS, data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }, timeout=20)
        r.raise_for_status()
        self._tok = r.json()["access_token"]
        self._exp = now + 3300
        return self._tok

    def mail_send(self, to: str, subject: str, text: str | None = None, html: str | None = None,
                  cc: list[str] | None = None, bcc: list[str] | None = None):
        tok = self._token()
        url = f"{self.MAIL_API}/accounts/{self.mail_account}/messages"
        payload = {"toAddress": to, "subject": subject}
        if html:
            payload["content"] = html
        elif text:
            payload["mailFormat"] = "text"
            payload["content"] = text
        if cc:
            payload["ccAddress"] = ",".join(cc)
        if bcc:
            payload["bccAddress"] = ",".join(bcc)
        r = requests.post(url, json=payload, headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
        r.raise_for_status()
        return r.json()

    def bigin_upsert_contact(self, email: str, first_name: str | None = None, last_name: str | None = None,
                              phone: str | None = None, company: str | None = None, tags: list[str] | None = None):
        tok = self._token()
        s = requests.get(f"{self.BIGIN_API}/Contacts/search", params={"email": email},
                         headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
        if s.status_code == 200 and s.json().get("data"):
            return s.json()["data"][0]
        body = {"data": [{
            "Email": email,
            "First_Name": first_name,
            "Last_Name": last_name or (email.split('@')[0] if email else None),
            "Phone": phone,
            "Company": company,
            "Tag": tags or [],
        }]}
        c = requests.post(f"{self.BIGIN_API}/Contacts", json=body,
                          headers={"Authorization": f"Zoho-oauthtoken {tok}"}, timeout=20)
        c.raise_for_status()
        return c.json()["data"][0]
