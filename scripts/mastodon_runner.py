#!/usr/bin/env python3
"""Autonomous Mastodon syndication (launchd, weekly). Posts a teaser + URL
(Mastodon auto-links + builds a preview card). Reuses content/syndication_queue.json."""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "mastodon_state.json")
LOG = os.path.join(ROOT, "content", "mastodon.log")


def log(m):
    import datetime as dt
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
    if not os.path.exists(os.path.join(ROOT, "secrets", "mastodon.env")):
        log("Mastodon not connected (no secrets/mastodon.env) — skipping."); return
    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Mastodon."); return
    import variants
    v = variants.get("mastodon", nxt["id"])
    if v:
        text = f"{v['text']}\n\n{nxt['url']}\n\n{' '.join(v.get('tags', []))}"
    else:
        blurb = nxt.get("blurb", "")[:380]
        text = f"{blurb}\n\n{nxt['url']}\n\n#contractor #trades #plumber #roofer #hvac #electrician"
    import mastodon_publish
    res = mastodon_publish.publish(text[:500])
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED '{nxt['id']}' to Mastodon -> {res.get('url')}")
    try:
        import log_change
        log_change.add("site", f"Posted to Mastodon: {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
