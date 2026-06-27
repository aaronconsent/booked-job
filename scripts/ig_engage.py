#!/usr/bin/env python3
"""
Instagram inbound pass — mirrors fb_engage's safe pattern: collect new comments on
our own IG media into content/inbox.md for a human to answer in voice. Does NOT
auto-reply with generated text (reads as spam, risks a young account). IG has no
like-a-comment API, so this is collect-for-human only.

Best-effort: logs cleanly if the token lacks instagram_manage_comments. Run by launchd.
State: content/ig_engage_state.json
"""
import datetime as dt, json, os, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GRAPH = "https://graph.facebook.com/v21.0"
INBOX = os.path.join(ROOT, "content", "inbox.md")
STATE = os.path.join(ROOT, "content", "ig_engage_state.json")
LOG = os.path.join(ROOT, "content", "ig_engage.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "fb.env")):
        if "=" in line:
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def get(path, params):
    try:
        with urllib.request.urlopen(f"{GRAPH}/{path}?" + urllib.parse.urlencode(params), timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        return {"_err": ex.read().decode()[:200]}
    except Exception as ex:
        return {"_err": str(ex)}


def main():
    e = env(); tok = e.get("FB_SYSTEM_TOKEN") or e.get("FB_PAGE_TOKEN"); ig = e.get("FB_IG_ID")
    if not (tok and ig):
        log("IG not configured — skipping."); return
    handled = set(json.load(open(STATE)).get("done", [])) if os.path.exists(STATE) else set()
    media = get(f"{ig}/media", {"fields": "id,caption", "limit": 15, "access_token": tok})
    if "_err" in media:
        log(f"media fetch failed: {media['_err']}"); return
    new = []
    for m in media.get("data", []):
        cs = get(f"{m['id']}/comments", {"fields": "id,text,username,timestamp", "access_token": tok})
        if "_err" in cs:
            log(f"comments need instagram_manage_comments? {cs['_err']}"); return
        for c in cs.get("data", []):
            if c["id"] in handled:
                continue
            handled.add(c["id"])
            new.append(((m.get("caption", "") or "")[:40], c.get("username", "?"), c.get("text", ""), (c.get("timestamp", "") or "")[:16]))
    json.dump({"done": list(handled)}, open(STATE, "w"), indent=2)
    if new:
        with open(INBOX, "a") as f:
            f.write(f"\n## [Instagram] {dt.datetime.now():%Y-%m-%d %H:%M} — {len(new)} new\n")
            for cap, who, msg, when in new:
                f.write(f"- **@{who}** on \"{cap}…\" ({when}): {msg}\n")
    log(f"IG: {len(new)} new comments logged to inbox.md")


if __name__ == "__main__":
    main()
