#!/usr/bin/env python3
"""One-time SEO fix (2026-07-21): Bing flagged duplicate <title> + <meta
description> tags. Root cause = the ~16 "Lead Sources" trade-marketing guides
(blog_batch_3/4) all rendered the SAME templated meta ("...marketing that books
jobs: own your Google presence... Sourced.") and near-identical titles.

This rewrites <title>, <meta name=description>, og:title, og:description to
UNIQUE, trade-specific copy per page — each leading with a distinct angle/stat so
Bing sees no duplicates and CTR improves. A few high-intent pages also get a
Reddit-search-intent title (people search "best leads for <trade> reddit"), framed
honestly (we answer the question pros bring from Reddit with real numbers — we do
NOT impersonate Reddit content).

Idempotent: only rewrites tags that still match the OLD templated value.
  python3 scripts/fix_meta_uniqueness.py            # dry run (report)
  python3 scripts/fix_meta_uniqueness.py --apply    # write changes
"""
import html, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BLOG = os.path.join(ROOT, "site", "blog")

# slug -> (unique title, unique meta description). ~155-char descriptions, each a
# distinct angle so none collide.
FIX = {
 # ---- trade-marketing guides (were all identical meta) ----
 "plumber-marketing": ("Plumber Marketing in 2026: More Jobs Without Buying Leads",
   "Plumber marketing that actually books jobs: win the map pack (median ~337 reviews), answer calls in 5 minutes, and skip $542/job shared leads for Google LSA."),
 "electrician-marketing": ("Electrician Marketing: The Playbook Pros Actually Use (2026)",
   "Electricians get the cheapest leads in the trades — ~$39 on Google LSA at 8.52x ROAS. The full playbook: profile, reviews, speed to lead, then paid. No shared-lead traps."),
 "painter-marketing": ("Painting Business Marketing: Fill Your Calendar in 2026",
   "Painting marketing in order of return: own your Google profile, stack reviews, answer fast, and buy Google LSA (~$168/booked job) instead of $542/job Angi leads."),
 "landscaping-marketing-guide": ("Landscaping Marketing: Book a Full Season in 2026",
   "Landscaper marketing built for recurring revenue: win the map pack, lock in maintenance contracts, answer leads in minutes, and stop renting shared leads at $542 a booked job."),
 "garage-door-marketing": ("Garage Door Marketing: Win the Same-Day 'Door Stuck' Search",
   "Garage-door work is a same-day emergency search — the fastest responder wins. Own Google LSA (~$168/job), the map pack, and reviews before you spend a dollar on ads."),
 "fencing-marketing": ("Fence Contractor Marketing: More Quotes, Fewer Tire-Kickers",
   "Fence buyers compare 3-4 quotes and read every review first. How fencing pros win: reviews that clear 4 stars, fast quotes, and Google LSA over $542/job shared leads."),
 "concrete-contractor-marketing": ("Concrete Marketing: Let Your Before/Afters Sell the Job",
   "Concrete is high-ticket and photo-driven. Turn driveway and patio before/afters into booked jobs — plus the map pack, reviews, and LSA math ($168 vs $542 per booked job)."),
 "tree-service-marketing": ("Tree Service Marketing: Own the Storm-Damage Rush",
   "Removal and storm calls are urgent — 78% of homeowners hire the first tree service that answers. How to be first: Google LSA, reviews, and a phone you actually pick up."),
 "pool-service-marketing": ("Pool Service Marketing: One Client, Years of Revenue",
   "Pool service is recurring revenue — one booked client is worth seasons. Win the map pack, keep clients longer, and book LSA leads near $168 while Angi charges triple."),
 "appliance-repair-marketing": ("Appliance Repair Marketing: Answer Fast, Book the Emergency",
   "A dead fridge is an emergency — appliance repair lives on speed to lead. The average shop misses 14% of calls. Catch them and book at ~$168/job, not $542 on shared apps."),
 "gutter-marketing": ("Gutter Marketing: Book More Installs Without Renting Leads",
   "Gutters are seasonal and referral-driven. Make reviews do the selling, rank in the map pack, and buy Google LSA (~$168/job) over $542/job shared leads."),
 "flooring-marketing": ("Flooring Marketing: Make Your Website the Showroom",
   "Flooring buyers compare finishes online first — and 98% leave a site without calling. Fix the site, win reviews, and cut cost per booked job from $542 to ~$168 with LSA."),
 "handyman-marketing": ("Handyman Marketing: How to Stay Booked All Year",
   "Handyman work is repeat-and-referral — the first great job books the next five. Win reviews (91% skip shops under 4 stars), rank locally, and skip $542/job lead apps."),
 "pressure-washing-marketing": ("Pressure Washing Marketing: Let the Before/After Do the Ads",
   "Pressure washing is the ultimate before/after trade — the footage is the ad. Turn results into booked jobs, win the map pack, and buy LSA over $542/job shared leads."),
 "junk-removal-marketing": ("Junk Removal Marketing: Win the Same-Day Haul Search",
   "Junk removal is a same-day, phone-first buy — 78% hire the first responder. Be first with Google LSA (~$168/job), reviews, and instant callback, not shared leads."),
 "window-cleaning-marketing": ("Window Cleaning Marketing: Build a Route of Recurring Clients",
   "Window cleaning is route-based recurring revenue — one client, many visits. Win the map pack, stack reviews, and pull LSA leads near $168 a job, a third of Angi's price."),
 "get-more-google-reviews": ("How to Get More Google Reviews: A System That Books Jobs",
   "The one-tap system that gets contractors more Google reviews: when to ask, the exact text to send, and how to turn a finished job into a 5-star review the same day."),
 # ---- title-only collisions (marketing-statistics pair) ----
 "contractor-marketing-statistics": ("Contractor Marketing Statistics 2026: The Numbers That Decide Who Books",
   "The key contractor-marketing numbers in one place: cost per booked job by channel, review thresholds to rank, speed-to-lead impact, and where AI search is shifting demand."),
 "hvac-marketing-statistics": ("HVAC Marketing Statistics 2026: Lead Costs, the 519-Review Bar & Speed to Lead",
   "The HVAC marketing numbers that matter: cost per booked job by channel, the ~519 median reviews it takes to rank, speed-to-lead impact, and what actually moves the phone."),
 # ---- Reddit-search-intent titles (people search "best leads for <trade> reddit") ----
 "best-leads-for-plumbers": ("Best Leads for Plumbers in 2026: The Reddit Question, Answered With Real Numbers",
   "Plumbers ask this constantly on Reddit — here's the data answer. Google LSA: ~$57/lead, 44.5% book, $1,714 ticket, 6.85x ROAS (SearchLight 2026). Why LSA beats shared leads."),
 "best-leads-for-electricians": ("Best Leads for Electricians in 2026: The Reddit Answer, Backed by Data",
   "The question every electrician asks on Reddit, answered with numbers: Google LSA runs ~$39/lead at 8.52x ROAS (SearchLight 2026) — cheapest in the trades. Why LSA wins."),
 "best-leads-for-hvac-contractors": ("Best Leads for HVAC Contractors in 2026: The Reddit Debate, Settled by Numbers",
   "HVAC pros argue this on Reddit — here's the math. Google LSA: $51/lead at 9.55x ROAS (SearchLight 2026) vs shared leads that get resold to 5 shops. Why LSA books more jobs."),
 "should-you-pay-for-leads": ("Should Contractors Pay for Leads? The Reddit Question, Answered Honestly",
   "The lead-buying debate contractors have on Reddit, settled with real math: why a $35 shared lead can cost $700 per booked job, and when LSA beats Angi and Thumbtack."),
}

TAGS = [
 (r"(<title>)(.*?)(</title>)", 0),
 (r'(<meta name="description" content=")(.*?)(")', 1),
 (r'(<meta property="og:title" content=")(.*?)(")', 0),
 (r'(<meta property="og:description" content=")(.*?)(")', 1),
]


def esc_title(s):
    return html.escape(s, quote=False)


def esc_attr(s):
    return html.escape(s, quote=True)


def apply_fix(write):
    changed = miss = 0
    for slug, (title, desc) in FIX.items():
        p = os.path.join(BLOG, slug, "index.html")
        if not os.path.exists(p):
            print(f"  ⚠️  {slug}: file missing"); miss += 1; continue
        h = open(p, encoding="utf-8").read(); before = h
        for pat, which in TAGS:
            val = esc_title(title) if pat.startswith("(<title>") else esc_attr(title if which == 0 else desc)
            h = re.sub(pat, lambda m, v=val: m.group(1) + v + m.group(3), h, count=1, flags=re.S)
        if h != before:
            changed += 1
            if write:
                open(p, "w", encoding="utf-8").write(h)
            print(f"  {'✏️ ' if write else '•'} {slug}")
    print(f"\n{'APPLIED' if write else 'DRY-RUN'}: {changed} pages rewritten, {miss} missing")
    return changed


if __name__ == "__main__":
    apply_fix("--apply" in sys.argv)
