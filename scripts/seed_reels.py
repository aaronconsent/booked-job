#!/usr/bin/env python3
"""Seed content/reels_queue.json — the Reels the runner produces + publishes.

PURE ENGAGEMENT (2026-07-17): every script is native, no links, ends on a follow
+ a genuine question. Reels are the acquisition engine (STRATEGY.md), so this is
the renewable pool: reel_runner renders one/day via TTS. build() also PRESERVES
any already-rendered clips (podcast/ad shorts with a `video` field) but strips
booked-job.com / URLs from their descriptions so nothing pushes traffic
off-platform.
"""
import json, os, re

REELS = [
    {"id": "money-leaks", "hook": "3 ways shops bleed money",
     "script": "Here's three ways your shop bleeds money you never even see. Number one: change orders you never billed for. The job grew, the invoice didn't. Number two: quick favors. There's no such thing as a five minute favor on a paying job. Number three: you're not charging for the drive. Windshield time is still time. Plug those three leaks, and you just gave yourself a raise. Follow Booked Job for more.",
     "description": "Three leaks that quietly drain your shop every month. Which one's getting you? 👇 #trades #contractor #smallbusiness"},

    {"id": "low-bid", "hook": "The cheapest bid costs the most",
     "script": "Ever lose a job to a guy half your price? Let him have it. Here's what happens next. He lowballs the bid to win it, then cuts corners to survive it. The customer pays twice. Once for the cheap job, once for you to fix it. Your price isn't high. It's honest. Don't chase the bottom. Follow Booked Job.",
     "description": "Stop apologizing for your price. The lowball always comes back around. #contractor #pricing #trades"},

    {"id": "last-guy", "hook": "Look what the last guy did",
     "script": "You ever pull off a panel and just stop? A garden hose where the p-trap should be. Wire nuts buried in a wall. Caulk holding up a roof. The last guy didn't save them money. He sold them a problem with a delay on it. This is why the cheap call is never the cheap call. Follow Booked Job for more from the field.",
     "description": "Drop your worst 'the last guy did it' find below. 👇 #plumbing #electrician #hvac #trades"},

    {"id": "slow-season", "hook": "Slow season starts in summer",
     "script": "Here's the trap. The phone's ringing now, so you stop marketing. Then January hits and it's dead silent. The work you book in winter was sold in summer. The time to fill the pipe is when you're busy, not when you're broke. Market in your good months. Coast through your slow ones. Follow Booked Job.",
     "description": "The busy season is exactly when you should be marketing. Most shops learn this in January. #contractor #smallbusiness"},

    {"id": "quick-favor", "hook": "The 5-minute favor that isn't",
     "script": "While I'm here, can you just take a quick look at this? Eight words that have cost contractors billions. There's no quick look on a paying job. You look, you touch it, you own it. Be helpful, but put it on the invoice. Your time is the product. Follow Booked Job for more.",
     "description": "'While you're here…' — name a more expensive sentence. 👇 #trades #contractor #getpaid"},

    # ---- added 2026-07-17: expand the renewable reel pool ----
    {"id": "missed-call", "hook": "Every missed call is a booked job",
     "script": "Here's the most expensive sound in your business: your phone ringing while you're under a sink. You don't answer, so they call the next guy. And the next guy books the job. Studies say most homeowners call three shops and hire the first one that picks up. Not the cheapest. The first. If you can't answer, get someone who can. A missed call isn't a missed call. It's a booked job you handed to your competitor. Follow Booked Job.",
     "description": "The first shop to pick up usually wins the job — not the cheapest. Who's answering your phone? 👇 #contractor #trades #smallbusiness"},

    {"id": "cheaper", "hook": "\"Can you do it cheaper?\"",
     "script": "Customer asks, can you do it cheaper? Here's the answer that stops it cold. Sure. I can use cheaper parts, skip the permit, and rush the job. Or I can do it right, once, and you never think about it again. Which one do you actually want? Cheaper isn't a price. It's a decision about who fixes it next year. Follow Booked Job for more.",
     "description": "The one-line answer to 'can you do it cheaper?' What's yours? 👇 #pricing #contractor #trades"},

    {"id": "deposit", "hook": "No deposit, no material order",
     "script": "Learned this one the hard way. Six thousand dollars of custom material sitting in my garage because the customer ghosted after I ordered it. Never again. Now the rule is simple. No deposit, no material order. A serious customer has no problem putting money down. The ones who fight you on a deposit are the ones who'll fight you on the final bill. Protect your cash. Follow Booked Job.",
     "description": "What's your deposit rule? The garage full of unpaid material taught me mine. 👇 #getpaid #contractor #smallbusiness"},

    {"id": "review-timing", "hook": "Ask for the review at 'wow'",
     "script": "Timing is everything on Google reviews. Most guys text a review link three days later, when the customer's already moved on. Here's the fix. The second they say, wow, that looks great, that's your moment. Hand them your phone, right there, review already pulled up. You'll triple your reviews and the reviews rank you higher than any ad. Catch them at wow, not on Wednesday. Follow Booked Job.",
     "description": "The best time to ask for a review is the exact second they say 'wow.' When do you ask? 👇 #googlereviews #contractor #trades"},

    {"id": "speed-to-lead", "hook": "Five minutes or you lose the lead",
     "script": "Here's a number that'll sting. A lead you call back in five minutes is twenty times more likely to book than one you call back in thirty. Twenty times. That lead filled out three forms. Whoever calls first, wins. The other guys are letting leads sit in an inbox till lunch. Beat them on speed and you don't have to beat them on price. Call back fast. Follow Booked Job.",
     "description": "Call a lead back in 5 minutes vs 30 and you're 20x more likely to book it. Speed beats price. #contractor #trades #leads"},

    {"id": "show-up", "hook": "The trades don't have a wage problem",
     "script": "Everybody says the trades have a labor shortage. That's not it. Posted for a helper this week. Three no-shows and one guy who quit because I asked him to sweep. The trades don't have a wage problem. They have a show-up problem. The guys who actually show up, on time, ready to work? They're worth double and they know it. If that's you, you'll never be out of work. Follow Booked Job.",
     "description": "It's not a labor shortage, it's a follow-through shortage. Who's actually reliable and hiring? Drop your city. 👇 #trades #hiring"},

    {"id": "diagnostic-fee", "hook": "Stop waiving the diagnostic fee",
     "script": "Customer says, since you're already here, can you just waive the service fee? Here's why you don't. That fee isn't for showing up. It's for knowing exactly what's wrong in ten minutes when it'd take them ten hours and a wrecked weekend. The knowledge is the product. You spent years learning to make it look easy. Charge for the easy. Follow Booked Job.",
     "description": "The diagnostic fee pays for knowing which part — that's the whole job. Do you hold the line? 👇 #contractor #pricing #trades"},

    {"id": "cash-job", "hook": "\"Cash, and skip the paperwork\"",
     "script": "Customer wants to do it in cash and skip the paperwork. Sounds like a favor. It's a trap. That paperwork, the contract, the invoice, the permit, that's what protects you when they claim you never did the work, or the inspector comes knocking. No paper means no proof. The five percent you save today is the lawsuit you pay for next year. Always paper the job. Follow Booked Job.",
     "description": "'Cash and skip the paperwork' protects them, not you. How do you say no without losing the job? 👇 #contractor #getpaid #trades"},

    {"id": "youtube-expert", "hook": "\"I watched a video, it looked easy\"",
     "script": "Customer tells you, I watched a video, it looked easy. Here's what I've learned to say. It did look easy. That's exactly why I have a job. The video didn't show the corroded fitting behind the wall, the code violation, or the part that's discontinued. You're not paying me to do the easy version. You're paying me so the easy version doesn't turn into a flood at 2 a.m. Follow Booked Job.",
     "description": "It looked easy in the video. That's the whole business model. 😅 #plumbing #electrician #contractor #trades"},

    {"id": "chasing-invoices", "hook": "Three months chasing one invoice",
     "script": "Three months chasing a customer for a four thousand dollar invoice. Sound familiar? Here's the hard truth. You're not a bank. Every week that invoice sits unpaid, it's a loan you didn't agree to give. Set net terms in writing, take a deposit up front, and don't start the next phase until the last one's paid. The nicest thing you can do for your business is get paid on time. Follow Booked Job.",
     "description": "At what point is a $4k unpaid invoice worth the lien? Asking for me. 👇 #getpaid #contractor #smallbusiness"},

    {"id": "milwaukee-dewalt", "hook": "Milwaukee or DeWalt?",
     "script": "Alright, let's start a fight. Milwaukee or DeWalt. Everybody's got a side and nobody's neutral. Red guys swear the torque is unmatched. Yellow guys say theirs never dies. The truth? They're both miles ahead of whatever was in your hand ten years ago. But you already picked a side in your head, didn't you? Tell me which one and why. Follow Booked Job.",
     "description": "Milwaukee or DeWalt. Pick a side. The comments are a war zone. 👇 #tools #contractor #trades"},
]


def _clean(desc):
    """Strip URLs / booked-job.com mentions from an inherited description (pure-engagement)."""
    d = re.sub(r"https?://\S+", "", desc or "")
    d = re.sub(r"\s*(?:at|on|visit|see)?\s*booked-?job\.com\b", "", d, flags=re.I)
    return re.sub(r"\s{2,}", " ", d).strip()


def build():
    root = os.path.join(os.path.dirname(__file__), "..", "content")
    qpath = os.path.join(root, "reels_queue.json")
    os.makedirs(root, exist_ok=True)
    ids = {r["id"] for r in REELS}
    reels = list(REELS)
    # Preserve already-rendered clips (podcast/ad shorts) but strip their links.
    if os.path.exists(qpath):
        for r in json.load(open(qpath)).get("reels", []):
            if r.get("video") and r["id"] not in ids:
                r = dict(r); r["description"] = _clean(r.get("description", "")); r.pop("link", None)
                reels.append(r)
    json.dump({"reels": reels}, open(qpath, "w"), indent=2, ensure_ascii=False)
    pre = sum(1 for r in reels if r.get("video"))
    print(f"wrote content/reels_queue.json ({len(reels)} reels: {len(REELS)} TTS scripts + {pre} pre-rendered, links stripped)")


if __name__ == "__main__":
    build()
