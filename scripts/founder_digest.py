#!/usr/bin/env python3
"""Founder digest — emails Aaron a personal status update (via Resend, the same
rails as health_alert/newsletter), so he knows what the autonomous machine is
doing while traveling. Direct to his inbox — no bot, no setup.

Runs hourly inside run_all but self-gates: a rollup every ~2h during the day,
PLUS an immediate email when a major event lands (podcast upload, blog publish,
agent failure).

  python3 scripts/founder_digest.py --test    # send now, bypass gates
  python3 scripts/founder_digest.py --status   # print what it would send, don't send
"""
import argparse, datetime as dt, json, os, re, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
CHANGELOG = os.path.join(ROOT, "site", "dashboard", "changelog.json")
HEALTH = os.path.join(ROOT, "content", "agent_health.json")
STATE = os.path.join(ROOT, "content", "founder_digest_state.json")
LOG = os.path.join(ROOT, "content", "founder_digest.log")
FOUNDER_EMAIL = "hello@aaron.chat"   # who these go to (override with ALERT_TO in resend.env)
WINDOW = (7, 22)          # only send rollups 7am–10pm (host tz = America/Chicago)
GAP_HOURS = 2             # rollup cadence
MAJOR = re.compile(r"podcast episode|blog drip|published \d+ staged|went live|deploy failed|FAIL|outreach reply", re.I)


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def log(m):
    line = f"{dt.datetime.now():%Y-%m-%dT%H:%M:%S}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def resend_env():
    p = os.path.join(ROOT, "secrets", "resend.env")
    e = {}
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); e[k] = v
    return e


def send_email(subject, html, e):
    to = e.get("ALERT_TO") or FOUNDER_EMAIL
    req = urllib.request.Request("https://api.resend.com/emails",
                                 data=json.dumps({"from": e["RESEND_FROM"], "to": [to],
                                                  "subject": subject, "html": html}).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {e['RESEND_API_KEY']}")
    req.add_header("Content-Type", "application/json"); req.add_header("User-Agent", "curl/8.4.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return to


CHANNEL = re.compile(r"\b(Bluesky|Mastodon|Threads|Telegram|Tumblr|Telegraph|Blogger|GitHub|Pinterest|"
                     r"LinkedIn|TikTok|Facebook|Instagram|IG|FB|YouTube)\b")


def channel_of(text):
    m = CHANNEL.search(text)
    return m.group(1) if m else None


def compose(now):
    st = load(STATE, {})
    # first-ever run: only look back GAP_HOURS so the first digest isn't a giant backlog
    last_ts = st.get("last_ts") or (now - dt.timedelta(hours=GAP_HOURS)).strftime("%Y-%m-%dT%H:%M")
    entries = load(CHANGELOG, {"entries": []})["entries"]
    fresh = [e for e in entries if e.get("ts", "") > last_ts]
    today = now.date().isoformat()
    today_all = [e for e in entries if e.get("ts", "").startswith(today)]

    by_ch, majors = {}, []
    for e in fresh:
        t = e.get("text", "")
        if MAJOR.search(t):
            majors.append(f"{e.get('icon', '•')} {t[:120]}")
        ch = channel_of(t)
        if ch:
            by_ch[ch] = by_ch.get(ch, 0) + 1
    majors = list(dict.fromkeys(majors))

    health = load(HEALTH, {})
    failing = [f"{a.replace('.py','')} ({n}×)" for a, n in health.items() if isinstance(n, int) and n >= 3]

    hh = now.strftime("%-I:%M %p")
    rows = []
    if majors:
        rows.append("<p><b>Just happened:</b><br>" + "<br>".join(majors[:6]) + "</p>")
    if fresh:
        top = sorted(by_ch.items(), key=lambda x: -x[1])
        brk = " · ".join(f"{c} {n}" for c, n in top[:9]) or "misc"
        rows.append(f"<p>📤 <b>{len(fresh)} posts</b> since the last update — {brk}</p>")
    else:
        rows.append("<p>😴 Quiet couple of hours — nothing new posted.</p>")
    rows.append(f"<p>📊 <b>{len(today_all)}</b> posts so far today</p>")
    rows.append("<p>⚠️ <b>Needs a look:</b> " + ", ".join(failing[:6]) + "</p>" if failing
                else "<p>✅ All agents healthy</p>")
    html = (f"<div style='font:15px/1.5 -apple-system,sans-serif'><h2 style='margin:0 0 4px'>"
            f"🤖 Booked Job — {hh}</h2>" + "".join(rows) +
            "<p style='color:#888;font-size:13px'>Dashboard: "
            "<a href='https://booked-job.com/dashboard/'>booked-job.com/dashboard</a> · "
            "reply STOP to pause these.</p></div>")
    subject = (f"🎙️ Booked Job: {majors[0].split(' ', 1)[-1][:48]}" if majors
               else f"Booked Job — {hh} update ({len(today_all)} today)")
    return subject, html, bool(majors), (fresh[0]["ts"] if fresh else last_ts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="send now, bypass gates")
    ap.add_argument("--status", action="store_true", help="print, don't send")
    a = ap.parse_args()

    now = dt.datetime.now()
    subject, html, has_major, newest_ts = compose(now)
    e = resend_env()

    if a.status:
        print(subject + "\n" + re.sub("<[^>]+>", "", html))
        print(f"[major={has_major} resend={'set' if e.get('RESEND_API_KEY') else 'MISSING'}]"); return
    if not e.get("RESEND_API_KEY"):
        log("skip: no secrets/resend.env RESEND_API_KEY."); return

    st = load(STATE, {})
    if not a.test:
        last = st.get("last_iso")
        in_window = WINDOW[0] <= now.hour < WINDOW[1]
        gap_ok = (not last) or (now - dt.datetime.fromisoformat(last)).total_seconds() / 3600 >= GAP_HOURS
        if not (has_major or (in_window and gap_ok)):
            log(f"skip: no major event and not due (in_window={in_window}, gap_ok={gap_ok})"); return
    try:
        to = send_email(subject, html, e)
        log(f"emailed digest to {to} ({'major' if has_major else 'rollup'}).")
    except Exception as ex:
        log(f"send failed: {str(ex)[:160]}"); return
    st.update({"last_iso": now.isoformat(timespec="seconds"), "last_ts": newest_ts})
    json.dump(st, open(STATE, "w"), indent=2)


if __name__ == "__main__":
    main()
