#!/usr/bin/env python3
"""Create a Pin on the Booked Job board (Pinterest API v5) with an inline
base64 image + a link back to the canonical article. Reads secrets/pinterest.env."""
import base64, json, os, sys, urllib.parse, urllib.request


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "pinterest.env")
    if not os.path.exists(p):
        sys.exit("secrets/pinterest.env missing — run pinterest_oauth.py first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def api_base(e):
    # Sandbox token only works against the sandbox host; production token against prod.
    return e.get("PINTEREST_API_BASE", "https://api.pinterest.com/v5").rstrip("/")


def access_token(e):
    # Direct token (sandbox, or a non-expiring access token) takes precedence.
    if e.get("PINTEREST_ACCESS_TOKEN"):
        return e["PINTEREST_ACCESS_TOKEN"]
    # Otherwise exchange the OAuth refresh token (production flow).
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": e["PINTEREST_REFRESH_TOKEN"]}).encode()
    basic = base64.b64encode(f"{e['PINTEREST_CLIENT_ID']}:{e['PINTEREST_CLIENT_SECRET']}".encode()).decode()
    req = urllib.request.Request(f"{api_base(e)}/oauth/token", data=body)
    req.add_header("Authorization", f"Basic {basic}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def publish(title, description, link, image_path):
    e = env()
    tok = access_token(e)
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = json.dumps({
        "board_id": e["PINTEREST_BOARD_ID"], "title": title[:100], "description": description[:500],
        "link": link,
        "media_source": {"source_type": "image_base64", "content_type": "image/png", "data": b64},
    }).encode()
    req = urllib.request.Request(f"{api_base(e)}/pins", data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Pinterest publish failed {ex.code}: {ex.read().decode()[:400]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True); ap.add_argument("--description", default="")
    ap.add_argument("--link", required=True); ap.add_argument("--image", required=True)
    a = ap.parse_args()
    print(json.dumps(publish(a.title, a.description, a.link, a.image), indent=2))
