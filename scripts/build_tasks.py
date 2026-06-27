#!/usr/bin/env python3
"""Build the daily manual-task list (launchd, morning). Merges standing tasks
(content/tasks_config.json) with DYNAMIC reply tasks pulled from the Bluesky/Threads
engagement queues (already populated with real threads + direct links). Writes
site/dashboard/tasks.json. Done-state + grades are tracked server-side by the Worker."""
import datetime as dt, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CFG = os.path.join(ROOT, "content", "tasks_config.json")
OUT = os.path.join(ROOT, "site", "dashboard", "tasks.json")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def queue_tasks(state_file, platform, emoji, max_n=5):
    q = load(os.path.join(ROOT, "content", state_file), {}).get("queue", [])
    out = []
    for i, item in enumerate(q[:max_n]):
        handle = item.get("handle") or item.get("user") or "a trade account"
        text = (item.get("text") or "").strip().replace("\n", " ")[:90]
        out.append({"id": f"{platform.lower()}-q{i}", "platform": platform, "emoji": emoji,
                    "task": f"Reply to @{handle}: “{text}…”",
                    "note": "Add genuine value or a question — these are live threads the daemon surfaced.",
                    "link": item.get("url", ""), "est": "2 min"})
    return out


def main():
    cfg = load(CFG, {"daily": [], "setup": []})
    daily = list(cfg.get("daily", []))
    # dynamic reply tasks from the engagement queues (real threads + links)
    daily += queue_tasks("bluesky_engage_state.json", "Bluesky", "\U0001F98B", 5)
    daily += queue_tasks("threads_engage_state.json", "Threads", "\U0001F9F5", 5)
    data = {"date": dt.date.today().isoformat(), "daily": daily, "setup": cfg.get("setup", [])}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"wrote tasks.json — {len(daily)} daily, {len(data['setup'])} setup")


if __name__ == "__main__":
    main()
