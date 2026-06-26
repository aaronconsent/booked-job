# Booked Job — Channel Registry

Status of every distribution channel. Updated 2026-06-26.

## ✅ Connected & autonomous (launchd agents run without Claude)

| Channel | What it does | Agent | Cadence |
|---|---|---|---|
| **Facebook Page** | Posts + Reels + $7/day ads (paused), auto-engage | `publisher`, `reels`, `engage` | daily / Tue+Fri / 3×day |
| **YouTube Shorts** | Faceless TTS Shorts from reel content | `youtube` | weekly |
| **Instagram Reels** | Reuses reel videos via Content Publishing API | `instagram` | weekly |
| **Blog (booked-job.com)** | SEO/AEO pillar articles + RSS feed | (manual + strategist) | weekly |
| **Blogger** | Canonical-summary syndication | `blogger` | weekly |
| **Tumblr** | Canonical-summary syndication | `tumblr` | weekly |
| **Telegraph** | Unique-summary + backlink (no signup) | `telegraph` | Sat |
| **Bluesky** | Teaser + link card (@bookedjob.bsky.social) | `bluesky` | Thu |
| **Mastodon** | Teaser + link (@bookedjob@mastodon.social, rel=me verified) | `mastodon` | Sat |
| **GitHub Pages** | Full canonical mirror at contractors.webhd.com | `ghpages` | Tue |
| **Email newsletter** | Resend broadcasts to captured list | `newsletter` | weekly |
| **Stats/Dashboard** | Refreshes dashboard data + git push | `stats` | 4×day |
| **Weekly report** | Sunday digest | `report` | Mon |

## ⏳ Pending (waiting on an external approval/action)

| Channel | Blocked on |
|---|---|
| **Pinterest** | Trial-access approval (App 1584930) → then secret + OAuth |
| **Google Business Profile** | Google verification + API access; review machine staged |
| **LinkedIn (RSS)** | **Feed is DONE & validated** (booked-job.com/feed.xml, application/rss+xml, 4 items). The *first* company page (110527722) rejected it with "Something went wrong" — confirmed this is a **LinkedIn-side requirement that the page have existing content/activity** before it accepts a feed (the same feed worked on a warmed-up account). **Deferred:** post a few manual updates to warm the page, then re-add the feed at /admin/settings/manage-content/. No code change needed. |

## 🔲 Not yet built (from the channel list)
- **Yelp** — claim listing + reviews play (no posting API; pairs with GBP review machine)

## Notes
- The **RSS feed** (`site/feed.xml`, built by `scripts/build_feed.py`) also feeds Flipboard/NewsBreak if added later. Content-type forced to `application/rss+xml` via `site/_headers` (the Worker is bypassed for static assets).
- All syndication runners read `content/syndication_queue.json` and track their own `*_state.json` so each channel drips the next unposted article independently.
