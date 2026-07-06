#!/usr/bin/env python3
"""Auto-cut vertical shorts from rendered podcast episodes (the flywheel: each
episode -> 2-3 shorts that feed the daily drip). ffmpeg-slices the segment, adds
it to video_pool.json + yt_queue.json (pre-rendered) so the runners distribute it."""
import json, os, subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MANIFEST_DIR = os.path.join(ROOT, "..", "remotion-studio", "public", "audio")
EP_DIR = os.path.join(ROOT, "..", "remotion-studio", "out")
OUT_DIR = os.path.join(ROOT, "site", "reels")
BASE = "https://booked-job.com"
INTRO, GAP, FPS, PAD = 96, 7, 30, 0.35
TAGS = ["contractor", "homeservices", "leadgeneration", "marketing"]

# episode -> [{slug, s, e, hook}]  (s,e = inclusive line indices, 0-based)
HIGHLIGHTS = {
    "podcast-ep01": [
        {"slug": "shared", "s": 3, "e": 6, "hook": "One Angi lead — sold to 5 other guys"},
        {"slug": "wrongnum", "s": 7, "e": 10, "hook": "The number Angi doesn't want you doing"},
        {"slug": "cost", "s": 10, "e": 12, "hook": "$542 vs $168 — the Angi tax"},
        {"slug": "refunds", "s": 13, "e": 16, "hook": "Why Angi refunds 15-22% of your leads"},
        {"slug": "ftc", "s": 17, "e": 20, "hook": "The $7.2M FTC fine on Angi's leads"},
        {"slug": "starter", "s": 21, "e": 24, "hook": "The ONE time Angi actually makes sense"},
        {"slug": "speed", "s": 25, "e": 28, "hook": "Answer in 5 minutes or lose the job"},
        {"slug": "verdict", "s": 29, "e": 32, "hook": "When to fire Angi"},
    ],
    "podcast-ep02": [
        {"slug": "invisible", "s": 3, "e": 5, "hook": "91% won't call a shop under 4 stars"},
        {"slug": "howmany", "s": 6, "e": 9, "hook": "519 reviews to rank #1 — you've got 12"},
        {"slug": "peak", "s": 10, "e": 12, "hook": "Ask for the review at the PEAK"},
        {"slug": "onetap", "s": 13, "e": 17, "hook": "The 2 review rules nobody follows"},
        {"slug": "fake", "s": 18, "e": 20, "hook": "Never buy fake reviews — here's why"},
        {"slug": "system", "s": 21, "e": 22, "hook": "The 90-day review system"},
    ],
    "podcast-ep03": [
        {"slug": "lie", "s": 0, "e": 3, "hook": "Cost per lead is a lie"},
        {"slug": "trap", "s": 5, "e": 8, "hook": "Why the 'cheap' lead is the expensive one"},
        {"slug": "channels", "s": 9, "e": 11, "hook": "Angi vs Thumbtack vs Google — real cost"},
        {"slug": "exclusive", "s": 12, "e": 15, "hook": "Why an 'expensive' exclusive lead wins"},
        {"slug": "track", "s": 16, "e": 18, "hook": "The 1 number that cuts half your ad spend"},
        {"slug": "verdict", "s": 19, "e": 21, "hook": "The 2 numbers every contractor tracks"},
    ],
}


def line_secs(manifest):
    starts, acc = [], INTRO
    for l in manifest:
        starts.append(acc); acc += l["frames"] + GAP
    return starts


def add_pool(pid, url, hook):
    p = os.path.join(ROOT, "content", "video_pool.json")
    pool = json.load(open(p)) if os.path.exists(p) else {"videos": []}
    if any(v["id"] == pid for v in pool["videos"]):
        return
    cap = f"{hook} — the full breakdown's on the pod. Free playbook: {BASE} 👇"
    pool["videos"].insert(0, {"id": pid, "file": f"site/reels/{pid}.mp4", "url": url,
                              "hook": hook, "caption": cap, "tags": TAGS})
    json.dump(pool, open(p, "w"), indent=2, ensure_ascii=False)


def add_ytq(pid, hook):
    p = os.path.join(ROOT, "content", "yt_queue.json")
    q = json.load(open(p)) if os.path.exists(p) else {"shorts": []}
    if any(s["id"] == pid for s in q["shorts"]):
        return
    q["shorts"].insert(0, {"id": pid, "hook": hook, "title": f"{hook} #Shorts"[:100],
                           "description": f"{hook}\n\nFull episode + free playbook: {BASE} #Shorts",
                           "tags": TAGS, "video": f"site/reels/{pid}.mp4"})
    json.dump(q, open(p, "w"), indent=2, ensure_ascii=False)


def cut(ep):
    mpath = os.path.join(MANIFEST_DIR, ep, "manifest.json")
    vpath = os.path.join(EP_DIR, f"booked-job-{ep}.mp4")
    if not (os.path.exists(mpath) and os.path.exists(vpath)):
        print(f"  {ep}: missing manifest or video"); return 0
    m = json.load(open(mpath)); starts = line_secs(m)
    os.makedirs(OUT_DIR, exist_ok=True)
    n = 0
    for h in HIGHLIGHTS.get(ep, []):
        start = max(0, starts[h["s"]] / FPS - PAD)
        end = (starts[h["e"]] + m[h["e"]]["frames"]) / FPS + PAD
        pid = f"pod-{ep.replace('podcast-', '')}-{h['slug']}"
        out = os.path.join(OUT_DIR, f"{pid}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vpath, "-ss", f"{start:.2f}",
                        "-to", f"{end:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        "-c:a", "aac", "-movflags", "+faststart", out], check=True)
        add_pool(pid, f"{BASE}/reels/{pid}.mp4", h["hook"])
        add_ytq(pid, h["hook"])
        print(f"  cut {pid}  ({end-start:.0f}s)"); n += 1
    return n


def main():
    total = 0
    for ep in HIGHLIGHTS:
        total += cut(ep)
    print(f"cut {total} shorts -> site/reels/ + video_pool + yt_queue")


if __name__ == "__main__":
    main()
