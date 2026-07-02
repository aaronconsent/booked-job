#!/usr/bin/env python3
"""
Shared VIDEO POOL → per-platform video runners at INDEPENDENT cadences.

One rendered video (in content/video_pool.json, public at booked-job.com/reels/…)
is an evergreen asset that each platform pulls from at its own daily rate. Each
platform tracks its own consumption, so a clip can hit IG, TikTok, LinkedIn,
Pinterest, Bluesky, Tumblr and Telegram on different days without collisions.
The pool cycles (evergreen) once a platform has run through it; reel_runner keeps
adding fresh clips.

  python3 scripts/video_pool_runner.py            # post due videos everywhere
  python3 scripts/video_pool_runner.py --dry-run  # show what would post, no API
  python3 scripts/video_pool_runner.py --force    # bypass cap+spacing (1/platform)
  python3 scripts/video_pool_runner.py --only ig  # a single platform
"""
import argparse, datetime as dt, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
POOL = os.path.join(ROOT, "content", "video_pool.json")
STATE = os.path.join(ROOT, "content", "video_pool_state.json")
LOG = os.path.join(ROOT, "content", "video_pool.log")
ACTIVE = (6, 22)   # only post between 6am–10pm local (TZ=America/Chicago on the cloud)


def load(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line, flush=True)
    try:
        open(LOG, "a").write(line + "\n")
    except Exception:
        pass


# ---- per-platform publishers (return truthy on success, raise on failure) ----
def post_ig(v):
    import ig_publish
    return ig_publish.publish(v["url"], v["caption"])


def post_fb(v):
    import fb_post_reel
    return fb_post_reel.publish_reel(os.path.join(ROOT, v["file"]), v["caption"])


def _buffer(channel_key, v):
    import buffer_publish as BP
    e = BP.env(); ch = e.get(channel_key)
    if not ch:
        raise RuntimeError(f"{channel_key} not set in buffer.env")
    return BP.queue_video(ch, v["caption"], v["url"], title=v.get("hook"))


def post_tiktok(v):    return _buffer("BUFFER_TIKTOK_CHANNEL", v)
def post_linkedin(v):  return _buffer("BUFFER_LINKEDIN_CHANNEL", v)
def post_pinterest(v): return _buffer("BUFFER_PINTEREST_CHANNEL", v)


def post_bluesky(v):
    import bluesky_publish
    return bluesky_publish.publish_video(v["caption"][:300], v["url"], alt=v.get("hook", ""))


def post_telegram(v):
    import telegram_publish
    return telegram_publish.send_video(v["url"], v["caption"])


def post_tumblr(v):
    import tumblr_publish
    return tumblr_publish.publish_video(v["caption"], v["url"], tags=(v.get("tags") or []))


# name -> {cap: posts/day, post: fn, exclude?: [id-substrings to skip on this platform]}.
# spacing is derived from cap. LinkedIn stays professional — no edgy podcast bits.
PLATFORMS = {
    "facebook":  {"cap": 4, "post": post_fb},
    "ig":        {"cap": 3, "post": post_ig},
    "tiktok":    {"cap": 4, "post": post_tiktok},
    "linkedin":  {"cap": 4, "post": post_linkedin, "exclude": ["porno", "clip2-game"]},
    "pinterest": {"cap": 6, "post": post_pinterest, "exclude": ["porno"]},
    "bluesky":   {"cap": 4, "post": post_bluesky},
    "telegram":  {"cap": 1, "post": post_telegram},
    "tumblr":    {"cap": 4, "post": post_tumblr, "exclude": ["porno"]},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    pool = load(POOL, {"videos": []})["videos"]
    if not pool:
        log("video pool empty — render clips first"); return
    state = load(STATE, {})
    now = dt.datetime.now(); today = now.date().isoformat()
    if not a.force and not (ACTIVE[0] <= now.hour < ACTIVE[1]):
        log(f"outside active window {ACTIVE} (now {now.hour}h)"); return

    for name, cfg in PLATFORMS.items():
        if a.only and name != a.only:
            continue
        st = state.setdefault(name, {"posted": [], "last_iso": None, "day": {"date": today, "count": 0}})
        if st["day"]["date"] != today:
            st["day"] = {"date": today, "count": 0}
        cap = cfg["cap"]; spacing = max(1, round(14 / cap))
        if not a.force:
            if st["day"]["count"] >= cap:
                continue
            if st.get("last_iso"):
                gap = (now - dt.datetime.fromisoformat(st["last_iso"])).total_seconds() / 3600
                if gap < spacing:
                    continue
        ok = [v for v in pool if not any(x in v["id"] for x in cfg.get("exclude", []))]
        unposted = [v for v in ok if v["id"] not in st["posted"]]
        if not unposted:                       # cycled through — reuse the evergreen pool
            st["posted"] = [i for i in st["posted"] if i not in {v["id"] for v in ok}]
            unposted = ok
        if not unposted:
            continue
        v = unposted[0]
        if a.dry_run:
            log(f"{name}: DRY would post '{v['id']}' ({st['day']['count']}/{cap} today, spacing {spacing}h)")
            continue
        try:
            cfg["post"](v)
            st["posted"].append(v["id"]); st["last_iso"] = now.isoformat(timespec="seconds")
            st["day"]["count"] += 1
            log(f"{name}: POSTED '{v['id']}' -> {st['day']['count']}/{cap} today")
        except Exception as ex:
            log(f"{name}: FAILED '{v['id']}': {str(ex)[:160]}")
    if not a.dry_run:
        json.dump(state, open(STATE, "w"), indent=2)


if __name__ == "__main__":
    main()
