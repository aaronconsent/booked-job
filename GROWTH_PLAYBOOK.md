# Booked Job — Per-Channel Growth & Engagement Playbook

Research date: 2026-06-26. Sources: official API docs + practitioner research (Reddit, BlackHatWorld,
SEO/AEO/growth blogs, 2025-26). Context: **all accounts at ZERO**, autonomous machine, soft-funnel to
Consent Resolve. Risk labels: ✅ ToS-safe · ⚠️ grey-hat · ☠️ ban-bait (esp. fatal to <90-day accounts).

## THE GOVERNING FINDING
**Official APIs are publish-and-respond tools, not outreach tools.** Meta (FB/IG/Threads) and YouTube
APIs let you publish + manage *your own* comments/DMs + read insights — they **cannot** like, follow, or
comment on *others'* content (removed by design to kill engagement bots). The **only** platforms whose
APIs permit programmatic follow/like/reply are the **open protocols: Bluesky, Mastodon, Tumblr.** Of
those, only **Bluesky** is culturally tolerant + has the right-ish audience. So:
> **Automation = your publishing engine + inbound responder + (Bluesky only) tasteful engagement.
> All other growth outreach is HUMAN-led replies/comments. The single best asset to grow is the OWNED
> EMAIL LIST — make it the scoreboard, not follower counts.**

---

## PER-CHANNEL

### Threads — BEST Meta cold-start (lead here)
- **API:** publish (250/day), reply incl. self-threads (1,000/day), `keyword_search` (500/7d), insights, cross-post to IG. ❌ no like/follow others.
- **Why it wins:** a 0-follower account reaches thousands organically; follower count isn't a distribution gate. **Replies > likes**; reply-velocity in first 30-90 min dominates.
- **Setting:** human **70/30 reply-guy method** (70% value replies to bigger contractor/SMB accounts, 30% original) — 10-20 manual replies/day + 2-3 opinion/conversation-bait posts/day (auto-published). Use `keyword_search` ("roofing leads", "HVAC slow season") to surface threads → human replies. ⚠️ auto-replying to strangers at scale = spam risk.

### Instagram — Reels cold-start engine
- **API:** publish Reels (≤90s, 50/day), manage own comments/DMs, hashtag-read (30/7d), insights. ❌ no like/follow/comment-others (no endpoint).
- **Setting:** **5-7 original Reels/wk, 90 days**, hook in 2s, CTA "send to a contractor friend" (DM-sends = top signal). Use **Trial Reels** to test on cold audiences. ☠️ NEVER follow/unfollow, pods, cold-DM, 3rd-party auto-tools on a <90-day account — lowest enforcement thresholds = instant nuke. Manual: 15 min/day real comments on bigger trade accounts + 1-2 Collab posts/mo.

### Facebook — hardest; treat as Reels-distribution + trust asset
- **API:** publish (incl. Reels), manage own comments/DMs, insights. ❌ no outbound engagement.
- **Setting:** cross-post best Reels (free reach). **Real growth is in Groups, not the Page** (20-40% reach vs 1-6%) — human persona providing value in local homeowner/contractor Groups ("who's a good plumber in [city]"). Saves/Shares > likes; link in comments not in-feed.

### YouTube Shorts — discovery equalizer (follower-count-independent)
- **API (owner token):** upload (~1,600 quota units; ~5-6/day ceiling on 10k), reply/moderate own comments, playlists, analytics. ❌ no auto-sub/like/comment-others; ☠️ sub4sub/bots.
- **Setting:** **1-2 Shorts/day, 90 days / ~150 videos** (the "niche-lock" threshold). Open on the payoff (>70% past 3s), **20-35s**, seamless loop, ≥65% retention to escape test pool. **Owner-token autoresponder: reply to comments in first hour** (correlates with wider distribution) + auto-pin CTA. 70/30 feed-first vs search-first ("how to fix X" = evergreen homeowner intent). Original VO is now an algo *bonus* under 50k.

### Bluesky — THE ONE real automated-engagement play ⭐
- **API (AT Protocol):** follow/like/repost/reply are records you write (`createRecord`); searchPosts, searchActors, getFeed, getFollows. Rate ceiling ~11,666 creates/day — a full routine = ~1% of cap.
- **Discovery:** custom feeds (~60%) + starter packs (~43%) + reply-velocity. **Publish our OWN feed ("Home Services Talk") + starter pack** = owned distribution.
- **Setting (the buildable daemon):** warm-up wk1 (follow 5-10/day, like 10-15, 3-5 human replies, **NO bio link**). Ramp wk2-8: follow 20-40/day **dripped + jittered**, like 20-30, repost 2-4, **10-20 human-written replies** (auto-queue threads <30 min old), 1-2 posts/day. Add bio link only after ~1k followers.
- ☠️ **Hard lines:** 50 follows in ~2 min on fresh acct = instant ban; bio link + mass-following = #1 flag; follow-churn >1,800 watched; never auto-reply to strangers. Jitter everything; one persisted session; mind per-IP limit on Cloudflare.

### Mastodon — presence only
- **API allows** follow/favourite/boost/reply, but **culture is the most anti-bot online** (#FediBlock → defederation, not appealable). **Setting:** set `bot=true`, auto-publish 2-5 original tips/wk (2-5 CamelCase hashtags = only discovery surface), **all engagement manual**. Pick a commercial-friendly instance. Never automate engagement here.

### Pinterest — evergreen SEO traffic engine (not social)
- **API v5:** publish pins/boards/video + analytics (OUTBOUND_CLICK = KPI). No social-engagement API (don't need one — growth = search).
- **Setting:** **3-5 fresh pins/day** (3-5 design variants per article = each "fresh"), keyword-architected boards ("Marketing for Plumbers", "HVAC Lead Generation"), long-tail keywords in titles/descriptions. Video pins ~3x outbound clicks. Pins drive traffic for *years*. ☠️ velocity spikes / same image spammed across boards = shadowban. *(Pending standard access.)*

### Telegram — owned-audience nurture, not discovery
- **Bot API:** posts to own channel (~unlimited). ❌ no growth API (bots can't follow/join/engage); userbots = ☠️ ban.
- **Setting:** make it a **destination, not a source** — fund it with cross-platform CTAs. Native growth = **shareable folder swaps + shoutout/SFS swaps with adjacent non-competing channels + directory submissions** (TGStat, Lyzem). Keyword the name/description. Make it PUBLIC first.

### Tumblr — researched & DECLINED for this ICP
- API permissive (follow 200/day, like 1,000/day, reblog), but audience is Gen-Z fandom/aesthetic — **buyers and contractors are absent**. Keep as passive blog-syndication only; don't invest in engagement.

---

## CROSS-CHANNEL STRATEGY (the synthesis)
1. **Make the EMAIL LIST the scoreboard**, not followers — it's the only owned, algorithm-proof asset and the only one that funnels to Consent Resolve (email ROI ~30:1).
2. **Conversion hinge = an interactive lead magnet** (calculators convert ~70% better than PDFs). **We already have the Angi + margin calculators** — gate/CTA them to email capture. Add a "score your shop's lead-gen" self-audit.
3. **One content engine → atomize, don't re-strategize.** YouTube long-form = the truth → clip to Shorts/Reels → text takes to Threads/Bluesky → newsletter owns it. Repurpose ≠ repost (strip watermarks, rewrite captions native — mismatch tanks reach 42-72%).
4. **Growth outreach is human-led** and lives in: Facebook Groups (strongest ICP fit — homeowners ask "who do I call?"), Threads reply-guy, YouTube comments. Budget ~30-45 min/day human engagement.
5. **AEO / AI-citation (realistic from zero, off-site only):** seed **G2/Capterra/Trustpilot reviews** (0 reviews → ~1% citation; **1-13 reviews → 53% citation**) — highest-ROI, near-zero-risk. Get into *others'* "best-of" listicles (~22% of AI citations); **never self-publish a listicle ranking yourself #1** (suppressed Jan 2026; AI omits self-promoters 69% of the time). Genuine Reddit presence (still #1 cited domain).
6. **A face beats a faceless logo** in trades (a trust culture). Semi-faceless (consistent VO + real jobsite footage + named persona) if no on-camera face.

## DEAD / OVERRATED IN 2026 (don't waste effort)
Mass AI-spun content (March 2026 spam update), keyword stuffing, PBN/guest-post link schemes, **self-ranking "best tools" listicles**, engagement bait/pods, hashtag spam, follow/unfollow bots, bought followers (pollutes geo signal for a local brand), X organic without paid, `llms.txt` (bots ignore it).

## THE SINGLE HIGHEST-LEVERAGE MOVE (honest pick)
Be the genuinely useful **expert (a real human/founder persona) inside local-homeowner + contractor Facebook Groups + YouTube**, and convert that attention to the **owned email list via an interactive lead magnet** → nurture → soft-funnel to Consent Resolve. Lowest-risk (human-admin enforcement = single-group blast radius), where the ICP actually is (97% of plumbers on FB), and it feeds the only asset that closes.

## WHAT WE CAN BUILD (automation that's both safe + high-ROI)
1. **Bluesky engagement daemon** — search contractor keywords → auto-like relevant + drip-follow (jittered, human-paced, guard-railed) → queue hot threads for human reply; publish our own custom feed + starter pack. *The one place automation genuinely grows.*
2. **YouTube first-hour comment autoresponder** + auto-pinned CTA (owner token, ✅ safe, boosts distribution).
3. **FB/IG/Threads inbound autoresponder** — reply to comments/DMs on our own content.
4. **Threads keyword-surfacing** → human-reply queue.
5. **Lead-magnet email capture** on the existing calculators + make email subs the dashboard North Star.
