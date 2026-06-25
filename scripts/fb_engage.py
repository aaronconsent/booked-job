#!/usr/bin/env python3
"""
Booked Job engagement pass. For recent posts:
  - LIKE new comments as the Page (safe, warm signal; research says reply/engage
    fast on a new page),
  - collect comments into content/inbox.md so a human (or a future Claude session)
    can reply in voice.

Deliberately does NOT auto-reply with generated text — generic auto-replies read
as spam and risk the new page. Liking + a triaged inbox is the safe autonomous play.

Run a couple times a day by launchd. Tracks handled comment ids in content/engage_state.json.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import fb_post

GRAPH = "https://graph.facebook.com/v21.0"
ESTATE = os.path.join(ROOT, "content", "engage_state.json")
INBOX = os.path.join(ROOT, "content", "inbox.md")


def get(path, params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": e.read().decode()}


def like(comment_id, token):
    body = urllib.parse.urlencode({"access_token": token}).encode()
    req = urllib.request.Request(f"{GRAPH}/{comment_id}/likes", data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()).get("success", True)
    except urllib.error.HTTPError:
        return False


def main():
    env = fb_post.load_env()
    page, token = env["FB_PAGE_ID"], env["FB_PAGE_TOKEN"]
    handled = set(json.load(open(ESTATE)).get("liked", [])) if os.path.exists(ESTATE) else set()

    posts = get(f"{page}/posts", {"fields": "id,message", "limit": 15, "access_token": token})
    new_comments, liked_now = [], 0
    for p in posts.get("data", []):
        cs = get(f"{p['id']}/comments", {"fields": "id,from,message,created_time,like_count",
                                         "limit": 50, "access_token": token})
        for c in cs.get("data", []):
            if c["id"] in handled:
                continue
            if like(c["id"], token):
                liked_now += 1
            handled.add(c["id"])
            who = c.get("from", {}).get("name", "someone")
            new_comments.append((p.get("message", "")[:40], who, c.get("message", ""), c.get("created_time", "")[:16]))

    json.dump({"liked": list(handled)}, open(ESTATE, "w"), indent=2)

    if new_comments:
        with open(INBOX, "a") as f:
            f.write(f"\n## {dt.datetime.now():%Y-%m-%d %H:%M} — {len(new_comments)} new\n")
            for post_msg, who, msg, when in new_comments:
                f.write(f"- **{who}** on _{post_msg}…_ ({when}): {msg}\n")
    print(f"engage: liked {liked_now} new comments, {len(new_comments)} logged to inbox.md")


if __name__ == "__main__":
    main()
