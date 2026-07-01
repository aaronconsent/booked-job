#!/usr/bin/env python3
"""
Autonomous Instagram Reels runner (launchd). Reuses the Shorts video already
made for YouTube (or generates one), hosts it at booked-job.com/v/<id>.mp4,
waits for it to go live, then publishes it as an IG Reel.

Reuses content/yt_queue.json. State: content/ig_state.json. Log: content/ig.log.
Gated until Instagram is connected (token with instagram scopes + linked IG).
Flags: --force, --dry-run, --status.
"""
import argparse, datetime as dt, json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_reel, ig_publish

QUEUE = os.path.join(ROOT, "content", "yt_queue.json")
STATE = os.path.join(ROOT, "content", "ig_state.json")
LOG = os.path.join(ROOT, "content", "ig.log")
VDIR = os.path.join(ROOT, "site", "v")
POST_DAYS = {0, 1, 2, 3, 4, 5, 6}   # daily (safe-aggressive — IG tolerates 1-2/day)
WINDOW = (9, 15)


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def ig_ready():
    """True if Instagram is connected (linked IG + token scopes)."""
    try:
        ig_publish.ig_user_id(ig_publish.env())
        return True
    except SystemExit:
        return False
    except Exception:
        return False


def url_live(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    shorts = load(QUEUE, {"shorts": []})["shorts"]
    state = load(STATE, {"done": []})
    done = set(state["done"])

    if a.status:
        print(json.dumps({"done": len(done), "remaining": [s["id"] for s in shorts if s["id"] not in done]}, indent=2)); return

    if not a.dry_run and not ig_ready():
        log("Instagram not connected yet (no linked IG / scopes) — skipping."); return

    now = dt.datetime.now()
    if not a.force and not a.dry_run:
        if now.weekday() not in POST_DAYS or not (WINDOW[0] <= now.hour < WINDOW[1]):
            log("skip: outside IG window."); return

    nxt = next((s for s in shorts if s["id"] not in done), None)
    if not nxt:
        log("IG queue empty."); return

    # reuse the YouTube Short video if it exists, else generate
    src = os.path.join(ROOT, "content", "shorts", f"{nxt['id']}.mp4")
    if not os.path.exists(src):
        log(f"generating video for '{nxt['id']}' …")
        make_reel.build(nxt["hook"], nxt["script"], src, backend="elevenlabs")

    os.makedirs(VDIR, exist_ok=True)
    dst = os.path.join(VDIR, f"{nxt['id']}.mp4")
    if not os.path.exists(dst):
        import shutil; shutil.copy(src, dst)

    if a.dry_run:
        log(f"DRY-RUN ready '{nxt['id']}' (host + publish skipped)"); return

    # host it: push to the site, wait until live
    url = f"https://booked-job.com/v/{nxt['id']}.mp4"
    subprocess.run(["git", "add", dst], cwd=ROOT, check=False)
    subprocess.run(["git", "commit", "-q", "-m", f"ig: host video {nxt['id']}"], cwd=ROOT, check=False)
    subprocess.run(["git", "push", "-q"], cwd=ROOT, check=False)
    for _ in range(75):  # ~10 min — Cloudflare deploy of the new video can lag
        if url_live(url):
            break
        time.sleep(8)
    if not url_live(url):
        log(f"video not live at {url} yet — will retry next run."); return

    caption = nxt["description"].replace("https://booked-job.com/", "booked-job.com/")
    res = ig_publish.publish(url, caption)
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PUBLISHED IG Reel '{nxt['id']}' -> {res.get('id')}")
    try:
        import log_change
        log_change.add("reel", f"Published Instagram Reel: {nxt['title'].split('#')[0].strip()}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
