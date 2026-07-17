#!/usr/bin/env python3
"""Autonomous Threads feed (launchd). PURE ENGAGEMENT (2026-07-17): posts native
engagement content from the shared pool (content/queue.json) — no links, no blog
teasers. Threads' top growth signal is replies, so we keep the self-reply chain
when the pool item carries one."""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

STATE = os.path.join(ROOT, "content", "threads_state.json")
LOG = os.path.join(ROOT, "content", "threads.log")


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
    if not os.path.exists(os.path.join(ROOT, "secrets", "threads.env")):
        log("Threads not connected (no secrets/threads.env) — skipping."); return
    import post_cadence
    if not a.force and not post_cadence.due(state, 4):
        log("skip: Threads cadence gate (~6/day)"); return
    nxt, reset = engagement_pool.next_unposted(done)
    if not nxt:
        log("engagement pool empty — nothing for Threads."); return
    if reset:
        done = set(); log("engagement pool exhausted — recycling from the top.")
    text = engagement_pool.text_of(nxt)
    import threads_publish
    threads_publish.refresh_and_save()  # keep the 60-day token alive
    res = threads_publish.publish_text(text[:500])
    done.add(nxt["id"]); state["done"] = list(done); post_cadence.stamp(state)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED '{nxt['id']}' ({nxt.get('archetype')}) to Threads -> {res.get('id')}")
    try:
        import log_change
        log_change.add("site", f"Posted engagement to Threads: {nxt['id'].replace('-', ' ')}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
