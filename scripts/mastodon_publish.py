#!/usr/bin/env python3
"""Mastodon publisher — posts a status (auto-generates a link preview card).
Reads secrets/mastodon.env: MASTODON_INSTANCE (e.g. https://mastodon.social),
MASTODON_TOKEN (access token with write:statuses)."""
import json, os, sys, urllib.parse, urllib.request


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "mastodon.env")
    if not os.path.exists(p):
        sys.exit("secrets/mastodon.env missing.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def upload_media(path, alt):
    """Upload an image with a (mandatory, on the fediverse) alt-text description."""
    import os
    e = env(); inst = e["MASTODON_INSTANCE"].rstrip("/")
    boundary = "----bookedjobBOUNDARY7zX"
    with open(path, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{alt}\r\n".encode()
            + f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: image/png\r\n\r\n".encode()
            + data + f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(f"{inst}/api/v2/media", data=body, method="POST")
    req.add_header("Authorization", f"Bearer {e['MASTODON_TOKEN']}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())["id"]


def publish(text, media_ids=None):
    e = env()
    inst = e["MASTODON_INSTANCE"].rstrip("/")
    params = [("status", text)] + [("media_ids[]", m) for m in (media_ids or [])]
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{inst}/api/v1/statuses", data=body, method="POST")
    req.add_header("Authorization", f"Bearer {e['MASTODON_TOKEN']}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Mastodon error {ex.code}: {ex.read().decode()[:300]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--text", required=True)
    a = ap.parse_args()
    print(json.dumps({"url": publish(a.text).get("url")}, indent=2))
