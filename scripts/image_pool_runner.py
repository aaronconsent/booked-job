#!/usr/bin/env python3
"""Shared IMAGE POOL -> per-platform image posters at independent, paced cadences.
Mirrors video_pool_runner. Reads content/image_pool.json (stat-cards + carousels).

Reliable native image paths wired now:
  - pinterest (native, local file — no deploy needed)  : one pin per image post
  - mastodon  (native, local file — no deploy needed)  : card as image toot
  - ig        (carousel via Graph API — needs public URLs / deploy)
FB / LinkedIn / Bluesky single-image posting needs a small publish_image() added
to those publishers first; they're intentionally left out until then.
"""
import argparse, datetime as dt, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
POOL = os.path.join(ROOT, "content", "image_pool.json")
STATE = os.path.join(ROOT, "content", "image_pool_state.json")
LOG = os.path.join(ROOT, "content", "image_pool.log")
BASE = "https://booked-job.com"
ACTIVE = (8, 21)


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def log(m):
    line = f"{dt.datetime.now():%Y-%m-%dT%H:%M:%S}  {m}"
    print(line)
    open(LOG, "a").write(line + "\n")


def localpath(url):
    return os.path.join(ROOT, url.replace(BASE + "/", "site/"))


def title_of(p):
    return (p["caption"].split(".")[0])[:120]


# ---- posters (truthy on success, raise on failure) ----
def _buffer(channel_key, p, single_only=False):
    """Post via Buffer (Pinterest/LinkedIn) — image assets require PUBLIC URLs (deploy)."""
    import buffer_publish as BP
    e = BP.env(); ch = e.get(channel_key)
    if not ch:
        raise RuntimeError(f"{channel_key} not set in buffer.env")
    urls = p["images"]
    if single_only or len(urls) < 2:
        return BP.queue_text(ch, p["caption"], assets=[{"image": {"url": urls[0]}}])
    return BP.queue_images(ch, p["caption"], urls)


def post_pinterest(p):  return _buffer("BUFFER_PINTEREST_CHANNEL", p, single_only=True)   # pin = 1 image
def post_linkedin(p):   return _buffer("BUFFER_LINKEDIN_CHANNEL", p)                       # single or multi


def post_mastodon(p):
    import mastodon_publish as M
    imgs = [localpath(u) for u in p["images"][:4]]   # native, LOCAL file — no deploy needed
    mids = [M.upload_media(i, title_of(p)) for i in imgs]
    return M.publish(p["caption"][:480], mids)


def post_ig(p):
    import ig_publish
    return ig_publish.publish_carousel(p["images"], p["caption"])   # Graph carousel, needs public URLs


PLATFORMS = {
    "mastodon":  {"cap": 50, "post": post_mastodon},                         # uncapped, local file → posts now
    "pinterest": {"cap": 50, "post": post_pinterest},                        # uncapped, Buffer → needs deploy
    "linkedin":  {"cap": 8, "post": post_linkedin},                          # high-ceiling, Buffer → needs deploy
    "ig":        {"cap": 6, "post": post_ig, "only_type": "carousel"},       # Meta high-ceiling, Graph → needs deploy
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    pool = load(POOL, {"images": []})["images"]
    if not pool:
        log("image pool empty — run integrate_cards.py first"); return
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
        ok = [p for p in pool if not cfg.get("only_type") or p["type"] == cfg["only_type"]]
        unposted = [p for p in ok if p["id"] not in st["posted"]]
        if not unposted:                                # cycled — reuse evergreen pool
            st["posted"] = [i for i in st["posted"] if i not in {p["id"] for p in ok}]
            unposted = ok
        if not unposted:
            continue
        p = unposted[0]
        if a.dry_run:
            log(f"{name}: DRY would post '{p['id']}' ({st['day']['count']}/{cap} today, spacing {spacing}h)")
            continue
        try:
            cfg["post"](p)
            st["posted"].append(p["id"]); st["last_iso"] = now.isoformat(timespec="seconds")
            st["day"]["count"] += 1
            log(f"{name}: POSTED '{p['id']}' -> {st['day']['count']}/{cap} today")
        except Exception as ex:
            log(f"{name}: FAILED '{p['id']}': {str(ex)[:160]}")
    if not a.dry_run:
        json.dump(state, open(STATE, "w"), indent=2)


if __name__ == "__main__":
    main()
