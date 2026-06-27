#!/usr/bin/env python3
"""
Bluesky engagement daemon (launchd, a few times/day) — the ONE channel whose API
permits tasteful automated engagement. Conservative + guard-railed:

  • SEARCHES contractor/trades keywords for relevant posts
  • LIKES genuinely relevant posts   (daily cap, jittered)
  • DRIP-FOLLOWS relevant authors    (daily cap, jittered, NO unfollow churn)
  • QUEUES hot threads for a HUMAN to reply to  (never auto-replies to strangers)

Guardrails (from growth research): warm-up ramp (low caps first 7 days), small
per-run batches, randomized jitter between every action, no follow/unfollow churn,
no auto-reply. Bio funnel-link should stay OFF the profile until ~1k followers
(that's a manual profile setting — the daemon never touches it).

State: content/bluesky_engage_state.json · Human queue: content/bluesky_replies.md
"""
import datetime as dt, json, os, random, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import bluesky_publish as B

PDS = "https://bsky.social/xrpc"
STATE = os.path.join(ROOT, "content", "bluesky_engage_state.json")
QUEUE_MD = os.path.join(ROOT, "content", "bluesky_replies.md")
LOG = os.path.join(ROOT, "content", "bluesky_engage.log")

KEYWORDS = [
    "contractor marketing", "roofing business", "hvac business owner", "plumber business",
    "electrician business", "home service business", "contractor leads", "trades business",
    "field service business", "small business owner trades", "skilled trades", "general contractor",
]
PER_RUN = {"follow": 4, "like": 6}          # small batch each run (launchd runs ~4x/day)
REPLY_QUEUE_MAX = 40


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load_state():
    s = json.load(open(STATE)) if os.path.exists(STATE) else {}
    today = dt.date.today().isoformat()
    s.setdefault("started", today)
    if s.get("day") != today:                # reset daily counters
        s["day"] = today; s["follows_today"] = 0; s["likes_today"] = 0
    s.setdefault("followed", []); s.setdefault("liked", []); s.setdefault("queue", [])
    return s


def daily_caps(started):
    days = (dt.date.today() - dt.date.fromisoformat(started)).days
    return {"follow": 8, "like": 12} if days < 7 else {"follow": 25, "like": 25}  # warm-up vs ramp


def jitter():
    time.sleep(random.uniform(4, 22))        # human-paced drip


def _get(path, jwt):
    req = urllib.request.Request(f"{PDS}/{path}")
    req.add_header("Authorization", f"Bearer {jwt}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def now_iso():
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")


def write_queue_md(queue):
    lines = ["# Bluesky — threads queued for YOUR reply", "",
             "_Auto-surfaced relevant conversations. Reply by hand (keeps it human + safe). Newest first._", ""]
    for q in queue[:REPLY_QUEUE_MAX]:
        lines += [f"- **@{q['handle']}**: {q['text']}", f"  → {q['url']}", ""]
    open(QUEUE_MD, "w").write("\n".join(lines))


def main():
    if not os.path.exists(os.path.join(ROOT, "secrets", "bluesky.env")):
        log("Bluesky not connected — skipping."); return
    s = load_state()
    caps = daily_caps(s["started"])
    e = B.env(); sess = B.session(e); jwt = sess["accessJwt"]; me = sess["did"]
    followed, liked, queue = set(s["followed"]), set(s["liked"]), s["queue"]
    run_f = run_l = 0
    random.shuffle(KEYWORDS)

    for kw in KEYWORDS:
        if run_f >= PER_RUN["follow"] and run_l >= PER_RUN["like"]:
            break
        try:
            res = _get("app.bsky.feed.searchPosts?" + urllib.parse.urlencode({"q": kw, "limit": 25}), jwt)
        except Exception as ex:
            log(f"search '{kw}' failed: {ex}"); continue
        for p in res.get("posts", []):
            author = p.get("author", {}); did = author.get("did"); rec = p.get("record", {})
            text = (rec.get("text") or "").strip()
            if not did or did == me or "en" not in (rec.get("langs") or ["en"]):
                continue
            # LIKE
            if (run_l < PER_RUN["like"] and s["likes_today"] < caps["like"] and p["uri"] not in liked):
                try:
                    B._post("com.atproto.repo.createRecord", {"repo": me, "collection": "app.bsky.feed.like",
                            "record": {"$type": "app.bsky.feed.like", "subject": {"uri": p["uri"], "cid": p["cid"]},
                                       "createdAt": now_iso()}}, jwt)
                    liked.add(p["uri"]); s["likes_today"] += 1; run_l += 1; jitter()
                except Exception as ex:
                    log(f"like failed: {ex}")
            # FOLLOW (no churn — only accounts we've never followed)
            if (run_f < PER_RUN["follow"] and s["follows_today"] < caps["follow"] and did not in followed):
                try:
                    B._post("com.atproto.repo.createRecord", {"repo": me, "collection": "app.bsky.graph.follow",
                            "record": {"$type": "app.bsky.graph.follow", "subject": did, "createdAt": now_iso()}}, jwt)
                    followed.add(did); s["follows_today"] += 1; run_f += 1; jitter()
                except Exception as ex:
                    log(f"follow failed: {ex}")
            # QUEUE strong opportunities for a HUMAN (questions / asks)
            if ("?" in text or any(w in text.lower() for w in ("how do", "anyone", "recommend", "advice"))):
                url = f"https://bsky.app/profile/{author.get('handle')}/post/{p['uri'].split('/')[-1]}"
                if not any(q["url"] == url for q in queue):
                    queue.insert(0, {"handle": author.get("handle"), "text": text[:200], "url": url})
            if run_f >= PER_RUN["follow"] and run_l >= PER_RUN["like"]:
                break

    s["followed"] = list(followed)[-5000:]; s["liked"] = list(liked)[-5000:]
    s["queue"] = queue[:REPLY_QUEUE_MAX]
    json.dump(s, open(STATE, "w"), indent=2)
    write_queue_md(queue)
    log(f"run: +{run_f} follows (+{s['follows_today']}/{caps['follow']} today), "
        f"+{run_l} likes (+{s['likes_today']}/{caps['like']} today), {len(queue)} threads queued for reply")


if __name__ == "__main__":
    main()
