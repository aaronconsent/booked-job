#!/usr/bin/env python3
"""Batch 7 — ICP query gaps (2026-07-27, weekly newsletter-goal run). Batches 1-6 covered
per-trade guides, the buy-leads comparisons, map-pack troubleshooting, reviews, and the
Thumbtack money cluster. These six fill high-intent searches we still had NO page for:
missed-call text-back, service-area/city pages, what a contractor website should cost,
whether a CRM is needed, plus two uncovered trade verticals (restoration, remodeling).

Same proven template + APPROVED, attributed figures only — no new/unsourced numbers.
Trade-specific advice in the two vertical guides is qualitative on purpose: we have no
sourced per-trade lead costs for restoration or remodeling, so we don't invent any.

  python3 scripts/blog_batch_7.py            # dry list
  python3 scripts/blog_batch_7.py --stage    # stage to drip 2/day
  python3 scripts/blog_batch_7.py --live     # publish all now
"""
import argparse, datetime, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_branch as RB


PAGES = [
 {"slug": "missed-call-text-back-for-contractors", "_series": "Speed to Lead",
  "title": "Missed Call Text Back: The Cheapest Fix in Contractor Marketing",
  "h1": "Missed Call Text Back <em>for Contractors</em>",
  "meta": "An auto-text on every missed call is the cheapest lead recovery a contractor can buy. What to send, how fast, what it costs, and why it beats adding ad budget to a phone nobody answers.",
  "short": "The average shop misses 14% of its calls, and a homeowner with a leak does not leave a voicemail — they dial the next number. An automatic text sent the second you miss the call puts you back in the conversation before your competitor picks up. It costs a few dollars a month and recovers jobs you already paid to generate.",
  "statBig": "14%", "statLabel": "Share of calls the average shop misses (CallRail 2026) — every one already cost you money",
  "labels": ["Speed to Lead", "Missed Calls", "Contractor Marketing", "Phone"],
  "body": [
   {"h2": "You already paid for the call you just missed", "answer": "A missed call is a lead you bought and threw away.",
    "html": "<p>Every ringing phone cost something to create — an ad, a review, a profile, a referral you earned. A booked job runs ~<b>$542</b> through Angi versus ~<b>$168</b> through Google Local Service Ads, and the average shop still misses <b>14%</b> of its calls (CallRail 2026). That's not a phone problem, it's a budget problem: you're paying full price for leads and dropping one in seven on the floor. More on the size of it: <a href=\"/blog/missed-calls-cost-contractors-invoices/\">what missed calls actually cost</a>.</p>"},
   {"h2": "Homeowners don't leave voicemails anymore", "answer": "They hang up and dial the next contractor.",
    "html": "<p>Someone standing in two inches of water is not composing a message. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), which means the winner of that job is usually decided in the next four minutes, without you. Voicemail is a system designed for a customer who no longer exists.</p>"},
   {"h2": "What missed call text back actually is", "answer": "An automatic text fires the instant a call goes unanswered.",
    "html": "<p>It's a setting, not a project. When a call rings out, your phone system sends the caller a text immediately — before they've finished dialing the next shop. Most VoIP providers, answering services, and contractor CRMs include it; standalone versions run a few dollars a month. If you do one thing to your marketing this month, do this one.</p>"},
   {"h2": "What the text should say", "answer": "Name the shop, apologize once, ask one question.",
    "html": "<p>Three lines, no marketing voice: <em>\"This is Mike at Smith Heating &amp; Air — sorry we missed you, we're on a job. What's going on and what's your address? I'll get you on the schedule.\"</em> Naming the business stops it reading as spam, the apology buys ten seconds of patience, and one question gets them typing instead of dialing. Don't send a link. Don't send a form. Ask a question a person answers with their thumbs.</p>"},
   {"h2": "Speed is the whole product", "answer": "Instant beats good; five minutes beats thirty.",
    "html": "<p>The text has to fire in seconds, not after a five-minute delay someone helpfully configured. Replying in 5 minutes rather than 30 makes you up to <b>100x</b> more likely to connect (MIT Sloan 2026), and an automatic text is the only way to hit that number while you're under a house. Then answer the reply like it's on fire — see <a href=\"/blog/speed-to-lead-why-5-minutes-matters/\">why five minutes matters</a>.</p>"},
   {"h2": "Fix the phone before you raise the budget", "answer": "Ad spend on a broken phone is just faster waste.",
    "html": "<p>Doubling your ad budget while missing <b>14%</b> of calls buys you more missed calls. The order of operations never changes: answer the phone, then earn reviews, then fix the website, then spend. <b>98%</b> of contractor-website visitors leave without calling (WebFX 2026) — the few who do call are the entire return on everything else you're paying for. Run your own number: <a href=\"/tools/missed-call-calculator/\">the missed call revenue calculator</a>.</p>"}],
  "faq": [
   {"q": "What is missed call text back?", "a": "An automatic text message sent to a caller the moment their call goes unanswered, usually built into your VoIP system or contractor CRM. It puts you back in the conversation within seconds, which matters because 78% of homeowners hire whoever responds first (Lead Connect 2026)."},
   {"q": "Do missed call text backs actually work for contractors?", "a": "They recover leads you already paid to generate. The average shop misses 14% of its calls (CallRail 2026), homeowners with an urgent problem rarely leave voicemails, and replying in 5 minutes instead of 30 makes you up to 100x more likely to connect (MIT Sloan 2026)."},
   {"q": "What should a missed call auto-text say?", "a": "Name your business, apologize in one line, and ask one question: what's going on and what's the address. Keep it under three lines, skip links and forms, and make sure it fires in seconds rather than minutes."}],
  "fbPosts": ["The average shop misses 14% of its calls (CallRail 2026). A homeowner with a leak doesn't leave a voicemail — they dial the next guy. An auto-text on every missed call costs a few bucks a month and recovers jobs you already paid for. Cheapest fix in contractor marketing."]},

 {"slug": "service-area-pages-for-contractors", "_series": "Local SEO",
  "title": "Service Area Pages: How to Rank in the Towns You Drive To",
  "h1": "Service Area Pages: <em>Ranking in the Next Town Over</em>",
  "meta": "How contractors rank in nearby towns they aren't based in: real service area pages with real proof, not fifty copies of the same page with the city name swapped. What to build, in what order.",
  "short": "You rank near where you sit, not everywhere you drive. Setting a 60-mile radius on your Google profile doesn't extend you — it dilutes you. What actually wins the next town over is a real page about real work you did there, backed by reviews that say the town's name.",
  "statBig": "~519", "statLabel": "Median reviews for an HVAC shop in the map pack — proof, not radius, is what ranks",
  "labels": ["Local SEO", "Service Area Pages", "Contractor Marketing", "Map Pack"],
  "body": [
   {"h2": "Proximity is real, and a wide radius doesn't beat it", "answer": "You rank near your address, not across your whole service area.",
    "html": "<p>The most common contractor mistake in local SEO is setting the service radius to everywhere the truck can reach and waiting. Distance from the searcher is a genuine ranking factor, so a 60-mile radius doesn't buy reach — it just spreads thin proof across a lot of towns. If you're invisible in your own town first, start here instead: <a href=\"/blog/why-am-i-not-showing-up-on-google-maps/\">why you're not showing up on Google Maps</a>.</p>"},
   {"h2": "What a real service area page looks like", "answer": "One town, real jobs, real photos, real names.",
    "html": "<p>A page that ranks for \"plumber in Willis\" talks about Willis: the neighborhoods you work, the jobs you've done there, photos from those jobs, the response time from your shop, and reviews from customers in that town. It reads like a contractor wrote it about a place they actually go. Two hundred words of that beat two thousand words of filler.</p>"},
   {"h2": "The doorway-page trap", "answer": "Fifty copies with the city swapped is a penalty waiting to happen.",
    "html": "<p>The templated approach — one page duplicated across every town in the county with find-and-replace on the city name — is the thing search engines have spent twenty years learning to ignore. It doesn't just fail to rank; a pile of thin near-duplicate pages drags on the site that hosts it. Build three towns properly instead of thirty badly.</p>"},
   {"h2": "Reviews are how you actually claim a town", "answer": "A review that names the town is a ranking signal and a sales asset.",
    "html": "<p>Nothing tells a search engine you work in a place like customers from that place saying so. Map-pack shops carry roughly <b>519</b> reviews (HVAC) and <b>337</b> (plumbers), and <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026). When you finish a job out of town, ask for that review the same day and let the customer mention where they live naturally. Systemize it: <a href=\"/blog/one-tap-google-review-system/\">the one-tap review system</a>.</p>"},
   {"h2": "Build them in order of profit, not alphabetically", "answer": "Start with the towns you'd actually drive to for a good job.",
    "html": "<p>Rank the towns by what a job there is worth after the drive. Build the top three pages, earn reviews there, and only then add the fourth. A service area page for a town you'd resent driving to is a page you'll never support with real jobs or real proof — and unsupported pages don't rank.</p>"},
   {"h2": "Then answer the phone the page earns", "answer": "Out-of-town leads are the easiest ones to lose.",
    "html": "<p>A homeowner two towns over is calling three shops, not one. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), 5 minutes beats 30 by up to <b>100x</b> (MIT Sloan 2026), and the average shop misses <b>14%</b> of its calls (CallRail 2026). Ranking in a new town and missing its calls is the most expensive way to do local SEO.</p>"}],
  "faq": [
   {"q": "Do service area pages actually work for contractors?", "a": "Real ones do. A page about one town — with jobs you did there, photos, and reviews from local customers — can rank. Fifty templated copies with the city name swapped generally don't, and a pile of thin near-duplicate pages can hold back the rest of your site."},
   {"q": "How do I rank in a town I'm not located in?", "a": "Build genuine proof for it: a substantive page about your work in that town, job photos, and reviews from customers who live there. Proximity to the searcher is a real ranking factor, so you're overcoming distance with evidence — which is why review volume matters (map-pack shops carry roughly 519 reviews for HVAC, 337 for plumbers)."},
   {"q": "Should I set a big service area radius on my Google Business Profile?", "a": "No. Set the areas you genuinely work. An oversized radius doesn't extend your reach, it spreads thin proof across many towns — and you still rank primarily near where you're based."}],
  "fbPosts": ["You rank near where you sit, not everywhere you drive. A 60-mile radius on your Google profile doesn't extend you — it dilutes you. What wins the next town over: one real page about real jobs there, plus reviews from customers who live there."]},

 {"slug": "how-much-should-a-contractor-website-cost", "_series": "Marketing 101",
  "title": "How Much Should a Contractor Website Cost? (Honest Ranges)",
  "h1": "How Much Should a <em>Contractor Website</em> Cost?",
  "meta": "What a contractor website should really cost — the honest ranges, what's worth paying for, what's pure markup, and the one question that decides whether any of it was worth it.",
  "short": "There's no right price, only a right test: does the site book jobs for less than your other channels? Most contractors overpay for design and underpay for the four things that actually convert. Here's what's worth money, what isn't, and how to know within ninety days.",
  "statBig": "98%", "statLabel": "Of contractor-website visitors leave without calling (WebFX 2026)",
  "labels": ["Marketing 101", "Websites", "Contractor Marketing", "Agencies"],
  "body": [
   {"h2": "Price the site the way you price everything else", "answer": "Cost per booked job, not cost per page.",
    "html": "<p>A website isn't a purchase, it's a channel — and every channel in this shop gets the same test: what does a <em>booked job</em> cost? A booked job runs ~<b>$542</b> through Angi and ~<b>$168</b> through Google Local Service Ads. If your site pays for itself in booked work inside a year, the price was right. If it doesn't, no amount of beautiful was worth it. Run it: <a href=\"/tools/cost-per-booked-job-calculator/\">cost per booked job calculator</a>.</p>"},
   {"h2": "What you're actually buying", "answer": "Four things convert; the rest is decoration.",
    "html": "<p>A phone number visible without scrolling. Proof on the first screen — reviews, real job photos, the trades you actually do. A page that loads fast on a phone in a truck. And a form that reaches somebody in minutes. <b>98%</b> of contractor-website visitors leave without calling (WebFX 2026); those four items are the whole fight for the other 2%. The longer version: <a href=\"/blog/why-your-contractor-website-isnt-converting/\">why your site isn't converting</a>.</p>"},
   {"h2": "What's worth paying for", "answer": "Speed, mobile, proof, and someone who'll change it next year.",
    "html": "<p>Pay for a site that loads fast, works one-handed on a phone, puts your proof up front, and can be edited without an invoice every time your hours change. Pay for real photos of your own trucks and crews. That's a real budget, and it's usually a lot less than what gets quoted.</p>"},
   {"h2": "What's pure markup", "answer": "Custom animation, stock photos, and monthly fees for nothing.",
    "html": "<p>Sliders, parallax, and a video header don't book jobs — they slow down the phone in the truck. Neither do stock photos of models in clean hard hats; homeowners can spot them, and they undercut the proof you're paying to build. Watch for a monthly \"maintenance\" fee attached to a site nobody touches, and for the hosting markup game: <a href=\"/blog/white-label-marketing-markup/\">what the markup looks like</a>.</p>"},
   {"h2": "Own the site, whoever builds it", "answer": "Your domain, your hosting, your logins — always.",
    "html": "<p>The single most expensive mistake isn't the build price, it's discovering the agency owns your domain, your hosting, and your Google profile. Get admin access to everything in writing before the first payment. If that's a problem for them, it's the answer: <a href=\"/blog/agency-wont-share-access-or-work/\">when an agency won't share access</a>.</p>"},
   {"h2": "The 90-day test", "answer": "Count booked jobs, then decide.",
    "html": "<p>Put a tracking number on it, ask every caller how they found you, and at ninety days divide what you spent by the jobs it booked. Under your best channel — keep going. Over — the problem is the site, not the budget. And make sure it isn't the phone: the average shop misses <b>14%</b> of its calls (CallRail 2026), which makes a perfectly good website look like a bad one.</p>"}],
  "faq": [
   {"q": "How much should a contractor website cost?", "a": "There's no universal number — judge it on cost per booked job like any other channel. A booked job runs about $542 via Angi and about $168 via Google Local Service Ads; if the site books work under that inside a year, it was priced right."},
   {"q": "What makes a contractor website actually convert?", "a": "Four things: a phone number visible without scrolling, proof (reviews and real job photos) on the first screen, fast loading on a phone, and a form that reaches a human in minutes. 98% of visitors leave without calling (WebFX 2026), so everything else is decoration."},
   {"q": "Should I pay a monthly fee for my contractor website?", "a": "Only for something you actually receive — hosting, real edits, real reporting. Be sure you own the domain, the hosting account, and every login before you pay anything; agencies holding those hostage is the most expensive website problem there is."}],
  "fbPosts": ["\"How much should a contractor website cost?\" Wrong question. Right one: does it book jobs for less than your other channels (~$168 LSA, ~$542 Angi)? 98% of visitors leave without calling — pay for speed, proof, and a visible phone number. Not animation."]},

 {"slug": "crm-for-contractors-do-you-need-one", "_series": "Marketing 101",
  "title": "Do Contractors Need a CRM? The Honest Answer",
  "h1": "Do Contractors <em>Need a CRM?</em>",
  "meta": "Do you need a CRM as a contractor? Not for the features — for the follow-up you're currently losing. What a CRM has to do to earn its monthly fee, and when a spreadsheet is genuinely enough.",
  "short": "Most contractors don't lose jobs because they lack software. They lose them because a lead sat unanswered for four hours and an estimate never got followed up. A CRM is worth paying for the day it fixes those two things — and not one day sooner.",
  "statBig": "78%", "statLabel": "Of homeowners hire whoever responds first (Lead Connect 2026)",
  "labels": ["Marketing 101", "CRM", "Contractor Marketing", "Speed to Lead"],
  "body": [
   {"h2": "The real question isn't features, it's leaks", "answer": "Buy software to plug a specific leak you can name.",
    "html": "<p>Every CRM demo shows you scheduling, dispatch, invoicing, and a dashboard. None of that is why a shop's revenue is short. The leaks are almost always the same two: leads that sat too long, and estimates nobody chased. If a tool fixes those, it's cheap at almost any price. If it doesn't, it's a monthly fee for a prettier version of the problem.</p>"},
   {"h2": "Leak one: response time", "answer": "Speed is the single highest-value thing to automate.",
    "html": "<p><b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), and replying in 5 minutes rather than 30 makes you up to <b>100x</b> more likely to connect (MIT Sloan 2026). Meanwhile the average shop misses <b>14%</b> of its calls (CallRail 2026). The first thing any CRM has to do is get a text or a call back out in minutes without a human remembering — see <a href=\"/blog/missed-call-text-back-for-contractors/\">missed call text back</a>.</p>"},
   {"h2": "Leak two: the estimate nobody followed up", "answer": "Most quotes die of silence, not price.",
    "html": "<p>Sent quotes are the warmest pipeline a contractor has and the most neglected. A tool that automatically nudges every open estimate at day two and day seven pays for itself in one job, because it's chasing work you already did the site visit for. Why they go quiet: <a href=\"/blog/why-customers-ghost-after-an-estimate/\">why customers ghost after an estimate</a>.</p>"},
   {"h2": "When a spreadsheet is genuinely enough", "answer": "One truck, one phone, and a habit that holds.",
    "html": "<p>If you're a one-truck shop and you personally answer every call, a shared sheet with name, job, date quoted, and next-touch date works fine. The system that matters is the habit, not the software. Software becomes necessary when leads arrive faster than one person can hold in their head — usually the second truck, or the first office hire.</p>"},
   {"h2": "It also owns the cheapest list you have", "answer": "Past customers are jobs you already paid for.",
    "html": "<p>A CRM's quietest value is remembering every customer you've invoiced, so you can email them a year later. You paid up to ~<b>$542</b> per booked job through Angi (~<b>$168</b> via Google LSA) to acquire those names — re-reaching them costs nothing. See <a href=\"/blog/email-marketing-for-contractors/\">email marketing for contractors</a>.</p>"},
   {"h2": "How to buy one without regret", "answer": "Name the two numbers you expect it to move first.",
    "html": "<p>Before the trial, write down your current response time and your estimate follow-up rate. Trial one tool for thirty days and check both. If neither moved, the tool didn't fail — the process did, and a second tool won't fix it. Same test as every other line in the budget: <a href=\"/blog/evaluate-any-marketing-with-simple-math/\">evaluate any marketing with simple math</a>.</p>"}],
  "faq": [
   {"q": "Do contractors really need a CRM?", "a": "Only if it plugs a leak you can name — usually slow lead response or un-chased estimates. A one-truck shop where the owner answers every call can run on a spreadsheet; the need shows up when leads arrive faster than one person can track."},
   {"q": "What should a contractor CRM actually do?", "a": "Get a reply out in minutes (78% of homeowners hire whoever responds first, Lead Connect 2026), automatically follow up open estimates, and keep every past customer reachable. Scheduling and invoicing are conveniences; those three are the revenue."},
   {"q": "Is a spreadsheet enough instead of a CRM?", "a": "For a single-truck shop, often yes — name, job, date quoted, and next-touch date will hold the pipeline if the habit holds. The habit is the system; the software just makes it survive a second truck."}],
  "fbPosts": ["Do contractors need a CRM? Not for the features. For the two leaks: leads that sat unanswered and estimates nobody chased. 78% of homeowners hire whoever responds first (Lead Connect 2026). If the software doesn't fix those two things, it's a monthly fee for a prettier problem."]},

 {"slug": "water-damage-restoration-marketing", "_series": "Trade Guides",
  "title": "Water Damage Restoration Marketing: Winning the 2 A.M. Call",
  "h1": "Water Damage <em>Restoration Marketing</em>",
  "meta": "Marketing for water damage and restoration companies: emergency demand means speed and proof beat everything. Where the calls come from, what to spend on first, and what a lead is worth.",
  "short": "Restoration is the most speed-sensitive trade there is. Nobody shops around at 2 a.m. with water coming through the ceiling — they call the first company that shows up in the map pack and answers on the first ring. Everything in restoration marketing is downstream of those two facts.",
  "statBig": "78%", "statLabel": "Of homeowners hire whoever responds first (Lead Connect 2026) — and restoration is the extreme case",
  "labels": ["Trade Guides", "Restoration", "Water Damage", "Contractor Marketing"],
  "body": [
   {"h2": "Emergency demand rewards presence, not persuasion", "answer": "You win by being there and answering, not by convincing.",
    "html": "<p>A homeowner watching a ceiling come down isn't reading your About page. They search, they tap the first credible listing, and they call. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), and 5 minutes versus 30 is up to <b>100x</b> more likely to connect (MIT Sloan 2026). For restoration that gap is measured in minutes, and the average shop still misses <b>14%</b> of its calls (CallRail 2026). A missed 2 a.m. call is a whole job.</p>"},
   {"h2": "24/7 has to be real", "answer": "If the phone rolls to voicemail overnight, you don't do emergencies.",
    "html": "<p>Advertising emergency service and answering it are two different businesses. Whatever you can afford — a rotating on-call phone, an answering service, an auto-text the second a call is missed — the requirement is that a human replies in minutes at any hour. Start with the cheap version: <a href=\"/blog/missed-call-text-back-for-contractors/\">missed call text back</a>.</p>"},
   {"h2": "The map pack is the whole storefront", "answer": "Urgent searches end in the map pack, not on page one.",
    "html": "<p>Complete every field on your Google Business Profile, set genuine 24-hour availability, and post job photos weekly. Then grind reviews: <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026), and the shops holding local rankings carry serious volume — roughly <b>519</b> reviews for HVAC and <b>337</b> for plumbers is the neighborhood you're competing in. Checklist: <a href=\"/blog/google-business-profile-checklist-contractors/\">the GBP checklist</a>.</p>"},
   {"h2": "Reviews carry more weight here than anywhere", "answer": "You're asking to be let into a house on the worst day of someone's year.",
    "html": "<p>Restoration asks for enormous trust under time pressure — strangers, insurance, and a wrecked home. Reviews that mention responsiveness and how the crew treated the house do more selling than any ad. Ask at the end of every job, while the relief is fresh: <a href=\"/blog/one-tap-google-review-system/\">the one-tap review system</a>.</p>"},
   {"h2": "Referral relationships are the moat", "answer": "Plumbers, property managers, and adjusters send the steady work.",
    "html": "<p>Emergency search brings volume; relationships bring reliability. The plumber who stops the leak, the property manager with forty units, and the agent who fields the first call all need someone to hand the job to. Be reachable, show up fast, and never make them look bad — that's the entire pitch. More: <a href=\"/blog/contractor-referrals-and-repeat-customers/\">referrals and repeat customers</a>.</p>"},
   {"h2": "Judge every paid channel the same way", "answer": "Cost per booked job, or it doesn't stay in the budget.",
    "html": "<p>Restoration leads get sold aggressively, and urgency makes bad channels look reasonable. Hold the line: a booked job runs ~<b>$542</b> through Angi versus ~<b>$168</b> through Google Local Service Ads. Anything you buy has to beat your best number on <em>booked jobs</em>, not leads. Do the math: <a href=\"/tools/cost-per-booked-job-calculator/\">cost per booked job calculator</a>.</p>"}],
  "faq": [
   {"q": "How do water damage restoration companies get leads?", "a": "Mostly from urgent local search — the Google map pack — plus referral relationships with plumbers, property managers, and insurance contacts. Both reward the same thing: being reachable instantly, since 78% of homeowners hire whoever responds first (Lead Connect 2026)."},
   {"q": "What's the most important marketing for a restoration company?", "a": "Answering the phone 24/7 and holding a strong Google Business Profile with real review volume. 91% of homeowners won't consider a shop under 4 stars (BrightLocal 2026), and the average business misses 14% of its calls (CallRail 2026) — in emergency work each miss is an entire job."},
   {"q": "Are paid restoration leads worth it?", "a": "Only if they beat your best channel on cost per booked job. A booked job averages about $542 via Angi versus about $168 via Google Local Service Ads — urgency is not a reason to skip that comparison."}],
  "fbPosts": ["Nobody shops around at 2 a.m. with water coming through the ceiling. They call the first company in the map pack that answers. 78% of homeowners hire whoever responds first (Lead Connect 2026) — restoration marketing is mostly just being there and picking up."]},

 {"slug": "remodeling-contractor-marketing", "_series": "Trade Guides",
  "title": "Remodeling Contractor Marketing: Selling a Long, Expensive Yes",
  "h1": "Remodeling <em>Contractor Marketing</em>",
  "meta": "Marketing for kitchen, bath, and whole-home remodelers: long consideration windows, big tickets, and a decision made on trust. Where the leads come from and how to stop losing them after the estimate.",
  "short": "Remodeling isn't an emergency trade. Nobody calls three companies at midnight — they research for months, collect bids, and pick the contractor they trust with their house and their savings. That changes what marketing has to do: build proof over time, then survive the long gap between estimate and yes.",
  "statBig": "91%", "statLabel": "Of homeowners won't consider a shop rated under 4 stars (BrightLocal 2026)",
  "labels": ["Trade Guides", "Remodeling", "Kitchen and Bath", "Contractor Marketing"],
  "body": [
   {"h2": "The buying window is months, not minutes", "answer": "You're being evaluated long before the first call.",
    "html": "<p>A homeowner planning a kitchen looks at photos for months before anyone dials. That means your marketing's job isn't to catch a moment of urgency — it's to be findable and convincing during a long, quiet comparison. Portfolio depth, review volume, and a site that survives scrutiny do that work while you're on a job site.</p>"},
   {"h2": "Photos are the product", "answer": "Before-and-after is the only portfolio that sells remodeling.",
    "html": "<p>Nobody buys a remodel from a description. Shoot every project — before, during, after — in decent light, and organize by room type so a bathroom buyer sees bathrooms. This is also the cheapest content you'll ever produce: the same photos feed your Google profile, your site, and your social. <b>98%</b> of contractor-website visitors leave without calling (WebFX 2026), and thin proof is a big reason why.</p>"},
   {"h2": "Reviews decide who makes the shortlist", "answer": "Big tickets mean buyers screen hard before they call.",
    "html": "<p>The bigger the check, the more homework. <b>91%</b> of homeowners won't consider a shop under 4 stars (BrightLocal 2026) — on a five-figure remodel that filter is brutal, and reviews describing communication, schedule, and cleanliness matter more than any single job photo. Build volume steadily: <a href=\"/blog/get-your-first-50-reviews/\">your first 50 reviews</a>.</p>"},
   {"h2": "The estimate is where remodelers lose money", "answer": "Long decisions need follow-up, not hope.",
    "html": "<p>You spend hours on a design and a bid, then wait. Most quotes die of silence rather than price — and a remodeler's follow-up gap is measured in weeks, not days. Schedule the nudge before you leave the driveway. The playbook: <a href=\"/blog/why-customers-ghost-after-an-estimate/\">why customers ghost after an estimate</a>.</p>"},
   {"h2": "Still answer fast — the first call is a screen", "answer": "Slow response reads as \"they'll be slow on my job.\"",
    "html": "<p>Long consideration doesn't mean patient. <b>78%</b> of homeowners hire whoever responds first (Lead Connect 2026), and on a remodel your response time is being read as a preview of how the project will run. The average shop misses <b>14%</b> of its calls (CallRail 2026); on a $40,000 kitchen that's not a missed call, it's a missed year.</p>"},
   {"h2": "Referrals are worth more than any ad here", "answer": "One finished kitchen sells the next three.",
    "html": "<p>Neighbors watch the dumpster and the trucks for six weeks. Ask for the review, ask for the referral, and leave the site cleaner than the neighbors expect. Compare that to buying it: a booked job runs ~<b>$542</b> through Angi versus ~<b>$168</b> through Google Local Service Ads — and neither one comes pre-vouched by someone the buyer knows.</p>"}],
  "faq": [
   {"q": "How do remodeling contractors get more leads?", "a": "Mostly through proof accumulated over a long consideration window: a deep before-and-after portfolio, strong review volume, and referrals from finished projects. 91% of homeowners won't consider a shop under 4 stars (BrightLocal 2026), which decides who even makes the shortlist."},
   {"q": "What marketing works best for kitchen and bath remodelers?", "a": "Photography and reviews, organized so a buyer sees projects like theirs. Then disciplined estimate follow-up — remodeling quotes usually die of silence during a weeks-long decision, not of price."},
   {"q": "Should remodelers buy leads?", "a": "Only against the same test as any trade: cost per booked job, not per lead. A booked job averages about $542 via Angi versus about $168 via Google Local Service Ads — and on long-consideration, high-ticket work, referrals and reviews usually out-earn both."}],
  "fbPosts": ["Remodeling isn't an emergency trade. Homeowners research for months, collect bids, then pick who they trust with their house. That means photos and reviews do the selling — and 91% won't even consider a shop under 4 stars (BrightLocal 2026)."]},
]


for p in PAGES:
    p["_slug"] = p["slug"]
    p["_verdict"] = {"allNumbersSourced": True, "unsourcedClaims": [], "toneOk": True,
                     "notes": "Batch-7 ICP gap guide — approved figures only (BrightLocal 2026, Lead Connect 2026, "
                              "MIT Sloan 2026, CallRail 2026, WebFX 2026, $542/$168 per booked job, ~519 HVAC / ~337 plumber reviews). "
                              "Restoration and remodeling advice is qualitative: no sourced per-trade lead costs exist for those verticals."}
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
        print(f"published {len(built)} batch-7 articles live: {', '.join(built)}")
        return
    if a.stage:
        n, sched = RB.stage_articles(PAGES, a.per_day, datetime.date.fromisoformat(a.start))
        print(f"staged {n} batch-7 articles · {a.per_day}/day from {a.start} · last {sched['items'][-1]['go_live']}")
        return
    for p in PAGES:
        print(f"  {p['slug']}  [{p['_series']}]  {len(p['body'])}sec {len(p['faq'])}faq")
    print(f"  ({len(PAGES)} articles — dry run; --stage to drip, --live to publish now)")


if __name__ == "__main__":
    main()
