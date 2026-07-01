#!/usr/bin/env python3
"""
Autonomous Reels runner (launchd, ~2x/week). Produces the next queued Reel with
ElevenLabs voice + synced captions, publishes it via the Graph API, marks it done.

Reels are the #1 from-zero reach lever. Paced 2/week to respect ElevenLabs credits.
State: content/reels_state.json. Log: content/reels.log.

Flags: --force (ignore schedule), --dry-run (build but don't publish), --status.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_reel, fb_post_reel, fb_post

QUEUE = os.path.join(ROOT, "content", "reels_queue.json")
STATE = os.path.join(ROOT, "content", "reels_state.json")
LOG = os.path.join(ROOT, "content", "reels.log")
OUTDIR = os.path.join(ROOT, "content", "reels")

POST_DAYS = {0, 1, 2, 3, 4, 5, 6}  # daily — each reel fans to FB+IG+TikTok
WINDOW = (6, 22)        # all day (uncapped — max reels, ElevenLabs spend OK'd by Aaron 2026-07-01)
BACKEND = "elevenlabs"  # falls back by editing make_reel default if credits run out


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    queue = load(QUEUE, {"reels": []})["reels"]
    state = load(STATE, {"done": [], "last_iso": None})
    done = set(state["done"])

    if a.status:
        rem = [r["id"] for r in queue if r["id"] not in done]
        print(json.dumps({"done": len(done), "remaining": rem}, indent=2)); return

    nxt = next((r for r in queue if r["id"] not in done), None)
    if not nxt:
        log("reels queue empty — refill content/reels_queue.json"); return

    now = dt.datetime.now()
    if not a.force:
        if now.weekday() not in POST_DAYS:
            log(f"skip: {now:%A} not a reel day"); return
        if not (WINDOW[0] <= now.hour < WINDOW[1]):
            log(f"skip: outside reel window {WINDOW}"); return
        if state.get("last_iso"):
            gap = (now - dt.datetime.fromisoformat(state["last_iso"])).total_seconds() / 3600
            if gap < 4:                       # ~1 reel / 4h = up to ~4/day (was 20h)
                log(f"skip: only {gap:.1f}h since last reel (<4h)"); return

    out = os.path.join(OUTDIR, f"{nxt['id']}.mp4")
    pre = nxt.get("video")
    if pre:   # pre-rendered clip (course shorts, podcast clips) — post as-is, no TTS/render
        src = pre if os.path.isabs(pre) else os.path.join(ROOT, pre)
        if not os.path.exists(src):
            log(f"PRE-RENDERED MISSING '{nxt['id']}': {src}"); return
        out = src
        log(f"using pre-rendered video '{nxt['id']}' -> {out}")
    else:
        log(f"building reel '{nxt['id']}' …")
        try:
            make_reel.build(nxt["hook"], nxt["script"], out, backend=BACKEND)
        except SystemExit as e:
            log(f"BUILD FAILED '{nxt['id']}': {e}"); return

    if a.dry_run:
        log(f"DRY-RUN built {out}, not publishing"); return

    res = fb_post_reel.publish_reel(out, nxt.get("description", ""))
    done.add(nxt["id"])
    state["done"] = list(done)
    state["last_iso"] = now.isoformat(timespec="seconds")
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PUBLISHED reel '{nxt['id']}' (FB) -> {res.get('video_id')}")

    # Fan out to IG Reels + TikTok — both need the clip at a PUBLIC url (site/reels/<file>).
    cap = nxt.get("description", "")
    base = os.path.basename(out)
    hosted = os.path.join(ROOT, "site", "reels", base)
    if not os.path.exists(hosted):
        try:
            import shutil; os.makedirs(os.path.dirname(hosted), exist_ok=True); shutil.copy(out, hosted)
            log(f"  copied to site/reels/{base} (push to make it public for IG/TikTok)")
        except Exception as e:
            log(f"  host-copy failed: {str(e)[:100]}")
    pub_url = f"https://booked-job.com/reels/{base}"
    # IG Reels (Graph API)
    try:
        import urllib.request
        if urllib.request.urlopen(pub_url, timeout=15).status == 200:
            import ig_publish; ig_publish.publish(pub_url, cap); log("  -> IG Reel posted")
    except Exception as e:
        log(f"  IG reel skipped/failed: {str(e)[:100]}")
    # TikTok (via Buffer)
    try:
        import buffer_publish as BP
        be = BP.env(); tt = be.get("BUFFER_TIKTOK_CHANNEL") if isinstance(be, dict) else None
        if tt:
            BP.queue_video(tt, cap, pub_url, title=nxt.get("hook", "")); log("  -> TikTok queued (Buffer)")
    except Exception as e:
        log(f"  TikTok skipped/failed: {str(e)[:100]}")
    try:
        import log_change
        log_change.add("reel", f"Published Reel: {nxt['hook']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
