#!/usr/bin/env python3
"""Autonomous backlink outreach — the no-humans version of link building.

Weekly cycle (self-gated inside the hourly run_all):
1. PROSPECT: Apify google-search-scraper finds pages that write about contractor
   marketing costs/tools (rotating query set — resource pages, stat roundups).
2. FILTER: drop platforms/socials, our own + syndication domains, and any domain
   we've ever contacted (state, permanent dedupe).
3. CONTACT: fetch the page (+/contact) and extract a same-domain email.
4. PITCH: short, honest, 1:1 email — offers the matching free asset (stats page
   or a calculator) as a resource for THEIR page. Identification + opt-out in
   the footer. Sent via Resend.

Hard caps: MAX_SENDS per weekly cycle (5), one email per domain EVER, no
follow-ups. Kill switch: create content/outreach_paused to stop sends.
Flags: --dry-run (full cycle, no email), --status.
"""
import argparse, datetime as dt, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
STATE = os.path.join(ROOT, "content", "outreach_state.json")
LOG = os.path.join(ROOT, "content", "outreach.log")
PAUSE = os.path.join(ROOT, "content", "outreach_paused")
MAX_SENDS = 5
GAP_DAYS = 7
ACTOR = "apify~google-search-scraper"

# rotating prospect queries — each targets pages that cite the numbers we own
QUERIES = [
    'contractor marketing "cost per lead" guide',
    '"resources for contractors" marketing tools',
    'hvac marketing statistics blog',
    'plumbing marketing guide "google reviews"',
    'best free calculators for contractors small business',
    '"angi" review contractors blog worth it',
    'roofing marketing "lead generation" cost guide',
    'home services marketing benchmarks report',
]
SKIP_DOMAINS = re.compile(
    r"(facebook|youtube|reddit|quora|pinterest|amazon|linkedin|tiktok|instagram|twitter|x\.com|wikipedia|"
    r"booked-job|blogspot|tumblr|telegra\.ph|github|angi|homeadvisor|thumbtack|yelp|google|bing|apple|"
    r"spotify|medium\.com|indeed|glassdoor)", re.I)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
BAD_EMAIL = re.compile(r"(noreply|no-reply|example\.|sentry|wixpress|\.png|\.jpg|\.gif|@[0-9]|abuse@|privacy@)", re.I)

# asset matched to what their page is about
ASSETS = [
    (re.compile(r"review", re.I), "our free Google Review Calculator (how many reviews to hit a rating / catch a competitor)",
     "https://booked-job.com/tools/google-review-calculator/"),
    (re.compile(r"cost|lead|price|pricing|angi|statistic|benchmark", re.I),
     "our free Cost Per Booked Job Calculator and a sourced 2026 stats roundup (Angi ~$542 vs Google LSA ~$168 per booked job)",
     "https://booked-job.com/tools/cost-per-booked-job-calculator/"),
    (re.compile(r"."), "our sourced 2026 contractor-marketing stats page",
     "https://booked-job.com/blog/contractor-marketing-statistics/"),
]


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def env(name):
    p = os.path.join(ROOT, "secrets", f"{name}.env")
    e = {}
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); e[k] = v
    return e


def search(query, tok, n=10):
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={tok}"
    body = json.dumps({"queries": query, "resultsPerPage": n, "maxPagesPerQuery": 1,
                       "countryCode": "us", "saveHtml": False}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        items = json.loads(r.read().decode())
    out = []
    for it in items:
        for res in it.get("organicResults", []):
            if res.get("url"):
                out.append({"url": res["url"], "title": res.get("title", "")})
    return out


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; BookedJobBot/1.0)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read(400_000).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def find_email(page_url):
    """Same-domain email from the page, then /contact, then homepage."""
    host = urllib.parse.urlparse(page_url).netloc.replace("www.", "")
    base = f"https://{urllib.parse.urlparse(page_url).netloc}"
    for u in (page_url, base + "/contact", base + "/contact-us", base):
        html = fetch(u)
        for m in EMAIL_RE.findall(html):
            if BAD_EMAIL.search(m):
                continue
            if m.lower().split("@")[1].endswith(host.split(":")[0]):
                return m
    return None


def compose(title, page_url, host):
    for rx, desc, link in ASSETS:
        if rx.search(title or ""):
            asset_desc, asset_link = desc, link; break
    subject = "A free resource for your page on " + (title[:60].rstrip() or host)
    body = f"""<p>Hi — I run Booked Job, a free (no product, no paywall) education site on the real math of contractor marketing.</p>
<p>I found your page "{title[:90]}" ({page_url}) and thought {asset_desc} might be genuinely useful to your readers:</p>
<p><a href="{asset_link}">{asset_link}</a></p>
<p>Every number is sourced inline. If it fits the page, a link would make my week — and if you'd like a custom version (your trade, your numbers), I'll build it, free.</p>
<p>Either way, thanks for writing for the trades.</p>
<p>— Aaron Phillips, Booked Job<br>
<a href="https://booked-job.com">booked-job.com</a> · hello@booked-job.com</p>
<p style="color:#888;font-size:12px">One-time note from Booked Job (booked-job.com). Reply "no thanks" and we won't email again.</p>"""
    return subject, body


def send(to, subject, html, resend_env):
    req = urllib.request.Request("https://api.resend.com/emails",
                                 data=json.dumps({"from": resend_env["RESEND_FROM"], "to": [to],
                                                  "reply_to": "hello@booked-job.com",   # CF Email Routing -> Aaron's inbox
                                                  "subject": subject, "html": html}).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {resend_env['RESEND_API_KEY']}")
    req.add_header("Content-Type", "application/json"); req.add_header("User-Agent", "curl/8.4.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    st = load(STATE, {"contacted": {}, "last_iso": None, "qi": 0})
    if a.status:
        print(json.dumps({"contacted": len(st["contacted"]), "last": st["last_iso"], "next_query": QUERIES[st["qi"] % len(QUERIES)]}, indent=2)); return
    if os.path.exists(PAUSE):
        log("outreach paused (content/outreach_paused exists)"); return
    if not a.force and st.get("last_iso"):
        days = (dt.datetime.now() - dt.datetime.fromisoformat(st["last_iso"])).days
        if days < GAP_DAYS:
            log(f"skip: weekly gate ({days}d since last cycle)"); return
    apify = env("apify").get("APIFY_TOKEN") or env("apify").get("APIFY_API_TOKEN")
    resend = env("resend")
    if not apify or not resend.get("RESEND_API_KEY"):
        log("missing apify or resend credentials — skipping"); return

    q = QUERIES[st["qi"] % len(QUERIES)]
    log(f"prospecting: {q!r}")
    try:
        results = search(q, apify)
    except Exception as e:
        log(f"search failed: {str(e)[:140]}"); return
    sent = 0
    for r in results:
        if sent >= MAX_SENDS:
            break
        host = urllib.parse.urlparse(r["url"]).netloc.replace("www.", "")
        if SKIP_DOMAINS.search(r["url"]) or host in st["contacted"]:
            continue
        email = find_email(r["url"])
        if not email:
            st["contacted"][host] = "no-contact"; continue
        subject, body = compose(r["title"], r["url"], host)
        if a.dry_run:
            log(f"DRY would email {email} ({host}) — {subject[:70]}"); sent += 1; continue
        try:
            send(email, subject, body, resend)
            st["contacted"][host] = dt.date.today().isoformat()
            sent += 1
            log(f"SENT pitch to {email} ({host}) re: {r['title'][:60]}")
        except Exception as e:
            log(f"send failed {email}: {str(e)[:100]}")
    if not a.dry_run:
        st["last_iso"] = dt.datetime.now().isoformat(timespec="seconds"); st["qi"] = st.get("qi", 0) + 1
        json.dump(st, open(STATE, "w"), indent=2)
    log(f"cycle done — {sent} pitch(es) {'(dry)' if a.dry_run else 'sent'}, {len(st['contacted'])} domains tracked")


if __name__ == "__main__":
    main()
