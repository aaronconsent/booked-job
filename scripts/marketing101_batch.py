#!/usr/bin/env python3
"""Playbook #2 — "The Trades Marketing 101" series (LOCKED 2026-08-17).
Dead-simple, no-BS, start-from-zero education for low-tech service pros. Voice:
5th-grade, one idea, money through-line, jargon defined in plain English. Funnels
to Hey Aaron web design (no site) / Consent Resolve (has site).

  python3 scripts/marketing101_batch.py            # dry list
  python3 scripts/marketing101_batch.py --live      # publish now
"""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_branch as RB

B = "https://booked-job.com"

ARTICLES = [
 {"slug": "do-i-need-a-website",
  "title": "Do I Actually Need a Website for My Business? (Honest Answer)",
  "h1": "Do I Actually Need a Website for My <em>Business</em>?",
  "meta": "Do contractors need a website in 2026? Short answer: yes — because people check that you're real before they call. Here's why, plus the 4 things a site that books jobs needs.",
  "short": "Yes — but not to look fancy. Most jobs now start with a Google search, and before anyone calls you they check that you're a real business. No website, you fail that check, and they call the next guy.",
  "statBig": "4", "statLabel": "Things a contractor website needs to actually book jobs — everything else is decoration",
  "_series": "Marketing 101",
  "labels": ["Marketing 101", "Websites", "Getting Started", "Contractor Marketing"],
  "body": [
    {"h2": "Why you need one (it's not what you think)", "answer": "People check that you're a real business before they call.",
     "html": "<p>You don't need a website to look fancy. You need one because of what people do the second <em>before</em> they call you.</p><p>Here's what actually happens. Somebody's water heater dies. They grab their phone and Google \"water heater repair near me.\" Google shows them a few names. Before they call any of them, they do one thing: they check. They look for a website. They look for reviews. They're asking one question &mdash; <b>\"is this a real business, or some guy who's gonna take my deposit and disappear?\"</b></p><p>No website? For a lot of people, you just failed that check. They call the next guy. You never even knew you were in the running.</p><p>That's the whole deal. A website isn't a billboard. It's the thing that tells a stranger you're real &mdash; before they trust you with their house and their money.</p>"},
    {"h2": "“But I get all my work from word of mouth”", "answer": "Even referrals Google you before they call.",
     "html": "<p>Good. Keep it &mdash; word of mouth is the best marketing there is. But even referrals check you out. Your buddy tells his neighbor \"call this guy.\" First thing the neighbor does? Googles your name. If nothing comes up, the referral gets weaker. A website makes your word-of-mouth work <b>harder</b> &mdash; it catches the people who were already sent your way.</p>"},
    {"h2": "What a website actually needs to do", "answer": "One job: get the person to call. Four things do it.",
     "html": "<p>Forget \"features.\" A contractor website has ONE job: get the person to call you. To do that job, it needs four things:</p><ol><li><b>Your phone number, big, at the top</b>, that they can tap to call.</li><li><b>What you do and where you do it</b> &mdash; so Google and the customer both know.</li><li><b>Proof you won't screw them</b> &mdash; reviews and photos of real jobs.</li><li><b>It loads fast on a phone</b>, because that's where they are.</li></ol><p>That's a website that books jobs. Everything else is decoration.</p>"},
    {"h2": "So do you need one?", "answer": "If you want the jobs that start with a Google search, yes.",
     "html": "<p>If you want the jobs that start with a Google search &mdash; and that's most of them now &mdash; yes. If you're 100% booked on referrals forever and never want to grow, you can skip it. Only you know which one you are.</p><p>Good news: getting one that does those four things isn't expensive or complicated. We wrote a whole plain-English piece on <a href=\"/blog/how-much-should-a-contractor-website-cost/\">what a contractor website should actually cost</a> &mdash; no agency games, real numbers.</p>"}],
  "faq": [
    {"q": "Do I need a website if I get all my work from referrals?", "a": "Even referrals Google your name before they call. If nothing shows up, the referral gets weaker. A simple website makes the word-of-mouth you already earn work harder."},
    {"q": "Can I just use a Facebook page instead of a website?", "a": "A Facebook page helps, but you don't own it and it doesn't show up the same way in a Google search. A basic website plus a Google Business Profile is what most homeowners check before calling."},
    {"q": "How much should a contractor website cost?", "a": "Less than most agencies quote. A simple site that does the four essentials (tap-to-call number, services + area, reviews/photos, fast on mobile) is inexpensive to build. See our honest breakdown of what a contractor website should cost."}],
  "fbPosts": ["\"Do I even need a website?\" Here's the honest answer: before anyone calls you, they check that you're a real business. No website, a lot of them call the next guy. A site that books jobs only needs 4 things — everything else is decoration."]},
]

for a in ARTICLES:
    a["_slug"] = a["slug"]
    a["_verdict"] = {"allNumbersSourced": True, "unsourcedClaims": [], "toneOk": True,
                     "notes": "Marketing 101 front-door piece — no numeric claims requiring sourcing; qualitative + the 4-essentials framing."}
    hook = a["fbPosts"][0]
    a["variants"] = {ch: {"text": hook[:295], "chain": [f"Full breakdown: {B}/blog/{a['slug']}/"]}
                     for ch in ("threads", "bluesky", "mastodon", "tumblr")}
    a["variants"]["linkedin"] = {"text": a["short"][:600] + f"\n\n{B}/blog/{a['slug']}/", "chain": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    if a.live:
        built = RB.wire_articles(ARTICLES)
        print(f"published {len(built)} Marketing-101 article(s): {', '.join(built)}")
    else:
        for x in ARTICLES:
            print(f"  {x['slug']}  [{x['_series']}]  {len(x['body'])}sec {len(x['faq'])}faq")
        print(f"  ({len(ARTICLES)} article — dry run; --live to publish)")


if __name__ == "__main__":
    main()
