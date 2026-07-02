#!/usr/bin/env python3
"""'The Rip' — hook-first 9:16 data reels from the sourced stats DB. Authors a
doodle-engine script (hook → payoff → CTA) per rip and renders it VERTICAL
(DOODLE_W=1080 DOODLE_H=1920) using the existing doodle engine (VO word-timing,
kinetic captions, Torque Marshal, SFX, the character). Every number traces to
content/stats.json — no invented figures.

  python3 scripts/make_rip.py            # render all rips -> site/reels/rip-*.mp4 + queue
  python3 scripts/make_rip.py angi-rip   # a single rip
  python3 scripts/make_rip.py --list
"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")

# Each scene: text (kinetic on-screen phrase), emph (word to punch), vo (Torque Marshal
# narration), mood. All numbers below are in content/stats.json.
RIPS = {
 "angi-rip": {
   "hook": "Angi's $542 secret", "cap": "Angi sells your lead to a dozen guys, then you race to the bottom. The real cost per booked job? $542. #contractor #angi #trades",
   "scenes": [
     {"text": "ANGI: $542 A JOB", "emph": "$542", "mood": "frustrated", "vo": "Here's the number Angi really doesn't want you to see."},
     {"text": "SOLD TO 12 GUYS", "emph": "12", "mood": "frustrated", "vo": "They sell your fifty-dollar lead to a dozen contractors, then you race each other to the bottom on price."},
     {"text": "REAL COST: $542", "emph": "$542", "mood": "thinking", "vo": "Once you count the leads that never close, your real cost per booked job is five hundred forty two dollars. Win it through your own site? About two ninety."},
     {"text": "STOP RENTING LEADS", "emph": "RENTING", "mood": "delighted", "vo": "Angi isn't a lead source. It's a tax on not having your own. Follow Booked Job."},
   ]},
 "reviews-rip": {
   "hook": "519 reviews to rank", "cap": "Want to rank #1 for HVAC in your town? The top shop has 519 Google reviews. Here's the real bar by trade. #hvac #contractor #googlereviews",
   "scenes": [
     {"text": "519 REVIEWS TO RANK", "emph": "519", "mood": "thinking", "vo": "Want to rank number one for H-VAC in your town? Here's the actual bar."},
     {"text": "THE TOP SHOP HAS 519", "emph": "519", "mood": "thinking", "vo": "The median top-ranked H-VAC contractor has five hundred nineteen Google reviews. Plumbers, three thirty seven. Roofers, one forty four."},
     {"text": "YOU HAVE 12", "emph": "12", "mood": "frustrated", "vo": "So if you've got twelve reviews, you're not losing to better work. You're losing to more proof."},
     {"text": "ASK EVERY CUSTOMER", "emph": "EVERY", "mood": "delighted", "vo": "Text the review link the second the job's done. Every single customer. Follow Booked Job."},
   ]},
 "speed-rip": {
   "hook": "78% hire the first", "cap": "78% of homeowners hire whoever responds first — not the cheapest, not the best. If it rings to voicemail, that job's gone. #speedtolead #contractor #trades",
   "scenes": [
     {"text": "78% HIRE THE FIRST", "emph": "78%", "mood": "thinking", "vo": "Seventy-eight percent of homeowners hire whoever answers first."},
     {"text": "NOT THE BEST. THE FASTEST.", "emph": "FASTEST", "mood": "thinking", "vo": "Not the cheapest. Not the best reviewed. The first truck to call them back."},
     {"text": "YOU'RE AT VOICEMAIL", "emph": "VOICEMAIL", "mood": "frustrated", "vo": "And if you're under a sink while the phone rings out to voicemail, that job just went to the next name on Google."},
     {"text": "ANSWER THE PHONE", "emph": "ANSWER", "mood": "delighted", "vo": "It's the cheapest lead you'll ever get. Answer the phone. Follow Booked Job."},
   ]},
}

# 9:16 layout: kinetic caption in the upper third, BIG character filling the lower
# two-thirds (fills the frame — no dead space).
CHAR = {"x": 190, "y": 640, "scale": 1.45, "gesture_at": 2, "hat": "hardhat", "tool": "wrench"}
TEXT_Y = 320


def script_for(rip):
    scenes = []
    for i, s in enumerate(rip["scenes"]):
        scenes.append({"id": f"s{i}", "text": s["text"], "text_y": TEXT_Y, "emph": s.get("emph", ""),
                       "mood": s.get("mood", "neutral"), "vo": s["vo"],
                       "char": {**CHAR, "gesture_at": 1 if i == 0 else 3}})
    return {"scenes": scenes}


def render(rid, rip):
    sp = os.path.join(tempfile.mkdtemp(prefix="rip_"), f"{rid}.json")
    json.dump(script_for(rip), open(sp, "w"))
    out = os.path.join(ROOT, "site", "reels", f"rip-{rid}.mp4")
    env = {**os.environ, "DOODLE_W": "1080", "DOODLE_H": "1920"}
    print(f"rendering {rid} (9:16) …")
    subprocess.run([sys.executable, os.path.join(HERE, "doodle_engine.py"), sp, out], env=env, check=True)
    return out


def queue(rid, rip):
    url = f"https://booked-job.com/reels/rip-{rid}.mp4"
    rq = json.load(open(os.path.join(ROOT, "content", "reels_queue.json")))
    if not any(r["id"] == f"rip-{rid}" for r in rq["reels"]):
        rq["reels"].append({"id": f"rip-{rid}", "hook": rip["hook"], "description": rip["cap"], "video": f"site/reels/rip-{rid}.mp4"})
        json.dump(rq, open(os.path.join(ROOT, "content", "reels_queue.json"), "w"), indent=2)
    vp = json.load(open(os.path.join(ROOT, "content", "video_pool.json")))
    if not any(v["id"] == f"rip-{rid}" for v in vp["videos"]):
        vp["videos"].append({"id": f"rip-{rid}", "file": f"site/reels/rip-{rid}.mp4", "url": url, "hook": rip["hook"], "caption": rip["cap"]})
        json.dump(vp, open(os.path.join(ROOT, "content", "video_pool.json"), "w"), indent=2)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--list" in sys.argv:
        print("\n".join(RIPS)); return
    ids = args or list(RIPS)
    for rid in ids:
        if rid not in RIPS:
            print(f"unknown rip {rid}"); continue
        out = render(rid, RIPS[rid]); queue(rid, RIPS[rid])
        print(f"  ✓ {out}")


if __name__ == "__main__":
    main()
