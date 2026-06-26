#!/usr/bin/env python3
"""
Publish a Reel to Instagram via the Graph API (Content Publishing).
IG Reels require a PUBLIC video_url, so the caller hosts the MP4 on
booked-job.com and passes its URL.

Flow: resolve IG user id -> create REELS container (video_url) -> poll until
FINISHED -> media_publish. Reads secrets/fb.env (FB_SYSTEM_TOKEN + FB_PAGE_ID;
caches FB_IG_ID once resolved).
"""
import json, os, sys, time, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "fb.env")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _get(path, params):
    with urllib.request.urlopen(f"{GRAPH}/{path}?" + urllib.parse.urlencode(params), timeout=30) as r:
        return json.loads(r.read().decode())


def _post(path, params):
    req = urllib.request.Request(f"{GRAPH}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"IG API error {ex.code} on {path}: {ex.read().decode()[:400]}")


def ig_user_id(e):
    if e.get("FB_IG_ID"):
        return e["FB_IG_ID"]
    d = _get(e["FB_PAGE_ID"], {"fields": "instagram_business_account", "access_token": e["FB_SYSTEM_TOKEN"]})
    iga = d.get("instagram_business_account", {}).get("id")
    if not iga:
        sys.exit("No Instagram business account linked to the page. Connect IG to the Booked Job page first.")
    # cache it
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "fb.env")
    with open(p, "a") as f:
        f.write(f"FB_IG_ID={iga}\n")
    return iga


def publish(video_url, caption):
    e = env()
    tok = e["FB_SYSTEM_TOKEN"]
    ig = ig_user_id(e)
    # 1) container
    c = _post(f"{ig}/media", {"media_type": "REELS", "video_url": video_url,
                              "caption": caption, "share_to_feed": "true", "access_token": tok})
    cid = c["id"]
    # 2) poll
    for _ in range(40):
        time.sleep(6)
        st = _get(cid, {"fields": "status_code", "access_token": tok}).get("status_code")
        if st == "FINISHED":
            break
        if st == "ERROR":
            sys.exit(f"IG container processing error for {cid}")
    # 3) publish
    pub = _post(f"{ig}/media_publish", {"creation_id": cid, "access_token": tok})
    return pub


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-url", required=True)
    ap.add_argument("--caption", default="")
    a = ap.parse_args()
    print(json.dumps(publish(a.video_url, a.caption), indent=2))
