#!/usr/bin/env python3
"""
Telegraph (telegra.ph) publisher — open API, no signup. setup() creates an
account token (stored in secrets/telegraph.env); publish() posts a page.

Telegraph has NO canonical support + nofollow links, so we publish a UNIQUE
summary + a link back to the full article on booked-job.com (tier-2 surface).
"""
import json, os, sys, urllib.parse, urllib.request

API = "https://api.telegra.ph"


def _call(method, params):
    req = urllib.request.Request(f"{API}/{method}", data=urllib.parse.urlencode(params).encode(), method="POST")
    req.add_header("User-Agent", "booked-job-bot")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Telegraph error {ex.code}: {ex.read().decode()[:300]}")
    if not d.get("ok"):
        sys.exit(f"Telegraph not ok: {d}")
    return d["result"]


def setup():
    r = _call("createAccount", {"short_name": "BookedJob", "author_name": "Booked Job",
                                "author_url": "https://booked-job.com"})
    out = os.path.join(os.path.dirname(__file__), "..", "secrets", "telegraph.env")
    with open(out, "w") as f:
        f.write(f"TELEGRAPH_TOKEN={r['access_token']}\n")
    os.chmod(out, 0o600)
    return r


def token():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "telegraph.env")
    for line in open(p):
        if line.startswith("TELEGRAPH_TOKEN="):
            return line.strip().split("=", 1)[1]
    sys.exit("no TELEGRAPH_TOKEN — run setup first")


def publish(title, nodes):
    r = _call("createPage", {"access_token": token(), "title": title[:256],
                             "author_name": "Booked Job", "author_url": "https://booked-job.com",
                             "content": json.dumps(nodes), "return_content": "false"})
    return r  # {path, url, ...}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true")
    a = ap.parse_args()
    if a.setup:
        print(json.dumps(setup(), indent=2))
