#!/usr/bin/env python3
"""
Autonomous Pinterest syndication (launchd, weekly). Generates a branded 2:3 pin
image for the next queued item and creates a Pin linking back to the canonical
article — long-lived referral traffic + a followable backlink. Reuses
content/syndication_queue.json.

State: content/pinterest_state.json. Log: content/pinterest.log.
Flags: --force, --dry-run, --status.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_pin

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "pinterest_state.json")
LOG = os.path.join(ROOT, "content", "pinterest.log")
PINS = os.path.join(ROOT, "content", "pins")


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

    if not os.path.exists(os.path.join(ROOT, "secrets", "pinterest.env")) and not a.dry_run:
        log("Pinterest not connected yet (no secrets/pinterest.env) — skipping."); return

    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Pinterest."); return

    title = nxt.get("short_title") or nxt["title"]
    teaser = (nxt.get("blurb", "") or "").split(".")[0][:90]
    img = os.path.join(PINS, f"{nxt['id']}.png")
    make_pin.make(title, teaser, img)

    if a.dry_run:
        log(f"DRY-RUN built pin image for '{nxt['id']}', not publishing"); return

    import pinterest_publish
    res = pinterest_publish.publish(nxt["title"], nxt.get("blurb", ""), nxt["url"], img)
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PINNED '{nxt['id']}' -> pin {res.get('id', 'ok')}")
    try:
        import log_change
        log_change.add("site", f"Syndicated to Pinterest (backlink): {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
