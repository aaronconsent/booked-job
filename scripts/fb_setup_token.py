#!/usr/bin/env python3
"""
Exchange a short-lived Graph API Explorer token for a long-lived Page token,
verify it against the Booked Job page, and write secrets/fb.env.

Usage:
    python3 scripts/fb_setup_token.py \
        --app-id <APP_ID> --app-secret <APP_SECRET> \
        --short-token <EXPLORER_USER_TOKEN> --page-id 61591176670582

You can also set FB_APP_ID / FB_APP_SECRET / FB_SHORT_TOKEN / FB_PAGE_ID in the env.

What it does:
  1. short-lived USER token  -> long-lived USER token (~60 days)
  2. long-lived USER token   -> PAGE token (page tokens minted from a long-lived
                                user token do not expire as long as the user token
                                is valid / the permission isn't revoked)
  3. verifies the page token with a /me read and a debug_token call
  4. writes secrets/fb.env (gitignored) with the values the publisher uses
"""
import argparse, json, os, sys, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


def _get(path, params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", default=os.environ.get("FB_APP_ID"))
    ap.add_argument("--app-secret", default=os.environ.get("FB_APP_SECRET"))
    ap.add_argument("--short-token", default=os.environ.get("FB_SHORT_TOKEN"))
    ap.add_argument("--page-id", default=os.environ.get("FB_PAGE_ID", "61591176670582"))
    a = ap.parse_args()

    missing = [k for k, v in {
        "--app-id": a.app_id, "--app-secret": a.app_secret, "--short-token": a.short_token
    }.items() if not v]
    if missing:
        sys.exit(f"Missing required args: {', '.join(missing)}")

    print("1/4  short-lived user token -> long-lived user token …")
    ll = _get("oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "client_id": a.app_id,
        "client_secret": a.app_secret,
        "fb_exchange_token": a.short_token,
    })
    ll_user = ll["access_token"]
    print(f"     ok (expires_in={ll.get('expires_in','n/a')}s)")

    print("2/4  long-lived user token -> page tokens …")
    accts = _get("me/accounts", {"access_token": ll_user})
    pages = {p["id"]: p for p in accts.get("data", [])}
    if a.page_id not in pages:
        ids = ", ".join(pages) or "(none — token may lack pages scopes / page role)"
        sys.exit(f"Page {a.page_id} not found among managed pages: {ids}")
    page = pages[a.page_id]
    page_token = page["access_token"]
    print(f"     ok — page: {page.get('name','?')} ({a.page_id})")

    print("3/4  verifying page token …")
    me = _get(f"{a.page_id}", {"fields": "id,name,fan_count", "access_token": page_token})
    dbg = _get("debug_token", {"input_token": page_token, "access_token": f"{a.app_id}|{a.app_secret}"})
    d = dbg.get("data", {})
    print(f"     page='{me.get('name')}' fans={me.get('fan_count','?')} "
          f"type={d.get('type')} expires={d.get('expires_at','never') or 'never'}")
    scopes = d.get("scopes", [])
    need = {"pages_manage_posts", "pages_read_engagement"}
    if not need.issubset(set(scopes)):
        print(f"     WARNING: missing scopes {need - set(scopes)} — posting may fail.", file=sys.stderr)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "secrets")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "fb.env")
    with open(out, "w") as f:
        f.write(f"FB_APP_ID={a.app_id}\n")
        f.write(f"FB_APP_SECRET={a.app_secret}\n")
        f.write(f"FB_PAGE_ID={a.page_id}\n")
        f.write(f"FB_PAGE_TOKEN={page_token}\n")
        f.write(f"FB_LONGLIVED_USER_TOKEN={ll_user}\n")
    os.chmod(out, 0o600)
    print(f"4/4  wrote {os.path.relpath(out)} (gitignored, mode 600). Ready to post.")


if __name__ == "__main__":
    main()
