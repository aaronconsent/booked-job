#!/usr/bin/env python3
"""
Upload a video to YouTube via the Data API v3 (resumable, pure stdlib).
Reads OAuth creds from secrets/youtube.env:
    YT_CLIENT_ID=...
    YT_CLIENT_SECRET=...
    YT_REFRESH_TOKEN=...   (from scripts/yt_oauth.py)

Usage:
    python3 scripts/yt_upload.py --video content/reels/money-leaks.mp4 \
        --title "3 Ways Shops Bleed Money" --description "..." --tags "trades,contractor" \
        [--privacy public|unlisted|private] [--dry-run]
"""
import argparse, json, os, sys, urllib.parse, urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "youtube.env")
    if not os.path.exists(p):
        sys.exit("secrets/youtube.env missing — run yt_oauth.py first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def access_token(e):
    body = urllib.parse.urlencode({
        "client_id": e["YT_CLIENT_ID"], "client_secret": e["YT_CLIENT_SECRET"],
        "refresh_token": e["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=body), timeout=30) as r:
            return json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as ex:
        sys.exit(f"token refresh failed {ex.code}: {ex.read().decode()[:300]}")


def publish(video, title, description, tags, privacy="public", category="22"):
    e = env()
    tok = access_token(e)
    size = os.path.getsize(video)
    meta = json.dumps({
        "snippet": {"title": title[:100], "description": description[:4900],
                    "tags": tags, "categoryId": category},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}).encode()

    # 1) start resumable session
    req = urllib.request.Request(UPLOAD_URL, data=meta, method="POST")
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Content-Type", "application/json; charset=UTF-8")
    req.add_header("X-Upload-Content-Type", "video/*")
    req.add_header("X-Upload-Content-Length", str(size))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            session_url = r.headers["Location"]
    except urllib.error.HTTPError as ex:
        sys.exit(f"YouTube start failed {ex.code}: {ex.read().decode()[:400]}")

    # 2) upload bytes
    with open(video, "rb") as f:
        data = f.read()
    put = urllib.request.Request(session_url, data=data, method="PUT")
    put.add_header("Content-Type", "video/*")
    put.add_header("Content-Length", str(size))
    try:
        with urllib.request.urlopen(put, timeout=600) as r:
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"YouTube upload failed {ex.code}: {ex.read().decode()[:400]}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    ap.add_argument("--category", default="22")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    if a.dry_run:
        print(json.dumps({"dry_run": True, "video": a.video, "title": a.title,
                          "tags": tags, "privacy": a.privacy}, indent=2)); return
    res = publish(a.video, a.title, a.description, tags, a.privacy, a.category)
    vid = res.get("id")
    print(json.dumps({"video_id": vid, "url": f"https://youtu.be/{vid}",
                      "status": res.get("status", {})}, indent=2))


if __name__ == "__main__":
    main()
