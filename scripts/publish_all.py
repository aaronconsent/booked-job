#!/usr/bin/env python3
"""
Batch-publish the Marketing 101 courses to YouTube (Booked Job) as UNLISTED,
with title + description + tags + custom thumbnail. Reuses secrets/youtube.env.

    python3 scripts/publish_all.py 1 2 3        # publish specific courses
    python3 scripts/publish_all.py all          # publish all defined
Privacy defaults to unlisted; pass --public to go straight to public.
"""
import argparse, json, os, sys, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
CDIR = os.path.join(ROOT, "content", "course")
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId="

NXT = {1: "Course 2: Know Your Numbers (CPL & CPBJ)", 2: "Course 3: Where Customers Find You",
       3: "Course 4: Your Google Business Profile", 4: "Course 5: Your Website's One Job",
       5: "Course 6: Reviews Are Currency", 6: "Course 7: Should You Pay for Leads?",
       7: "Course 8: Paid Ads Without Burning Cash", 8: "Course 9: Get Found by Google AND AI",
       9: "Course 10: Your Marketing Scorecard", 10: "the full Marketing 101 playlist"}

C = {
 1: ("course1-intro", "What Marketing ACTUALLY Is — For Contractors Who Hate Marketing",
     "You didn't get into the trades to become a marketer. Good news: you don't have to. What marketing actually is — get found, get picked, get booked — why likes and followers don't pay payroll, and the two numbers that decide whether your marketing makes money or bleeds you dry.",
     "contractor marketing,marketing for contractors,home service marketing,plumber marketing,hvac marketing,lead generation,trades business"),
 2: ("course2-intro", "Why Cheap Leads Are Bankrupting Contractors (The 2 Numbers)",
     "A cheap lead that never books is the most expensive lead there is — and most contractors have never run the math. Cost Per Lead vs Cost Per Booked Job: why a low CPL lies, how a slipping close rate doubles your real cost, and how to find your true number from last month in 5 minutes.",
     "cost per lead,cost per booked job,CPL,CPBJ,contractor marketing,lead generation,marketing roi,home services"),
 3: ("course3-intro", "The 5 Doors Every Customer Comes Through (Contractor Marketing)",
     "Customers don't find you by magic — they come through exactly five doors. The five (Google, website, paid ads, lead apps, reviews), which two are free and come first, what a healthy lead mix looks like, and why 100% from one app is a time bomb.",
     "contractor marketing,lead generation,marketing channels,google business profile,angi,thumbtack,home services"),
 4: ("course4-intro", "Get to the Top of Google for Free (Contractors: Your Map Pack)",
     "There's free real estate at the top of every local search — the map pack. What it is and why only 3 spots matter, how to claim your Google Business Profile (free, ~10 min), and why a complete profile beats a blank box every single time.",
     "google business profile,GBP,map pack,local seo,contractor marketing,get found on google,home services"),
 5: ("course5-intro", "Why 98% of People Leave Your Contractor Website (Fix This)",
     "Your contractor website has one job: turn a visitor into a phone call. Most fail — the average site converts 2-3%. The five things that actually work, why a $10k pretty site loses to an ugly one with a giant phone number, and the 3-second test.",
     "contractor website,website conversion,home service marketing,get more calls,mobile website,small business website"),
 6: ("course6-intro", "Why They Call the Other Guy: Reviews Decide It (Course 6)",
     "Before a customer hears your voice, they've already decided whether they trust you — by reading your reviews. Why 9 of 10 read them (and skip you under 4 stars), the three things that matter, why 140 reviews beats 12 even at a higher price, and how to make asking a system.",
     "google reviews,online reputation,contractor marketing,get more reviews,reviews for contractors,local seo"),
 7: ("course7-intro", "Should Contractors Pay for Leads? (Angi, Thumbtack, LSA — The Honest Math)",
     "Should you buy leads? Sometimes yes, sometimes it's a trap. LSA vs shared-lead apps, why a $35 shared lead can cost $700/job while a $120 exclusive costs $342, and how to tell worth-it from trap. Judge by cost per booked job, never the lead price.",
     "should you pay for leads,angi leads,thumbtack,google local service ads,LSA,shared leads,contractor marketing"),
 8: ("course8-intro", "Stop Burning Money on Google Ads (Contractor's First Ad Dollar)",
     "Paid ads are where contractors torch cash fastest — but done right, your first ad dollar comes back with friends. Why search ads catch high intent, the missed-call trap that sets a $200 job on fire, start tiny with tight keywords, and judge by cost per booked job.",
     "google ads for contractors,ppc,search ads,contractor marketing,paid ads,cost per booked job"),
 9: ("course9-intro", "Get Found by Google AND AI (Contractors: The New Front Door)",
     "Getting found used to mean Google. Now a third of people ask a chatbot who to hire. How to show up in both: SEO in plain English, how the AI picks who it names, and why one solid foundation feeds both doors.",
     "seo for contractors,AI search,AEO,chatgpt,google business profile,local seo,contractor marketing"),
 10: ("course10-intro", "Your Marketing Scorecard — Run It Like an Owner (Finale)",
      "The finale of Marketing 101. Put the whole thing on one page: the five numbers to track monthly (CPL, CPBJ, close rate, reviews, response time), how to rate them green/yellow/red, and why knowing your numbers makes you impossible to fleece.",
      "marketing scorecard,kpis,contractor marketing,small business,cost per booked job,home services,marketing dashboard"),
}


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "youtube.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def token(e):
    body = urllib.parse.urlencode({"client_id": e["YT_CLIENT_ID"], "client_secret": e["YT_CLIENT_SECRET"],
        "refresh_token": e["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=body), timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def upload(tok, n, privacy):
    base, title, desc, tags = C[n]
    video = os.path.join(CDIR, base + ".mp4")
    thumb = os.path.join(CDIR, base.replace("-intro", "-thumbnail") + ".png")
    full_desc = f"{desc}\n\nNo jargon. No vests. No bullshit.\n\n▶ Next — {NXT.get(n,'')}\n\U0001f517 booked-job.com"
    size = os.path.getsize(video)
    meta = json.dumps({"snippet": {"title": title[:100], "description": full_desc[:4900],
        "tags": [t.strip() for t in tags.split(",")], "categoryId": "22"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}).encode()
    req = urllib.request.Request(UPLOAD_URL, data=meta, method="POST")
    req.add_header("Authorization", f"Bearer {tok}"); req.add_header("Content-Type", "application/json; charset=UTF-8")
    req.add_header("X-Upload-Content-Type", "video/*"); req.add_header("X-Upload-Content-Length", str(size))
    sess = urllib.request.urlopen(req, timeout=60).headers["Location"]
    put = urllib.request.Request(sess, data=open(video, "rb").read(), method="PUT")
    put.add_header("Content-Type", "video/*"); put.add_header("Content-Length", str(size))
    res = json.loads(urllib.request.urlopen(put, timeout=900).read().decode())
    vid = res.get("id"); st = res.get("status", {}).get("privacyStatus", "?")
    # thumbnail
    tnote = ""
    try:
        treq = urllib.request.Request(THUMB_URL + vid, data=open(thumb, "rb").read(), method="POST")
        treq.add_header("Authorization", f"Bearer {tok}"); treq.add_header("Content-Type", "image/png")
        urllib.request.urlopen(treq, timeout=60); tnote = "thumb ✓"
    except urllib.error.HTTPError as ex:
        tnote = f"thumb FAILED {ex.code} (channel may need verification for custom thumbnails)"
    return {"course": n, "video_id": vid, "url": f"https://youtu.be/{vid}", "privacy": st, "thumb": tnote, "title": title}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("courses", nargs="+")
    ap.add_argument("--public", action="store_true")
    a = ap.parse_args()
    nums = sorted(C) if a.courses == ["all"] else [int(x) for x in a.courses]
    privacy = "public" if a.public else "unlisted"
    e = env()
    for n in nums:
        if not os.path.exists(os.path.join(CDIR, C[n][0] + ".mp4")):
            print(json.dumps({"course": n, "skipped": "mp4 not found yet"})); continue
        try:
            print(json.dumps(upload(token(e), n, privacy)), flush=True)
        except urllib.error.HTTPError as ex:
            print(json.dumps({"course": n, "ERROR": ex.code, "detail": ex.read().decode()[:300]}), flush=True)


if __name__ == "__main__":
    main()
