#!/usr/bin/env python3
"""Post a reel as an IG + FB video Story (launchd) — extra ephemeral reach from
video we already produce. Reuses the hosted reels in site/v/. Cycles through them.
State: content/reel_story_state.json"""
import argparse, datetime as dt, glob, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

VDIR = os.path.join(ROOT, "site", "v")
STATE = os.path.join(ROOT, "content", "reel_story_state.json")
LOG = os.path.join(ROOT, "content", "reel_story.log")
BASE = "https://booked-job.com/v"


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def is_live(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    vids = [os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(f"{VDIR}/*.mp4"))]
    state = load(STATE, {"done": []}); done = set(state["done"])
    if a.status:
        print(json.dumps({"done": list(done), "videos": vids}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "fb.env")):
        log("FB/IG not connected — skipping."); return
    nxt = next((v for v in vids if v not in done), None)
    if not nxt:
        done = set(); nxt = vids[0] if vids else None  # cycle
    if not nxt:
        log("no reels to post as stories."); return
    url = f"{BASE}/{nxt}.mp4"; local = os.path.join(VDIR, f"{nxt}.mp4")
    if not is_live(url):
        log(f"'{nxt}' not live yet — retry next run"); return
    # IG video story
    try:
        import ig_publish
        r = ig_publish.publish_video_story(url)
        log(f"IG video story posted '{nxt}' -> {r.get('id')}")
    except Exception as ex:
        log(f"IG video story failed '{nxt}': {ex}")
    # FB video story
    try:
        import fb_post_reel
        r = fb_post_reel.publish_video_story(local)
        log(f"FB video story posted '{nxt}' -> {r.get('video_id')}")
    except Exception as ex:
        log(f"FB video story failed '{nxt}': {ex}")
    done.add(nxt); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)


if __name__ == "__main__":
    main()
