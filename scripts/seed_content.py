#!/usr/bin/env python3
"""
Seed the Booked Job content queue: generate branded cards for one-liner posts
and write content/queue.json (an ordered drip the publisher works through).

Re-runnable: regenerates cards + queue.json. Does NOT touch posted-state
(publisher tracks that separately in content/state.json).

PURE ENGAGEMENT PLAY (Aaron, 2026-07-17): 100% native engagement archetypes,
NO in-feed links (link lives in bio/pinned only). Goal = mass top-of-funnel
service-pro reach + follower growth via saves/shares/comments, not conversion.
Every post here carries link=None, comment=None by design.

Archetypes follow STRATEGY.md (lead with proof + grievance/identity humor;
genuine questions, NEVER "comment YES" bait; pure "tips" rank lowest):
  T1  hack-job ("look what the last guy did") · before/after · pricing drama
  T2  "stuff homeowners say" · trade humor · tool/brand wars · "that one guy"
  T3  tool talk · owner solidarity / hiring · slow-season & getting-paid
"""
import json, os
from make_card import make

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "content", "assets")
os.makedirs(ASSETS, exist_ok=True)

# Each post: caption (FB body) + optional card {text,label,accent}. Card posts go
# out as IMAGE posts (card carries the punchline; caption invites talk). No links.
POSTS = [
    # ===================== TIER 1 =====================
    # --- pricing / quoting drama ---
    {"id": "pricing-pick-two", "archetype": "pricing-drama",
     "caption": "Quoting, in one sentence. What would you add to the list? 👇",
     "card": {"text": "You want it fast, cheap, and perfect? Pick two and lower your expectations.", "label": "Quoting truth"}},
    {"id": "pricing-insurance", "archetype": "pricing-drama",
     "caption": "Every shop has had this exact conversation. 🤝",
     "card": {"text": "Customer: “Can you do it cheaper?” Me: “Can your insurance do it cheaper?”", "label": "Heard on the job"}},
    {"id": "pricing-low-bid", "archetype": "pricing-drama",
     "caption": "Cheap work isn't cheap. It's just paid for twice. Seen it?",
     "card": {"text": "If the bid's suspiciously low, the disaster's waiting in the drywall.", "label": "Field wisdom"}},
    {"id": "pricing-once-not-twice", "archetype": "pricing-drama",
     "caption": "The part is cheap. Knowing which part isn't. Where do you land on this? 👇",
     "card": {"text": "“Why's it so expensive?” Because I'm fixing it once instead of twice.", "label": "Quoting truth", "accent": "yellow"}},
    {"id": "pricing-diagnostic-fee", "archetype": "pricing-drama",
     "caption": "Customer wants the diagnostic fee waived “since you're already here.” The knowledge IS the product. Do you hold the line or eat it? 👇"},
    {"id": "pricing-callback", "archetype": "pricing-drama",
     "caption": "The other guy's quote and yours aren't the same job. Homeowners find that out on visit #2. 🔧",
     "card": {"text": "The cheap guy's quote didn't include the second visit. Mine did.", "label": "Field wisdom", "accent": "yellow"}},
    {"id": "pricing-friend-price", "archetype": "pricing-drama",
     "caption": "The “friend price” is full price plus the headache. Every shop learns this once. What finally made you stop giving it? 👇"},

    # --- hack-job / "look what the last guy did" (UGC prompts) ---
    {"id": "lastguy-worst", "archetype": "hack-job",
     "caption": "What's the worst “the last guy did it” job you've walked into? Photos absolutely encouraged. We'll feature the best (worst) ones. 👇"},
    {"id": "lastguy-rate", "archetype": "hack-job",
     "caption": "Found behind the drywall this week: a garden hose doing a P-trap's job. Rate the previous install 1–10. I'll start — it's on fire. 🔥"},
    {"id": "lastguy-panel", "archetype": "hack-job",
     "caption": "Opened a panel today and found wire nuts holding things together like a craft project. What's the scariest thing you've found behind a wall? 👇"},
    {"id": "lastguy-flextape", "archetype": "hack-job",
     "caption": "Flex tape on a supply line isn't a repair — it's a countdown. Post the worst “temporary fix” you've inherited. 👇"},
    {"id": "lastguy-diy", "archetype": "hack-job",
     "caption": "Homeowner “saved money” doing it himself. Now I'm charging double to undo it. What's the most expensive DIY you've had to rip back out? 👇"},

    # --- before / after (the Tier-1 format that's also a lead-gen asset) ---
    {"id": "ugc-before-after", "archetype": "before-after",
     "caption": "Drop your best before/after. Any trade — roof, panel, re-pipe, install, cleanout. Let's see the work that doesn't get enough credit. 👇"},
    {"id": "ba-credit", "archetype": "before-after",
     "caption": "Nobody claps when it's done right — the light just turns on, the water just drains. Post the job you were proudest of that no one noticed. 👇"},

    # ===================== TIER 2 =====================
    # --- stuff homeowners say ---
    {"id": "homeowner-lie", "archetype": "homeowner-says",
     "caption": "Drop the runner-up below. 👇",
     "card": {"text": "“It was working fine before you got here.” Name a bigger lie.", "label": "Stuff homeowners say"}},
    {"id": "homeowner-drain", "archetype": "homeowner-says",
     "caption": "Plumbers, you're up first. The rest of us are not ready. 👇",
     "card": {"text": "Weirdest thing you've pulled out of a drain? I'll wait.", "label": "Roll call"}},
    {"id": "homeowner-quick", "archetype": "homeowner-says",
     "caption": "There is no “just quickly.” Every trade knows it. What's the line that makes you brace? 👇",
     "card": {"text": "“While you're here, can you just quickly…” No. No I cannot 'just quickly.'", "label": "Stuff homeowners say"}},
    {"id": "homeowner-youtube", "archetype": "homeowner-says",
     "caption": "It looked easy in the video. That's the whole business model. 😅",
     "card": {"text": "“I watched a video, it looked easy.” It did. That's why I have a job.", "label": "Stuff homeowners say", "accent": "yellow"}},
    {"id": "homeowner-neighbor", "archetype": "homeowner-says",
     "caption": "The magic words: “my neighbor's guy.” Cool. Go call him. 👇",
     "card": {"text": "“My neighbor's guy does it for half.” Great — call your neighbor's guy.", "label": "Heard on the job"}},
    {"id": "homeowner-cash", "archetype": "homeowner-says",
     "caption": "“Can we do cash and skip the paperwork?” The paperwork is what protects THEM. How do you explain that without losing the job? 👇"},

    # --- trade humor / identity ---
    {"id": "humor-10mm", "archetype": "trade-humor",
     "caption": "It's somewhere in the truck. It's always somewhere in the truck.",
     "card": {"text": "If I had a dollar for every 10mm socket I've lost, I could buy a 10mm socket I'd lose.", "label": "A universal truth"}},
    {"id": "humor-that-guy", "archetype": "trade-humor",
     "caption": "Every jobsite has “that guy.” What's his signature move? 👇"},
    {"id": "humor-quick-job", "archetype": "trade-humor",
     "caption": "The “quick 30-minute job” has never once taken 30 minutes. Not once. What's your longest “quick” job? 👇",
     "card": {"text": "There's no such thing as a “quick” 30-minute job. That's a myth told to children.", "label": "A universal truth"}},
    {"id": "humor-one-more", "archetype": "trade-humor",
     "caption": "“Just one more thing before you go.” We all felt that in our spine. 😮‍💨",
     "card": {"text": "“One more thing before you go” is how a 2-hour job becomes a lifestyle.", "label": "A universal truth", "accent": "yellow"}},
    {"id": "humor-clean-shirt", "archetype": "trade-humor",
     "caption": "Put on a clean shirt for ONE estimate and somehow ended up crawling through 40 years of attic insulation. Every time. What's your version? 👇"},
    {"id": "humor-friday", "archetype": "trade-humor",
     "caption": "Friday, 3pm, phone rings — emergency call. You taking it or letting it ring? No wrong answers. 👇"},

    # --- tool / brand wars ---
    {"id": "tools-mil-vs-dewalt", "archetype": "tool-wars",
     "caption": "Settle it in the comments. We're not picking sides. (Yes we are.) 👇",
     "card": {"text": "Milwaukee or DeWalt. Pick a side. The comments are now a war zone.", "label": "New tool day", "accent": "yellow"}},
    {"id": "tools-ford-chevy", "archetype": "tool-wars",
     "caption": "Work-truck edition. Choose your fighter. This will not stay civil. 👇",
     "card": {"text": "Ford or Chevy for a work truck? Choose your fighter.", "label": "New truck day", "accent": "yellow"}},
    {"id": "tools-borrowed", "archetype": "tool-wars",
     "caption": "You lend tools on a jobsite: never / to a chosen few / to anyone with a pulse? The wrong answer is how you lose a $200 impact. 👇"},
    {"id": "tools-burning-truck", "archetype": "tool-wars",
     "caption": "One tool you'd run back into a burning truck for. Go. 👇"},

    # --- "that one guy" ---
    {"id": "guy-radio", "archetype": "that-guy",
     "caption": "Every crew has the guy who guards the radio like it's a hostage situation. What's the ONE song that starts a jobsite fight? 👇"},
    {"id": "guy-measures", "archetype": "that-guy",
     "caption": "We all know him. Tag him (gently). 👇",
     "card": {"text": "Every jobsite has the guy who measures once and cuts three times.", "label": "That one guy"}},

    # ===================== TIER 3 =====================
    # --- owner solidarity / hiring ---
    {"id": "labor-show-up", "archetype": "owner-solidarity",
     "caption": "Posted for a helper. Three no-shows and one guy who quit because I asked him to sweep. The trades don't have a wage problem — they have a “show up” problem. Who's actually hiring right now? Drop your city. 👇"},
    {"id": "labor-ghost", "archetype": "owner-solidarity",
     "caption": "Guy accepted the job, said “see you Monday,” vanished. It's not a labor shortage, it's a follow-through shortage. Who's reliable and actually looking? Drop your city. 👇"},
    {"id": "labor-good-help", "archetype": "owner-solidarity",
     "caption": "Hardest part of running a shop this year: finding work / finding good help / getting paid on time? Pick your poison. 👇"},

    # --- slow season / getting paid ---
    {"id": "biz-slow-season", "archetype": "business",
     "caption": "Slow-season survival rule #1: the time to market is when you're busy, not when the phone stops. The work you book in summer fills January. What are you doing NOW to stay booked through winter? 👇"},
    {"id": "biz-money-leaks", "archetype": "business",
     "caption": "Three ways shops bleed money they never see:\n\n1. Unbilled change orders\n2. “Quick favors” that aren't quick\n3. Not charging for the drive\n\nWhich one's getting you this year? 👇"},
    {"id": "biz-chasing-invoices", "archetype": "business",
     "caption": "Third month chasing a customer for a $4k invoice. At what point is it worth the lien? Asking for me, honestly. 👇"},
    {"id": "biz-deposit", "archetype": "business",
     "caption": "No deposit, no material order. I learned that with $6k of custom material sitting in my garage. What's your deposit rule? 👇"},
    {"id": "biz-review-timing", "archetype": "business",
     "caption": "The best time to ask for the Google review is the second the customer says “wow, looks great” — not three days later by text. When do YOU ask? 👇"},

    # ---- added 2026-07-17: library expansion, batch 2 ----
    {"id": "pricing-scope-creep", "archetype": "pricing-drama",
     "caption": "Job was quoted for one thing. Now it's “while you're at it” five times over. When do you re-quote vs. eat it? 👇"},
    {"id": "lastguy-caulk", "archetype": "hack-job",
     "caption": "Caulk is not a structural material. Somebody tell the last guy. 👇",
     "card": {"text": "Found a roof held together with caulk and hope. Caulk is not a structural material.", "label": "Field wisdom"}},
    {"id": "lastguy-extension-cord", "archetype": "hack-job",
     "caption": "AC unit wired off an extension cord run through a window. Rate it 1–10. I'll start: call the fire department. 🔥 👇"},
    {"id": "homeowner-warranty", "archetype": "homeowner-says",
     "caption": "Every trade has gotten this one. 😮‍💨",
     "card": {"text": "“Is this under warranty?” It's a 30-year-old unit held together by dust. No.", "label": "Stuff homeowners say", "accent": "yellow"}},
    {"id": "homeowner-son", "archetype": "homeowner-says",
     "caption": "“My son said it should be cheaper.” Cool — have your son do it. What's the funniest “my ___ said” you've gotten? 👇"},
    {"id": "homeowner-permit", "archetype": "homeowner-says",
     "caption": "“Do we really need a permit?” Yes — and here's the version where you find out why at resale. How do you explain permits without the eye-roll? 👇"},
    {"id": "humor-gas-station", "archetype": "trade-humor",
     "caption": "You take a real lunch, or eat a gas-station sandwich doing 75 to the next call? Be honest. 👇"},
    {"id": "humor-porta-potty", "archetype": "trade-humor",
     "caption": "IYKYK. Roofers in July, you have it worst. 👇",
     "card": {"text": "The jobsite porta-potty in July is a punishment invented by people who've never used one.", "label": "A universal truth"}},
    {"id": "humor-monday", "archetype": "trade-humor",
     "caption": "Monday, first call is a callback on someone else's screwup. You laughing or crying? 👇"},
    {"id": "tools-loyalty", "archetype": "tool-wars",
     "caption": "You ride-or-die one battery platform, or a “whatever's on sale” mercenary? There's no in-between. 👇"},
    {"id": "tools-lost-tape", "archetype": "tool-wars",
     "caption": "Name the tool you lose the most. It's the tape. It's always the tape. 👇",
     "card": {"text": "Nobody in the history of the trades has finished a job with the tape measure they started with.", "label": "A universal truth", "accent": "yellow"}},
    {"id": "guy-safety", "archetype": "that-guy",
     "caption": "Every crew has the guy who runs the safety meeting AND the guy who's the reason for the next one. Which are you? 👇"},
    {"id": "labor-phone", "archetype": "owner-solidarity",
     "caption": "Helper's on his phone more than his tools. You say something, or let the work speak for itself? 👇"},
    {"id": "biz-fire-customer", "archetype": "business",
     "caption": "Best money move some years is firing your worst customer — the one who haggles, pays late, and refers people just like them. Ever done it? 👇"},
    {"id": "biz-truck-payment", "archetype": "business",
     "caption": "New wrapped truck: rolling billboard that pays for itself, or a payment that owns you? Where do you land? 👇"},
    {"id": "biz-gbp-stale", "archetype": "business",
     "caption": "Half of you have a Google Business Profile you set up once in 2019 and never touched. When's the last time you posted on it? 👇"},
    {"id": "ba-nobody-sees", "archetype": "before-after",
     "caption": "The jobs you're proudest of are the ones nobody ever thinks about again. Post one. 👇",
     "card": {"text": "The best work in the trades is the work nobody ever sees again.", "label": "Field wisdom"}},
]


def build():
    queue = []
    for p in POSTS:
        card = p.get("card")
        # `text` = the full native post for text-only channels (Threads/Bluesky/
        # LinkedIn), which can't show the card image: punchline + the invite.
        # FB (publisher.py) ignores `text` and uses caption + the card image.
        text = f"{card['text']}\n\n{p['caption']}" if card else p["caption"]
        item = {"id": p["id"], "archetype": p["archetype"], "caption": p["caption"],
                "text": text, "image": None, "link": None, "comment": None}
        if card:
            out = os.path.join(ASSETS, f"{p['id']}.png")
            make(card["text"], card.get("label", ""), out, card.get("accent", "orange"))
            item["image"] = os.path.relpath(out, ROOT)
        queue.append(item)
    qpath = os.path.join(ROOT, "content", "queue.json")
    with open(qpath, "w") as f:
        json.dump({"posts": queue}, f, indent=2, ensure_ascii=False)
    cards = sum(1 for p in POSTS if p.get("card"))
    print(f"Wrote {len(queue)} pure-engagement posts to content/queue.json "
          f"({cards} cards, {len(queue)-cards} text, 0 links).")


if __name__ == "__main__":
    build()
