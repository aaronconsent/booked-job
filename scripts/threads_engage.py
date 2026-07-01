#!/usr/bin/env python3
"""Threads engagement (launchd) — surfaces REPLIES to our own posts (people
engaging with us) to a HUMAN reply queue. Uses own-post replies instead of public
keyword_search, which needs the gated threads_keyword_search permission.
Queue: content/threads_replies.md · State: content/threads_engage_state.json"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
API = "https://graph.threads.net/v1.0"
STATE = os.path.join(ROOT, "content", "threads_engage_state.json")
QUEUE_MD = os.path.join(ROOT, "content", "threads_replies.md")
LOG = os.path.join(ROOT, "content", "threads_engage.log")
QUEUE_MAX = 40
POST_LOOKBACK = 20   # scan replies on our last N posts


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "threads.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def get(path, params, tok):
    params["access_token"] = tok
    try:
        with urllib.request.urlopen(f"{API}/{path}?" + urllib.parse.urlencode(params), timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        log(f"{path} {ex.code}: {ex.read().decode()[:140]}"); return {}


def main():
    if not os.path.exists(os.path.join(ROOT, "secrets", "threads.env")):
        log("Threads not connected — skipping."); return
    e = env(); tok = e["THREADS_TOKEN"]; uid = e["THREADS_USER_ID"]
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"queue": [], "seen": []}
    queue, seen = st.get("queue", []), set(st.get("seen", []))
    me = get(uid, {"fields": "username"}, tok).get("username", "")
    posts = get(f"{uid}/threads", {"fields": "id,text", "limit": str(POST_LOOKBACK)}, tok).get("data", [])
    added = 0
    for p in posts:
        reps = get(f"{p['id']}/replies", {"fields": "id,text,username,permalink"}, tok).get("data", [])
        for r in reps:
            rid = r.get("id")
            if not rid or rid in seen or not r.get("text") or r.get("username") == me:
                continue   # skip seen + our own chain replies
            seen.add(rid); added += 1
            queue.insert(0, {"user": r.get("username"), "text": r["text"][:200],
                             "url": r.get("permalink"), "on": (p.get("text") or "")[:60]})
    queue = queue[:QUEUE_MAX]
    st["queue"] = queue; st["seen"] = list(seen)[-2000:]
    json.dump(st, open(STATE, "w"), indent=2)
    lines = ["# Threads — replies to our posts, queued for YOUR reply", "",
             "_People engaging with our Threads posts. Reply by hand. Newest first._", ""]
    for q in queue:
        lines += [f"- **@{q['user']}** (on: {q.get('on','')}…): {q['text']}", f"  → {q.get('url')}", ""]
    open(QUEUE_MD, "w").write("\n".join(lines))
    log(f"run: +{added} new replies surfaced, {len(queue)} in reply queue")


if __name__ == "__main__":
    main()
