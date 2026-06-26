# Content Distribution Research — Channels We Haven't Built

Research date: 2026-06-26. Sources: content-syndication / parasite-SEO / AEO practitioner
articles, platform API docs, decentralized-social comparisons. Scored for **Booked Job's**
needs: trades ICP, **autonomous via API/RSS**, SEO/AEO value, soft-funnel to Consent Resolve.

Legend — Publish method: **API** (programmatic) · **RSS** (set feed once, they pull) · **Manual**.
Fit: 🟢 do · 🟡 maybe · 🔴 skip.

## Already built (for reference)
FB · IG · YouTube · Blog · Blogger · Tumblr · Telegraph · Bluesky · Mastodon · GitHub Pages ·
Email (Resend) · Pinterest (sandbox, pending). LinkedIn feed done (page warming). GBP pending.

---

## 🟢 Tier 1 — Build now (real API, good fit, fully autonomous)

| Platform | Publish | Why it fits | Notes |
|---|---|---|---|
| **Threads** (Meta) | API | We **already hold Meta tokens**; real Threads API; same content as FB/IG; text-first = great for hot takes | Lowest-effort, highest-certainty add |
| **Telegram** | Bot API | Free, trivial Bot API; broadcast **channel** = a clean owned content feed; bots post 24/7 | Need to create a public channel |
| **Flipboard** | RSS | Pipe our existing `feed.xml` into a Flipboard **Magazine** — zero ongoing effort; curation + discovery | Wants full-content RSS w/ images (we have it) |

## 🟡 Tier 2 — Worth it, but a tradeoff

| Platform | Publish | Benefit | Catch |
|---|---|---|---|
| **Substack** | RSS import + Manual | DA 91, **discovery network** (Notes + recommendations grows the list), indexable archive | No publish API; semi-manual; 2nd newsletter to feed |
| **Discord** | Webhook (API) | Trivial webhook auto-post; real-time community hub | Need our own server + members first |
| **Quora** | Manual | **AEO gold** — answers get quoted by ChatGPT/Perplexity; DA 87 | No posting API; manual Q&A |
| **Reddit** | API (sensitive) | **#1 AI-citation source (~40%)**, DA 91, huge SERP visibility post Google deal | ToS/astroturf risk — only legit participation, no covert automation (we held this line) |
| **Bing Places** | Listing | Feeds Bing + Copilot/ChatGPT local answers; listings = 42% of AI citations | One-time setup |
| **Apple Business Connect** | Listing | Apple Maps/Siri discovery | One-time setup |

## 🔴 Tier 3 — Skip (wrong audience / not worth it)

| Platform | Why skip |
|---|---|
| **Medium** | API deprecated (no new tokens) — manual only |
| **Dev.to / Hashnode / HackerNoon** | Developer audiences — ICP mismatch |
| **Nostr / Lemmy / Farcaster (Warpcast)** | Open APIs but tiny/crypto-leaning audiences; Farcaster costs $5 + wallet |
| **VK** | Russian market — wrong geography |
| **Dribbble** | Design portfolios — wrong audience |
| **X / Twitter** | Posting API now ~$100/mo |
| **TikTok** | Ruled out (approval gating) |

---

## ⭐ Architectural option: Postiz (consolidation)
**[Postiz](https://github.com/gitroomhq/postiz-app)** is an open-source, self-hostable scheduler
with a **public API + MCP server** covering **~30 networks**: Threads, Bluesky, Mastodon, Telegram,
Discord, Reddit, Pinterest, LinkedIn, Threads, TikTok, YouTube, Google Business, Lemmy, Warpcast,
Nostr, WordPress, and more.

- **Pro:** one integration instead of N bespoke scripts; MCP lets the AI agent post directly; adds
  networks we don't have (Threads/Telegram/Reddit) in one shot.
- **Con:** another service to self-host + maintain; less fine-grained control than our current
  per-channel Python scripts (which already work and are free).
- **Verdict:** worth considering IF we want to add many networks at once. Otherwise our bespoke
  scripts are fine for the 1–3 high-value adds.

## AEO takeaway (shapes priority)
- **Reddit ~40%** and **YouTube (now #1)** dominate AI citations. We have YouTube; Reddit is the
  gap (sensitive).
- **Listings = 42%, first-party = 44%** of citations → GBP + **Bing Places + Apple Business
  Connect** punch above their weight for AI/local discovery.
- **Freshness matters:** 83% of cited pages updated within 12 months → keep the blog refreshed.

## Recommended next adds (in order)
1. **Threads** — autonomous, we hold the keys
2. **Telegram** — free, trivial Bot API, owned broadcast feed
3. **Flipboard** — point our RSS at a Magazine, done
4. **Bing Places + Apple Business Connect** — quick AEO/local listings
5. *(Optional)* **Substack** for the discovery network; evaluate **Postiz** if we want to add 5+ networks at once
