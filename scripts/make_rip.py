#!/usr/bin/env python3
"""'The Rip' — hook-first 9:16 STORY reels from the sourced stats DB. Each rip is a
5-beat narrative rendered by the doodle engine (VO word-timing, kinetic captions,
Torque Marshal, SFX, character + props + backgrounds). Every number traces to
content/stats.json — no invented figures.

Scene schema (rich): text, emph, sub, vo, mood, env|wash, char{x,y,scale,gesture_at,
hat,tool}, assets[{id,w,x,y,anim,at_word,sfx}]. Props are real ids in doodle/assets/.

  python3 scripts/make_rip.py            # render all -> site/reels/rip-*.mp4 + queue
  python3 scripts/make_rip.py angi-rip   # one rip
"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")

# small character parked bottom-left so props own the frame
def C(mood, gesture=2, scale=0.72, x=70, y=1230):
    return {"x": x, "y": y, "scale": scale, "gesture_at": gesture, "hat": "hardhat", "tool": "wrench"}
TY = 230   # caption baseline (top)

RIPS = {
 "angi-rip": {
   "hook": "Angi's dirty math", "cap": "Angi sells your ONE lead to a dozen contractors, then you race to the bottom. Real cost per booked job: $542 vs ~$290 on your own. #contractor #angi #trades",
   "scenes": [
     {"text": "ANGI'S DIRTY MATH", "emph": "MATH", "mood": "frustrated", "env": "street",
      "vo": "Let me show you the math Angi really doesn't want you to see.",
      "assets": [{"id": "leadapp", "w": 470, "x": 560, "y": 520, "anim": "popIn", "at_word": 1, "sfx": "pop"}]},
     {"text": "1 LEAD → 12 TRUCKS", "emph": "12", "mood": "frustrated", "sub": "the same $50 lead",
      "vo": "They take your one fifty-dollar lead, and they sell it to a dozen different contractors.",
      "assets": [{"id": "sharedlead", "w": 430, "x": 300, "y": 500, "anim": "popIn", "at_word": 4, "sfx": "pop"},
                 {"id": "funnelpeople", "w": 520, "x": 520, "y": 900, "anim": "dropIn", "at_word": 10, "sfx": "thunk"}]},
     {"text": "RACE TO THE BOTTOM", "emph": "BOTTOM", "mood": "frustrated", "wash": "blue",
      "vo": "So all of you race each other straight to the bottom on price.",
      "assets": [{"id": "scale", "w": 500, "x": 330, "y": 520, "anim": "popIn", "at_word": 4, "sfx": "pop"},
                 {"id": "moneyfire", "w": 380, "x": 640, "y": 980, "anim": "popIn", "at_word": 8, "sfx": "whoosh"}]},
     {"text": "YOUR REAL COST", "emph": "REAL", "mood": "thinking", "hero": "$542", "sub": "per booked job",
      "vo": "Count the leads that never close, and your real cost per booked job is five hundred forty-two dollars. Win it on your own site? About two-ninety.",
      "assets": []},
     {"text": "OWN YOUR LEADS", "emph": "OWN", "mood": "delighted", "env": "yard",
      "vo": "Stop renting. Own your leads. Follow Booked Job.",
      "assets": [{"id": "mobilesite", "w": 440, "x": 320, "y": 520, "anim": "popIn", "at_word": 2, "sfx": "pop"},
                 {"id": "trophy", "w": 340, "x": 650, "y": 980, "anim": "popIn", "at_word": 5, "sfx": "ding"}]},
   ]},
 "reviews-rip": {
   "hook": "519 reviews to rank", "cap": "Want to rank #1 for HVAC in your town? The top shop has 519 Google reviews. Plumbing 337, roofing 144. You have 12. Ask every customer. #hvac #googlereviews #contractor",
   "scenes": [
     {"text": "WANT TO RANK #1?", "emph": "#1", "mood": "thinking", "env": "city",
      "vo": "Want to rank number one for H-VAC in your town? Here's the real bar.",
      "assets": [{"id": "mappin", "w": 380, "x": 350, "y": 520, "anim": "dropIn", "at_word": 2, "sfx": "thunk"},
                 {"id": "searchbar", "w": 620, "x": 250, "y": 900, "anim": "slideIn", "at_word": 6, "sfx": "zip"}]},
     {"text": "THE TOP SHOP HAS", "emph": "TOP", "mood": "thinking", "hero": "519", "sub": "median reviews to rank",
      "vo": "The median top-ranked H-VAC contractor has five hundred nineteen Google reviews.",
      "assets": [{"id": "reviewstars", "w": 560, "x": 260, "y": 520, "anim": "popIn", "at_word": 6, "sfx": "ding"},
                 {"id": "trophy", "w": 360, "x": 620, "y": 980, "anim": "popIn", "at_word": 8, "sfx": "pop"}]},
     {"text": "PLUMBING 337 · ROOFING 144", "emph": "337", "mood": "thinking", "wash": "yellow",
      "vo": "Plumbers need three thirty-seven. Roofers, one forty-four. Every trade has its bar.",
      "assets": [{"id": "scorecard", "w": 480, "x": 300, "y": 560, "anim": "slideIn", "at_word": 2, "sfx": "zip"}]},
     {"text": "YOU HAVE", "emph": "YOU", "mood": "frustrated", "hero": "12", "sub": "not losing on work — on proof",
      "vo": "So if you've got twelve reviews, you're not losing to better work. You're losing to more proof.",
      "assets": [{"id": "reviewbubble", "w": 400, "x": 340, "y": 520, "anim": "popIn", "at_word": 4, "sfx": "pop"},
                 {"id": "ghost", "w": 340, "x": 660, "y": 950, "anim": "popIn", "at_word": 10, "sfx": "whoosh"}]},
     {"text": "ASK EVERY CUSTOMER", "emph": "EVERY", "mood": "delighted", "env": "yard",
      "vo": "Text the review link the second the job's done. Every single customer. Follow Booked Job.",
      "assets": [{"id": "phonestars", "w": 420, "x": 330, "y": 520, "anim": "popIn", "at_word": 0, "sfx": "ding"},
                 {"id": "handshake", "w": 400, "x": 620, "y": 970, "anim": "popIn", "at_word": 7, "sfx": "pop"}]},
   ]},
 "speed-rip": {
   "hook": "78% hire the first", "cap": "78% of homeowners hire whoever responds FIRST — not the cheapest, not the best. If it rings to voicemail, that job's gone to the next truck. #speedtolead #contractor #trades",
   "scenes": [
     {"text": "HOMEOWNERS HIRE", "emph": "HIRE", "mood": "thinking", "hero": "78%", "sub": "whoever answers first", "env": "suburb",
      "vo": "Seventy-eight percent of homeowners hire whoever answers first.",
      "assets": [{"id": "stopwatch", "w": 420, "x": 330, "y": 520, "anim": "popIn", "at_word": 0, "sfx": "tick"},
                 {"id": "callbutton", "w": 380, "x": 640, "y": 940, "anim": "popIn", "at_word": 6, "sfx": "pop"}]},
     {"text": "NOT BEST. FASTEST.", "emph": "FASTEST", "mood": "thinking", "sub": "first truck to call back",
      "vo": "Not the cheapest. Not the best reviewed. The first truck to call them back.",
      "assets": [{"id": "truck", "w": 520, "x": 290, "y": 560, "anim": "slideIn", "at_word": 8, "sfx": "zip"}]},
     {"text": "RINGS → VOICEMAIL", "emph": "VOICEMAIL", "mood": "frustrated", "wash": "blue",
      "vo": "But if you're under a sink while the phone rings out to voicemail...",
      "assets": [{"id": "phone", "w": 380, "x": 350, "y": 520, "anim": "popIn", "at_word": 5, "sfx": "pop"},
                 {"id": "ghost", "w": 360, "x": 640, "y": 950, "anim": "popIn", "at_word": 8, "sfx": "whoosh"}]},
     {"text": "JOB → NEXT GUY", "emph": "NEXT", "mood": "frustrated", "sub": "gone in one ring",
      "vo": "...that job just went to the next name on Google.",
      "assets": [{"id": "housetruck", "w": 540, "x": 280, "y": 540, "anim": "slideIn", "at_word": 6, "sfx": "zip"}]},
     {"text": "ANSWER THE PHONE", "emph": "ANSWER", "mood": "delighted", "env": "yard",
      "vo": "It's the cheapest lead you'll ever get. Answer the phone. Follow Booked Job.",
      "assets": [{"id": "callbutton", "w": 400, "x": 330, "y": 520, "anim": "popIn", "at_word": 0, "sfx": "ding"},
                 {"id": "thumbsup", "w": 340, "x": 650, "y": 970, "anim": "popIn", "at_word": 6, "sfx": "pop"}]},
   ]},
}

MOODGEST = {0: 1}  # first scene gesture earlier


def script_for(rip):
    scenes = []
    for i, s in enumerate(rip["scenes"]):
        sc = {"id": f"s{i}", "text": s["text"], "text_y": TY, "emph": s.get("emph", ""),
              "vo": s["vo"], "mood": s.get("mood", "neutral"),
              "char": C(s.get("mood", "neutral"), gesture=1 if i == 0 else 3),
              "assets": s.get("assets", [])}
        if s.get("sub"): sc["sub"] = s["sub"]
        if s.get("hero"): sc["hero"] = s["hero"]
        if s.get("env"): sc["env"] = s["env"]
        if s.get("wash"): sc["wash"] = s["wash"]
        scenes.append(sc)
    return {"scenes": scenes}


def render(rid, rip):
    sp = os.path.join(tempfile.mkdtemp(prefix="rip_"), f"{rid}.json")
    json.dump(script_for(rip), open(sp, "w"))
    out = os.path.join(ROOT, "site", "reels", f"rip-{rid}.mp4")
    env = {**os.environ, "DOODLE_W": "1080", "DOODLE_H": "1920"}
    print(f"rendering {rid} (9:16 story) …")
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
    ids = [a for a in sys.argv[1:] if not a.startswith("-")] or list(RIPS)
    for rid in ids:
        if rid not in RIPS:
            print(f"unknown rip {rid}"); continue
        render(rid, RIPS[rid]); queue(rid, RIPS[rid]); print(f"  ✓ rip-{rid}")


if __name__ == "__main__":
    main()
