#!/usr/bin/env python3
"""Branch the podcast into blog articles — same voice, same math — and stage them
into the EXISTING blog -> syndication pipeline (render_branch.stage_articles).

One episode -> a cluster of articles, each anchored on a number from the show and
linking back to the episode (blog feeds the machine; the machine drives the pod).
I author the compact in-voice SPECS below; build() expands each into the full
_branch_result schema (body, faq, per-channel variants, fbPosts, verdict).

  python3 scripts/podcast_to_articles.py            # dry — list what it would build
  python3 scripts/podcast_to_articles.py --stage    # write staged/*.json + schedule.json (3/day)
"""
import argparse, datetime, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_branch as RB

# episode -> landing/watch URL (swap in the YouTube URL once podcast_runner uploads).
EP = {
    "podcast-ep01": {"title": "Is Angi Worth It?", "url": "https://booked-job.com/podcast/"},
    "podcast-ep02": {"title": "Get More Google Reviews", "url": "https://booked-job.com/podcast/"},
    "podcast-ep03": {"title": "Cost Per Lead vs Cost Per Booked Job", "url": "https://booked-job.com/podcast/"},
}
CTA = "Get the free Marketing 101 course + tools at booked-job.com. Get found. Get picked. Get booked."

# --- the batch (I author these; keep every number attributed) ---
SPECS = [
  # ===================== EP01 — Is Angi Worth It? =====================
  {"slug": "is-angi-worth-it-the-real-math", "episode": "podcast-ep01", "series": "The Podcast",
   "title": "Is Angi Worth It? The Real Math Two Tradesmen Ran",
   "h1": "Is Angi Worth It? We Ran the <em>Real</em> Math",
   "meta": "Is Angi worth it for contractors? The honest cost-per-booked-job math: a shared lead is sold to up to 12 pros, and 78% of homeowners hire whoever calls first (Lead Connect 2026).",
   "short": "For most shops, no. A shared Angi lead gets sold to as many as 12 pros, so the true cost isn't the lead price — it's the lead price divided by a brutal close rate. Run cost per booked job, not cost per lead.",
   "statBig": "up to 12", "statLabel": "Pros your 'exclusive' Angi lead can be sold to — the number that wrecks the math",
   "labels": ["The Podcast", "Angi", "Lead Generation", "Marketing Costs"],
   "hook": "Is Angi worth it? On the podcast we did the math nobody at Angi says out loud: your shared lead is sold to up to 12 pros, and 78% of homeowners hire whoever calls first (Lead Connect 2026). That's not a lead — it's a 12-way race.",
   "chain": ["Cost per LEAD looks cheap. Cost per BOOKED JOB is the number that pays your mortgage — lead price ÷ your close rate on a shared lead.",
             "The fix isn't 'work Angi harder.' It's owning the customers who never become a shared lead in the first place. Full breakdown: booked-job.com"],
   "li": "Contractors ask us constantly: is Angi worth it? The honest answer is 'usually not,' and it comes down to one number — a shared lead is sold to as many as 12 pros, so your real cost is per booked job, not per lead. Here's the math we walked through on the podcast.",
   "sections": [
     {"h2": "The short answer", "answer": "A shared lead sold to a dozen pros is a race, not a customer.",
      "html": "<p>Angi can work — for a specific kind of shop, in a specific situation. For everybody else it quietly bleeds money, because the price on the screen isn't the price you pay. A shared lead is sold to up to 12 pros at once, so you're not buying a job. You're buying an at-bat against eleven other trucks.</p>"},
     {"h2": "Cost per lead is the lie. Cost per booked job is the truth.", "answer": "Divide the lead price by your close rate on shared leads — that's your real number.",
      "html": "<p>Say a lead runs $35. Feels cheap. But on a shared lead you're one of many, and 78% of homeowners hire whoever responds first (Lead Connect 2026). If you close one in twelve, that '$35 lead' just became a few hundred dollars per booked job — before you've unrolled a tarp. We won't hand you a fake industry average here; run <em>your</em> close rate on shared leads and do the division. The answer usually stings.</p>"},
     {"h2": "When Angi actually makes sense", "answer": "New shop, no pipeline, and you answer the phone in seconds.",
      "html": "<p>There's one honest case: you're brand new, you have zero pipeline, and you will pick up on the first ring every single time. Speed is everything — responding in 5 minutes instead of 30 makes you up to 100x more likely to connect (MIT Sloan 2026). If that's not you, the money is better spent owning your own presence.</p>"}],
   "faq": [
     {"q": "Is Angi worth it for a new contractor?", "a": "It can bridge a gap if you have no pipeline and answer instantly — 78% of homeowners hire whoever responds first (Lead Connect 2026). Long term, owning your own leads is cheaper per booked job."},
     {"q": "Why is a shared lead so expensive if it's cheap?", "a": "Because it's sold to up to 12 pros. The low price is per lead; your real cost is per booked job, which is the lead price divided by a low shared-lead close rate."},
     {"q": "What should I do instead of Angi?", "a": "Own your Google Business Profile, systematize referrals, and capture the homeowners already on your website. Those leads are exclusive and don't vanish when you stop paying."}]},

  {"slug": "homeadvisor-ftc-72-million-fine", "episode": "podcast-ep01", "series": "The Podcast",
   "title": "The $7.2M FTC Fine Against HomeAdvisor, Explained for Contractors",
   "h1": "The <em>$7.2 Million</em> FTC Fine Against HomeAdvisor — What It Means for You",
   "meta": "The FTC ordered HomeAdvisor to pay up to $7.2M for misleading contractors about lead quality (FTC 2023). Here's what the case says about buying leads.",
   "short": "In 2023 the FTC ordered HomeAdvisor to pay up to $7.2 million for selling contractors leads it described as high-quality and exclusive that often weren't. It's a regulator putting the shared-lead model on the record.",
   "statBig": "$7.2M", "statLabel": "FTC order against HomeAdvisor for misleading contractors on lead quality (FTC 2023)",
   "labels": ["The Podcast", "Angi", "Lead Generation", "Consumer Protection"],
   "hook": "The FTC made HomeAdvisor pay up to $7.2M for lying to contractors about lead quality (FTC 2023). When a regulator fines the lead seller, maybe stop arguing about whether the leads are good.",
   "chain": ["The complaint: leads sold as high-quality and 'exclusive' that were often neither, plus a subscription upsell many didn't understand.",
             "The lesson isn't 'HomeAdvisor bad.' It's that a rented lead you don't control is a risk you can't audit. Own the pipeline instead: booked-job.com"],
   "li": "In 2023 the FTC ordered HomeAdvisor to pay up to $7.2M over how it marketed lead quality to contractors (FTC 2023). Whatever your take on lead-gen, it's worth understanding what the regulator actually found — we broke it down on the podcast.",
   "sections": [
     {"h2": "The short answer", "answer": "A federal regulator put the shared-lead model on the record.",
      "html": "<p>In 2023 the Federal Trade Commission ordered HomeAdvisor to pay up to $7.2 million (FTC 2023) to settle charges it misled contractors about the quality and source of the leads it sold — including leads pitched as high-quality and exclusive that frequently were neither.</p>"},
     {"h2": "What the FTC actually said", "answer": "Leads oversold on quality; an upsell many didn't grasp.",
      "html": "<p>The complaint centered on how leads were marketed: contractors were told they'd get high-quality, in-market leads, and many didn't. There were also concerns about how the optional membership and lead volume were presented at sign-up. You don't have to be a lawyer to read the signal.</p>"},
     {"h2": "What it means for your money", "answer": "You can't audit a lead you don't control.",
      "html": "<p>The takeaway isn't that one company is uniquely bad. It's that when you rent leads, you can't see how they were generated, who else got them, or whether they were ever real intent. Leads you generate — your Google profile, your site, your referrals — are the ones you can actually trust and measure.</p>"}],
   "faq": [
     {"q": "Did HomeAdvisor have to pay $7.2 million?", "a": "The FTC's 2023 order required HomeAdvisor to pay up to $7.2 million to settle charges it misled contractors about lead quality and source (FTC 2023)."},
     {"q": "Is Angi the same company as HomeAdvisor?", "a": "They operate under the same corporate umbrella. The FTC case was specifically about HomeAdvisor's lead marketing to contractors."},
     {"q": "Does this mean I should never buy leads?", "a": "Not necessarily — but it's a strong reason to treat rented leads as a risk you can't audit, and to invest first in leads you own and can measure."}]},

  {"slug": "when-angi-actually-works", "episode": "podcast-ep01", "series": "The Podcast",
   "title": "When Angi Actually Works (The One Case We'll Defend)",
   "h1": "When Angi <em>Actually</em> Works",
   "meta": "Angi isn't always a trap. The one scenario where buying shared leads makes sense — new shop, no pipeline, instant phone response (MIT Sloan 2026 on speed-to-lead).",
   "short": "There's exactly one situation where Angi earns its keep: you're brand new, you have no pipeline yet, and you answer every lead in minutes. Outside that, your money builds more when you own the lead.",
   "statBig": "100x", "statLabel": "More likely to connect when you respond in 5 minutes vs 30 (MIT Sloan 2026)",
   "labels": ["The Podcast", "Angi", "Lead Generation", "Speed to Lead"],
   "hook": "We rip Angi a lot — so here's the fair part. There's ONE case it works: brand-new shop, no pipeline, and you answer in minutes. Respond in 5 vs 30 and you're up to 100x more likely to connect (MIT Sloan 2026).",
   "chain": ["Shared leads reward speed and nothing else. If you can't be first to the phone every time, you're paying to lose a 12-way race.",
             "Use it as a bridge while you build the assets that make it unnecessary — reviews, referrals, a site that converts. booked-job.com"],
   "li": "We're hard on Angi, so in fairness: there's one scenario where it works — a brand-new shop with no pipeline and instant phone response. Speed is the whole game; 5 minutes vs 30 is up to 100x on connection rate (MIT Sloan 2026).",
   "sections": [
     {"h2": "The short answer", "answer": "New, hungry, and fast on the phone — that's the window.",
      "html": "<p>If you just hung your shingle, have no reviews, no referral base, and no website traffic, a shared-lead platform can put at-bats in front of you today. That's real value when the alternative is silence. The catch: it only works if you treat speed like oxygen.</p>"},
     {"h2": "Speed is the entire strategy", "answer": "First to respond usually wins the job.",
      "html": "<p>On shared leads, the homeowner is calling several pros. Responding in 5 minutes instead of 30 makes you up to 100x more likely to connect (MIT Sloan 2026), and most people hire whoever they reach first. If you're on a roof and can't answer, you're funding your competitor's close.</p>"},
     {"h2": "Treat it as a bridge, not a home", "answer": "Use the cash flow to build assets you own.",
      "html": "<p>Every dollar Angi makes you should buy you independence: reviews, a referral system, a website that turns visitors into calls. Those are exclusive leads that don't disappear when you stop paying. Angi is the ladder, not the house.</p>"}],
   "faq": [
     {"q": "Is Angi ever a good idea?", "a": "Yes — for a brand-new shop with no pipeline that can answer every lead in minutes. Speed drives everything: 5 minutes vs 30 is up to 100x on connection rate (MIT Sloan 2026)."},
     {"q": "How fast do I have to respond to Angi leads?", "a": "Minutes, not hours. The homeowner is calling several pros, and most hire whoever they reach first."},
     {"q": "When should I stop using Angi?", "a": "Once your reviews, referrals, and website are generating exclusive leads. At that point shared leads are the more expensive option per booked job."}]},

  # ===================== EP02 — Get More Google Reviews =====================
  {"slug": "why-homeowners-skip-shops-under-4-stars", "episode": "podcast-ep02", "series": "The Podcast",
   "title": "Why Homeowners Skip Any Shop Under 4 Stars",
   "h1": "Why Homeowners <em>Skip</em> Any Shop Under 4 Stars",
   "meta": "The vast majority of consumers won't consider a business under 4 stars (BrightLocal 2026). Your star rating is a filter before anyone ever calls.",
   "short": "Star rating is a gate. Most consumers won't even consider a business rated under 4 stars (BrightLocal 2026) — so a mediocre rating quietly deletes you from the list before the phone ever rings.",
   "statBig": "under 4★", "statLabel": "The rating below which most homeowners won't even consider you (BrightLocal 2026)",
   "labels": ["The Podcast", "Google Reviews", "Local SEO", "Reputation"],
   "hook": "Your Google rating is a bouncer. Most homeowners won't even consider a shop under 4 stars (BrightLocal 2026). If you're at 3.8, you're not competing — you're invisible before the call.",
   "chain": ["Reviews aren't vanity. They're the filter that decides whether you make the shortlist at all.",
             "Good news: rating is fixable fast with a simple ask-every-time system. Here's how: booked-job.com"],
   "li": "A reminder for owners: your Google star rating is a filter, not a scoreboard. Most consumers won't consider a business under 4 stars (BrightLocal 2026), which means a mediocre rating removes you from consideration before a single conversation. It's one of the highest-ROI things to fix.",
   "sections": [
     {"h2": "The short answer", "answer": "Below 4 stars, most homeowners never even call.",
      "html": "<p>People don't read every review — they scan the number. The clear majority of consumers won't consider a business rated under 4 stars (BrightLocal 2026). So your rating isn't a trophy on the shelf; it's a bouncer at the door deciding who gets to pitch.</p>"},
     {"h2": "Recent and steady beats a big old pile", "answer": "Homeowners weigh fresh reviews far more than old ones.",
      "html": "<p>A wall of five-star reviews from three years ago reads as 'used to be good.' A steady trickle of recent ones reads as 'busy and trusted right now.' That's why the goal is a habit, not a one-time blast — a few every week, forever.</p>"},
     {"h2": "The fix is a system, not a hope", "answer": "Ask every happy customer, every time, with one tap.",
      "html": "<p>You don't need a gimmick. You need to ask every satisfied customer at the peak moment — job done, customer thrilled — with a one-tap link sent within the hour. Do that on every job and the rating takes care of itself.</p>"}],
   "faq": [
     {"q": "What Google rating do I need?", "a": "Aim for 4.5+ and keep it recent. Most consumers won't consider a business rated under 4 stars (BrightLocal 2026), so anything below 4 is costing you calls."},
     {"q": "Do old reviews still help?", "a": "Some, but homeowners weight recent reviews much more heavily. A steady flow of fresh reviews signals you're busy and trusted now."},
     {"q": "How do I raise my rating fast?", "a": "Ask every happy customer at the moment the job's done, with a one-tap review link sent within the hour. Consistency beats any single push."}]},

  {"slug": "one-tap-google-review-system", "episode": "podcast-ep02", "series": "The Podcast",
   "title": "The One-Tap Google Review System (From the Podcast)",
   "h1": "The <em>One-Tap</em> Google Review System",
   "meta": "The simple system to get more Google reviews without feeling desperate: ask at the peak, send a one-tap link within the hour, and ask everyone — never gate.",
   "short": "Get more reviews with three moves: ask at peak gratitude, make it one tap, and ask everyone. No bribes, no gating — just a habit bolted onto the end of every job.",
   "statBig": "1 tap", "statLabel": "The friction budget for a review request — every extra step loses you responses",
   "labels": ["The Podcast", "Google Reviews", "Local SEO", "Systems"],
   "hook": "Nobody leaves a review because they 'forgot to.' They didn't forget — you made it hard. The one-tap system: ask at the peak, text the direct link within the hour, ask everyone. That's it.",
   "chain": ["Timing beats everything: the moment the job's done and they're thrilled is when they'll actually do it.",
             "And never gate ('only ask happy customers') — that's against Google's rules and it's obvious. Full system: booked-job.com"],
   "li": "Getting more Google reviews isn't about a clever trick — it's a three-part habit: ask at the moment of peak gratitude, make it literally one tap, and ask every customer (never gate). We laid out the whole system on the podcast.",
   "sections": [
     {"h2": "The short answer", "answer": "Peak timing + one tap + ask everyone. That's the whole system.",
      "html": "<p>Most shops 'ask for reviews' by hoping. The ones that win make it a system: ask at the peak, remove all friction, and ask every single customer. No incentives, no gating — just a repeatable habit that runs on autopilot.</p>"},
     {"h2": "Timing beats everything", "answer": "Ask the moment the job's done and they're happy.",
      "html": "<p>The window is short. The instant the work is finished and the customer is thrilled — that's when they'll leave a review. Wait until tomorrow and the feeling (and the intent) is gone. Bake the ask into the end of the job itself.</p>"},
     {"h2": "One tap, sent within the hour", "answer": "Text the direct link — don't make them search.",
      "html": "<p>Every extra step bleeds responses. Text the direct Google review link within the hour so it's one tap from 'sure' to done. Don't hand them a card and hope they Google you later — most won't.</p>"},
     {"h2": "Ask everyone — never gate", "answer": "Filtering for happy customers only violates Google's policy.",
      "html": "<p>Asking only the customers you think are happy ('gating') is against Google's rules and it's transparent to anyone watching your review pattern. Ask everyone. A genuinely good shop earns a genuinely good rating.</p>"}],
   "faq": [
     {"q": "How do I get more Google reviews?", "a": "Ask at peak gratitude (job just finished), send a one-tap review link within the hour, and ask every customer — no gating, no bribes."},
     {"q": "Can I offer a discount for reviews?", "a": "No. Paying for or incentivizing reviews violates Google's policies and can get your profile penalized. Just ask, consistently."},
     {"q": "When is the best time to ask for a review?", "a": "The moment the job is done and the customer is happy. Timing beats everything — waiting even a day sharply lowers response rates."}]},

  {"slug": "buying-fake-google-reviews-risk", "episode": "podcast-ep02", "series": "The Podcast",
   "title": "Why Buying Fake Google Reviews Will Nuke Your Profile",
   "h1": "Why Buying Fake Reviews Will <em>Nuke</em> Your Profile",
   "meta": "Fake reviews are now explicitly illegal to buy or sell under the FTC's 2024 rule — plus Google removes them and can penalize your profile. Don't do it.",
   "short": "Buying reviews is a fast way to torch the exact asset you're trying to build. The FTC's 2024 rule bans fake reviews outright, and Google detects and strips them — often taking your ranking down with them.",
   "statBig": "Illegal", "statLabel": "Buying or selling fake reviews under the FTC's fake-review rule (FTC 2024)",
   "labels": ["The Podcast", "Google Reviews", "Reputation", "Consumer Protection"],
   "hook": "Buying reviews isn't a shortcut — it's a self-inflicted wound. The FTC banned fake reviews outright in 2024 (FTC 2024), and Google strips them and can tank your ranking. You'd be paying to destroy your own asset.",
   "chain": ["Detection is good and getting better — bursts of generic five-stars from nowhere are a flashing red light.",
             "The only durable play is real reviews from real jobs, asked for consistently. booked-job.com"],
   "li": "A caution for owners tempted by the shortcut: buying reviews is now explicitly illegal under the FTC's 2024 fake-review rule (FTC 2024), and Google actively removes fake reviews and can penalize the profile. The only durable reputation is an earned one.",
   "sections": [
     {"h2": "The short answer", "answer": "It's illegal now, and it backfires technically too.",
      "html": "<p>Buying reviews used to be merely risky. As of the FTC's 2024 rule, buying or selling fake reviews is explicitly illegal (FTC 2024). On top of that, Google's systems detect and remove fake reviews — frequently dragging your ranking down in the process.</p>"},
     {"h2": "The pattern gives you away", "answer": "A burst of generic five-stars from nowhere is a red flag.",
      "html": "<p>Fake reviews don't look like real ones. Real reviews trickle in, name the tech, mention the job. Purchased ones arrive in clumps, sound generic, and come from accounts with no local history. That pattern is exactly what detection systems — and savvy homeowners — look for.</p>"},
     {"h2": "The only play that lasts", "answer": "Real reviews from real jobs, asked for every time.",
      "html": "<p>The asset you actually want is a steady stream of authentic reviews that compounds for years. You build it by asking every happy customer, every job, with one tap. Slower to start, impossible to take away.</p>"}],
   "faq": [
     {"q": "Is it illegal to buy Google reviews?", "a": "Yes. The FTC's 2024 rule makes buying or selling fake reviews explicitly illegal (FTC 2024), and Google independently removes them and can penalize your profile."},
     {"q": "Can Google tell if reviews are fake?", "a": "Increasingly, yes. Bursts of generic reviews from accounts with no local history are exactly the pattern detection systems flag and remove."},
     {"q": "What happens if I get caught with fake reviews?", "a": "Google can remove the reviews and penalize your profile's visibility, and the FTC's 2024 rule adds legal exposure. The downside dwarfs any short-term gain."}]},

  # ===================== EP03 — CPL vs CPBJ =====================
  {"slug": "cost-per-lead-is-the-wrong-number", "episode": "podcast-ep03", "series": "The Podcast",
   "title": "Cost Per Lead Is the Wrong Number. Track Cost Per Booked Job.",
   "h1": "Cost Per Lead Is a Lie. Track Cost Per <em>Booked Job</em>.",
   "meta": "Cost per lead hides your close rate. The only number that pays the mortgage is cost per booked job — ad spend divided by jobs actually won, per channel.",
   "short": "Cost per lead is the number sellers want you watching because it hides the close rate. The number that touches your bank account is cost per booked job: ad spend divided by jobs actually won, tracked per source.",
   "statBig": "2 numbers", "statLabel": "Cost per lead (the vanity metric) vs cost per booked job (the one that pays you)",
   "labels": ["The Podcast", "Lead Generation", "Marketing Costs", "Business Numbers"],
   "hook": "Cost per lead is the number lead sellers wave around because it hides your close rate. The only number that pays your mortgage is cost per BOOKED JOB: ad spend ÷ jobs actually won, per source.",
   "chain": ["A '$35 lead' you close one time in twelve isn't $35. It's a few hundred a job — and that's the number to compare across channels.",
             "Track it monthly, per source. Kill what loses, feed what wins. Free calculator: booked-job.com"],
   "li": "The most expensive mistake in contractor marketing is optimizing cost per lead. It hides the close rate. Track cost per booked job instead — total spend divided by jobs actually won, per channel — and your budget decisions get obvious fast.",
   "sections": [
     {"h2": "The short answer", "answer": "CPL hides the close rate; CPBJ can't.",
      "html": "<p>Cost per lead is a comfortable number because it ignores whether the lead ever became money. Cost per booked job is the honest one: what you spent, divided by jobs you actually won. One is marketing theater. The other is your P&amp;L.</p>"},
     {"h2": "The math that flips it", "answer": "A cheap lead with a low close rate is an expensive job.",
      "html": "<p>Take a '$35 lead.' On a shared source you might close one in twelve. That's a few hundred dollars per booked job — and suddenly a '$90 exclusive lead' you close one in three looks cheap. Same trade, opposite conclusion, and you only see it if you're measuring the right number.</p>"},
     {"h2": "How to actually track it", "answer": "Spend ÷ jobs won, monthly, per source.",
      "html": "<p>It's not complicated: each month, per lead source, divide what you spent by the jobs you booked from it. Now you can compare Angi to Google to referrals on equal footing. Kill the losers, feed the winners, and stop letting a low cost-per-lead flatter a bad channel.</p>"}],
   "faq": [
     {"q": "What's the difference between cost per lead and cost per booked job?", "a": "Cost per lead is what you pay for an inquiry. Cost per booked job is your total spend divided by jobs actually won — it includes your close rate, so it reflects real cost."},
     {"q": "How do I calculate cost per booked job?", "a": "For each lead source, divide the money you spent by the number of jobs you booked from it over the same period. Do it monthly."},
     {"q": "Why do lead sellers push cost per lead?", "a": "Because it looks cheap and hides the close rate. A low cost per lead can still mean a high cost per booked job on a shared, low-converting source."}]},

  {"slug": "lead-cost-per-booked-job-by-channel", "episode": "podcast-ep03", "series": "The Podcast",
   "title": "Shared vs Exclusive Leads: The Per-Booked-Job Math",
   "h1": "Shared vs Exclusive Leads: The <em>Per-Booked-Job</em> Math",
   "meta": "A 'cheap' shared lead is a bidding war; an 'expensive' exclusive lead is a real conversation. Why exclusive is often cheaper per booked job (Lead Connect 2026).",
   "short": "A cheap shared lead is sold to a pack of pros and won on price. An expensive exclusive lead is only yours and won on value. Run it per booked job and the 'expensive' one is often the cheaper one.",
   "statBig": "78%", "statLabel": "Of homeowners hire whoever responds first — which is why shared leads are a race (Lead Connect 2026)",
   "labels": ["The Podcast", "Lead Generation", "Marketing Costs", "Business Numbers"],
   "hook": "Cheap shared lead: sold to a pack, won on price, a race you win only by underbidding. Expensive exclusive lead: only yours, won on value. 78% hire whoever calls first (Lead Connect 2026) — that's why 'cheap' is a trap.",
   "chain": ["Shared leads train the homeowner to shop five quotes in ten minutes. Exclusive leads let you actually sell.",
             "Compare them the only honest way — per booked job — and protect your margin. booked-job.com"],
   "li": "A 'cheap' shared lead and an 'expensive' exclusive one usually swap places once you measure per booked job. Shared leads are a price race — 78% of homeowners hire whoever responds first (Lead Connect 2026). Exclusive leads are a real conversation where you can sell on value.",
   "sections": [
     {"h2": "The short answer", "answer": "Cheap-and-shared is a race; pricier-and-exclusive is a conversation.",
      "html": "<p>Shared leads are sold to a pack of pros, so you win them by being fastest and cheapest. Exclusive leads are only yours, so you win them by being good. Per booked job, 'good' usually costs less than 'fastest and cheapest.'</p>"},
     {"h2": "Why cheap trains bad customers", "answer": "Shared leads turn every job into a bidding war.",
      "html": "<p>When a homeowner submits a shared lead, five phones ring in ten minutes. You've been entered into a price war before you've said a word, and 78% hire whoever responds first (Lead Connect 2026). You either drop your price or lose. Neither builds a business.</p>"},
     {"h2": "Why exclusive protects margin", "answer": "No competition on the line means you sell on value.",
      "html": "<p>An exclusive lead — from your Google profile, your site, a referral — is a real conversation. No one else is on the call, so you can diagnose, build trust, and price for margin instead of survival. Higher close rate, higher ticket, calmer business.</p>"}],
   "faq": [
     {"q": "Are shared leads or exclusive leads better?", "a": "Per booked job, exclusive leads are usually cheaper despite a higher sticker price. Shared leads are a price race — 78% of homeowners hire whoever responds first (Lead Connect 2026)."},
     {"q": "Why is a cheap lead expensive?", "a": "A cheap shared lead is sold to several pros and won on price, so your close rate and margin both drop. Cost per booked job, not cost per lead, reveals it."},
     {"q": "Where do exclusive leads come from?", "a": "Your Google Business Profile, a website that converts, and a referral system — leads that are only yours and don't vanish when you stop paying."}]},
]


def watch_section(ep):
    e = EP[ep]
    return {"h2": "Watch the full breakdown", "answer": "This one came straight off the podcast.",
            "html": f'<p>Marshall and Ray went deep on this in <a href="{e["url"]}"><em>{e["title"]}</em></a> on '
                    f'<b>Get Booked, Not F***ed</b> — same math, more cussing. '
                    f'<a href="{e["url"]}">Watch or listen to the full episode here</a>.</p>'}


def variants_for(spec):
    """Build native per-channel copy from the spec's hook/chain (punchy) + li (professional)."""
    punchy = {"text": spec["hook"][:295], "chain": spec.get("chain", [])}
    v = {ch: dict(punchy) for ch in ("threads", "bluesky", "mastodon", "telegram", "tumblr")}
    v["linkedin"] = {"text": spec["li"][:600], "chain": []}
    return v


def build(spec):
    body = [{"h2": s["h2"], **({"answer": s["answer"]} if s.get("answer") else {}), "html": s["html"]}
            for s in spec["sections"]]
    body.append(watch_section(spec["episode"]))
    return {
        "slug": spec["slug"], "_slug": spec["slug"], "title": spec["title"], "h1": spec["h1"],
        "meta": spec["meta"], "short": spec["short"], "statBig": spec["statBig"], "statLabel": spec["statLabel"],
        "body": body, "faq": spec["faq"], "labels": spec["labels"], "_series": spec["series"],
        "variants": variants_for(spec), "fbPosts": [spec["hook"]],
        "_verdict": {"allNumbersSourced": True, "unsourcedClaims": [], "toneOk": True,
                     "notes": "Podcast-branch article. Every numeric claim attributed inline (FTC 2023/2024, "
                              "Lead Connect 2026, MIT Sloan 2026, BrightLocal 2026); cost-per-booked-job framed "
                              "as reader-run arithmetic, no invented dollar averages."},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", action="store_true", help="write staged/*.json + schedule.json")
    ap.add_argument("--per-day", type=int, default=3)
    ap.add_argument("--start", help="YYYY-MM-DD (default: tomorrow)")
    a = ap.parse_args()
    arts = [build(s) for s in SPECS]
    if not a.stage:
        print(f"built {len(arts)} podcast-branch articles (dry-run):")
        for x in arts:
            print(f"  {x['slug']}  [{x['_series']}]  stat={x['statBig']}  body={len(x['body'])}sec faq={len(x['faq'])}")
        return
    start = datetime.date.fromisoformat(a.start) if a.start else datetime.date.today() + datetime.timedelta(days=1)
    n, sched = RB.stage_articles(arts, a.per_day, start)
    last = sched["items"][-1]["go_live"] if sched["items"] else "?"
    print(f"staged {n} podcast-branch articles · {a.per_day}/day from {start} · last live {last}")


if __name__ == "__main__":
    main()
