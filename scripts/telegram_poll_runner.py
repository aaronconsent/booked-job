#!/usr/bin/env python3
"""Telegram quiz-poll engagement bait (launchd). Posts the next un-posted quiz
poll to the channel — native interaction + drives to an article via the answer
explanation. Source: content/telegram_polls.json. State: content/telegram_poll_state.json"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

POLLS = os.path.join(ROOT, "content", "telegram_polls.json")
STATE = os.path.join(ROOT, "content", "telegram_poll_state.json")
LOG = os.path.join(ROOT, "content", "telegram_poll.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    polls = load(POLLS, {"polls": []})["polls"]
    state = load(STATE, {"done": []}); done = set(state["done"])
    if a.status:
        print(json.dumps({"done": len(done), "remaining": [p["id"] for p in polls if p["id"] not in done]}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "telegram.env")):
        log("Telegram not connected — skipping."); return
    nxt = next((p for p in polls if p["id"] not in done), None)
    if not nxt:
        # cycle back to the start so the channel always has fresh polls
        done = set(); nxt = polls[0] if polls else None
    if not nxt:
        log("no polls configured."); return
    import telegram_publish
    res = telegram_publish.send_poll(nxt["q"], nxt["options"], nxt.get("correct"), nxt.get("explain"))
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"POSTED poll '{nxt['id']}' (msg {res.get('result', {}).get('message_id')})")


if __name__ == "__main__":
    main()
