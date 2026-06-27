#!/usr/bin/env python3
"""Threads keyword-surfacing (launchd) — searches public Threads for live
contractor conversations and writes them to a HUMAN reply queue. NEVER auto-replies
to strangers (that's the spam line). Needs the threads_keyword_search permission.
Queue: content/threads_replies.md · State: content/threads_engage_state.json"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
API = "https://graph.threads.net/v1.0"
STATE = os.path.join(ROOT, "content", "threads_engage_state.json")
QUEUE_MD = os.path.join(ROOT, "content", "threads_replies.md")
LOG = os.path.join(ROOT, "content", "threads_engage.log")

KEYWORDS = ["contractor marketing", "roofing leads", "hvac slow season", "plumber pricing",
            "electrician business", "contractor leads", "trades business owner", "home service business"]
QUEUE_MAX = 40


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "threads.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def main():
    if not os.path.exists(os.path.join(ROOT, "secrets", "threads.env")):
        log("Threads not connected — skipping."); return
    e = env(); tok = e["THREADS_TOKEN"]
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"queue": [], "seen": []}
    queue, seen = st.get("queue", []), set(st.get("seen", []))
    added = 0
    for kw in KEYWORDS:
        q = urllib.parse.urlencode({"q": kw, "search_type": "RECENT",
                                    "fields": "id,text,username,permalink", "access_token": tok})
        try:
            with urllib.request.urlopen(f"{API}/keyword_search?{q}", timeout=30) as r:
                data = json.loads(r.read().decode()).get("data", [])
        except urllib.error.HTTPError as ex:
            log(f"keyword_search '{kw}' {ex.code}: {ex.read().decode()[:160]} (token may lack threads_keyword_search)")
            return
        for p in data:
            pid = p.get("id")
            if not pid or pid in seen or not p.get("text"):
                continue
            seen.add(pid); added += 1
            queue.insert(0, {"user": p.get("username"), "text": p["text"][:200],
                             "url": p.get("permalink"), "kw": kw})
    queue = queue[:QUEUE_MAX]
    st["queue"] = queue; st["seen"] = list(seen)[-2000:]
    json.dump(st, open(STATE, "w"), indent=2)
    lines = ["# Threads — conversations queued for YOUR reply", "",
             "_Live contractor threads surfaced by keyword. Reply by hand (the 70/30 reply-guy method). Newest first._", ""]
    for q in queue:
        lines += [f"- **@{q['user']}** ({q['kw']}): {q['text']}", f"  → {q['url']}", ""]
    open(QUEUE_MD, "w").write("\n".join(lines))
    log(f"run: +{added} new threads surfaced, {len(queue)} in reply queue")


if __name__ == "__main__":
    main()
