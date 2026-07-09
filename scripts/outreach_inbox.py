#!/usr/bin/env python3
"""Poll the worker's captured inbox (hello@booked-job.com -> Email Worker -> KV)
and surface NEW replies: changelog entry (feeds the founder digest, which emails
Aaron immediately on replies) + outreach log. Read-only; never sends anything.
State: content/outreach_inbox_state.json (last seen ts)."""
import datetime as dt, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
STATE = os.path.join(ROOT, "content", "outreach_inbox_state.json")
LOG = os.path.join(ROOT, "content", "outreach.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def key():
    p = os.path.join(ROOT, "secrets", "ops.env")
    if os.path.exists(p):
        for ln in open(p):
            if ln.startswith("INBOX_KEY="):
                return ln.strip().split("=", 1)[1]
    return None


def main():
    k = key()
    if not k:
        log("inbox: no secrets/ops.env INBOX_KEY — skipping"); return
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"last_ts": ""}
    url = f"https://booked-job.com/ops/inbox?key={k}"
    if st["last_ts"]:
        url += f"&since={st['last_ts']}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        log(f"inbox fetch failed: {str(e)[:120]}"); return
    msgs = data.get("messages", [])
    if not msgs:
        print("inbox: nothing new"); return
    for m in msgs:
        line = f"Outreach reply from {m['from']}: {m['subject'][:80]}"
        log("REPLY " + line)
        try:
            import log_change
            log_change.add("engage", "📧 " + line)   # digest treats replies as major -> instant email
        except Exception:
            pass
    st["last_ts"] = max(m["ts"] for m in msgs)
    json.dump(st, open(STATE, "w"), indent=2)
    log(f"inbox: {len(msgs)} new message(s) surfaced")


if __name__ == "__main__":
    main()
