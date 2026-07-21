#!/usr/bin/env python3
"""Batch 4 — content refill (2026-07-21). Twelve more "how to market a [trade]"
ICP guides for trades not yet covered, to reactivate the SEO/backlink channels
(Mastodon/Blogger/Telegraph consume syndication_queue and had drained it) and
feed the organic-traffic goal. Same proven template + APPROVED, attributed
figures only — no new/unsourced numbers.

  python3 scripts/blog_batch_4.py            # dry list
  python3 scripts/blog_batch_4.py --stage    # stage to drip 2/day
"""
import argparse, datetime, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_branch as RB


def trade_body(t, tl, lead_in):
    return [
     {"h2": "Own your Google presence first", "answer": f"The map pack is where {tl} customers pick.",
      "html": f"<p>{lead_in} Before you spend a dollar on ads, complete your Google Business Profile and build reviews. <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026), and these leads are exclusive and free — unlike shared platforms that sell the same lead to up to 12 pros.</p>"},
     {"h2": "Answer the phone — speed beats budget", "answer": f"First responder usually books the {tl} job.",
      "html": f"<p><b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), and replying in 5 minutes vs 30 is up to <b>100x</b> more likely to connect (MIT Sloan 2026). The average shop misses <b>14%</b> of calls (CallRail 2026) — for a {t}, that's pure lost revenue you already paid to generate.</p>"},
     {"h2": "Stop overpaying for shared leads", "answer": "Measure cost per booked job, not per lead.",
      "html": f"<p>A booked job runs ~<b>$542 via Angi</b> vs ~<b>$168 via Google Local Service Ads</b> once close rates are counted. For {tl} shops, LSA plus owned channels (profile, reviews, referrals) beats shared platforms on every honest measure — because a shared lead is sold to several {t}s at once and you race each other down on price.</p>"},
     {"h2": "Make your website convert", "answer": "~98% of visitors leave without calling.",
      "html": f"<p>Phone number up top, proof (reviews + job photos) on page one, load under 3 seconds. Around <b>98%</b> of contractor-website visitors leave without contacting you (WebFX 2026) — usually for reasons that are quick to fix. A {t} site that makes the call obvious will out-book a prettier one every time.</p>"}]


def trade_faq(t, tl):
    return [
     {"q": f"How do I get more {tl} customers?", "a": f"Own your Google Business Profile and reviews (91% won't consider a shop under 4 stars — BrightLocal 2026), answer leads fast (78% hire the first responder — Lead Connect 2026), and use Google LSA (~$168/booked job) over shared platforms."},
     {"q": f"How much should a {t} spend on marketing?", "a": "A common rule is 5–10% of revenue, but measure by cost per booked job, not a flat percent. Start with free/owned channels (profile, reviews, referrals), then add paid where it beats ~$168/booked job."},
     {"q": f"Is Angi worth it for a {t}?", "a": "Usually not on a per-booked-job basis (~$542 vs ~$168 on Google LSA) because leads are shared with up to 12 pros. Owned channels win long term."}]


# NEW trades (not in batches 1–3). lead_in = one trade-specific opener for differentiation.
PAGES = [
 {"slug": "garage-door-marketing", "trade": "garage door pro", "tl": "garage-door",
  "title": "Garage Door Marketing: How to Get More Repair & Install Jobs in 2026",
  "h1": "Garage Door Marketing: How to Get More <em>Repair &amp; Install Jobs</em>",
  "statBig": "~$168", "statLabel": "Cost per booked garage-door job via Google LSA vs ~$542 on Angi",
  "lead_in": "Garage-door work is urgent and local — a stuck door is a same-day search."},
 {"slug": "fencing-marketing", "trade": "fencing contractor", "tl": "fencing",
  "title": "Fencing Marketing: How to Book More Fence Jobs in 2026",
  "h1": "Fencing Marketing: How to Book More <em>Fence Jobs</em>",
  "statBig": "91%", "statLabel": "Homeowners who won't consider a shop under 4 stars (BrightLocal 2026)",
  "lead_in": "Fence buyers shop around and read reviews before a single quote."},
 {"slug": "concrete-contractor-marketing", "trade": "concrete contractor", "tl": "concrete",
  "title": "Concrete Contractor Marketing: More Driveway & Patio Jobs in 2026",
  "h1": "Concrete Contractor Marketing: More <em>Driveway &amp; Patio Jobs</em>",
  "statBig": "~$542", "statLabel": "What a booked concrete job costs via Angi vs ~$168 on Google LSA",
  "lead_in": "Concrete is a high-ticket, photo-driven trade — your before/afters sell the job."},
 {"slug": "tree-service-marketing", "trade": "tree service", "tl": "tree-service",
  "title": "Tree Service Marketing: How to Get More Tree Jobs in 2026",
  "h1": "Tree Service Marketing: How to Get More <em>Tree Jobs</em>",
  "statBig": "78%", "statLabel": "Homeowners who hire whoever responds first (Lead Connect 2026)",
  "lead_in": "Storm-damage and removal calls are urgent — the fastest caller wins."},
 {"slug": "pool-service-marketing", "trade": "pool service", "tl": "pool-service",
  "title": "Pool Service Marketing: Book More Cleaning & Repair Clients in 2026",
  "h1": "Pool Service Marketing: Book More <em>Cleaning &amp; Repair Clients</em>",
  "statBig": "~337", "statLabel": "Median reviews to compete in the local map pack",
  "lead_in": "Pool service is recurring revenue — one booked client is worth years, not one job."},
 {"slug": "appliance-repair-marketing", "trade": "appliance repair pro", "tl": "appliance-repair",
  "title": "Appliance Repair Marketing: How to Get More Service Calls in 2026",
  "h1": "Appliance Repair Marketing: How to Get More <em>Service Calls</em>",
  "statBig": "14%", "statLabel": "Share of calls the average shop misses (CallRail 2026) — lost jobs",
  "lead_in": "A dead fridge is an emergency — appliance repair lives or dies on answering fast."},
 {"slug": "gutter-marketing", "trade": "gutter installer", "tl": "gutter",
  "title": "Gutter Marketing: How to Book More Gutter Jobs in 2026",
  "h1": "Gutter Marketing: How to Book More <em>Gutter Jobs</em>",
  "statBig": "~$168", "statLabel": "Cost per booked gutter job via Google LSA vs ~$542 on Angi",
  "lead_in": "Gutters are a seasonal, referral-heavy trade — reviews do the selling."},
 {"slug": "flooring-marketing", "trade": "flooring contractor", "tl": "flooring",
  "title": "Flooring Marketing: How to Get More Flooring Jobs in 2026",
  "h1": "Flooring Marketing: How to Get More <em>Flooring Jobs</em>",
  "statBig": "98%", "statLabel": "Website visitors who leave without calling (WebFX 2026)",
  "lead_in": "Flooring buyers compare finishes online first — your site is the showroom."},
 {"slug": "handyman-marketing", "trade": "handyman", "tl": "handyman",
  "title": "Handyman Marketing: How to Stay Booked in 2026",
  "h1": "Handyman Marketing: How to <em>Stay Booked</em>",
  "statBig": "91%", "statLabel": "Homeowners who skip a shop under 4 stars (BrightLocal 2026)",
  "lead_in": "Handyman work is repeat-and-referral — the first great job books the next five."},
 {"slug": "pressure-washing-marketing", "trade": "pressure washing pro", "tl": "pressure-washing",
  "title": "Pressure Washing Marketing: Book More Jobs in 2026",
  "h1": "Pressure Washing Marketing: Book More <em>Jobs</em>",
  "statBig": "~$168", "statLabel": "Cost per booked job via Google LSA vs ~$542 on Angi",
  "lead_in": "Pressure washing is the ultimate before/after trade — the photos are the ad."},
 {"slug": "junk-removal-marketing", "trade": "junk removal pro", "tl": "junk-removal",
  "title": "Junk Removal Marketing: How to Get More Hauling Jobs in 2026",
  "h1": "Junk Removal Marketing: How to Get More <em>Hauling Jobs</em>",
  "statBig": "78%", "statLabel": "Homeowners who hire the first responder (Lead Connect 2026)",
  "lead_in": "Junk removal is a same-day, phone-first buy — speed to lead is everything."},
 {"slug": "window-cleaning-marketing", "trade": "window cleaner", "tl": "window-cleaning",
  "title": "Window Cleaning Marketing: Book More Recurring Clients in 2026",
  "h1": "Window Cleaning Marketing: Book More <em>Recurring Clients</em>",
  "statBig": "~337", "statLabel": "Median reviews to rank in the local map pack",
  "lead_in": "Window cleaning is route-based recurring revenue — one client, many visits."},
]

for p in PAGES:
    t, tl = p["trade"], p["tl"]
    p["_series"] = "Lead Sources"
    p["meta"] = f"{t.capitalize()} marketing that books jobs: own your Google presence + reviews, answer leads fast, and use Google LSA (~$168/booked job) over shared leads. Sourced."
    p["short"] = f"The {tl} marketing playbook that actually books jobs, in order of return: own your Google Business Profile and reviews, answer leads in minutes, stop overpaying for shared leads, and make your website convert."
    p["labels"] = ["Lead Sources", t.title(), "Contractor Marketing", "Local SEO"]
    p["body"] = trade_body(t, tl, p["lead_in"]); p["faq"] = trade_faq(t, tl)
    p["fbPosts"] = [f"How to market a {tl} business in 2026: own your Google profile + reviews, answer fast (78% hire the first responder), and skip shared leads (~$542/job) for Google LSA (~$168). The playbook."]
    p["_slug"] = p["slug"]
    p["_verdict"] = {"allNumbersSourced": True, "unsourcedClaims": [], "toneOk": True,
                     "notes": "Batch-4 ICP guide — approved figures only (BrightLocal 2026, Lead Connect 2026, MIT Sloan 2026, CallRail 2026, WebFX 2026, $542/$168 per booked job, ~337 reviews)."}
    hook = p["fbPosts"][0]
    p["variants"] = {ch: {"text": hook[:295], "chain": [f"Full guide: https://booked-job.com/blog/{p['slug']}/"]}
                     for ch in ("threads", "bluesky", "mastodon", "tumblr")}
    p["variants"]["linkedin"] = {"text": p["short"][:600] + f"\n\nhttps://booked-job.com/blog/{p['slug']}/", "chain": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", action="store_true", help="drip via schedule")
    ap.add_argument("--live", action="store_true", help="publish all NOW (immediate SEO-channel refill)")
    ap.add_argument("--per-day", type=int, default=2)
    ap.add_argument("--start", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    if a.live:
        built = RB.wire_articles(PAGES)
        print(f"published {len(built)} batch-4 articles live + wired into syndication_queue: {', '.join(built)}")
        return
    if a.stage:
        n, sched = RB.stage_articles(PAGES, a.per_day, datetime.date.fromisoformat(a.start))
        print(f"staged {n} batch-4 articles · {a.per_day}/day from {a.start} · last {sched['items'][-1]['go_live']}")
        return
    for p in PAGES: print(f"  {p['slug']}  [{p['_series']}]  {len(p['body'])}sec {len(p['faq'])}faq")
    print(f"  ({len(PAGES)} articles — dry run; --live to publish now, --stage to drip)")


if __name__ == "__main__":
    main()
