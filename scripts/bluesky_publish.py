#!/usr/bin/env python3
"""Bluesky (AT Protocol) publisher. Posts a short teaser + an external link card.
Reads secrets/bluesky.env: BLUESKY_HANDLE, BLUESKY_APP_PASSWORD."""
import datetime as dt, json, os, sys, urllib.request

PDS = "https://bsky.social/xrpc"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "bluesky.env")
    if not os.path.exists(p):
        sys.exit("secrets/bluesky.env missing.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _post(path, body, jwt=None):
    req = urllib.request.Request(f"{PDS}/{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    if jwt:
        req.add_header("Authorization", f"Bearer {jwt}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Bluesky error {ex.code} on {path}: {ex.read().decode()[:300]}")


def session(e):
    return _post("com.atproto.server.createSession",
                 {"identifier": e["BLUESKY_HANDLE"], "password": e["BLUESKY_APP_PASSWORD"]})


def publish(text, link, link_title, link_desc):
    e = env(); s = session(e)
    record = {
        "$type": "app.bsky.feed.post", "text": text[:300],
        "createdAt": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "embed": {"$type": "app.bsky.embed.external",
                  "external": {"uri": link, "title": link_title[:300], "description": link_desc[:1000]}},
    }
    return _post("com.atproto.repo.createRecord",
                 {"repo": s["did"], "collection": "app.bsky.feed.post", "record": record}, s["accessJwt"])


def publish_thread(first_text, link, link_title, link_desc, replies):
    """Post a thread: first post carries the link card, replies chain off it
    (threads earn ~3x more replies on Bluesky)."""
    e = env(); s = session(e); jwt = s["accessJwt"]; did = s["did"]
    now = lambda: dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def mk(record):
        return _post("com.atproto.repo.createRecord",
                     {"repo": did, "collection": "app.bsky.feed.post", "record": record}, jwt)

    r1 = mk({"$type": "app.bsky.feed.post", "text": first_text[:300], "createdAt": now(),
             "embed": {"$type": "app.bsky.embed.external",
                       "external": {"uri": link, "title": link_title[:300], "description": link_desc[:1000]}}})
    root = {"uri": r1["uri"], "cid": r1["cid"]}; parent = root
    for rt in replies:
        rr = mk({"$type": "app.bsky.feed.post", "text": rt[:300], "createdAt": now(),
                 "reply": {"root": root, "parent": parent}})
        parent = {"uri": rr["uri"], "cid": rr["cid"]}
    return r1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True); ap.add_argument("--link", required=True)
    ap.add_argument("--title", default=""); ap.add_argument("--desc", default="")
    a = ap.parse_args()
    print(json.dumps(publish(a.text, a.link, a.title, a.desc), indent=2))
