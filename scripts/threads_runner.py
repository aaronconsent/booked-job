#!/usr/bin/env python3
"""Autonomous Threads syndication (launchd, weekly). Posts a teaser + link for
the next queued article. Reuses content/syndication_queue.json."""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
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
    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"done": []}); done = set(state["done"])
    if a.status:
        print(json.dumps({"done": len(done), "remaining": [i["id"] for i in items if i["id"] not in done]}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "threads.env")):
        log("Threads not connected (no secrets/threads.env) — skipping."); return
    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Threads."); return
    hook = (nxt.get("short_title") or nxt["title"])
    blurb = (nxt.get("blurb", "") or "").split(". ")[0][:220]
    text = f"{hook}\n\n{blurb}.\n\n{nxt['url']}"
    import threads_publish
    res = threads_publish.publish_text(text[:500])
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED '{nxt['id']}' to Threads -> {res.get('id')}")
    try:
        import log_change
        log_change.add("site", f"Posted to Threads: {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
