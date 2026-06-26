#!/usr/bin/env python3
"""
Pinterest OAuth2 connect (API v5). Reuses the hosted callback
https://booked-job.com/oauth/callback. Captures a refresh token + a target
board id (creates a 'Booked Job' board if none exists). Writes secrets/pinterest.env.

  1) auth URL:   python3 scripts/pinterest_oauth.py --client-id <K> --auth-url
  2) exchange:   python3 scripts/pinterest_oauth.py --client-id <K> --client-secret <S> --code <CODE>
"""
import argparse, base64, json, os, sys, urllib.parse, urllib.request

REDIRECT = "https://booked-job.com/oauth/callback"
AUTH = "https://www.pinterest.com/oauth/"
TOKEN = "https://api.pinterest.com/v5/oauth/token"
API = "https://api.pinterest.com/v5"
SCOPE = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"


def auth_url(cid):
    return AUTH + "?" + urllib.parse.urlencode({"client_id": cid, "redirect_uri": REDIRECT,
        "response_type": "code", "scope": SCOPE, "state": "bookedjob"})


def _basic(cid, csec):
    return base64.b64encode(f"{cid}:{csec}".encode()).decode()


def api_get(path, tok):
    r = urllib.request.Request(f"{API}/{path}")
    r.add_header("Authorization", f"Bearer {tok}")
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret")
    ap.add_argument("--code")
    ap.add_argument("--auth-url", action="store_true")
    a = ap.parse_args()

    if a.auth_url or not a.code:
        print(auth_url(a.client_id))
        if not a.code:
            return
    if not a.client_secret:
        sys.exit("--client-secret required to exchange the code.")

    body = urllib.parse.urlencode({"grant_type": "authorization_code", "code": a.code,
        "redirect_uri": REDIRECT}).encode()
    req = urllib.request.Request(TOKEN, data=body)
    req.add_header("Authorization", f"Basic {_basic(a.client_id, a.client_secret)}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"token exchange failed {ex.code}: {ex.read().decode()[:300]}")
    if "refresh_token" not in tok:
        sys.exit(f"No refresh_token: {tok}")
    at = tok["access_token"]

    # find or create a board
    board_id = board_name = ""
    try:
        boards = api_get("boards", at).get("items", [])
        if boards:
            board_id, board_name = boards[0]["id"], boards[0]["name"]
        else:
            cb = urllib.request.Request(f"{API}/boards", method="POST",
                data=json.dumps({"name": "Booked Job", "description": "For service pros who'd rather be working."}).encode())
            cb.add_header("Authorization", f"Bearer {at}")
            cb.add_header("Content-Type", "application/json")
            nb = json.loads(urllib.request.urlopen(cb, timeout=30).read().decode())
            board_id, board_name = nb["id"], nb["name"]
    except Exception as ex:
        print(f">>> (couldn't read/create board: {ex})")

    out = os.path.join(os.path.dirname(__file__), "..", "secrets", "pinterest.env")
    with open(out, "w") as f:
        f.write(f"PINTEREST_CLIENT_ID={a.client_id}\nPINTEREST_CLIENT_SECRET={a.client_secret}\n")
        f.write(f"PINTEREST_REFRESH_TOKEN={tok['refresh_token']}\nPINTEREST_BOARD_ID={board_id}\nPINTEREST_BOARD_NAME={board_name}\n")
    os.chmod(out, 0o600)
    print(f"\n✅ wrote secrets/pinterest.env")
    print(f">>> PINTEREST BOARD: '{board_name}' ({board_id})")


if __name__ == "__main__":
    main()
