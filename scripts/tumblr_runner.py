#!/usr/bin/env python3
"""
Autonomous Tumblr syndication (launchd, weekly). Posts the next queued item to
the Booked Job Tumblr as a text + link block — a high-DA, fast-indexing surface
+ a backlink to the canonical article. Reuses content/syndication_queue.json.

State: content/tumblr_state.json. Log: content/tumblr.log.
Flags: --force, --dry-run, --status.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "tumblr_state.json")
LOG = os.path.join(ROOT, "content", "tumblr.log")


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

    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"done": []})
    done = set(state["done"])

    if a.status:
        print(json.dumps({"done": len(done), "remaining": [i["id"] for i in items if i["id"] not in done]}, indent=2)); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "tumblr.env")) and not a.dry_run:
        log("Tumblr not connected yet (no secrets/tumblr.env) — skipping."); return

    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Tumblr."); return

    text = nxt.get("blurb") or nxt["title"]
    if a.dry_run:
        log(f"DRY-RUN would post '{nxt['id']}' to Tumblr"); return

    import tumblr_publish
    res = tumblr_publish.publish(text, nxt["url"], nxt["title"], nxt.get("blurb", ""), nxt.get("labels", []))
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED '{nxt['id']}' to Tumblr -> {res.get('response', {}).get('id_string', 'ok')}")
    try:
        import log_change
        log_change.add("site", f"Syndicated to Tumblr (backlink): {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
