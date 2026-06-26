#!/usr/bin/env python3
"""Publish a post to the Booked Job Blogger blog (Blogger API v3).
Reads secrets/blogger.env. Used by blogger_runner.py to syndicate summaries
with a dofollow link back to the canonical article on booked-job.com."""
import json, os, sys, urllib.parse, urllib.request

TOKEN = "https://oauth2.googleapis.com/token"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "blogger.env")
    if not os.path.exists(p):
        sys.exit("secrets/blogger.env missing — run blogger_oauth.py first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def access_token(e):
    body = urllib.parse.urlencode({"client_id": e["BLOGGER_CLIENT_ID"], "client_secret": e["BLOGGER_CLIENT_SECRET"],
        "refresh_token": e["BLOGGER_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN, data=body), timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def publish(title, content_html, labels=None):
    e = env()
    tok = access_token(e)
    url = f"https://www.googleapis.com/blogger/v3/blogs/{e['BLOGGER_BLOG_ID']}/posts"
    payload = json.dumps({"kind": "blogger#post", "title": title,
                          "content": content_html, "labels": labels or []}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Blogger publish failed {ex.code}: {ex.read().decode()[:400]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--content", required=True)
    ap.add_argument("--labels", default="")
    a = ap.parse_args()
    res = publish(a.title, a.content, [x.strip() for x in a.labels.split(",") if x.strip()])
    print(json.dumps({"id": res.get("id"), "url": res.get("url")}, indent=2))
