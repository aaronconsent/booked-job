#!/usr/bin/env python3
"""Founder digest — DMs Aaron a personal status update via the Booked Job bot
(@bookedjobrobot), so he knows what the autonomous machine is doing while away.

Sends to his PRIVATE chat (content/ops.json -> founder_chat_id), NOT the public
@bookedjob channel. Runs hourly inside run_all but self-gates: a rollup every
~2h during the day, PLUS an immediate ping when a major event lands (podcast
upload, blog publish, agent failure). Reuses the existing TELEGRAM_BOT_TOKEN.

  python3 scripts/founder_digest.py --test    # send a one-off digest now (bypass gates)
  python3 scripts/founder_digest.py --status   # print what it would send, don't send
"""
import argparse, datetime as dt, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
CHANGELOG = os.path.join(ROOT, "site", "dashboard", "changelog.json")
HEALTH = os.path.join(ROOT, "content", "agent_health.json")
OPS = os.path.join(ROOT, "content", "ops.json")
STATE = os.path.join(ROOT, "content", "founder_digest_state.json")
LOG = os.path.join(ROOT, "content", "founder_digest.log")
WINDOW = (7, 22)          # only send rollups between 7am–10pm (host tz = America/Chicago)
GAP_HOURS = 2             # rollup cadence
# a changelog entry whose text matches any of these forces an immediate send:
MAJOR = re.compile(r"podcast episode|blog drip|published \d+ staged|went live|deploy failed|FAIL", re.I)


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def log(m):
    line = f"{dt.datetime.now():%Y-%m-%dT%H:%M:%S}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def token():
    p = os.path.join(ROOT, "secrets", "telegram.env")
    if os.path.exists(p):
        for ln in open(p):
            if ln.startswith("TELEGRAM_BOT_TOKEN="):
                return ln.strip().split("=", 1)[1]
    return None


def founder_chat():
    return str(load(OPS, {}).get("founder_chat_id") or "") or None


def send(text, chat_id, tok):
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text,
                                   "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=30) as r:
        return json.loads(r.read().decode())


CHANNEL = re.compile(r"(?:to|on)\s+([A-Z][A-Za-z ]+?)(?::|$|\s-)|"
                     r"\b(Bluesky|Mastodon|Threads|Telegram|Tumblr|Telegraph|Blogger|GitHub|Pinterest|"
                     r"LinkedIn|TikTok|Facebook|Instagram|IG|FB|YouTube)\b")


def channel_of(text):
    m = CHANNEL.search(text)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip()


def compose(now):
    st = load(STATE, {})
    # first-ever run: only look back GAP_HOURS so the first digest isn't a giant backlog
    last_ts = st.get("last_ts") or (now - dt.timedelta(hours=GAP_HOURS)).strftime("%Y-%m-%dT%H:%M")
    entries = load(CHANGELOG, {"entries": []})["entries"]
    fresh = [e for e in entries if e.get("ts", "") > last_ts]
    today = now.date().isoformat()
    today_all = [e for e in entries if e.get("ts", "").startswith(today)]

    # count posts by channel among fresh entries
    by_ch = {}
    majors = []
    for e in fresh:
        t = e.get("text", "")
        if MAJOR.search(t):
            majors.append(f"{e.get('icon','•')} {t[:110]}")
        ch = channel_of(t)
        if ch:
            by_ch[ch] = by_ch.get(ch, 0) + 1

    health = load(HEALTH, {})
    failing = [f"{a} ({n}×)" for a, n in health.items() if isinstance(n, int) and n >= 3]

    majors = list(dict.fromkeys(majors))   # dedupe repeated event lines
    hh = now.strftime("%-I:%M %p")
    lines = [f"🤖 <b>Booked Job — {hh}</b>"]
    if majors:
        lines.append("")
        lines += majors[:6]
    lines.append("")
    if fresh:
        top = sorted(by_ch.items(), key=lambda x: -x[1])
        brk = " · ".join(f"{c} {n}" for c, n in top[:8]) if top else "misc"
        lines.append(f"📤 <b>{len(fresh)} posts</b> since last update — {brk}")
    else:
        lines.append("😴 Quiet couple hours — nothing new posted.")
    lines.append(f"📊 {len(today_all)} posts so far today")
    if failing:
        lines.append(f"⚠️ Needs a look: {', '.join(failing[:5])}")
    else:
        lines.append("✅ All agents healthy")
    return "\n".join(lines), bool(majors), (fresh[0]["ts"] if fresh else last_ts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="send now, bypass gates")
    ap.add_argument("--status", action="store_true", help="print, don't send")
    a = ap.parse_args()

    tok = token(); chat = founder_chat()
    now = dt.datetime.now()
    text, has_major, newest_ts = compose(now)

    if a.status:
        print(text); print(f"\n[major={has_major} chat={'set' if chat else 'MISSING'} tok={'set' if tok else 'MISSING'}]"); return
    if not tok or not chat:
        log("skip: TELEGRAM_BOT_TOKEN or content/ops.json founder_chat_id not set."); return

    st = load(STATE, {})
    if not a.test:
        last = st.get("last_iso")
        in_window = WINDOW[0] <= now.hour < WINDOW[1]
        gap_ok = (not last) or (now - dt.datetime.fromisoformat(last)).total_seconds() / 3600 >= GAP_HOURS
        # send if a major event just landed (any hour), else a rollup on cadence within the window
        if not (has_major or (in_window and gap_ok)):
            log(f"skip: no major event and not due (in_window={in_window}, gap_ok={gap_ok})"); return

    try:
        send(text, chat, tok)
        log(f"sent digest to founder ({'major' if has_major else 'rollup'}).")
    except Exception as e:
        log(f"send failed: {str(e)[:160]}"); return
    st.update({"last_iso": now.isoformat(timespec="seconds"), "last_ts": newest_ts})
    json.dump(st, open(STATE, "w"), indent=2)


if __name__ == "__main__":
    main()
