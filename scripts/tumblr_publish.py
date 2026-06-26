#!/usr/bin/env python3
"""Publish an NPF post (text + link block) to the Booked Job Tumblr (API v2,
OAuth2). Reads secrets/tumblr.env. Used by tumblr_runner.py for syndication."""
import json, os, sys, urllib.parse, urllib.request

TOKEN = "https://api.tumblr.com/v2/oauth2/token"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "tumblr.env")
    if not os.path.exists(p):
        sys.exit("secrets/tumblr.env missing — run tumblr_oauth.py first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def access_token(e):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": e["TUMBLR_REFRESH_TOKEN"],
        "client_id": e["TUMBLR_CLIENT_ID"], "client_secret": e["TUMBLR_CLIENT_SECRET"]}).encode()
    req = urllib.request.Request(TOKEN, data=body)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def publish(text, link, link_title, link_desc, tags=None):
    e = env()
    tok = access_token(e)
    blog = e["TUMBLR_BLOG"]
    payload = json.dumps({
        "content": [
            {"type": "text", "text": text},
            {"type": "link", "url": link, "title": link_title, "description": link_desc},
        ],
        "tags": ",".join(tags or []),
        "state": "published",
    }).encode()
    url = f"https://api.tumblr.com/v2/blog/{blog}.tumblr.com/posts"
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Tumblr publish failed {ex.code}: {ex.read().decode()[:400]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True); ap.add_argument("--link", required=True)
    ap.add_argument("--title", default=""); ap.add_argument("--desc", default=""); ap.add_argument("--tags", default="")
    a = ap.parse_args()
    res = publish(a.text, a.link, a.title, a.desc, [t.strip() for t in a.tags.split(",") if t.strip()])
    print(json.dumps(res.get("response", res), indent=2))
