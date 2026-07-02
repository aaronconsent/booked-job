#!/usr/bin/env python3
"""Fleet health alert — emails the operator when the machine breaks, so a dead token
or a stalled agent doesn't degrade a channel silently for days.

Fires on: any agent failing >=3 consecutive runs, or a content queue gone RED.
De-dupes (won't re-email the same issue set within 24h). Emails via Resend to
ALERT_TO (defaults to the Resend account). Runs last in run_all.

  python3 scripts/health_alert.py            # check + email if needed
  python3 scripts/health_alert.py --dry-run  # print, don't email
"""
import datetime as dt, hashlib, json, os, sys, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HEALTH = os.path.join(ROOT, "content", "agent_health.json")
DATA = os.path.join(ROOT, "site", "dashboard", "data.json")
STATE = os.path.join(ROOT, "content", "health_alert_state.json")
FAIL_THRESHOLD = 3


def jload(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d


def resend_env():
    p = os.path.join(ROOT, "secrets", "resend.env")
    e = {}
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); e[k] = v
    return e


def main():
    dry = "--dry-run" in sys.argv
    issues = []
    for agent, fails in jload(HEALTH, {}).items():
        if fails >= FAIL_THRESHOLD:
            issues.append(f"⚠️ {agent} — failed {fails} runs in a row")
    for r in jload(DATA, {}).get("runway", []):
        if r.get("status") == "red":
            d = r.get("days"); issues.append(f"📉 {r['label']} — content low ({d}d left)" if d is not None else f"📉 {r['label']} — thin")
    if not issues:
        print("health OK — no alert"); return

    sig = hashlib.sha256("|".join(sorted(issues)).encode()).hexdigest()[:12]
    st = jload(STATE, {})
    today = dt.date.today().isoformat()
    if st.get("sig") == sig and st.get("date") == today:
        print(f"{len(issues)} issue(s) but already alerted today — skipping"); return

    body = "<h2>Booked Job — health alert</h2><ul>" + "".join(f"<li>{i}</li>" for i in issues) + \
           "</ul><p>Dashboard: <a href='https://booked-job.com/dashboard/'>booked-job.com/dashboard</a></p>"
    if dry:
        print("DRY — would alert:\n  " + "\n  ".join(issues)); return

    e = resend_env()
    if not e.get("RESEND_API_KEY"):
        print("no Resend — can't email; issues:\n  " + "\n  ".join(issues)); return
    to = e.get("ALERT_TO") or e.get("RESEND_FROM", "").split("<")[-1].strip(">") or "hello@aaron.chat"
    req = urllib.request.Request("https://api.resend.com/emails",
                                 data=json.dumps({"from": e["RESEND_FROM"], "to": [to],
                                                  "subject": f"⚠️ Booked Job health — {len(issues)} issue(s)", "html": body}).encode(),
                                 method="POST")
    req.add_header("Authorization", f"Bearer {e['RESEND_API_KEY']}")
    req.add_header("Content-Type", "application/json"); req.add_header("User-Agent", "curl/8.4.0")
    try:
        urllib.request.urlopen(req, timeout=30)
        json.dump({"sig": sig, "date": today}, open(STATE, "w"))
        print(f"ALERTED {to} — {len(issues)} issue(s)")
    except urllib.error.HTTPError as ex:
        print(f"alert email failed {ex.code}: {ex.read().decode()[:160]}")


if __name__ == "__main__":
    main()
