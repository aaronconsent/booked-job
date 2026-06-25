#!/usr/bin/env python3
"""
Seed the Booked Job content queue: generate branded cards for one-liner posts
and write content/queue.json (an ordered drip the publisher works through).

Re-runnable: regenerates cards + queue.json. Does NOT touch posted-state
(publisher tracks that separately in content/state.json).

Archetypes follow STRATEGY.md: lead with proof + grievance/humor, genuine
questions (never "comment YES" bait), links only in first comment, none in the
first ~2 weeks of warm-up.
"""
import json, os
from make_card import make

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "content", "assets")
os.makedirs(ASSETS, exist_ok=True)

# Each post: caption (FB body), optional card {text,label,accent}, optional plain image.
# Card posts go out as IMAGE posts (card carries the punchline; caption invites talk).
POSTS = [
    # --- pricing / quoting drama (cards) ---
    {"id": "pricing-pick-two", "archetype": "pricing-drama",
     "caption": "Quoting, in one sentence. What would you add to the list? 👇",
     "card": {"text": "You want it fast, cheap, and perfect? Pick two and lower your expectations.", "label": "Quoting truth"}},
    {"id": "pricing-insurance", "archetype": "pricing-drama",
     "caption": "Every shop has had this exact conversation. 🤝",
     "card": {"text": "Customer: “Can you do it cheaper?” Me: “Can your insurance do it cheaper?”", "label": "Heard on the job"}},
    {"id": "pricing-low-bid", "archetype": "pricing-drama",
     "caption": "Cheap work isn't cheap. It's just paid for twice. Seen it?",
     "card": {"text": "If the bid's suspiciously low, the disaster's waiting in the drywall.", "label": "Field wisdom"}},

    # --- hack-job / look what the last guy did (UGC prompts) ---
    {"id": "lastguy-worst", "archetype": "hack-job",
     "caption": "What's the worst “the last guy did it” job you've walked into? Photos absolutely encouraged. We'll feature the best (worst) ones. 👇"},
    {"id": "lastguy-rate", "archetype": "hack-job",
     "caption": "Found behind the drywall this week: a garden hose doing a P-trap's job. Rate the previous install 1–10. I'll start — it's on fire. 🔥"},

    # --- stuff homeowners say (cards / questions) ---
    {"id": "homeowner-lie", "archetype": "homeowner-says",
     "caption": "Drop the runner-up below. 👇",
     "card": {"text": "“It was working fine before you got here.” Name a bigger lie.", "label": "Stuff homeowners say"}},
    {"id": "homeowner-drain", "archetype": "homeowner-says",
     "caption": "Plumbers, you're up first. The rest of us are not ready. 👇",
     "card": {"text": "Weirdest thing you've pulled out of a drain? I'll wait.", "label": "Roll call"}},

    # --- trade humor / identity ---
    {"id": "humor-10mm", "archetype": "trade-humor",
     "caption": "It's somewhere in the truck. It's always somewhere in the truck.",
     "card": {"text": "If I had a dollar for every 10mm socket I've lost, I could buy a 10mm socket I'd lose.", "label": "A universal truth"}},
    {"id": "humor-that-guy", "archetype": "trade-humor",
     "caption": "Every jobsite has “that guy.” What's his signature move? 👇"},

    # --- tool wars ---
    {"id": "tools-mil-vs-dewalt", "archetype": "tool-wars",
     "caption": "Settle it in the comments. We're not picking sides. (Yes we are.) 👇",
     "card": {"text": "Milwaukee or DeWalt. Pick a side. The comments are now a war zone.", "label": "New tool day", "accent": "yellow"}},

    # --- business / getting paid (value) ---
    {"id": "biz-slow-season", "archetype": "business",
     "caption": "Slow-season survival rule #1: the time to market is when you're busy, not when the phone stops. The work you book in summer is what fills January. What are you doing now to stay booked through winter? 👇"},
    {"id": "biz-money-leaks", "archetype": "business",
     "caption": "Three ways shops bleed money they never see:\n\n1. Unbilled change orders\n2. “Quick favors” that aren't quick\n3. Not charging for the drive\n\nWhich one's getting you this year? 👇"},

    # --- owner solidarity / labor ---
    {"id": "labor-show-up", "archetype": "owner-solidarity",
     "caption": "Posted for a helper. Three no-shows and one guy who quit because I asked him to sweep. The trades don't have a wage problem — they have a “show up” problem. Who's actually hiring right now? Drop your city. 👇"},

    # --- before/after UGC engine ---
    {"id": "ugc-before-after", "archetype": "before-after",
     "caption": "Drop your best before/after. Any trade — roof, panel, re-pipe, install, cleanout. Let's see the work that doesn't get enough credit. 👇"},
]


def build():
    queue = []
    for p in POSTS:
        item = {"id": p["id"], "archetype": p["archetype"], "caption": p["caption"],
                "image": None, "link": None, "comment": None}
        card = p.get("card")
        if card:
            out = os.path.join(ASSETS, f"{p['id']}.png")
            make(card["text"], card.get("label", ""), out, card.get("accent", "orange"))
            item["image"] = os.path.relpath(out, ROOT)
        queue.append(item)
    qpath = os.path.join(ROOT, "content", "queue.json")
    with open(qpath, "w") as f:
        json.dump({"posts": queue}, f, indent=2, ensure_ascii=False)
    cards = sum(1 for p in POSTS if p.get("card"))
    print(f"Wrote {len(queue)} posts to content/queue.json ({cards} cards, {len(queue)-cards} text).")


if __name__ == "__main__":
    build()
