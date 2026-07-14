#!/usr/bin/env python3
"""Upload the next long-form podcast VIDEO episode to YouTube (a real video, NOT a Short).
Reads content/podcast_video_queue.json; state content/podcast_video_state.json. This is
the VIDEO track — separate from the existing audio podcast (podcast.py / podcast_queue.json).
Paced: at most one episode per run, min 20h apart, in the active window. --force bypasses gates."""
import argparse, datetime as dt, json, os, sys, urllib.request
import yt_upload

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
QUEUE = os.path.join(ROOT, "content", "podcast_video_queue.json")
STATE = os.path.join(ROOT, "content", "podcast_video_state.json")
LOG = os.path.join(ROOT, "content", "podcast_video.log")
WINDOW = (9, 21)
GAP_HOURS = 20
CATEGORY = "27"  # Education


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def log(m):
    line = f"{dt.datetime.now():%Y-%m-%dT%H:%M:%S}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def ensure_local(ep):
    """Return a local path to the episode video, downloading from its URL if missing."""
    v = ep.get("video")
    if v and os.path.exists(os.path.join(ROOT, v)):
        return os.path.join(ROOT, v)
    url = ep.get("url")
    if url:
        out = os.path.join("/tmp", os.path.basename(url))
        if not os.path.exists(out):
            urllib.request.urlretrieve(url, out)
        return out
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    eps = load(QUEUE, {"episodes": []})["episodes"]
    if not eps:
        log("podcast queue empty"); return
    state = load(STATE, {"done": [], "last_iso": None})
    done = set(state["done"])
    now = dt.datetime.now()
    if not a.force:
        if not (WINDOW[0] <= now.hour < WINDOW[1]):
            log(f"skip: outside window {WINDOW}"); return
        if state.get("last_iso"):
            gap = (now - dt.datetime.fromisoformat(state["last_iso"])).total_seconds() / 3600
            if gap < GAP_HOURS:
                log(f"skip: only {gap:.0f}h since last episode"); return

    nxt = next((e for e in eps if e["id"] not in done), None)
    if not nxt:
        log("all episodes uploaded"); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "youtube.env")) and not a.dry_run:
        log("no youtube.env"); return

    src = ensure_local(nxt)
    if not src:
        log(f"MISSING video for '{nxt['id']}'"); return
    if a.dry_run:
        log(f"DRY would upload '{nxt['id']}' — {nxt['title'][:60]}"); return

    import cta
    try:
        res = yt_upload.publish(src, nxt["title"], cta.append(nxt["description"], "youtube"), nxt.get("tags", []),
                                privacy="public", category=CATEGORY)
    except Exception as e:
        log(f"upload FAILED for '{nxt['id']}': {str(e)[:220]}"); return
    vid = (res or {}).get("id")
    if not vid:   # don't mark done on a failed/empty upload (the old bug that hid the episodes)
        log(f"upload returned NO video id for '{nxt['id']}': {str(res)[:200]}"); return
    if vid and nxt.get("thumbnail"):
        tp = os.path.join(ROOT, nxt["thumbnail"])
        if os.path.exists(tp):
            try:
                yt_upload.set_thumbnail(vid, tp); log(f"set thumbnail for {vid}")
            except Exception as e:
                log(f"thumbnail failed: {str(e)[:120]}")
    done.add(nxt["id"])
    state["done"] = list(done); state["last_iso"] = now.isoformat(timespec="seconds")
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PUBLISHED episode '{nxt['id']}' -> https://youtu.be/{vid}")

    # repurpose: push the episode (as its YouTube link) into the syndication machine so
    # every text channel promotes it — the long-form can't be hosted (>25MB CF asset cap),
    # so we distribute the LINK, driving views back to the video. Native FB/LinkedIn video
    # re-upload would need a new uploader; link promotion uses proven rails.
    try:
        sp = os.path.join(ROOT, "content", "syndication_queue.json")
        synd = json.load(open(sp)); sid = f"pod-{nxt['id']}"
        if not any(i["id"] == sid for i in synd["items"]):
            synd["items"].append({
                "id": sid, "title": nxt["title"].split("|")[0].strip(), "short_title": "New episode",
                "blurb": nxt["description"].split("\n")[0][:280], "url": f"https://youtu.be/{vid}",
                "labels": nxt.get("tags", ["The Podcast"])[:4], "posted": {}})
            json.dump(synd, open(sp, "w"), indent=2)
            log(f"syndication: queued episode link as '{sid}' for all text channels")
    except Exception as e:
        log(f"syndication inject failed (non-fatal): {str(e)[:120]}")

    try:
        import log_change
        log_change.add("podcast", f"Published podcast episode: {nxt['title'].split('|')[0].strip()}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
