#!/usr/bin/env python3
"""Integrate the 30 Booked Job reels (rendered in remotion-studio/out) into the
video pool: copy each to site/reels/bj-<slug>.mp4 and add a pool entry with a
caption. Idempotent (dedup by id). Run again after adding reels.

  python3 scripts/integrate_reels.py            # stage into pool + site/reels
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "..", "remotion-studio", "out")
DEST = os.path.join(ROOT, "site", "reels")
POOL = os.path.join(ROOT, "content", "video_pool.json")
TAGS = ["contractorlife", "smallbusiness", "tradeslife", "homeservices"]

# slug -> (hook, caption-body, comment-bait, extra-tags)
R = {
 "angi": ("$79 for ONE Angi lead", "Angi charges $79 for a single lead — then sells it to 5 other guys. You're not buying a lead, you're buying a bidding war against yourself.", "What's the worst lead-site bill you've paid?", ["angi","leadgen"]),
 "reviews": ("519 reviews to rank", "You need 519 Google reviews to rank #1 in HVAC. Most shops have 12. The guy beating you didn't do better work — he just asked.", "Drop your review count 👇", ["googlereviews","hvac"]),
 "trade": ("Which trade prints money", "Ranking the trades by cash per job: HVAC $2,110, Plumbing $1,714, Electrical $1,434. Painters… we didn't have the heart.", "Where'd your trade land? Fight about it 👇", ["hvac","plumbing","electrician"]),
 "slow": ("Slow season starts in July", "Demand triples Feb→July then falls off a cliff. Everybody markets in July when it's easy. The winners market in February.", "Who's already dreading January?", ["marketing","seasonal"]),
 "cpbj": ("Angi costs $542 per job", "A booked job from Angi runs you $542. The same job from a Google ad? $168. Stop renting your business from a website.", "Worst you've paid a lead site?", ["angi","leadgen"]),
 "speed": ("Answer in 5 minutes", "78% of homeowners hire whoever answers first. Call back in 5 minutes and you're 21× more likely to close. Miss 1 in 7 calls and that's rent walking out the door.", "How fast do you call a lead back?", ["speedtolead","sales"]),
 "ftc": ("The FTC fined HomeAdvisor $7.2M", "You always felt the lead sites were lying. They were — the FTC fined Angi's HomeAdvisor $7.2M for deceiving contractors. You weren't crazy. You were right.", "Ever burned by a lead site?", ["angi","homeadvisor"]),
 "cpl": ("What a lead really costs", "One lead by trade: Electrical $39, HVAC $51, Plumbing $57, Roofing $79. And that's the cheap channel. Know your number or you're flying blind.", "What's a lead cost in your trade?", ["leadgen","hvac","roofing"]),
 "favor": ("'While you're here…'", "Name a more expensive sentence than 'while you're here, can you just take a quick look?' That look is free. Your drive back isn't.", "Worst 'while you're here' you've caught?", ["contractorhumor"]),
 "stars": ("91% won't call under 4 stars", "91% of people won't even call a shop under 4 stars. They filter you out before you ever ring. Your reputation sells before you say a word.", "How many reviews you sitting on?", ["googlereviews","reputation"]),
 "ai": ("Your customer asks ChatGPT", "Your next customer isn't Googling a plumber — they're asking ChatGPT. 35% now start with AI, and it names 3 shops. If you're not one, you don't exist.", "Asked AI who it recommends?", ["ai","aeo","seo"]),
 "scam": ("Guaranteed #1 = scam", "If a marketing company guarantees you #1 on Google — hang up. Google says nobody can promise that. Guaranteed rankings is the tell.", "Got a pitch like this? Drop it 👇", ["marketingscam","seo"]),
 "rev-hvac": ("HVAC: 519 to rank", "HVAC — you need 519 Google reviews to rank #1. The guy beating you just asked every customer. Start asking.", "HVAC pros — how many reviews you got?", ["hvac","hvaclife","googlereviews"]),
 "rev-plumb": ("Plumbers: 337 to rank", "Plumbers — 337 reviews to rank #1 on Google. Ask every time and you lap the whole town in 18 months.", "Plumbers — what's your review count?", ["plumbing","plumberlife","googlereviews"]),
 "rev-roof": ("Roofers: 144 to rank", "Roofers — just 144 reviews to rank #1 on Google. One season of asking. Your competition isn't. Go take the top spot.", "Roofers — you asking for reviews?", ["roofing","rooferlife","googlereviews"]),
 "rev-elec": ("Electricians: 64 to rank", "Electricians — only 64 reviews to rank #1 on Google. Lowest bar in the trades. So why aren't you at the top?", "Electricians — how many reviews?", ["electrician","sparky","googlereviews"]),
 "rev-paint": ("Painters: 109 to rank", "Painters — 109 reviews to rank #1 on Google. Every finished job is a review you forgot to ask for. Snap a photo, ask on the spot.", "Painters — asking for reviews yet?", ["painting","painterlife","googlereviews"]),
 "cheapbid": ("Cheapest bid costs the most", "You lowball to win, then eat change orders and cut corners to survive it. The guy who bid high has margin to do it right. Stop apologizing for your price.", "Ever lose a job on price and dodge a bullet?", ["pricing","contractorlife"]),
 "wordpress": ("Your WordPress site loses jobs", "It's slow, it breaks, every plugin's a door left unlocked. Homeowners bounce in under 90 seconds. If it loads like 2012 they're calling the next guy.", "What's your site built on?", ["webdesign","smallbusiness"]),
 "first10k": ("Your first $10K in marketing", "Don't hand it to an agency. Fix your Google profile (free), get 50 reviews (free), then put money into Local Service Ads. Foundation first, ads second.", "Where'd you waste your first marketing dollars?", ["marketing","smallbusiness"]),
 "yelp": ("Yelp: worth it?", "For most trades, no. Pay-to-play, free leads dry up, reviews get hidden if you don't advertise. Put that energy into Google.", "Yelp: worth it in your trade?", ["yelp","marketing"]),
 "anon98": ("98% of visitors vanish", "98% of the people who visit your site leave without a trace — no call, no form. You paid to get them there and they're gone. Capture them or keep renting.", "Know how many visitors your site gets?", ["marketing","leadgen"]),
 "missedcall": ("Every missed call = the other guy's job", "Shops miss about 1 in 7 calls. That customer isn't leaving a voicemail — they're dialing the next name on Google before you see the notification.", "How many calls you think you miss?", ["missedcalls","sales"]),
 "stormchaser": ("The storm-chaser scam", "After every big storm the roofing scammers roll in — free inspection, out-of-state plates, sign today, insurance games. Real roofers don't chase storms door to door.", "Seen the storm-chasers in your area?", ["roofing","scamalert"]),
 "freecheck": ("The 'free' system check", "That free HVAC check isn't free — it's a sales funnel. The tech is paid to find $4,000 of problems on a system that's fine. Honest work costs money.", "Ever been upsold on a 'free' check?", ["hvac","scamalert"]),
 "fakemaps": ("Someone cloned your Google listing", "Shady lead companies clone your Maps listing, grab your calls, and sell your customers back to you. Search your own name — if there are two of you, one is stealing.", "Ever found a fake listing of your shop?", ["googlemaps","scamalert"]),
 "agency12k": ("$12k/mo and nothing to show", "The same horror story: $12k a month to an agency, no leads, no reports, no access to their own accounts. If they won't show you the work, there is no work.", "Most you've paid for nothing?", ["marketingscam","agency"]),
 "reviews50": ("First 50 reviews, no begging", "Text every happy customer the day after with a direct link. Ask in person before you pull off the drive. People say yes when you make it easy.", "What's your review-ask look like?", ["googlereviews","howto"]),
 "gbp": ("Fix your Google profile", "Most contractors set up their Google Business Profile once and never touch it. Post weekly, answer every review, load photos, list every service. Best free marketing you're ignoring.", "When'd you last update your Google profile?", ["googlebusiness","localseo"]),
 "track": ("Track every lead source", "You can't fix marketing you don't track. Put a different number or QR code on every truck, sign, and ad. Guessing is how you burn $10k a year.", "How do you track where jobs come from?", ["marketing","howto"]),
}


def caption(hook, body, bait, tags):
    hashtags = " ".join("#" + t for t in tags + TAGS)
    return f"{body}\n\n\U0001F447 {bait}\n\n{hashtags}\nbooked-job.com"


def main():
    os.makedirs(DEST, exist_ok=True)
    pool = json.load(open(POOL)) if os.path.exists(POOL) else {"videos": []}
    have = {v["id"] for v in pool["videos"]}
    added = 0; missing = []
    for slug, (hook, body, bait, xt) in R.items():
        src = os.path.join(SRC, f"booked-job-reel-{slug}.mp4")
        if not os.path.exists(src):
            missing.append(slug); continue
        vid = f"bj-{slug}"
        shutil.copy(src, os.path.join(DEST, f"{vid}.mp4"))
        if vid in have:
            for v in pool["videos"]:
                if v["id"] == vid:
                    v["caption"] = caption(hook, body, bait, xt); v["hook"] = hook
            continue
        pool["videos"].append({
            "id": vid, "file": f"site/reels/{vid}.mp4",
            "url": f"https://booked-job.com/reels/{vid}.mp4",
            "hook": hook, "caption": caption(hook, body, bait, xt),
            "tags": xt + TAGS,
        })
        added += 1
    json.dump(pool, open(POOL, "w"), indent=2, ensure_ascii=False)
    print(f"copied {len(R)-len(missing)} reels to site/reels/; pool now {len(pool['videos'])} (+{added} new)")

    # also queue for YouTube Shorts (pre-rendered, vertical <60s + #Shorts)
    YTQ = os.path.join(ROOT, "content", "yt_queue.json")
    ytq = json.load(open(YTQ)) if os.path.exists(YTQ) else {"shorts": []}
    yhave = {s["id"] for s in ytq["shorts"]}
    yadded = 0
    for slug, (hook, body, bait, xt) in R.items():
        vid = f"bj-{slug}"
        if not os.path.exists(os.path.join(DEST, f"{vid}.mp4")):
            continue
        entry = {"id": vid, "hook": hook, "title": f"{hook} #Shorts"[:100],
                 "description": caption(hook, body, bait, xt) + " #Shorts",
                 "tags": xt + TAGS, "video": f"site/reels/{vid}.mp4"}
        if vid in yhave:
            for s in ytq["shorts"]:
                if s["id"] == vid:
                    s.update(entry)
        else:
            ytq["shorts"].append(entry); yadded += 1
    json.dump(ytq, open(YTQ, "w"), indent=2, ensure_ascii=False)
    print(f"yt_queue now {len(ytq['shorts'])} shorts (+{yadded} new)")
    if missing:
        print("MISSING (not rendered?):", missing)


if __name__ == "__main__":
    main()
