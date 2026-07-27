#!/usr/bin/env python3
"""Batch 6 — the Thumbtack money-cluster gap (2026-07-27, weekly strategist).

We own "is Angi worth it", "Thumbtack vs Angi" and "is Thumbtack worth it". The hole
flagged three weeks running and never written: what actually happens when you FIGHT a
bad Thumbtack charge — the refund categories, the 45-day window, and the bank-chargeback
trap that gets pro accounts held or closed. High-intent, contractor-as-reader, funnels
straight into the own-your-pipeline argument.

Sources verified 2026-07-27: BBB complaint profile (931 / 3yr, 251 / 12mo, not accredited,
verbatim pro complaint), Thumbtack Help "Troubleshooting pro account issues" + refund policy,
plus our already-approved per-booked-job benchmarks ($542 Angi/HomeAdvisor, ~$250 Thumbtack,
~$168 LSA, 78% first-responder / Lead Connect 2026).

Information gain (non-clonable): OUR math on what the refund queue is worth per booked job.

  python3 scripts/blog_batch_6.py            # dry list
  python3 scripts/blog_batch_6.py --live     # publish now
"""
import argparse, datetime, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_branch as RB

U = "https://booked-job.com/blog/thumbtack-refunds-chargebacks-deactivation/"

PAGES = [
 {"slug": "thumbtack-refunds-chargebacks-deactivation", "_series": "Lead Sources",
  "title": "Thumbtack Refunds and Chargebacks: What Happens When You Fight a Bad Lead",
  "h1": "Thumbtack Refunds, Chargebacks, and <em>Deactivation</em>",
  "meta": "What Thumbtack actually refunds, the 45-day window, and why calling your bank about a bad lead can get your pro account held or closed. Plus the math on what the refund queue is worth per booked job.",
  "short": "Thumbtack refunds four things — wrong location, wrong job type, bad contact info, duplicates — inside 45 days, at their discretion. A customer who simply ghosts you is not on that list. And if you skip the queue and call your bank instead, Thumbtack's own help docs say your pro account gets held. Work the refund queue; never charge back.",
  "statBig": "931", "statLabel": "Complaints closed against Thumbtack in 3 years — 251 in the last 12 months alone [BBB, July 2026]",
  "labels": ["Lead Sources", "Thumbtack", "Contractor Marketing", "Getting Paid"],
  "body": [
   {"h2": "What Thumbtack will actually refund",
    "answer": "Four categories, 45 days, their call.",
    "html": "<p>Thumbtack's published refund policy for pros covers a narrow list: the lead was in the wrong location, the wrong job type, had bad contact information, or was a duplicate of one you already paid for. You have <b>45 days</b> from the charge to ask, and Thumbtack decides case by case. Nothing about that list is unreasonable — the problem is what's missing from it.</p>"
    "<table class=\"cmp\"><thead><tr><th>Situation</th><th>On the published list?</th><th>What to do</th></tr></thead><tbody>"
    "<tr><td>Lead is outside your service area</td><td>Yes — wrong location</td><td>File it, with the address</td></tr>"
    "<tr><td>Roof job sent to a plumber</td><td>Yes — wrong job type</td><td>File it, quote the request</td></tr>"
    "<tr><td>Phone number is dead or fake</td><td>Yes — bad contact info</td><td>File it, screenshot the failed call</td></tr>"
    "<tr><td>Same homeowner, charged twice</td><td>Yes — duplicate</td><td>File it, reference both charges</td></tr>"
    "<tr><td>Customer reads your quote and ghosts</td><td><b>No</b></td><td>You eat it — unless nobody got a reply</td></tr>"
    "<tr><td>Homeowner hires the guy who answered first</td><td><b>No</b></td><td>You eat it. This is the model.</td></tr>"
    "</tbody></table>"
    "<p>As of mid-2026 there's also a narrow automatic credit for leads where the customer replied to <em>no</em> pro at all — but the conditions are tight, and it doesn't touch the ordinary case where you got outrun. For the wider argument about shared leads, see <a href=\"/blog/is-angi-worth-it/\">the real math on lead sites</a>.</p>"},

   {"h2": "The one thing that isn't refundable: losing the race",
    "answer": "Getting outrun isn't a defect. It's the product.",
    "html": "<p>Every shared lead goes to four or five pros at once, and <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026). So the most common way you lose money on Thumbtack — you quoted, they went quiet, they hired somebody else — is working exactly as designed, and it will never be refunded. That's not a scandal; it's the deal you signed. But it means your only two levers are answering faster (<a href=\"/blog/speed-to-lead-for-contractors/\">speed to lead</a>) and filing every refund you're actually owed.</p>"},

   {"h2": "Never call your bank. That's the trap.",
    "answer": "A chargeback puts your pro account on hold — Thumbtack's own docs say so.",
    "html": "<p>This is the part that costs guys their business. Thumbtack's own help documentation tells pros that a disputed charge puts a hold on the account, that you have to resolve the dispute with your bank and repay the balance before the hold lifts (about 15 minutes after it clears), and that in future you should request a refund <em>through Thumbtack</em> rather than disputing with your bank. Their terms also let them terminate accounts. Pros describe the same sequence in complaint after complaint: dispute a charge, lose the account, lose years of accumulated reviews with it.</p>"
    "<p>The BBB has closed <b>931</b> complaints against Thumbtack in three years — <b>251</b> in the last twelve months — and the company is not BBB accredited (BBB profile, July 2026). One pro's filing this month reads: <em>\"I do not see why I should pay for an unsolicited lead Thumbtack sent me when all I did was get on the website to search for a vendor.\"</em> Whatever you think of the charge, the way out is the refund queue and, if it stays broken, turning the budget off. Not your bank. Same rule as the <a href=\"/blog/angi-refunds-15-22-percent-junk-leads-scam/\">Angi refund runaround</a>.</p>"},

   {"h2": "What the refund queue is actually worth (our math)",
    "answer": "About $62 per booked job. That's the whole argument.",
    "html": "<p>Here's a number nobody else is going to run for you. Thumbtack costs roughly <b>$250 per booked job</b> once you account for shared leads and real close rates, against about <b>$168</b> for an exclusive Google LSA lead and about <b>$542</b> for Angi/HomeAdvisor (2026 lead-network comparisons). Now assume a quarter of your leads fall into Thumbtack's four refund categories — a conservative read of what pros report — and that you file every one of them inside the 45 days.</p>"
    "<table class=\"cmp\"><thead><tr><th>Channel / behavior</th><th>Cost per booked job</th><th>Lead is yours alone?</th></tr></thead><tbody>"
    "<tr><td>Google LSA (exclusive)</td><td>~$168</td><td>Yes</td></tr>"
    "<tr><td>Thumbtack, filing every eligible refund</td><td><b>~$188</b></td><td>No — 4-5 pros</td></tr>"
    "<tr><td>Thumbtack, filing nothing</td><td>~$250</td><td>No — 4-5 pros</td></tr>"
    "<tr><td>Angi / HomeAdvisor</td><td>~$542</td><td>No</td></tr>"
    "</tbody></table>"
    "<p><b>The gap is about $62 per booked job.</b> Assumptions are on the table so you can argue with them: 25% of leads eligible, all filed and granted, $250 baseline. Work the queue and Thumbtack lands within about twenty bucks of an exclusive LSA lead. Skip it and you're paying nearly 50% more than LSA for a lead four other trucks also bought. Twenty minutes of admin a week is the entire difference between a channel that pays and one that quietly doesn't — which is the same lesson as <a href=\"/blog/cost-per-lead-vs-cost-per-booked-job/\">cost per lead vs cost per booked job</a>.</p>"},

   {"h2": "The 20-minute Monday refund routine",
    "answer": "Same time every week, six steps, no arguing.",
    "html": "<ol>"
    "<li><b>Pull the week's charges.</b> Every lead you paid for, in one list.</li>"
    "<li><b>Mark the four categories.</b> Wrong location, wrong job type, bad contact info, duplicate. Only those get filed.</li>"
    "<li><b>Attach the proof.</b> A screenshot of the address, the request text, or the failed call. Refunds get granted on evidence, not on tone.</li>"
    "<li><b>File inside 45 days.</b> Anything older is gone. This is why it's a weekly job, not a quarterly one.</li>"
    "<li><b>Log every denial in a spreadsheet.</b> Date, amount, reason. Three months of that is either proof the channel works or the receipts you need to quit it.</li>"
    "<li><b>If it stays broken, cut the budget — don't charge back.</b> Turning off spend costs you nothing. A bank dispute can cost you the account.</li>"
    "</ol>"
    "<p>Do this and you'll know within a quarter whether Thumbtack is a channel or a leak. Most shops never find out because they never measure it.</p>"},

   {"h2": "The real fix: stop renting the phone",
    "answer": "Refunds recover dollars. Owning the pipeline ends the problem.",
    "html": "<p>Every hour spent fighting a $57 charge is an hour not spent on the asset that doesn't send invoices — your Google Business Profile, your reviews, and a website that converts the homeowners already looking for you. That's the ~$168-and-falling side of the ledger, and nobody can deactivate it. Start with <a href=\"/blog/google-business-profile-for-contractors/\">your Google Business Profile</a>, then <a href=\"/blog/get-more-google-reviews/\">the reviews that make the phone ring</a>. Keep Thumbtack running while you build if the math works — just work the queue, and never call the bank.</p>"}],

  "faq": [
   {"q": "Does Thumbtack refund leads that never respond?",
    "a": "Not as a rule. The published refund categories are wrong location, wrong job type, bad contact info, and duplicates — a customer who reads your quote and goes quiet isn't on that list. As of mid-2026 there's a narrow automatic credit for leads where the customer replied to no pro at all, but the conditions are tight."},
   {"q": "How long do I have to request a Thumbtack refund?",
    "a": "45 days from the charge, and the decision is Thumbtack's to make case by case. That window is why refunds should be a weekly 20-minute routine rather than something you get to when the statement looks wrong — anything older than 45 days is simply gone."},
   {"q": "Will Thumbtack deactivate my account if I dispute a charge with my bank?",
    "a": "A bank dispute puts a hold on your pro account per Thumbtack's own help docs, and you must resolve it with your bank and repay the balance before the hold lifts. Their terms permit termination, and pros report losing accounts and review history this way. Use the refund queue, and if it fails, cut the budget instead."},
   {"q": "Is Thumbtack cheaper than Angi for contractors?",
    "a": "Yes, on the per-booked-job math: roughly $250 for Thumbtack versus about $542 for Angi/HomeAdvisor, per 2026 lead-network comparisons. Google LSA runs about $168 and the lead is exclusive to you, which is why LSA usually beats both once you can answer fast."}],

  "fbPosts": ["Fighting a bad Thumbtack charge? Two rules. File inside 45 days — only wrong location, wrong job type, bad contact info, or duplicates qualify. And never call your bank: a chargeback puts your pro account on hold, and pros report losing the account and the reviews with it."],

  "variants": {
    "threads": {
     "text": "Blunt one: the pros who lose their Thumbtack account almost never lose it over a bad job. They lose it over a $57 chargeback. Thumbtack's own help docs say a bank dispute puts a hold on your pro account — and the reviews go with it. Agree, or am I missing something?\n\n" + U,
     "chain": [
      "Refundable: wrong location, wrong job type, bad contact info, duplicates. 45 days. That's the whole list.",
      "Not refundable: the homeowner who ghosts you after reading the quote. That's not a bug, that's the product — 78% hire whoever answers first. " + U]},
    "bluesky": {
     "text": "Ever notice the only Thumbtack charge you can't get refunded is the most common one — homeowner reads your quote, goes quiet, hires the guy who answered first? Four things qualify for a refund. That isn't one of them. 45-day window, too 👇",
     "chain": [
      "The trap nobody warns you about: skip the refund queue, call your bank instead, and your pro account goes on hold. Their own help docs say it.",
      "Worked out what the queue is worth: ~$62 per booked job. That's the difference between Thumbtack and an exclusive LSA lead → " + U]},
    "mastodon": {
     "text": "If you buy shared leads, learn the refund rules before you need them. Thumbtack refunds four things — wrong location, wrong job type, bad contact info, duplicates — inside 45 days. A customer who simply stops replying isn't covered. And disputing a charge with your bank puts the pro account on hold rather than fixing it, per the platform's own documentation. Full breakdown, including what filing every eligible refund is actually worth per booked job:",
     "tags": ["#SmallBusiness", "#Trades", "#Contractor", "#HomeService"]},
    "telegram": "💰 Monday money check: pull last week's Thumbtack charges and file every refund you're owed — <b>wrong location, wrong job type, bad contact info, duplicates</b>, inside <b>45 days</b>. Worth about <b>$62 per booked job</b> by our math. And whatever you do, don't dispute with your bank: that puts a hold on your pro account.\n\n" + U,
    "linkedin": "The most expensive mistake a contractor makes on a lead platform isn't buying a bad lead. It's disputing one with their bank.\n\nThumbtack's own help documentation is explicit: a disputed charge places a hold on the pro account, and the balance has to be resolved with the bank before it lifts. Their terms permit termination. Pros describe losing years of accumulated reviews over a $57 argument.\n\nThe unglamorous alternative is a 20-minute weekly routine. Four categories qualify for a refund — wrong location, wrong job type, bad contact info, duplicates — within 45 days of the charge.\n\nWe ran the margin math on what that routine is worth: filing every eligible refund moves Thumbtack from roughly $250 to roughly $188 per booked job, against about $168 for an exclusive Google LSA lead. Roughly $62 a job, for twenty minutes of admin a week.\n\nFull breakdown: " + U}},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="publish now")
    a = ap.parse_args()
    if a.live:
        built = RB.wire_articles(PAGES)
        print(f"published {len(built)} batch-6 article(s) live: {', '.join(built)}")
        return
    for p in PAGES:
        print(f"  {p['slug']}  [{p['_series']}]  {len(p['body'])}sec {len(p['faq'])}faq "
              f"{len(p['variants'])}variants")
    print(f"  ({len(PAGES)} article — dry run; --live to publish now)")


if __name__ == "__main__":
    main()
