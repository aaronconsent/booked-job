# Trades Audience Engine — Strategy (LOCKED 2026-06-25)

Independent, audience-first **content/media brand for the trades** (home-service owners:
plumbers, roofers, HVAC, electricians, landscapers). Its only job: attract service pros,
engage them, feed them content they love → soft-funnel warm audience to **Consent Resolve**
later. Built and grown autonomously by Claude. Brand name TBD (shortlist proposed; "Booked &
Busy" / "Slow Season" front-runners).

## Decisions (from Aaron, 2026-06-25)
- FB automation: **Meta Graph API** long-lived Page token (real autonomous post/comment).
- Paid: **$5–10/day**.
- Brand: **independent content brand**, soft funnel to Consent Resolve (not overt vendor).
- Domain: Claude proposes, Aaron registers. Deploy on **Cloudflare** (same as other sites).

## ICP (from consentresolve.com style-guide voice lock)
Home-service business owner/operator. Phone-first, in a truck, between jobs. Smart, practical,
time-poor, allergic to sales talk, burned by Angi/Thumbtack/HomeAdvisor. Cares about ONE thing:
more booked jobs without getting ripped off. Voice = sharp peer in the trade, 6th–7th grade,
short sentences, money is the through-line, no hype.

## THE GROWTH MODEL (research-backed, 2025–2026)
**Core truth:** follower count no longer gates reach — ~50% of FB feed is from *unconnected*
accounts. A 500-follower page can go viral. So:
- **Reels are the acquisition engine.** 4–6 ORIGINAL Reels/week. Publish same-day (Meta Oct 2025
  gives same-day Reels ~50% more distribution). Native/original = ~3.2× reach of reposts. NO
  TikTok watermarks, no recycled video (FB fingerprints first-uploader).
- **An owned FB Group is the nurture/funnel.** Group member-posts get ~20–40% reach vs 1–6% for
  Pages. Build our own "peer room" for home-service owners. Page = home base, Group = where trust
  compounds, Reels = top of funnel.
- **The website is just home base / link target**, not the growth engine.
- **Creator Fast Track (Mar 2026):** if we build 100K+ on IG/TikTok/YT first and are new to FB
  Reels, FB gives a perpetual distribution boost. Stretch goal, not day-1.

### Cold start: first 100 → 1,000
1. Original Reels 4–6/wk (the lever). 2. Build our Group, seed it. 3. Seed early engagement
legitimately (share Reels from personal profile, reply fast, post into relevant groups).
4. **No outbound links first ~2 weeks** — native posts + short video only. 5. Tiny $1–5 boost on
strong posts, invite reactors to follow. Realistic: ~1k followers in weeks–3mo; ~10k in ~6mo.

### Content archetypes (lead with proof + grievance/identity humor; pure "tips" rank lowest)
- **TIER 1:** "Look what the last guy did" hack-job photos · before/after transformations (only
  Tier-1 format that's also a lead-gen asset) · pricing/quoting drama one-liners.
- **TIER 2:** "Stuff homeowners say" (frame as a real question, NOT "comment YES") · relatable
  trade humor/memes · trade rivalry (Milwaukee vs DeWalt) · "that one guy on every jobsite."
- **TIER 3:** tool talk / #NTD · "can't find good help" owner solidarity · slow-season / getting-
  paid / chasing-invoices (better as blog/email fuel than viral).
- Hook must call out the ICP since paid delivery is broad: "If you run a plumbing/HVAC/roofing
  business…"

### Paid ($5–10/day)
- Page Likes is now a goal INSIDE the **Engagement** objective (not standalone).
- Structure: (1) cheap broad **video-view** campaign (CPV ~$0.01–0.02) to build retargeting pool;
  (2) **retarget warm viewers** (25/50/95% watchers + page/IG engagers) → Engagement/Page-Like,
  exclude existing followers; (3) occasional boost of a PROVEN organic post.
- Targeting: **go broad + Advantage+**, let creative qualify the audience. 8–15 distinct creatives,
  one broad ad set. Live interests: "Small business owners" (workhorse), "Business page admins,"
  "New active business" admins, "Entrepreneur." Owner workaround: CSV custom audience → 1–2% LAL.
- Judge at CAMPAIGN level after 5–7 days, not per-ad after 24h. US B2B CPMs high (~$15–25); weight
  Reels placements (~30–40% cheaper).

### Engagement / no-ban
- FB groups: ~50% value / 50% sharing wins, ZERO CTA in others' groups; designated promo threads
  only; never copy-paste same offer across groups (ban).
- Reddit (if used): account 30+ days, 100+ karma before any promo; ≤5–10 comments/day; trade subs
  (r/HVAC, r/Plumbing, r/electricians) are marketer-hostile — listen + answer as a genuine peer,
  never extract. Verify each sub's rules.
- DMs: never cold-DM a link.

### Risks — stay on the SAFE side (we automate, so this matters)
- **PROHIBITED:** engagement bait ("tag a friend/comment YES/share if"), clickbait, bought
  likes/followers, fake engagement, multi-account abuse. → reach kills or page disable.
- **RISKY (avoid):** engagement pods, bought followers, posting spikes/volume, all-link posting,
  recycled content, clock-like automated timing.
- **SAFE:** official Graph API scheduling (pace requests, ≤100 writes/sec, ~9k-point rate limit,
  60s block if exceeded), friend/group requests ≤20–50/day, **new-page warm-up 10–14 days** (full
  profile+cover+contact+2FA first; ramp posts wk1 2–3 → wk2 3–4 → wk3 5–6, jittered timing).

### Cadence & timing
- 1×/day or ~5×/wk, quality > volume. Tue–Thu best, skip Sat/Sun.
- Test windows: **early AM 5–8am** (blue-collar up early on phone) vs lunch 11am–1pm; evening
  7–9pm for homeowners. A/B with Page Insights.
- Format reach ladder: Reels 12–18% > video 6–10% > photo 4–6% > text/link 2–4%.
- **Links heavily penalized** — non-verified Pages capped at **2 in-body external links/MONTH**
  (Dec 2025). Workaround: **put links in the FIRST COMMENT** ("link in comments"), link-in-bio,
  Stories sticker, or DM. Boosted posts dodge the organic link penalty.

## Autonomous machine (to build once token + domain land)
1. **Website** (Cloudflare, static or Astro) — home base + blog (slow-season/getting-paid/business
   content = SEO + email fuel) + a soft Consent Resolve bridge. Link-in-bio hub.
2. **Content generator** — scheduled job produces a daily/near-daily content batch across the
   archetypes; Reels scripts + image/video assets (HeyGen/ElevenLabs/ffmpeg/PIL pipeline available).
3. **Publisher** — Graph API: post to Page, link-in-first-comment, schedule jittered Tue–Thu AM/lunch.
4. **Engager** — reply to comments, light group participation (value-first, no CTA).
5. **Paid manager** — $5–10/day broad video-view + retarget→follow; weekly campaign-level review.
6. **Reporter** — weekly digest to Aaron: followers, reach, top posts, spend, what to do next.
7. **Group** — create + seed the owned FB Group; route engaged followers in.

## Secrets needed from Aaron (then he walks away)
- Domain (registered) + Cloudflare access.
- Meta: App ID, App Secret, Page ID, long-lived Page access token (scopes: pages_manage_posts,
  pages_read_engagement, pages_manage_engagement, pages_read_user_content).
- Meta Ad Account + payment method (+ API access or agreed $5–10/day cap).
Store as secrets / wrangler secrets — never in the repo.

## Source confidence
High-confidence verified: Creator Fast Track, Dec 2025 link limit, June 2025 targeting
deprecation (Jan 15 2026 cutoff), Reels = primary reach lever, Page Likes folded into Engagement.
Flagged unreliable: BHW "0→50k/90d" (bought followers), dated CPLs, tool-brand interest targeting.
