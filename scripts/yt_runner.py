#!/usr/bin/env python3
"""
Autonomous YouTube Shorts runner (launchd, ~3x/week). Generates the next queued
Short with the faceless pipeline (ElevenLabs voice + synced captions) and uploads
it via the Data API. YouTube was the strongest single AI-citation signal in our
research, so this is a core organic channel — not an afterthought.

State: content/yt_state.json. Log: content/youtube.log.
Flags: --force, --dry-run, --status.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_reel, yt_upload

QUEUE = os.path.join(ROOT, "content", "yt_queue.json")
STATE = os.path.join(ROOT, "content", "yt_state.json")
LOG = os.path.join(ROOT, "content", "youtube.log")
OUTDIR = os.path.join(ROOT, "content", "shorts")

POST_DAYS = {0, 2, 4}   # Mon, Wed, Fri
WINDOW = (8, 12)


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

    shorts = load(QUEUE, {"shorts": []})["shorts"]
    state = load(STATE, {"done": [], "last_iso": None})
    done = set(state["done"])

    if a.status:
        rem = [s["id"] for s in shorts if s["id"] not in done]
        print(json.dumps({"done": len(done), "remaining": rem}, indent=2)); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "youtube.env")) and not a.dry_run:
        log("YouTube not connected yet (no secrets/youtube.env) — skipping."); return

    nxt = next((s for s in shorts if s["id"] not in done), None)
    if not nxt:
        log("YouTube queue empty — refill content/yt_queue.json"); return

    now = dt.datetime.now()
    if not a.force:
        if now.weekday() not in POST_DAYS:
            log(f"skip: {now:%A} not a Shorts day"); return
        if not (WINDOW[0] <= now.hour < WINDOW[1]):
            log(f"skip: outside window {WINDOW}"); return
        if state.get("last_iso"):
            gap = (now - dt.datetime.fromisoformat(state["last_iso"])).total_seconds() / 3600
            if gap < 30:
                log(f"skip: only {gap:.0f}h since last Short"); return

    out = os.path.join(OUTDIR, f"{nxt['id']}.mp4")
    log(f"building Short '{nxt['id']}' …")
    try:
        make_reel.build(nxt["hook"], nxt["script"], out, backend="elevenlabs")
    except SystemExit as e:
        log(f"BUILD FAILED '{nxt['id']}': {e}"); return

    if a.dry_run:
        log(f"DRY-RUN built {out}, not uploading"); return

    res = yt_upload.publish(out, nxt["title"], nxt["description"], nxt["tags"], privacy="public")
    vid = res.get("id")
    done.add(nxt["id"])
    state["done"] = list(done); state["last_iso"] = now.isoformat(timespec="seconds")
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PUBLISHED Short '{nxt['id']}' -> https://youtu.be/{vid}")
    try:
        import log_change
        log_change.add("reel", f"Published YouTube Short: {nxt['title'].split('#')[0].strip()}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
