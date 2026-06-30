#!/usr/bin/env python3
"""
Generate native 9:16 doodle SHORTS scripts (1080x1920) for the Marketing 101
campaign — one flagship short per lesson: HOOK -> PAYOFF -> CTA, ~20-25s.
Writes content/course/shorts/L<n>.json. Render with:
    DOODLE_W=1080 DOODLE_H=1920 python3 scripts/doodle_engine.py content/course/shorts/L2.json content/course/shorts/L2.mp4
"""
import json, os, sys

OUT = os.path.join(os.path.dirname(__file__), "..", "content", "course", "shorts")
CX = 540  # vertical center

# authored campaign copy: hook + payoff per lesson (this IS the new content)
S = {
 1: dict(emph="MARKETING",
   hook_t="NOBODY TAUGHT YOU MARKETING", hook_vo="Nobody ever taught you marketing. Here's the whole thing in twenty seconds.",
   hook_p=[("megaphone", None, "x")],
   pay_t="GET FOUND · PICKED · BOOKED", pay_e="BOOKED",
   pay_vo="It's three things. Get found. Get picked. Get booked. That's it. Likes don't pay payroll.",
   pay_p=[("foundperson","FOUND",None),("reviewstars","PICKED",None),("calendar","BOOKED",None)]),
 2: dict(emph="TRAP",
   hook_t="CHEAP LEADS ARE A TRAP", hook_vo="A cheap lead can be the most expensive thing you buy. Here's the math.",
   hook_p=[("mousetrap", None, None)],
   pay_t="$50 LEAD = $250 JOB", pay_e="$250",
   pay_vo="Fifty bucks a lead sounds great. But if only one in five books, your real cost is two hundred fifty a job. Judge by booked jobs, not leads.",
   pay_p=[("coin","$50 LEAD",None),("dollarstack","$250 JOB",None)]),
 3: dict(emph="FIVE",
   hook_t="ONLY FIVE DOORS", hook_vo="Customers find you through exactly five doors. Most of you use one.",
   hook_p=[("door", None, None)],
   pay_t="THE FREE ONES FIRST", pay_e="FREE",
   pay_vo="Two doors are free. Your Google profile, and your reviews. Build those before you ever pay for a lead.",
   pay_p=[("phonemap","GOOGLE",None),("reviewstars","REVIEWS",None)]),
 4: dict(emph="FREE",
   hook_t="TOP OF GOOGLE, FREE", hook_vo="There's free space at the very top of Google. Most contractors hand it to their competitor.",
   hook_p=[("phonemap", None, None)],
   pay_t="CLAIM IT — 10 MINUTES", pay_e="10",
   pay_vo="It's your Google Business Profile. Claim it, pick the right category, add real photos. Ten minutes, and you beat half your town.",
   pay_p=[("profilecard","YOUR PROFILE","check")]),
 5: dict(emph="98%",
   hook_t="98% LEAVE YOUR SITE", hook_vo="Ninety-eight out of a hundred people leave your website without calling. Here's why.",
   hook_p=[("laptop", None, None)],
   pay_t="ONE GIANT PHONE NUMBER", pay_e="ONE",
   pay_vo="Your site has one job. Get the call. Fast, mobile, a giant tap-to-call number. Pretty doesn't pay. Working pays.",
   pay_p=[("callbutton","TAP TO CALL","check")]),
 6: dict(emph="REVIEWS",
   hook_t="THEY CALL THE 5-STAR GUY", hook_vo="Same price, same skills. They call the guy with more reviews. Every single time.",
   hook_p=[("reviewstars", None, None)],
   pay_t="ASK EVERY HAPPY CUSTOMER", pay_e="EVERY",
   pay_vo="Nine of ten people read reviews first. Text every happy customer a review link the day you finish. Make it a system.",
   pay_p=[("phonestars","REVIEW LINK","check")]),
 7: dict(emph="$300",
   hook_t="$15 LEAD = $300 JOB", hook_vo="That cheap fifteen-dollar lead? It might be costing you three hundred a job.",
   hook_p=[("mousetrap", None, None)],
   pay_t="EXCLUSIVE WINS", pay_e="WINS",
   pay_vo="Shared leads go to five guys. Do the math. The expensive exclusive lead that actually books is the cheaper one.",
   pay_p=[("coin","$15 SHARED","x"),("handshake","EXCLUSIVE","check")]),
 8: dict(emph="BURNING",
   hook_t="STOP BURNING AD MONEY", hook_vo="Paid ads are where contractors torch cash the fastest. Let's not.",
   hook_p=[("moneyfire", None, None)],
   pay_t="ANSWER THE PHONE FIRST", pay_e="FIRST",
   pay_vo="A paid click that rings a phone nobody answers is a two hundred dollar job on fire. Answer every call before you spend a dime.",
   pay_p=[("callbutton","ANSWER","check")]),
 9: dict(emph="AI",
   hook_t="DOES AI KNOW YOU?", hook_vo="A third of people now ask A I who to hire. Does it name you?",
   hook_p=[("robot", None, None)],
   pay_t="ONE FOUNDATION WINS BOTH", pay_e="BOTH",
   pay_vo="The A I just repeats the web. A strong profile, real reviews, a clear site. The same stuff wins Google and the robot.",
   pay_p=[("profilecard","PROFILE",None),("reviewstars","REVIEWS",None)]),
 10: dict(emph="5",
   hook_t="5 NUMBERS RUN YOUR SHOP", hook_vo="Five numbers decide whether your marketing makes money or bleeds you dry.",
   hook_p=[("scorecard", None, None)],
   pay_t="TRACK THEM MONTHLY", pay_e="MONTHLY",
   pay_vo="Cost per lead, cost per booked job, close rate, reviews, response time. Check them monthly and nobody can fleece you.",
   pay_p=[("calculator","TRACK",None),("trafficlight","RATE IT",None)]),
}


def props_layout(plist, y):
    """Place 1-3 props centered across the 1080-wide vertical frame."""
    n = len(plist)
    xs = {1: [CX], 2: [360, 720], 3: [270, 540, 810]}[n]
    w = {1: 380, 2: 300, 3: 240}[n]
    out = []
    for (pid, label, mark), x in zip(plist, xs):
        a = {"id": pid, "w": w, "x": x, "y": y, "anim": "drawOn", "t": 0.4, "sfx": "pop"}
        if label: a["label"] = label
        if mark: a["mark"] = mark
        out.append(a)
    # stagger entries so they build
    for i, a in enumerate(out):
        a["t"] = 0.4 + i * 1.4
    return out


def build(n):
    s = S[n]
    scenes = [
        {"id": "hook", "text": s["hook_t"], "text_y": 170, "emph": s["emph"], "mood": "frustrated",
         "vo": s["hook_vo"], "assets": props_layout(s["hook_p"], 1080)},
        {"id": "payoff", "text": s["pay_t"], "text_y": 170, "emph": s["pay_e"], "mood": "neutral",
         "vo": s["pay_vo"], "assets": props_layout(s["pay_p"], 1120)},
        {"id": "cta", "text": "FREE COURSE", "sub": "ON YOUTUBE", "text_y": 170, "emph": "FREE", "mood": "delighted",
         "vo": "The whole free course is on our channel. Get found, get picked, get booked.",
         "char": {"x": 540, "y": 1080, "scale": 0.92, "hat": "hardhat", "tool": "wrench", "gesture_at": 1}},
    ]
    return {"_doc": f"Marketing 101 SHORT — Lesson {n} ({s['hook_t']}). Vertical 1080x1920.", "scenes": scenes}


def main():
    os.makedirs(OUT, exist_ok=True)
    nums = sorted(S) if (not sys.argv[1:] or sys.argv[1:] == ["all"]) else [int(x) for x in sys.argv[1:]]
    for n in nums:
        json.dump(build(n), open(os.path.join(OUT, f"L{n}.json"), "w"), indent=1)
    print(f"built {len(nums)} short scripts -> content/course/shorts/: " + ", ".join(f"L{n}" for n in nums))


if __name__ == "__main__":
    main()
