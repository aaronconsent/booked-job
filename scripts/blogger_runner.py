#!/usr/bin/env python3
"""
Autonomous Blogger syndication (launchd, weekly). Republishes the next queued
post summary to the Booked Job Blogger blog with a dofollow link back to the
canonical article on booked-job.com — a Google-owned authority surface + backlink.

Publishes summaries (not full duplicates) to avoid cannibalizing our own SEO.
State: content/blogger_state.json. Log: content/blogger.log.
Flags: --force, --dry-run, --status.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "blogger_state.json")
LOG = os.path.join(ROOT, "content", "blogger.log")


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

    if not os.path.exists(os.path.join(ROOT, "secrets", "blogger.env")) and not a.dry_run:
        log("Blogger not connected yet (no secrets/blogger.env) — skipping."); return

    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — add items to content/syndication_queue.json"); return

    if a.dry_run:
        log(f"DRY-RUN would publish '{nxt['id']}' to Blogger"); return

    import blogger_publish
    res = blogger_publish.publish(nxt["title"], nxt["content_html"], nxt.get("labels", []))
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"SYNDICATED '{nxt['id']}' -> {res.get('url')}")
    try:
        import log_change
        log_change.add("site", f"Syndicated to Blogger (backlink): {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
