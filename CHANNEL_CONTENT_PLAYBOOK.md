# Booked Job — Channel Content Playbook

Research 2026-06-27. Goal: **enable every API-postable format per channel** + give each channel
**unique, native content** (never the same asset cross-posted). Audience: home-service contractors;
soft-funnel to Consent Resolve.

## The operating rule
**One source idea → N differently-shaped assets.** A single weekly insight (e.g., "a $89 diagnostic
fee books more jobs than a free estimate") becomes a FB share-card, an IG saveable carousel, a Threads
debate chain, a LinkedIn PDF carousel, a Bluesky thread, a Telegram poll, a Pinterest keyword pin — never
a duplicate. Every channel's CTA ultimately routes a hand-raise into the **email list** (the real funnel).

---

## Per-channel spec (format to enable · unique angle · top tricks)

### Facebook — *community proof, engineer the share*
- **Enable via API:** multi-photo carousel (`attached_media`), photo Stories (`/photo_stories`), video Stories (`/video_stories`). (Have: feed cards, Reels.)
- **Angle/voice:** neighbor-next-door; "send this to your crew." Top signal = private shares + saves.
- **Tricks:** end cards with an explicit share CTA; saveable multi-photo before/after + line-item breakdowns; daily Stories (polls/"guess the repair cost"); customer-story video (45-60s, captioned); ≤2 feed posts/day.

### Instagram — *cold discovery + saveable teaching*
- **Enable via API:** carousels (2-10), Stories (`media_type=STORIES`). (Have: Reels.)
- **Angle/voice:** confident educator; the "screenshot-and-DM-to-your-apprentice" swipe-file. Top signal = DM sends + saves.
- **Tricks:** Reels for reach + weekly carousels for saves; build "DM this to your ops person" prompts; keyword-load captions (not hashtags); Stories as the link surface; dramatic visual in first 3s.

### Threads — *unfiltered operator hot-take + reply-bait*
- **Enable via API:** image, video, carousel (20), **programmatic self-reply chains** (`reply_to_id`, excluded from 250/day quota). (Have: text.)
- **Angle/voice:** blunt contrarian operator who asks the room. Top signal = replies + first-30-min velocity. Stay positive (ragebait demoted; positive accts grew 3x).
- **Tricks:** divisive-but-true claim + question; self-reply chains expanding the argument; post 2-3x/day + reply fast; mine replies for the next post.

### YouTube — *search + retention library (evergreen)*
- **Enable via API:** long-form (`videos.insert`), captions (`captions.insert`), thumbnails, playlists, Live. (Have: Shorts.) **Community posts NOT API** (manual/Studio only).
- **Angle/voice:** scripted, keyword-titled, chaptered, evergreen. Opposite of TikTok.
- **Tricks:** 30-40% Shorts / 60-70% long-form hybrid (~3x faster growth); title for the search bar; curiosity-gap + chapters for retention; topic-cluster playlists; auto-insert captions every upload.

### TikTok — *raw trend feed (of-the-moment)*
- **Enable via API:** video (Buffer ✓), photo carousels. **Direct-post is GATED** (audit: privacy policy + demo video + review) → use Buffer / inbox-upload interim; Stories/Live not API.
- **Angle/voice:** raw, native, hook-first, single-idea. Re-cut (don't re-upload) the YouTube idea.
- **Tricks:** hook in 2-4s, pattern-interrupt first; data-backed hooks (~35% higher eng); trending sounds w/ longevity (content > audio); lean raw on purpose; exploit photo carousels (underused).

### LinkedIn — *B2B authority / founder voice*
- **Enable via Buffer:** **PDF document carousels** (highest eng format, 6.6%), native video. **Polls NOT in Buffer** (manual). (Have: text+link.)
- **Angle/voice:** operator who gets the trades business (margin math, hiring, slow-season cash). Dwell time > likes.
- **Tricks:** 8-12 slide portrait PDF carousels (1080×1350); engineer the first-3-lines hook; win the first 60 min (reply to early comments); link in first comment not body; polls with 2-3 lines of framing (manual).

### Bluesky — *conversational early-adopter*
- **Enable via API:** image posts (4, +alt), video, quote posts, **threads**, **own custom feed**, **starter packs**. (Have: text + engagement daemon.)
- **Angle/voice:** looser, in-the-trenches, reply-first; the brand has personality and argues in replies.
- **Tricks:** threads not singles (~3x replies); reply velocity in first 15-30 min; **create our own "Trades Ops" custom feed** (60%+ discovery via feeds); build + join **starter packs** (43% of new follows); spend most effort in others' threads.

### Mastodon — *educational, anti-corporate, community-first*
- **Enable via API:** media attachments (+alt), **polls**, boosts, CWs. (Have: text.)
- **Angle/voice:** helpful educator who isn't selling; value independent of product; chronological, no algo.
- **Tricks:** 2-4 **CamelCase** hashtags (only discovery surface); **alt text mandatory** (table stakes); mix human replies/boosts so we don't trip the bot flag; lead with education, soft/rare CTA.

### Telegram — *insider daily drop*
- **Enable via Bot API:** photo (`sendPhoto`), video (`sendVideo`), **albums** (`sendMediaGroup` 2-10), **polls/quizzes** (`sendPoll`), GIFs, linked discussion group. (Have: text.)
- **Angle/voice:** peer-to-peer "here's what I'd do Monday morning"; highest-trust, lowest-polish.
- **Tricks:** broadcast + linked discussion group (biggest retention lever); daily quiz-poll engagement bait; cross-promo swaps with non-competing channels; "DM/comment for the template" → email capture.

### Pinterest — *evergreen visual search SEO* (pending Standard access)
- **Enable via API v5:** static pins (volume), **video pins** (~3x clicks, multi-step `/media`), carousels (2-5). 
- **Angle/voice:** keyword search — rank for what contractors type ("how to price a roof job").
- **Tricks:** 3-5 fresh-pin designs per article daily; keyword in title + description + board names; video pins (top-funnel) → carousels (clicks) → static (volume); captions on video pins.

### Email — *owned nurture-to-SaaS engine*
- **Enable via Resend:** **automated drip sequences** (automations = ~2% of sends, ~30% of revenue). (Have: broadcasts.)
- **Angle/voice:** the segmented welcome series that converts; soft product intro after value.
- **Tricks:** 5-email welcome drip (activate in 72h); segment by trade on signup (2x opens/5x CTR); soft SaaS intro framed as "the tool we built because we got tired of doing this"; feed list from every channel.

### Blog tier (Blogger/Tumblr/Telegraph/GitHub Pages) — *SEO/AEO depth*
- **Enable:** Tumblr NPF photo/quote/video post types (not just text); canonical syndication. (Have: article syndication.)
- **Tricks:** AEO question-headers + direct answers (get quoted by ChatGPT/Perplexity); GitHub Pages rides GH domain trust; Tumblr first-5 tags + image posts + raw tone; one article → infographic/quote-card/instant-read.

## Source ladder (which source asset feeds which channel)
- **Article** → blog/syndication (full + AEO), Pinterest (keyword pins), email (drip), LinkedIn (PDF carousel), Telegram/Bluesky/Threads/Mastodon (unique short takes).
- **Vertical video** → YouTube Short, FB/IG Reels, TikTok (re-cut raw), FB/IG Stories.
- **Insight/stat** → Threads debate chain, Bluesky thread, FB share-card, IG carousel, Telegram poll.
