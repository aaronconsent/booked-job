#!/usr/bin/env python3
"""Autonomous Telegram syndication (launchd, weekly). Posts the next queued
article to the Booked Job channel as a message with a link preview.
Reuses content/syndication_queue.json."""
import argparse, datetime as dt, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "telegram_state.json")
LOG = os.path.join(ROOT, "content", "telegram.log")


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
    if not os.path.exists(os.path.join(ROOT, "secrets", "telegram.env")):
        log("Telegram not connected (no secrets/telegram.env) — skipping."); return
    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Telegram."); return
    import variants
    v = variants.get("telegram", nxt["id"])
    if v:
        text = v  # variant is the full HTML-ready text
    else:
        title = html.escape(nxt["title"]); blurb = html.escape(nxt.get("blurb", "")[:350])
        text = f"<b>{title}</b>\n\n{blurb}\n\n{nxt['url']}"
    import telegram_publish
    res = telegram_publish.send_message(text)
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    mid = res.get("result", {}).get("message_id")
    log(f"POSTED '{nxt['id']}' to Telegram (msg {mid})")
    try:
        import log_change
        log_change.add("site", f"Posted to Telegram: {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
