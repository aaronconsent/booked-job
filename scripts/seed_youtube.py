#!/usr/bin/env python3
"""Seed content/yt_queue.json — YouTube Shorts with SEO metadata (title/desc/tags).
Reuses the faceless video pipeline; vertical + <60s + #Shorts => auto-classified Short."""
import json, os

LINK = "https://booked-job.com/"
BASE_TAGS = ["contractor", "trades", "home service business", "plumber", "roofer", "hvac", "electrician", "small business"]

SHORTS = [
    {"id": "is-angi-worth-it", "hook": "Is Angi worth it?",
     "script": "Is Angi worth it? Here's the math nobody shows you. Angi sells the same lead to up to twelve contractors. So once you count the leads that don't close, your real cost per booked job runs about fourteen hundred to twenty-five hundred dollars. Compare that to roughly two-ninety for a job you win through your own site or referrals. Angi isn't a lead source. It's a tax on not having your own. Follow Booked Job.",
     "title": "Is Angi Worth It for Contractors? The Real Cost Per Job #shorts",
     "description": "The real cost of an Angi lead for contractors — why your leads get shared with up to 12 pros, and what it actually costs per booked job. Full breakdown + free calculator: https://booked-job.com/blog/is-angi-worth-it/\n\n#shorts #contractor #angi #homeadvisor #thumbtack #trades #smallbusiness",
     "tags": BASE_TAGS + ["is angi worth it", "angi leads", "angi alternatives", "homeadvisor", "thumbtack"]},

    {"id": "money-leaks", "hook": "3 ways shops bleed money",
     "script": "Here's three ways your shop bleeds money you never even see. Number one: change orders you never billed for. The job grew, the invoice didn't. Number two: quick favors. There's no such thing as a five minute favor on a paying job. Number three: you're not charging for the drive. Windshield time is still time. Plug those three leaks, and you just gave yourself a raise. Follow Booked Job.",
     "title": "3 Ways Your Contracting Business Bleeds Money #shorts",
     "description": "Three money leaks every service business has — change orders, quick favors, and unbilled drive time. Fix them and give yourself a raise.\n\nMore for service pros: https://booked-job.com/\n\n#shorts #contractor #smallbusiness #trades #pricing",
     "tags": BASE_TAGS + ["contractor pricing", "contractor business", "getting paid"]},

    {"id": "low-bid", "hook": "The cheapest bid costs the most",
     "script": "Ever lose a job to a guy half your price? Let him have it. He lowballs the bid to win it, then cuts corners to survive it. The customer pays twice. Once for the cheap job, once for you to fix it. Your price isn't high. It's honest. Don't chase the bottom. Follow Booked Job.",
     "title": "Why the Cheapest Contractor Bid Costs the Most #shorts",
     "description": "Stop apologizing for your price. The lowball bid always comes back around — and the customer pays twice.\n\nhttps://booked-job.com/\n\n#shorts #contractor #pricing #trades #smallbusiness",
     "tags": BASE_TAGS + ["contractor pricing", "how to price a job", "bidding"]},

    {"id": "stop-renting-leads", "hook": "Stop renting your leads",
     "script": "Here's the trap with lead sites. The day you stop paying, the leads stop. You rented an audience instead of building one. Every dollar into shared leads is a dollar not building something that keeps producing after you turn it off. Own your leads. Own your shop. Follow Booked Job.",
     "title": "Stop Renting Your Leads (Angi, Thumbtack, HomeAdvisor) #shorts",
     "description": "Shared-lead sites rent you an audience. The second you stop paying, the leads vanish. Build channels you own instead.\n\nhttps://booked-job.com/blog/is-angi-worth-it/\n\n#shorts #contractor #angi #leadgeneration #trades",
     "tags": BASE_TAGS + ["lead generation", "angi alternatives", "contractor leads"]},
]


def build():
    root = os.path.join(os.path.dirname(__file__), "..", "content")
    json.dump({"shorts": SHORTS}, open(os.path.join(root, "yt_queue.json"), "w"), indent=2, ensure_ascii=False)
    print(f"wrote content/yt_queue.json ({len(SHORTS)} Shorts)")


if __name__ == "__main__":
    build()
