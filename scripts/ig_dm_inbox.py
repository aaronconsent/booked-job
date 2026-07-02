#!/usr/bin/env python3
"""Instagram DM inbox — pulls new DMs into a human inbox file so Aaron can reply by
hand (no auto-DM to strangers). Gated behind Instagram messaging Advanced Access:
until that's approved the conversations endpoint returns (#3) and this logs + skips.
Wired into run_all; ready to light up the moment the permission lands.

  Inbox: content/ig_dm_inbox.md · State: content/ig_dm_state.json
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
API = "https://graph.facebook.com/v22.0"
INBOX = os.path.join(ROOT, "content", "ig_dm_inbox.md")
STATE = os.path.join(ROOT, "content", "ig_dm_state.json")
LOG = os.path.join(ROOT, "content", "ig_dm_inbox.log")
MAX = 50


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "fb.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def get(path, params, tok):
    params["access_token"] = tok
    try:
        with urllib.request.urlopen(f"{API}/{path}?" + urllib.parse.urlencode(params), timeout=25) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        return {"_err": ex.code, "_body": ex.read().decode()[:160]}


def main():
    if not os.path.exists(os.path.join(ROOT, "secrets", "fb.env")):
        log("fb.env missing — skipping."); return
    e = env(); tok = e.get("FB_SYSTEM_TOKEN"); ig = e.get("FB_IG_ID")
    convos = get(f"{ig}/conversations", {"platform": "instagram", "fields": "id,updated_time"}, tok)
    if convos.get("_err"):
        log(f"conversations {convos['_err']}: {convos['_body']} — messaging Advanced Access not granted yet; skipping.")
        return
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"seen": [], "inbox": []}
    seen, inbox = set(st.get("seen", [])), st.get("inbox", [])
    added = 0
    for c in convos.get("data", []):
        msgs = get(f"{c['id']}", {"fields": "messages{id,message,from,created_time}"}, tok).get("messages", {}).get("data", [])
        for m in msgs:
            mid = m.get("id")
            if not mid or mid in seen or (m.get("from", {}).get("id") == ig):
                continue  # skip seen + our own outbound
            seen.add(mid); added += 1
            inbox.insert(0, {"from": m.get("from", {}).get("username", "?"), "text": (m.get("message") or "")[:280],
                             "at": m.get("created_time", "")})
    inbox = inbox[:MAX]
    st["seen"] = list(seen)[-2000:]; st["inbox"] = inbox
    json.dump(st, open(STATE, "w"), indent=2)
    lines = ["# Instagram DMs — reply by hand", ""]
    for d in inbox:
        lines += [f"- **@{d['from']}** ({d['at'][:10]}): {d['text']}", ""]
    open(INBOX, "w").write("\n".join(lines))
    log(f"run: +{added} new DMs, {len(inbox)} in inbox")


if __name__ == "__main__":
    main()
