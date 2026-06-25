#!/usr/bin/env python3
"""
Publish an MP4 as a Facebook Reel via the Graph API resumable upload
(start -> upload -> finish). Reels are the #1 reach lever for a from-zero page.

Usage:
    python3 scripts/fb_post_reel.py --video content/reels/money-leaks.mp4 \
        --description "..." [--dry-run]
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fb_post

GRAPH = "https://graph.facebook.com/v21.0"
RUPLOAD = "https://rupload.facebook.com/video-upload/v21.0"


def _json_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"Reels API error {e.code}: {e.read().decode()}")


def publish_reel(video, description="", env=None):
    """Publish an MP4 as a Reel. Returns dict with video_id/status. Reusable."""
    env = env or fb_post.load_env()
    page, token = env["FB_PAGE_ID"], env["FB_PAGE_TOKEN"]
    size = os.path.getsize(video)

    # phase 1: start
    start = _json_post(f"{GRAPH}/{page}/video_reels",
                       {"access_token": token, "upload_phase": "start"})
    video_id = start["video_id"]

    # phase 2: upload bytes
    with open(video, "rb") as f:
        blob = f.read()
    req = urllib.request.Request(f"{RUPLOAD}/{video_id}", data=blob, method="POST")
    req.add_header("Authorization", f"OAuth {token}")
    req.add_header("offset", "0")
    req.add_header("file_size", str(size))
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            up = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"Reels upload error {e.code}: {e.read().decode()}")
    if not up.get("success", True):
        sys.exit(f"upload not successful: {up}")

    # phase 3: finish + publish
    fin = _json_post(f"{GRAPH}/{page}/video_reels", {
        "access_token": token, "video_id": video_id,
        "upload_phase": "finish", "video_state": "PUBLISHED",
        "description": description})

    status = None
    for _ in range(10):
        time.sleep(6)
        s = urllib.request.urlopen(
            f"{GRAPH}/{video_id}?fields=status&access_token={urllib.parse.quote(token)}", timeout=30)
        status = json.loads(s.read().decode()).get("status", {})
        vs = status.get("video_status") or status.get("processing_phase", {}).get("status")
        if vs in ("ready", "published", "complete"):
            break
    return {"video_id": video_id, "finish": fin, "status": status}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.dry_run:
        print(json.dumps({"dry_run": True, "video": a.video,
                          "bytes": os.path.getsize(a.video),
                          "description": a.description}, indent=2)); return

    print(json.dumps(publish_reel(a.video, a.description), indent=2))


if __name__ == "__main__":
    main()
