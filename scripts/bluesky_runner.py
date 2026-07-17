#!/usr/bin/env python3
"""Autonomous Bluesky feed (launchd). PURE ENGAGEMENT (2026-07-17): posts native
engagement content from the shared pool (content/queue.json) — no links, no blog
teasers. Follower-growth surface, not a backlink surface."""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

STATE = os.path.join(ROOT, "content", "bluesky_state.json")
LOG = os.path.join(ROOT, "content", "bluesky.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    import engagement_pool
    state = load(STATE, {"done": []}); done = set(state["done"])
    if a.status:
        rem = [p["id"] for p in engagement_pool.posts() if p["id"] not in done]
        print(json.dumps({"done": len(done), "remaining": rem}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "bluesky.env")):
        log("Bluesky not connected (no secrets/bluesky.env) — skipping."); return
    import post_cadence
    if not a.force and not post_cadence.due(state, 4):
        log("skip: Bluesky cadence gate (~6/day)"); return
    nxt, reset = engagement_pool.next_unposted(done)
    if not nxt:
        log("engagement pool empty — nothing for Bluesky."); return
    if reset:
        done = set(); log("engagement pool exhausted — recycling from the top.")
    import bluesky_publish
    res = bluesky_publish.publish_text(engagement_pool.text_of(nxt)[:300])
    done.add(nxt["id"]); state["done"] = list(done); post_cadence.stamp(state)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED '{nxt['id']}' ({nxt.get('archetype')}) to Bluesky -> {res.get('uri')}")
    try:
        import log_change
        log_change.add("site", f"Posted engagement to Bluesky: {nxt['id'].replace('-', ' ')}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
