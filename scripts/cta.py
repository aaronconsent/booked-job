#!/usr/bin/env python3
"""Follow/subscribe CTAs appended to video captions at post time.

Why: 13k+ ad video views converted to ~3 followers — views were never asked to
do anything. Every outbound video caption now ends with a platform-appropriate
follow CTA. Variants rotate (keyed by caption hash) so feeds don't look botted;
`append()` is length-safe and no-ops if the caption already asks for a follow.
"""

VARIANTS = {
    "follow": [                       # FB / IG / TikTok / Tumblr / Bluesky
        "➕ Follow Booked Job for the real numbers behind getting booked.",
        "🛠️ Follow for the math nobody in marketing shows you.",
        "➕ Follow — we do this every day. Your pipeline will thank you.",
        "🔧 Follow Booked Job. Get found. Get picked. Get booked.",
    ],
    "subscribe": [                    # YouTube
        "🔔 Subscribe for the real numbers behind getting booked — new breakdowns every week.",
        "🔔 Subscribe — we run the math the lead sites won't.",
    ],
    "professional": [                 # LinkedIn
        "Follow Booked Job for the numbers behind contractor marketing.",
        "Follow for weekly contractor-marketing math — no fluff.",
    ],
    "save": [                         # Pinterest
        "📌 Save this + follow Booked Job for more trade math.",
    ],
}
PLATFORM_KIND = {
    "facebook": "follow", "fb": "follow", "ig": "follow", "instagram": "follow",
    "tiktok": "follow", "tumblr": "follow", "bluesky": "follow",
    "youtube": "subscribe", "yt": "subscribe",
    "linkedin": "professional", "pinterest": "save",
}
_ASKED = ("follow", "subscribe", "save this")


def pick(platform, seed_text=""):
    kind = PLATFORM_KIND.get(platform, "follow")
    pool = VARIANTS[kind]
    return pool[sum(map(ord, seed_text[:40])) % len(pool)]


def append(caption, platform, max_len=None):
    """Caption + platform CTA. No-op if it already asks; trims the CAPTION (never
    the CTA) when a max_len is given."""
    cap = (caption or "").rstrip()
    if any(w in cap.lower() for w in _ASKED):
        return cap if max_len is None else cap[:max_len]
    cta_line = pick(platform, cap)
    if max_len is not None and len(cap) + len(cta_line) + 2 > max_len:
        cap = cap[: max_len - len(cta_line) - 2].rstrip()
    return f"{cap}\n\n{cta_line}"
