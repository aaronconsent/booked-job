#!/usr/bin/env python3
"""Validate the Pinterest token, ensure a board exists, and save its ID into
secrets/pinterest.env. Works for sandbox (direct token) or production."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinterest_publish as P


def _get(e, path):
    req = urllib.request.Request(f"{P.api_base(e)}{path}")
    req.add_header("Authorization", f"Bearer {P.access_token(e)}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _post(e, path, body):
    req = urllib.request.Request(f"{P.api_base(e)}{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {P.access_token(e)}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    e = P.env()
    print("API base:", P.api_base(e))
    try:
        acct = _get(e, "/user_account")
        print("✅ token valid — account:", acct.get("username"), "| type:", acct.get("account_type"))
    except urllib.error.HTTPError as ex:
        sys.exit(f"❌ token check failed {ex.code}: {ex.read().decode()[:300]}")

    boards = _get(e, "/boards").get("items", [])
    board = next((b for b in boards if b["name"] == "Booked Job"), boards[0] if boards else None)
    if not board:
        board = _post(e, "/boards", {"name": "Booked Job",
                                     "description": "Real talk for service pros — getting more jobs, pricing, getting paid.",
                                     "privacy": "PUBLIC"})
        print("created board:", board["id"])
    print("✅ board:", board["name"], board["id"])

    # persist board id
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "pinterest.env")
    lines = [l for l in open(p) if not l.startswith("PINTEREST_BOARD_ID=")]
    lines.append(f"PINTEREST_BOARD_ID={board['id']}\n")
    open(p, "w").writelines(lines)
    print("saved PINTEREST_BOARD_ID to secrets/pinterest.env")


if __name__ == "__main__":
    main()
