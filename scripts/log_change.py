#!/usr/bin/env python3
"""Append an entry to the dashboard changelog. Used by automation + by hand.

    python3 scripts/log_change.py post "Published feed post: pricing-pick-two"
    python3 scripts/log_change.py reel "Published Reel: low-bid"
    python3 scripts/log_change.py ad   "Raised daily budget to $10"
"""
import datetime as dt, json, os, sys

LOG = os.path.join(os.path.dirname(__file__), "..", "site", "dashboard", "changelog.json")
ICON = {"post": "📝", "reel": "🎬", "ad": "💸", "engage": "💬", "build": "🛠️",
        "strategy": "🧭", "report": "📊", "site": "🌐"}


def add(kind, text):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    data = json.load(open(LOG)) if os.path.exists(LOG) else {"entries": []}
    data["entries"].insert(0, {"ts": dt.datetime.now().isoformat(timespec="minutes"),
                               "kind": kind, "icon": ICON.get(kind, "•"), "text": text})
    data["entries"] = data["entries"][:200]
    json.dump(data, open(LOG, "w"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: log_change.py <kind> <text>")
    add(sys.argv[1], " ".join(sys.argv[2:]))
    print("logged.")
