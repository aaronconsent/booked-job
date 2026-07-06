#!/usr/bin/env python3
"""Stage the Remotion image layer (stat-cards, thumbnails, carousels) into the
site for hosting, build content/image_pool.json for the image-post channels
(Pinterest/IG/FB/LinkedIn/Bluesky/Mastodon), and attach YouTube thumbnails to
the matching yt_queue shorts."""
import json, os, shutil, glob

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "..", "remotion-studio", "out")
SITE = os.path.join(ROOT, "site")
BASE = "https://booked-job.com"
TAGS = ["homeservices", "contractorlife", "trades", "smallbusiness", "marketing"]

# card/thumb slug -> caption (comment-bait built in). Numbers from stat banks.
CAP = {
    "cpbj": "Angi charges $542 for a booked job. Google does the same job for $168. You're not buying leads — you're buying a bidding war. What's the worst you've paid a lead site? 👇",
    "angi": "$79 for ONE Angi lead — and they sold it to 5 other guys. Stop renting your business from a website. Worst lead-site bill you've paid? 👇",
    "reviews": "You need 519 Google reviews to rank #1 in HVAC. Most shops have 12. Your best marketing is free and you're too busy to ask. How many reviews you sitting on? 👇",
    "rev-plumb": "337 reviews to rank #1 in plumbing. The guy beating you just asked every customer. Start today.",
    "rev-roof": "144 reviews to rank #1 in roofing. One season of asking gets you there. Go.",
    "rev-elec": "64 reviews to rank #1 in electrical — the lowest bar in the trades. No excuse.",
    "rev-paint": "109 reviews to rank #1 in painting. Every finished job is a review you didn't ask for.",
    "speed": "78% of homeowners hire whoever answers first. Not the cheapest — the fastest. How fast do you call a lead back? 👇",
    "ftc": "The FTC fined Angi's HomeAdvisor $7.2M for lying to contractors about lead quality. If you ever paid for a dead lead — you weren't crazy. Ever get burned? 👇",
    "stars": "91% of people won't even call a shop under 4 stars. Your reputation sells before you say a word. How many reviews you got? 👇",
    "ai": "35% of customers now ask ChatGPT, not Google. If the AI doesn't name you, you don't exist. Have you asked AI who it recommends? 👇",
    "anon98": "98% of your website visitors leave without a call or a form. That's not a traffic problem — it's a follow-up problem.",
    "missedcall": "1 in 7 calls to home-service shops goes unanswered. Every missed call is the other guy's booked job.",
    "trade": "HVAC prints the biggest ticket in the trades — $2,110 a job. Plumbing $1,714, electrical $1,434. Where'd your trade land? 👇",
}


def stage(subdir, pattern):
    dst = os.path.join(SITE, subdir); os.makedirs(dst, exist_ok=True)
    n = 0
    for f in glob.glob(os.path.join(SRC, pattern)):
        shutil.copy(f, os.path.join(dst, os.path.basename(f))); n += 1
    return n


def main():
    c = stage("cards", "cards/*.png")
    t = stage("thumbs", "thumbs/*.png")
    cr = stage("carousels", "carousels/*.png")
    print(f"staged: {c} cards, {t} thumbs, {cr} carousel slides -> site/")

    CHANS = ["pinterest", "instagram", "facebook", "linkedin", "bluesky", "mastodon"]
    pool = {"images": []}
    for slug, cap in CAP.items():
        img = f"site/cards/bj-{slug}-card.png"
        if not os.path.exists(os.path.join(ROOT, img)):
            continue
        pool["images"].append({"id": f"card-{slug}", "type": "image",
                               "images": [f"{BASE}/cards/bj-{slug}-card.png"],
                               "caption": cap, "tags": TAGS, "channels": CHANS})
    # carousel (ordered slides) — IG/LinkedIn
    cslides = sorted(glob.glob(os.path.join(SITE, "carousels", "leadsites-*.png")),
                     key=lambda p: int(p.rsplit("-", 1)[1].split(".")[0]))
    if cslides:
        pool["images"].append({"id": "carousel-leadsites", "type": "carousel",
                               "images": [f"{BASE}/carousels/{os.path.basename(p)}" for p in cslides],
                               "caption": "5 truths about lead sites nobody selling them will tell you. Save this before you sign anything. 👇",
                               "tags": TAGS, "channels": ["instagram", "linkedin", "facebook"]})
    json.dump(pool, open(os.path.join(ROOT, "content", "image_pool.json"), "w"), indent=2)
    print(f"image_pool.json: {len(pool['images'])} posts")

    # attach YT thumbnails to matching shorts
    YTQ = os.path.join(ROOT, "content", "yt_queue.json")
    if os.path.exists(YTQ):
        yq = json.load(open(YTQ)); attached = 0
        for s in yq["shorts"]:
            slug = s["id"][3:] if s["id"].startswith("bj-") else None
            thumb = f"site/thumbs/bj-{slug}-thumb.png" if slug else None
            if thumb and os.path.exists(os.path.join(ROOT, thumb)):
                s["thumbnail"] = thumb; attached += 1
        json.dump(yq, open(YTQ, "w"), indent=2, ensure_ascii=False)
        print(f"attached {attached} YouTube thumbnails to yt_queue")


if __name__ == "__main__":
    main()
