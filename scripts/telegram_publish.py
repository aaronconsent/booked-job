#!/usr/bin/env python3
"""Telegram publisher — posts to a broadcast channel via the Bot API.
Reads secrets/telegram.env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (e.g. @bookedjob)."""
import json, os, sys, urllib.parse, urllib.request


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "telegram.env")
    if not os.path.exists(p):
        sys.exit("secrets/telegram.env missing.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _call(method, params):
    e = env()
    url = f"https://api.telegram.org/bot{e['TELEGRAM_BOT_TOKEN']}/{method}"
    params = {"chat_id": e["TELEGRAM_CHAT_ID"], **params}
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Telegram error {ex.code}: {ex.read().decode()[:300]}")


def send_message(text):
    return _call("sendMessage", {"text": text, "parse_mode": "HTML", "disable_web_page_preview": "false"})


def send_poll(question, options, correct_option_id=None, explanation=None):
    """Post a poll/quiz to the channel. Pass correct_option_id for quiz mode."""
    params = {"question": question[:300],
              "options": json.dumps([{"text": o[:100]} for o in options]),
              "is_anonymous": "true"}
    if correct_option_id is not None:
        params["type"] = "quiz"; params["correct_option_id"] = correct_option_id
        if explanation:
            params["explanation"] = explanation[:200]
    return _call("sendPoll", params)


def send_photo(photo_url, caption=""):
    return _call("sendPhoto", {"photo": photo_url, "caption": caption[:1024], "parse_mode": "HTML"})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--text", required=True)
    a = ap.parse_args()
    print(json.dumps(send_message(a.text), indent=2))
