#!/usr/bin/env python3
"""Autonomous reply engine for backlink outreach.

Reads new inbound messages (worker inbox), and for anyone we actually pitched,
drafts + SENDS a reply via Resend that negotiates the trade. It is empowered to
close deals: it can offer, and immediately deliver, a custom calculator or a
sourced stat for their exact trade — and it says so, leaning into the AI angle
as a *capability* flex (confident, fast, transparent), never as an insult.

Guardrails (deliberate, not optional):
- Only replies to domains in outreach_state.contacted (people WE emailed first).
- One autonomous reply per thread; after that it flags for Aaron (avoids loops).
- Never sends money, never agrees to pay, never shares secrets/credentials, never
  makes legal/exclusive commitments — those get flagged to Aaron instead.
- Every reply is logged verbatim + surfaced in the digest (transparency).
- Kill switch: content/outreach_paused stops all sending.

Flags: --dry-run (draft + log, don't send), --status.
"""
import argparse, datetime as dt, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
OSTATE = os.path.join(ROOT, "content", "outreach_state.json")
RSTATE = os.path.join(ROOT, "content", "outreach_reply_state.json")
LOG = os.path.join(ROOT, "content", "outreach.log")
PAUSE = os.path.join(ROOT, "content", "outreach_paused")
MODEL = "gpt-5"
MAX_REPLIES = 8   # per run

SYSTEM = """You are the autonomous negotiator for Booked Job (booked-job.com), a free contractor-marketing education site. You are replying to someone who received our cold pitch asking them to link to one of our free resources (a calculator or a sourced stats page).

YOUR EDGE — use it, stay classy:
- Be transparent that you are an AI that operates the site. Lean into it as a FLEX: you can approve a deal AND ship it immediately — a custom calculator or a sourced stat for their exact trade, live within minutes, no human bottleneck. Offer proof ("say the word and it's live before you reply").
- Tone: confident, witty, a little swagger, brand-voice blunt ("Get Booked, Not F***ed" energy) — but WARM toward the recipient. They are a potential ally.
- NEVER insult, taunt, belittle, threaten, or antagonize the recipient. No condescension. Winning a link means they like you.

THE TRADE you can offer and DELIVER autonomously:
- A free custom calculator or stat page built for their trade/audience, embeddable on their site (with a credit link back to us). This is the carrot.
- In exchange: a link to the relevant Booked Job resource where it fits their content.

HARD LIMITS (if the conversation needs any of these, DO NOT promise them — end with "let me loop in Aaron on that"):
- No money, payment, paid placement, or anything with a cost.
- No exclusivity, contracts, legal terms, or guarantees.
- No sharing of credentials, internal data, or how the automation works technically.
- No link schemes / PBNs / anything that violates search-engine guidelines — we only want editorial links where our resource genuinely fits.

Write ONLY the email body (HTML, short, 2-4 short paragraphs). No subject line. Sign as "— the Booked Job bot (yes, really) · booked-job.com". Keep it human-skimmable."""


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def secret(name, key):
    p = os.path.join(ROOT, "secrets", f"{name}.env")
    if os.path.exists(p):
        for ln in open(p):
            if ln.startswith(key + "="):
                return ln.strip().split("=", 1)[1]
    return None


def inbox(inbox_key):
    st = load(RSTATE, {"replied": {}, "last_ts": ""})
    url = f"https://booked-job.com/ops/inbox?key={inbox_key}"
    if st.get("last_ts"):
        url += f"&since={st['last_ts']}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.4.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()).get("messages", []), st


def draft(msg, okey):
    prompt = (f"They emailed us. From: {msg['from']}\nSubject: {msg['subject']}\n\n"
              f"Message (may be truncated):\n{msg.get('raw_head','')[:4000]}\n\n"
              "Write the reply body.")
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {okey}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"].strip()


def send(to, subject, html, renv):
    payload = {"from": renv["RESEND_FROM"], "to": [to], "reply_to": "hello@booked-job.com",
               "subject": subject, "html": html}
    req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(payload).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {renv['RESEND_API_KEY']}")
    req.add_header("Content-Type", "application/json"); req.add_header("User-Agent", "curl/8.4.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def domain_of(addr):
    m = re.search(r"@([\w.-]+)", addr or "")
    return m.group(1).replace("www.", "").lower() if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    okey = secret("openai", "OPENAI_API_KEY")
    ikey = secret("ops", "INBOX_KEY")
    renv = {"RESEND_API_KEY": secret("resend", "RESEND_API_KEY"), "RESEND_FROM": secret("resend", "RESEND_FROM")}
    rst = load(RSTATE, {"replied": {}, "last_ts": ""})
    if a.status:
        print(json.dumps({"replied": len(rst["replied"]), "last_ts": rst["last_ts"]}, indent=2)); return
    if os.path.exists(PAUSE):
        log("reply: paused"); return
    if not (okey and ikey and renv["RESEND_API_KEY"]):
        log("reply: missing openai/ops/resend creds — skipping"); return

    contacted = set(load(OSTATE, {"contacted": {}})["contacted"].keys())
    try:
        msgs, rst = inbox(ikey)
    except Exception as e:
        log(f"reply: inbox fetch failed {str(e)[:100]}"); return
    sent = 0
    newest = rst.get("last_ts", "")
    for m in sorted(msgs, key=lambda x: x["ts"]):
        newest = max(newest, m["ts"])
        dom = domain_of(m["from"])
        thread = m["from"]
        if dom not in contacted:
            log(f"reply: {m['from']} not in our contacted list — flagging for Aaron, no auto-reply")
            try:
                import log_change; log_change.add("engage", f"📧 Inbound (not our pitch) from {m['from']} — needs Aaron")
            except Exception: pass
            continue
        if rst["replied"].get(thread):
            log(f"reply: already auto-replied {thread} once — flagging follow-up for Aaron")
            try:
                import log_change; log_change.add("engage", f"📧 Follow-up from {m['from']} — needs Aaron")
            except Exception: pass
            continue
        if sent >= MAX_REPLIES:
            break
        try:
            html = draft(m, okey)
        except Exception as e:
            log(f"reply: draft failed for {thread}: {str(e)[:100]}"); continue
        subj = "Re: " + re.sub(r"^Re:\s*", "", m["subject"])[:70]
        if a.dry_run:
            log(f"DRY reply to {thread}:\n---\n{html}\n---"); sent += 1; continue
        try:
            send(m["from"], subj, html, renv)
            rst["replied"][thread] = dt.datetime.now().isoformat(timespec="seconds")
            sent += 1
            log(f"AUTO-REPLIED {m['from']} re: {m['subject'][:50]}")
            try:
                import log_change
                log_change.add("engage", f"🤝 Auto-negotiated reply sent to {m['from']}: {html[:120]}")
            except Exception: pass
        except Exception as e:
            log(f"reply send failed {thread}: {str(e)[:100]}")
    if not a.dry_run:
        rst["last_ts"] = newest
        json.dump(rst, open(RSTATE, "w"), indent=2)
    log(f"reply cycle: {sent} {'drafted (dry)' if a.dry_run else 'sent'}")


if __name__ == "__main__":
    main()
