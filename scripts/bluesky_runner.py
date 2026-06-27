#!/usr/bin/env python3
"""Autonomous Bluesky syndication (launchd, weekly). Posts a teaser + link card
for the next queued article. Reuses content/syndication_queue.json."""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
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
    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"done": []}); done = set(state["done"])
    if a.status:
        print(json.dumps({"done": len(done), "remaining": [i["id"] for i in items if i["id"] not in done]}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "bluesky.env")):
        log("Bluesky not connected (no secrets/bluesky.env) — skipping."); return
    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Bluesky."); return
    import variants
    v = variants.get("bluesky", nxt["id"])
    teaser = v["text"] if v else (nxt.get("short_title") or nxt["title"]) + " — the honest math, plus a free calculator. 👇"
    import bluesky_publish
    chain = (v or {}).get("chain", []) if v else []
    if chain:
        res = bluesky_publish.publish_thread(teaser[:300], nxt["url"], nxt["title"], nxt.get("blurb", "")[:300], chain)
    else:
        res = bluesky_publish.publish(teaser[:300], nxt["url"], nxt["title"], nxt.get("blurb", "")[:300])
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED '{nxt['id']}' to Bluesky -> {res.get('uri')}")
    try:
        import log_change
        log_change.add("site", f"Posted to Bluesky: {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
