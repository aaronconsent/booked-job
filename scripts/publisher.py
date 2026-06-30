#!/usr/bin/env python3
"""
Booked Job autonomous drip publisher. Run by launchd a few times a day; it
decides whether to post the next queued item based on the warm-up ramp, posting
windows, weekend skip, and day-to-day timing jitter.

This is designed to run UNATTENDED on Aaron's Mac (not through Claude), so it
never needs the permission classifier. It reads secrets/fb.env and content/queue.json.

State lives in content/state.json. Logs to content/publish.log.

Flags:
  --force     post the next queued item now, ignoring schedule (for testing)
  --dry-run   show what it WOULD do, post nothing
  --status    print queue/state summary and exit
"""
import argparse, datetime as dt, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import fb_post  # reuse Graph API helpers + env loader

QUEUE = os.path.join(ROOT, "content", "queue.json")
STATE = os.path.join(ROOT, "content", "state.json")
LOG = os.path.join(ROOT, "content", "publish.log")

# Posting windows (local time), as (start_hour, end_hour). Research: blue-collar
# audience is up early; test AM vs lunch. Evening catches homeowners too.
WINDOWS = {"am": (6, 9), "lunch": (11, 13), "evening": (18, 20)}


def log(msg):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def load_json(path, default):
    if os.path.exists(path):
        return json.load(open(path))
    return default


def save_state(state):
    json.dump(state, open(STATE, "w"), indent=2, ensure_ascii=False)


def ramp_daily_cap(age_days):
    # Warm-up ramp from STRATEGY.md: wk1 ~3/wk, wk2 ~4/wk, wk3+ up to 5-6/wk.
    # Implemented as posting-DAYS allowed + 1/day cap (quality > volume).
    return 2  # safe-aggressive: up to 2 quality FB posts/day (3-5 is the platform ceiling;
              # held at 2 so we don't outrun content supply — raise once the variant engine feeds it)


def posting_days(age_days):
    # 7-day posting (Aaron's call 2026-06-30): post every day, weekends included.
    # Cap stays 1 quality post/day (ramp_daily_cap) so it's aggressive on cadence,
    # not spammy on volume.
    return {0, 1, 2, 3, 4, 5, 6}   # Mon-Sun


def chosen_slot_for_today(today):
    # Deterministic per-day jitter: pick which window today's post uses, so
    # timing varies day to day without clock-like sameness.
    h = int(hashlib.sha256(today.isoformat().encode()).hexdigest(), 16)
    return ["am", "lunch", "am", "evening", "lunch"][h % 5]


def next_unposted(queue, posted):
    for p in queue["posts"]:
        if p["id"] not in posted:
            return p
    return None


def publish(item, env):
    page_id, token = env["FB_PAGE_ID"], env["FB_PAGE_TOKEN"]
    image = item.get("image")
    if image:
        path = os.path.join(ROOT, image)
        res = fb_post._upload_photo(page_id, path, item["caption"], token)
        post_id = res.get("post_id") or res.get("id")
    else:
        res = fb_post._post(f"{page_id}/feed", {"message": item["caption"], "access_token": token})
        post_id = res.get("id")
    # link / first comment (warm-up: queue keeps these null for ~2 weeks)
    if item.get("link") or item.get("comment"):
        ctext = item.get("comment") or "Link in comments 👇"
        if item.get("link"):
            ctext = f"{ctext}\n{item['link']}"
        fb_post._post(f"{post_id}/comments", {"message": ctext, "access_token": token})
    return post_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    queue = load_json(QUEUE, {"posts": []})
    state = load_json(STATE, {"page_created": dt.date.today().isoformat(),
                              "posted": [], "last_post_iso": None, "by_date": {}})
    posted = set(state.get("posted", []))

    if a.status:
        remaining = [p["id"] for p in queue["posts"] if p["id"] not in posted]
        print(json.dumps({"posted": len(posted), "remaining": len(remaining),
                          "next": remaining[0] if remaining else None,
                          "last_post_iso": state.get("last_post_iso")}, indent=2))
        return

    now = dt.datetime.now()
    today = now.date()
    age = (today - dt.date.fromisoformat(state["page_created"])).days

    item = next_unposted(queue, posted)
    if not item:
        log("queue empty — nothing to post. (refill content/queue.json)")
        return

    if not a.force:
        # schedule gate
        if today.weekday() not in posting_days(age):
            log(f"skip: {today:%A} not a posting day (age {age}d).")
            return
        if state["by_date"].get(today.isoformat(), 0) >= ramp_daily_cap(age):
            log("skip: daily cap reached.")
            return
        slot = chosen_slot_for_today(today)
        s, e = WINDOWS[slot]
        if not (s <= now.hour < e):
            log(f"skip: outside today's window '{slot}' ({s}-{e}h), now {now.hour}h.")
            return
        if state.get("last_post_iso"):
            gap = (now - dt.datetime.fromisoformat(state["last_post_iso"])).total_seconds() / 3600
            if gap < 16:
                log(f"skip: only {gap:.1f}h since last post (<16h).")
                return

    if a.dry_run:
        log(f"DRY-RUN would post '{item['id']}' ({item['archetype']}) image={bool(item.get('image'))}")
        return

    env = fb_post.load_env()
    try:
        post_id = publish(item, env)
    except SystemExit as ex:
        log(f"ERROR posting '{item['id']}': {ex}")
        raise
    posted.add(item["id"])
    state["posted"] = list(posted)
    state["last_post_iso"] = now.isoformat(timespec="seconds")
    state["by_date"][today.isoformat()] = state["by_date"].get(today.isoformat(), 0) + 1
    save_state(state)
    log(f"POSTED '{item['id']}' ({item['archetype']}) -> {post_id}")
    try:
        import log_change
        log_change.add("post", f"Published post: {item['id'].replace('-', ' ')}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
