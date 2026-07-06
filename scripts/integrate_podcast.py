#!/usr/bin/env python3
"""Stage rendered podcast VIDEO episodes into the site + build
content/podcast_video_queue.json (SEO title/description/tags) for podcast_runner.py.
NOTE: this is the VIDEO/YouTube track — separate from the existing audio podcast
pipeline (podcast.py -> podcast_queue.json / feed.xml). Do not merge the two."""
import json, os, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "..", "remotion-studio", "out")
DEST = os.path.join(ROOT, "site", "podcast")
BASE = "https://booked-job.com"

TAGS = ["contractor marketing", "home services marketing", "lead generation", "hvac marketing",
        "plumbing marketing", "get more customers", "small business marketing", "booked job"]

# id -> (source filename, SEO title, description)
EPS = {
    "podcast-ep01": (
        "booked-job-podcast-ep01-wide.mp4",
        "Is Angi Worth It for Contractors? The REAL Math | Get Booked, Not F***ed Ep.01",
        "Everybody asks: is Angi worth it? We do the real math — not the sales pitch. Why an Angi "
        "booked job actually costs ~$542 vs ~$168 on Google Local Service Ads, why they refund "
        "15–22% of leads, the $7.2M FTC fine against HomeAdvisor, and the ONE case where Angi makes "
        "sense. Two tradesmen, no fluff.\n\nGet the free playbook: https://booked-job.com\n\n"
        "#contractor #homeservices #angi #leadgeneration"),
    "podcast-ep02": (
        "booked-job-podcast-ep02-wide.mp4",
        "How to Get More Google Reviews (The Contractor Playbook) | Get Booked, Not F***ed Ep.02",
        "91% of people won't even call a shop under 4 stars. Here's the exact system to get more "
        "Google reviews without feeling desperate: ask at the peak, one-tap link, reply to every "
        "review. Why you need ~519 to rank #1 in HVAC, and why buying fake reviews will nuke your "
        "profile.\n\nFree playbook: https://booked-job.com\n\n#googlereviews #contractor #localseo"),
    "podcast-ep03": (
        "booked-job-podcast-ep03-wide.mp4",
        "Cost Per Lead vs Cost Per Booked Job — The 2 Numbers | Get Booked, Not F***ed Ep.03",
        "Cost per lead is the number they WANT you watching — and it's a lie. The only number that "
        "pays your mortgage is cost per booked job. Angi ~$542, Thumbtack ~$250, Google LSA ~$168. "
        "Why a 'cheap' shared lead is a bidding war and an 'expensive' exclusive lead is actually "
        "cheaper — plus the one division that cuts half your ad spend.\n\n"
        "Free playbook: https://booked-job.com\n\n#leadgeneration #contractor #marketingtips"),
}


def main():
    os.makedirs(DEST, exist_ok=True)
    q = {"episodes": []}
    staged = 0
    for eid, (src_name, title, desc) in EPS.items():
        src = os.path.join(SRC, src_name)
        dst = os.path.join(DEST, f"{eid}.mp4")
        if os.path.exists(src):
            shutil.copy(src, dst); staged += 1
        elif not os.path.exists(dst):
            print(f"  skip {eid}: not rendered ({src_name}) and not already staged"); continue
        thumb = f"site/podcast/{eid}-thumb.png"
        q["episodes"].append({
            "id": eid, "title": title, "description": desc, "tags": TAGS,
            "video": f"site/podcast/{eid}.mp4", "url": f"{BASE}/podcast/{eid}.mp4",
            "thumbnail": thumb if os.path.exists(os.path.join(ROOT, thumb)) else None,
        })
    json.dump(q, open(os.path.join(ROOT, "content", "podcast_video_queue.json"), "w"), indent=2, ensure_ascii=False)
    print(f"staged {staged} episodes -> site/podcast/; podcast_video_queue.json: {len(q['episodes'])} episodes")


if __name__ == "__main__":
    main()
