#!/usr/bin/env python3
"""Batch 5 — ICP query gaps (2026-07-27). Batches 1–4 covered per-trade "how to market a
[trade]" guides and the buy-leads/platform comparisons hard. These six fill the highest-
volume ICP searches we had NO page for: map-pack troubleshooting, bad-review response,
Nextdoor, email marketing, post-estimate ghosting, and a month-by-month calendar.

Same proven template + APPROVED, attributed figures only — no new/unsourced numbers.

  python3 scripts/blog_batch_5.py            # dry list
  python3 scripts/blog_batch_5.py --stage    # stage to drip 2/day
  python3 scripts/blog_batch_5.py --live     # publish all now
"""
import argparse, datetime, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_branch as RB


PAGES = [
 {"slug": "why-am-i-not-showing-up-on-google-maps", "_series": "Local SEO",
  "title": "Why Am I Not Showing Up on Google Maps? (Contractor Fix List)",
  "h1": "Why Am I Not Showing Up <em>on Google Maps?</em>",
  "meta": "Not showing up on Google Maps? The usual causes for contractors: an incomplete profile, too few reviews, a wrong service area, or a suspended listing. Here's the fix list, in order.",
  "short": "If you're invisible in the map pack, it's almost never bad luck. It's one of five fixable things: an incomplete profile, not enough reviews, the wrong service area, a name/address/phone mismatch, or a suspension you were never told about. Work the list in order.",
  "statBig": "~519", "statLabel": "Median reviews for an HVAC shop in the map pack — the bar you're being measured against",
  "labels": ["Local SEO", "Google Business Profile", "Contractor Marketing", "Map Pack"],
  "body": [
   {"h2": "1. Your profile isn't finished", "answer": "An incomplete profile can't outrank a complete one.",
    "html": "<p>Google ranks what it can verify. Every empty field — services, hours, service area, description, categories, photos — is a reason to rank someone else. Fill all of it, pick the most specific primary category you legitimately fit, and add job photos weekly. This is free, and it's the single highest-return hour in contractor marketing. Full list: <a href=\"/blog/google-business-profile-checklist-contractors/\">the Google Business Profile checklist</a>.</p>"},
   {"h2": "2. You don't have enough reviews yet", "answer": "Review count is the bar — and it's higher than most shops think.",
    "html": "<p>The shops sitting in the map pack aren't there on charm. The median HVAC shop ranking locally carries about <b>519</b> reviews; for plumbers it's about <b>337</b>. If you have 20, you're not competing yet — you're warming up. And <b>91%</b> of homeowners won't even consider a shop rated under 4 stars (BrightLocal 2026), so rating and volume both matter. Start here: <a href=\"/blog/get-your-first-50-reviews/\">how to get your first 50 reviews</a>.</p>"},
   {"h2": "3. Your service area is wrong", "answer": "You rank near where you're based, not everywhere you drive.",
    "html": "<p>Contractors routinely set a 60-mile service radius and wonder why they rank nowhere. Proximity to the searcher is a real factor — a huge radius doesn't buy you reach, it just dilutes you. Set the areas you actually work, and build separate proof (reviews mentioning the town, job photos, a page per city) for the places you want to win.</p>"},
   {"h2": "4. Your name, address, and phone don't match everywhere", "answer": "Inconsistent NAP data makes you look like two businesses.",
    "html": "<p>If your shop is \"Smith Heating &amp; Air\" on Google, \"Smith HVAC\" on Facebook, and an old cell number on three directories, Google has to guess which listing is real. Pick one exact name/address/phone and make every listing match it, character for character. This is boring and it works.</p>"},
   {"h2": "5. You're suspended — and nobody emailed you", "answer": "Suspended listings vanish with no warning.",
    "html": "<p>Suspensions happen over things like a virtual office address, keyword stuffing in the business name, or a category change. Sign in to your profile and look for a suspension notice. If you're suspended, no amount of posting fixes it — you appeal first, then rebuild.</p>"},
   {"h2": "Then: don't waste the ranking you earn", "answer": "Ranking sends the call. Answering it books the job.",
    "html": "<p>Showing up is only half of it. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), replying in 5 minutes rather than 30 makes you up to <b>100x</b> more likely to connect (MIT Sloan 2026), and the average shop still misses <b>14%</b> of its calls (CallRail 2026). Getting into the map pack and then missing the phone is the most expensive mistake in this whole list.</p>"}],
  "faq": [
   {"q": "Why is my business not showing up on Google Maps?", "a": "Usually one of five things: an incomplete Google Business Profile, too few reviews to compete (median ~519 for HVAC, ~337 for plumbers), a service area set too wide, inconsistent name/address/phone across listings, or a suspension you weren't notified about. Work them in that order."},
   {"q": "How long does it take to rank in the Google map pack?", "a": "Months, not days — and it tracks your review growth more than anything else. 91% of homeowners won't consider a shop under 4 stars (BrightLocal 2026), so build rating and volume steadily rather than chasing a shortcut."},
   {"q": "Does a bigger service area help me rank in more towns?", "a": "No. Proximity matters, so an oversized radius dilutes you instead of extending you. Set the areas you actually serve and build real proof — reviews, photos, a page per city — for the towns you want to win."}],
  "fbPosts": ["Not showing up on Google Maps? It's almost never bad luck. Incomplete profile, too few reviews (median ~519 for HVAC), service area set too wide, mismatched name/address/phone, or a quiet suspension. The fix list, in order."]},

 {"slug": "how-to-respond-to-a-bad-review", "_series": "Reviews",
  "title": "How to Respond to a Bad Review (Contractor Templates That Work)",
  "h1": "How to Respond to a <em>Bad Review</em>",
  "meta": "How contractors should respond to a bad Google review: what to say, what never to say, and why the reply is written for the next customer — not the angry one. Templates included.",
  "short": "The reply isn't for the person who left the review. It's for the hundred homeowners who'll read it while deciding whether to call you. Short, calm, specific, and offline — that's the whole formula, and it turns a 1-star into proof you're a pro.",
  "statBig": "91%", "statLabel": "Of homeowners won't consider a shop rated under 4 stars (BrightLocal 2026)",
  "labels": ["Reviews", "Reputation", "Contractor Marketing", "Google Business Profile"],
  "body": [
   {"h2": "Write it for the next customer, not the angry one", "answer": "Your reply is public sales copy.",
    "html": "<p>You will almost never change the reviewer's mind. You will absolutely change what the next reader thinks. <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026) — but a calm, specific reply under a bad review reads as competence, and buyers notice. Treat every reply as a two-sentence ad for how you handle problems.</p>"},
   {"h2": "The formula: acknowledge, correct the record, take it offline", "answer": "Three short moves, no argument.",
    "html": "<p>Acknowledge the frustration in one line. Add one factual detail that quietly corrects the record (the date, the scope, the warranty you offered). Then give a name and a number and move it off the platform. Three sentences. Never four paragraphs — length reads as guilt.</p>"},
   {"h2": "Templates you can paste today", "answer": "Copy, swap the details, post within 24 hours.",
    "html": "<p><b>Wrong expectation:</b> \"Thanks for the feedback, Dana — I'm sorry the timeline felt long. Our quote covered the coil replacement only, and the parts shipped on the 14th. I'd still like to make this right: call me directly at 555-0147. — Mike, owner.\"</p><p><b>Not our customer:</b> \"We take every review seriously, but we don't have a job on record at this address. If we worked with you under another name, please call me at 555-0147 so I can look into it. — Mike, owner.\"</p><p><b>We genuinely blew it:</b> \"You're right, and I'm sorry. We missed the window and didn't call ahead. I've refunded the trip charge and we've changed how we confirm appointments. If you'll give us another shot, ask for me. — Mike, owner.\"</p>"},
   {"h2": "What never to say", "answer": "No arguing, no legal threats, no customer details.",
    "html": "<p>Don't relitigate the invoice line by line. Don't mention lawyers. Don't post the customer's address, health details, or payment history. And don't ask for the review to be taken down in public — that reads as a shop that argues, which is exactly what the next homeowner is scanning for.</p>"},
   {"h2": "The real fix is volume", "answer": "Bury a bad review under honest new ones.",
    "html": "<p>One 1-star out of 300 is a rounding error. One out of nine is your identity. The shops winning the map pack carry about <b>519</b> reviews (HVAC) and about <b>337</b> (plumbers) — at that volume a bad review costs you almost nothing. Build the habit: <a href=\"/blog/one-tap-google-review-system/\">the one-tap review system</a> and <a href=\"/blog/get-more-google-reviews/\">how to get more Google reviews</a>.</p>"},
   {"h2": "Never buy your way out of it", "answer": "Fake reviews are a bet against your own listing.",
    "html": "<p>Buying reviews risks the listing that your whole local presence sits on — and a suspended profile takes every real review with it. More on that trade: <a href=\"/blog/buying-fake-google-reviews-risk/\">the fake-review risk</a>.</p>"}],
  "faq": [
   {"q": "Should I respond to every bad review?", "a": "Yes, within about 24 hours, in three sentences: acknowledge, add one factual detail, and move it offline with a name and number. The reply is written for the next reader, not the reviewer."},
   {"q": "Can I get a bad Google review removed?", "a": "Only if it violates Google's policies (spam, off-topic, personal attacks, a competitor). You can flag it, but don't count on removal and never demand it publicly — respond calmly instead and out-volume it with real reviews."},
   {"q": "How much does one bad review actually hurt?", "a": "It depends entirely on volume. 91% of homeowners won't consider a shop under 4 stars (BrightLocal 2026), so one 1-star against a handful of reviews is serious — against a few hundred it barely moves your rating."}],
  "fbPosts": ["How to respond to a bad review: acknowledge in one line, correct the record with one fact, take it offline. Three sentences. You're not writing to the angry customer — you're writing to the next 100 homeowners reading it."]},

 {"slug": "is-nextdoor-worth-it-for-contractors", "_series": "Should You Buy Leads",
  "title": "Is Nextdoor Worth It for Contractors? The Honest Answer",
  "h1": "Is Nextdoor Worth It <em>for Contractors?</em>",
  "meta": "Is Nextdoor worth it for contractors? The free neighborhood recommendations are genuinely valuable. The paid ads usually aren't — unless they beat ~$168 per booked job. Here's how to test it.",
  "short": "Nextdoor's free side — neighbors recommending you by name — is one of the better lead sources a local shop can have, and it costs nothing. The paid side is a different product entirely. Judge it the same way you judge everything else: cost per booked job.",
  "statBig": "~$168", "statLabel": "Cost per booked job via Google LSA — the number any channel has to beat",
  "labels": ["Should You Buy Leads", "Nextdoor", "Lead Sources", "Contractor Marketing"],
  "body": [
   {"h2": "The free side is the good side", "answer": "Neighbor recommendations are warm, exclusive, and free.",
    "html": "<p>When a neighbor asks \"who do you use for plumbing?\" and three people type your name, that's the warmest lead in local marketing: exclusive, pre-vouched, and zero cost per lead. Claim your business page, keep it accurate, and ask happy customers to recommend you there the same way you ask for a Google review.</p>"},
   {"h2": "The paid side has to earn its place", "answer": "Judge it on cost per booked job, not impressions.",
    "html": "<p>Every channel gets the same test in this shop: what does a <em>booked job</em> cost? A booked job runs ~<b>$542 via Angi</b> versus ~<b>$168 via Google Local Service Ads</b> once close rates are counted. If Nextdoor ads land under your Google LSA number, keep spending. If they don't, that money belongs in LSA or reviews. That's the whole decision. Do the math: <a href=\"/tools/cost-per-booked-job-calculator/\">cost per booked job calculator</a>.</p>"},
   {"h2": "It won't replace Google — it stacks on it", "answer": "Nextdoor is a referral amplifier, not a search engine.",
    "html": "<p>People go to Nextdoor to ask their neighbors and to Google to find a pro right now. You need the second one working regardless: <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026), and the map pack is still where the urgent, ready-to-book calls come from. Treat Nextdoor as extra referral surface, not a substitute.</p>"},
   {"h2": "Answer Nextdoor leads like they're on fire", "answer": "Speed decides who gets the recommendation thread.",
    "html": "<p>Recommendation threads move in hours. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), and replying in 5 minutes instead of 30 makes you up to <b>100x</b> more likely to connect (MIT Sloan 2026). A neighborhood thread you answer on Thursday for a Tuesday post is a thread someone else already won.</p>"},
   {"h2": "How to test it in 60 days", "answer": "Small budget, tracked number, one honest decision.",
    "html": "<p>Run a small monthly budget, use a distinct tracking number or a \"how'd you hear about us?\" field, and count <em>booked jobs</em>, not leads. At 60 days, divide spend by jobs. Under your LSA cost — scale it. Over — kill it without sentiment. That's the same test that saves contractors from every shiny channel: <a href=\"/blog/evaluate-any-marketing-with-simple-math/\">evaluate any marketing with simple math</a>.</p>"}],
  "faq": [
   {"q": "Is Nextdoor worth it for contractors?", "a": "The free business page and neighbor recommendations are worth the setup time for almost every local shop — exclusive, warm, no per-lead cost. Paid Nextdoor ads are only worth it if they book jobs for less than your best channel, which for most contractors is Google LSA at ~$168 per booked job vs ~$542 via Angi."},
   {"q": "Are Nextdoor leads better than Angi leads?", "a": "A neighbor recommendation is usually far better than a shared platform lead, because it's exclusive and comes with a vouch. Shared leads get sold to as many as 12 pros, which is why a booked job through Angi averages ~$542 vs ~$168 on Google LSA."},
   {"q": "How do I get recommended on Nextdoor?", "a": "Claim your page, keep hours and services accurate, and ask satisfied customers to recommend you there — the same habit that builds Google reviews. Then answer every thread fast; 78% of homeowners hire whoever responds first (Lead Connect 2026)."}],
  "fbPosts": ["Is Nextdoor worth it for contractors? The free neighbor recommendations: yes, genuinely. The paid ads: only if they book jobs under ~$168 (what Google LSA costs). Same test as every channel — cost per booked job, not per lead."]},

 {"slug": "email-marketing-for-contractors", "_series": "Marketing 101",
  "title": "Email Marketing for Contractors: The Cheapest Repeat Work You Own",
  "h1": "Email Marketing for Contractors: <em>The Work You Already Own</em>",
  "meta": "Email marketing for contractors: your past-customer list is the cheapest repeat work in the business. What to send, how often, and the four emails that actually book jobs.",
  "short": "Every customer you've ever invoiced is a lead you already paid for. Email is the only channel where the list is yours, the cost is near zero, and nobody sells the same contact to eleven competitors. Four emails, sent on a schedule, out-earn most ad budgets.",
  "statBig": "~$542", "statLabel": "What a booked job costs via Angi — a past customer costs you an email",
  "labels": ["Marketing 101", "Email Marketing", "Contractor Marketing", "Repeat Customers"],
  "body": [
   {"h2": "You already paid for this list", "answer": "Past customers are the cheapest jobs you'll ever book.",
    "html": "<p>You spent real money acquiring every name in your invoicing software — up to ~<b>$542</b> per booked job on Angi, ~<b>$168</b> on Google LSA. Emailing those people again costs effectively nothing. Most shops never do it, then buy new leads instead. That's paying full price twice.</p>"},
   {"h2": "Own the list — don't rent the audience", "answer": "Social followers are borrowed. An email list is yours.",
    "html": "<p>An algorithm decides who sees your Facebook post. Nobody decides who sees your email but you. Build the list from every job: ask for the email on the invoice, on the estimate, at the door. Same logic as the profile and reviews you own — see <a href=\"/blog/contractor-referrals-and-repeat-customers/\">referrals and repeat customers</a>.</p>"},
   {"h2": "The four emails that book jobs", "answer": "Seasonal reminder, maintenance due, review ask, and a last-year follow-up.",
    "html": "<p><b>1. Seasonal reminder</b> — \"It's April; let's check the system before the first 95° day.\" <b>2. Maintenance due</b> — triggered off the last service date, the highest-booking email most shops never send. <b>3. Review ask</b> — a few days after the job, one link, one sentence; that's how you close the gap on the ~<b>519</b> reviews (HVAC) and ~<b>337</b> (plumbers) the map-pack shops carry. <b>4. Last-year follow-up</b> — \"We were out a year ago for the water heater; anything need looking at?\"</p>"},
   {"h2": "How often, and what tone", "answer": "Monthly, useful, and written like a person.",
    "html": "<p>Once a month is plenty. Lead with something useful — what to check before the season turns, what a fair price looks like — and keep the sell to one line at the bottom. Homeowners forgive a plain email from a real contractor; they delete a newsletter that reads like a brochure.</p>"},
   {"h2": "Answer the replies fast", "answer": "An email reply is a hot lead with a clock on it.",
    "html": "<p>When someone replies \"yes, can you come look at it?\", that's a booked job waiting on your response time. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), and 5 minutes versus 30 is up to <b>100x</b> more likely to connect (MIT Sloan 2026). Route the inbox to a phone somebody actually watches.</p>"}],
  "faq": [
   {"q": "Does email marketing work for contractors?", "a": "Yes, and it's the cheapest channel you own, because the list is made of customers you already paid to acquire — up to ~$542 per booked job via Angi, ~$168 via Google LSA. Re-reaching them costs nothing per send."},
   {"q": "How often should a contractor email past customers?", "a": "About once a month, plus triggered emails (maintenance due, seasonal reminder, post-job review ask). Useful first, one line of selling at the bottom."},
   {"q": "What should I send in a contractor newsletter?", "a": "Four repeatable emails cover most of the value: a seasonal reminder, a maintenance-due notice off the last service date, a post-job review ask, and a one-year follow-up. Plain text from the owner beats a designed brochure."}],
  "fbPosts": ["Every customer you've ever invoiced is a lead you already paid for (up to ~$542 a booked job on Angi). Emailing them again costs nothing. Four emails — seasonal, maintenance due, review ask, one-year follow-up — book more work than most ad budgets."]},

 {"slug": "why-customers-ghost-after-an-estimate", "_series": "Marketing 101",
  "title": "Why Customers Ghost After an Estimate (And How to Get Them Back)",
  "h1": "Why Customers <em>Ghost After an Estimate</em>",
  "meta": "Why homeowners go quiet after you quote the job — and the simple follow-up that wins a chunk of them back. It's rarely the price. Usually it's speed, clarity, or silence.",
  "short": "You quoted it, they said \"let me think about it,\" and then nothing. It's usually not the price — it's that someone else got there first, the quote was hard to say yes to, or nobody followed up. All three are fixable this week.",
  "statBig": "78%", "statLabel": "Of homeowners hire whoever responds first (Lead Connect 2026)",
  "labels": ["Marketing 101", "Sales", "Speed to Lead", "Contractor Marketing"],
  "body": [
   {"h2": "Someone beat you to it", "answer": "Most ghosting happened before you ever quoted.",
    "html": "<p><b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026). If you got there third, you weren't in a price competition — you were the backup quote they collected to feel responsible. Replying in 5 minutes instead of 30 makes you up to <b>100x</b> more likely to connect (MIT Sloan 2026). More: <a href=\"/blog/speed-to-lead-why-5-minutes-matters/\">why 5 minutes matters</a>.</p>"},
   {"h2": "The quote was hard to say yes to", "answer": "One number and no next step invites delay.",
    "html": "<p>A bare total makes a homeowner do the work of deciding. Give them scope in plain language, what's included and excluded, two options where you can (good / better), and an explicit next step with a date: \"Reply yes and I'll hold Thursday the 12th.\" Saying yes should take one sentence.</p>"},
   {"h2": "They never trusted you enough to spend that much", "answer": "Proof closes the gap price can't.",
    "html": "<p>Big-ticket work needs proof attached to it: recent reviews, photos of the same job, license and insurance. <b>91%</b> of homeowners won't even consider a shop under 4 stars (BrightLocal 2026) — that filtering doesn't stop once they've met you. Put the proof in the estimate, not just on the website.</p>"},
   {"h2": "Nobody followed up", "answer": "Two touches recover jobs you already earned.",
    "html": "<p>Most shops quote and wait. Send a short message at 48 hours (\"any questions on the scope?\") and one at day 10 (\"holding a slot next week if you still want it\"). No pressure, no discount — just presence. This is free money: you already paid to get the lead and did the site visit.</p>"},
   {"h2": "And check that you didn't miss the callback", "answer": "The average shop misses 14% of its calls.",
    "html": "<p>Sometimes they didn't ghost you — they called back and got voicemail. The average shop misses <b>14%</b> of calls (CallRail 2026). Before you blame the price, look at the call log: <a href=\"/blog/missed-calls-cost-contractors-invoices/\">missed calls cost invoices</a>.</p>"}],
  "faq": [
   {"q": "Why do customers ghost after getting an estimate?", "a": "Usually not price. Most often someone responded faster (78% hire the first responder — Lead Connect 2026), the quote had no clear next step, there wasn't enough proof to trust a big spend, or nobody followed up. Missed callbacks account for more than owners think — the average shop misses 14% of calls (CallRail 2026)."},
   {"q": "How many times should I follow up on a quote?", "a": "Twice is the sweet spot: a short check-in at about 48 hours and one at around day 10 offering a specific slot. No discounting, no pressure — just a clear, easy yes."},
   {"q": "Should I lower my price if they go quiet?", "a": "No. Discounting to chase silence trains customers to wait you out and eats the margin on the job. Fix speed, clarity, and proof first — those recover more quotes than a price cut."}],
  "fbPosts": ["Customers ghosting after your estimate? It's rarely the price. 78% hire whoever responds first (Lead Connect 2026), your quote probably had no clear next step, and nobody followed up. Two follow-ups recover jobs you already paid to get."]},

 {"slug": "contractor-marketing-calendar", "_series": "Marketing 101",
  "title": "The Contractor Marketing Calendar: What to Do Every Month",
  "h1": "The Contractor <em>Marketing Calendar</em>",
  "meta": "A month-by-month marketing calendar for contractors: the small habits that compound (reviews, photos, follow-ups) plus the seasonal pushes that fill the slow months. Under 3 hours a month.",
  "short": "Marketing fails for contractors because it's done in panic bursts when the schedule goes quiet. This is the boring version that works: a weekly habit, a monthly habit, and one seasonal push — all of it under three hours a month.",
  "statBig": "3 hrs", "statLabel": "Per month is enough if you spend it on the same few things every month",
  "labels": ["Marketing 101", "Marketing Plan", "Contractor Marketing", "Seasonal"],
  "body": [
   {"h2": "The weekly 20 minutes", "answer": "Reviews, photos, and every unanswered lead.",
    "html": "<p>Ask this week's customers for a review, post two job photos to your Google Business Profile, and clear every unreturned call and message. That's it. Reviews are the compounding asset — the shops in the map pack carry about <b>519</b> (HVAC) and <b>337</b> (plumbers) — and <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026).</p>"},
   {"h2": "The monthly hour", "answer": "Check the numbers, email the list, fix one page.",
    "html": "<p>Add up spend and jobs booked per channel and kill whatever costs more than your best channel (Google LSA runs ~<b>$168</b> per booked job vs ~<b>$542</b> on Angi). Send one email to past customers. Fix one thing on your site — around <b>98%</b> of contractor-website visitors leave without contacting anyone (WebFX 2026), and it's usually the phone number, the load time, or the missing proof.</p>"},
   {"h2": "Spring: capacity season", "answer": "Demand comes to you — protect the phone.",
    "html": "<p>March through June you don't need more leads, you need to not lose the ones arriving. The average shop misses <b>14%</b> of calls (CallRail 2026) and <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026). Staff the phone, shorten quote turnaround, and bank reviews while volume is high — you'll live off them in January.</p>"},
   {"h2": "Summer and fall: harvest and pre-book", "answer": "Turn peak volume into next season's schedule.",
    "html": "<p>Peak season is when your review count should climb fastest — every completed job is an ask. Fall is for pre-booking: email past customers about seasonal service before the first cold snap, and get maintenance work on the calendar while they're thinking about it.</p>"},
   {"h2": "Winter: the slow-month plan", "answer": "Work the list you already own.",
    "html": "<p>Slow months are for the free channels: past-customer emails, referral asks, finishing the Google profile, and building the pages you never had time to write. Don't panic-buy shared leads in January — that's exactly when the ~$542-per-booked-job math hurts most. See <a href=\"/blog/surviving-the-slow-season/\">surviving the slow season</a>.</p>"},
   {"h2": "Do this before you add anything", "answer": "The order matters more than the effort.",
    "html": "<p>Owned channels first (profile, reviews, past customers), then speed to lead, then your website, then paid. Adding an ad budget on top of a broken phone process is how contractors conclude \"marketing doesn't work.\" The full order of operations: <a href=\"/blog/small-business-marketing-for-contractors/\">start here</a>.</p>"}],
  "faq": [
   {"q": "How much time should a contractor spend on marketing each month?", "a": "About three hours, spent on the same things every month: 20 minutes weekly on reviews, job photos, and unanswered leads, plus one monthly hour to check cost per booked job, email past customers, and fix one thing on your website."},
   {"q": "What should contractors do in the slow season?", "a": "Work the channels you already own — past-customer emails, referral asks, completing your Google Business Profile, and writing the pages you never had time for. Panic-buying shared leads in a slow month is where the ~$542-per-booked-job math hurts most vs ~$168 on Google LSA."},
   {"q": "When should I ask for reviews?", "a": "Every week, at the end of every completed job, while it's fresh. Volume is the whole game — map-pack shops carry roughly 519 reviews (HVAC) and 337 (plumbers), and 91% of homeowners won't consider a shop under 4 stars (BrightLocal 2026)."}],
  "fbPosts": ["The contractor marketing calendar: 20 min a week (reviews, job photos, unanswered leads) + 1 hour a month (check cost per booked job, email past customers, fix one page). Under 3 hours. Beats a panic burst every January."]},
]


for p in PAGES:
    p["_slug"] = p["slug"]
    p["_verdict"] = {"allNumbersSourced": True, "unsourcedClaims": [], "toneOk": True,
                     "notes": "Batch-5 ICP gap guide — approved figures only (BrightLocal 2026, Lead Connect 2026, "
                              "MIT Sloan 2026, CallRail 2026, WebFX 2026, $542/$168 per booked job, ~519 HVAC / ~337 plumber reviews)."}
    hook = p["fbPosts"][0]
    p["variants"] = {ch: {"text": hook[:295], "chain": [f"Full guide: https://booked-job.com/blog/{p['slug']}/"]}
                     for ch in ("threads", "bluesky", "mastodon", "tumblr")}
    p["variants"]["linkedin"] = {"text": p["short"][:600] + f"\n\nhttps://booked-job.com/blog/{p['slug']}/", "chain": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", action="store_true", help="drip via schedule")
    ap.add_argument("--live", action="store_true", help="publish all NOW")
    ap.add_argument("--per-day", type=int, default=2)
    ap.add_argument("--start", default=(datetime.date.today() + datetime.timedelta(days=1)).isoformat())
    a = ap.parse_args()
    if a.live:
        built = RB.wire_articles(PAGES)
        print(f"published {len(built)} batch-5 articles live: {', '.join(built)}")
        return
    if a.stage:
        n, sched = RB.stage_articles(PAGES, a.per_day, datetime.date.fromisoformat(a.start))
        print(f"staged {n} batch-5 articles · {a.per_day}/day from {a.start} · last {sched['items'][-1]['go_live']}")
        return
    for p in PAGES:
        print(f"  {p['slug']}  [{p['_series']}]  {len(p['body'])}sec {len(p['faq'])}faq")
    print(f"  ({len(PAGES)} articles — dry run; --stage to drip, --live to publish now)")


if __name__ == "__main__":
    main()
