#!/usr/bin/env python3
"""
Optimize the Booked Job Page metadata via the Graph API.

REQUIRES the token to include the `pages_manage_metadata` scope (re-run
fb_setup_token.py with a fresh Explorer token after adding it). Without that
scope these writes return permission errors — which this script reports clearly.

Updates the text/metadata fields the API allows. Profile picture + cover photo
are NOT settable via the public Graph API on current versions — upload
content/brand/profile.png and content/brand/cover.png by hand in the FB UI.

Usage: python3 scripts/fb_page_setup.py [--dry-run]
"""
import argparse, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fb_post

GRAPH = "https://graph.facebook.com/v21.0"

FIELDS = {
    "about": "For service pros who'd rather be working. More booked jobs, a better-run shop, and the stuff only the trades get.",
    "description": (
        "Booked Job is for home-service business owners and operators — plumbers, "
        "roofers, HVAC techs, electricians. We post about one thing: keeping your "
        "schedule full and your pockets fuller. The good, the dumb, and the "
        "'look what the last guy did.' No pitch, no fluff, just what works in the field."
    ),
    "website": "https://booked-job.com",
    "single_line_address": "",
}


def post(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{GRAPH}/{path}", data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return False, e.read().decode()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = fb_post.load_env()
    page, token = env["FB_PAGE_ID"], env["FB_PAGE_TOKEN"]
    payload = {k: v for k, v in FIELDS.items() if v}

    if a.dry_run:
        print(json.dumps({"would_update": payload}, indent=2, ensure_ascii=False)); return

    payload["access_token"] = token
    ok, res = post(page, payload)
    if ok:
        print("Page metadata updated:", json.dumps(res))
    else:
        print("UPDATE FAILED (likely missing pages_manage_metadata scope):\n", res, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
