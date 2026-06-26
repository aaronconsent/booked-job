#!/usr/bin/env python3
"""Threads publisher (Meta Threads API, graph.threads.net — separate from the
Graph API). Two-step: create a media container, then publish it.
Reads secrets/threads.env: THREADS_USER_ID, THREADS_TOKEN."""
import json, os, sys, time, urllib.parse, urllib.request

API = "https://graph.threads.net/v1.0"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "threads.env")
    if not os.path.exists(p):
        sys.exit("secrets/threads.env missing.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _post(path, params):
    req = urllib.request.Request(f"{API}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Threads error {ex.code} on {path}: {ex.read().decode()[:300]}")


def refresh_and_save():
    """Refresh the long-lived token (valid 60 days, refreshable after 24h) and
    persist it. Best-effort — keeps the agent alive indefinitely across runs."""
    e = env()
    try:
        url = f"https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token={e['THREADS_TOKEN']}"
        with urllib.request.urlopen(url, timeout=30) as r:
            new = json.loads(r.read().decode()).get("access_token")
        if new and new != e["THREADS_TOKEN"]:
            p = os.path.join(os.path.dirname(__file__), "..", "secrets", "threads.env")
            lines = [(f"THREADS_TOKEN={new}\n" if l.startswith("THREADS_TOKEN=") else l) for l in open(p)]
            open(p, "w").writelines(lines)
            return True
    except Exception:
        pass
    return False


def publish_text(text):
    e = env()
    uid, tok = e["THREADS_USER_ID"], e["THREADS_TOKEN"]
    cont = _post(f"{uid}/threads", {"media_type": "TEXT", "text": text[:500], "access_token": tok})
    cid = cont["id"]
    time.sleep(3)  # Threads recommends a brief pause before publishing
    return _post(f"{uid}/threads_publish", {"creation_id": cid, "access_token": tok})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--text", required=True)
    a = ap.parse_args()
    print(json.dumps(publish_text(a.text), indent=2))
