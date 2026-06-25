# Booked Job — how the machine runs

Audience-first content brand for the trades (service-pro ICP) → soft funnel to
Consent Resolve. Grows the Facebook page + site autonomously. Strategy: `STRATEGY.md`.

## What's live
- **Site:** `site/` (static) — `index.html` landing + `go.html` link-in-bio hub.
  Deployed via Cloudflare Pages from GitHub `aaronconsent/booked-job`.
  **CF build output directory must be `site`** (build command empty, framework None).
- **Facebook Page:** "Booked Job" — public URL `profile.php?id=61591176670582`,
  API page id `1272845059238799`. Long-lived Page token in `secrets/fb.env` (never expires).

## The autonomous loop (launchd on Aaron's Mac — runs WITHOUT Claude)
| Agent | Schedule | Does |
|---|---|---|
| `com.bookedjob.publisher` | 7:10 / 12:20 / 18:40 daily | drips `content/queue.json` per warm-up ramp (Tue–Thu, 1/day, weekends off). One post/day; per-day jitter picks the window. |
| `com.bookedjob.engage` | 9:05 / 14:35 / 20:15 daily | likes new comments as the Page; logs comments to `content/inbox.md` for a human reply. |
| `com.bookedjob.report` | Mon 08:00 | writes `content/reports/report-DATE.md` (followers, reach, top posts, next steps). |

Plists live in `worker/` and are installed in `~/Library/LaunchAgents/`.
`launchctl list | grep bookedjob` shows status (0 = ok).

## Scripts (`scripts/`)
- `fb_setup_token.py` — exchange short token → long-lived Page token, writes `secrets/fb.env`.
- `fb_post.py` — single post (supports photo + link-in-first-comment). Manual use.
- `publisher.py` — the drip brain (`--status`, `--dry-run`, `--force`).
- `make_card.py` — branded 1080² quote/meme card (PIL).
- `seed_content.py` — (re)build cards + `content/queue.json` from the post list.
- `fb_engage.py` / `fb_report.py` — engagement + weekly report.

## Refilling content (the one recurring human/Claude task)
When `python3 scripts/publisher.py --status` shows < 5 remaining: add posts to the
`POSTS` list in `seed_content.py` (or edit `content/queue.json` directly) and re-run
`seed_content.py`. Keep the archetype mix from STRATEGY.md. Posted state is preserved
in `content/state.json`, so re-seeding never re-posts.

## Token refresh
The Page token (minted from a long-lived user token) doesn't expire. If it ever
breaks, re-run `fb_setup_token.py` with a fresh Explorer token + the app id/secret.

## NOT yet built (next phases)
- **Reels engine** (the #1 acquisition lever per research) — needs a video pipeline.
- **Owned FB Group** — create manually, then update the `data-slot="group"` link in `go.html`.
- **Paid $5–10/day** — broad video-view + retarget→follow (needs ad-account API access).
- **Self-refilling generator** — no LLM key in env; queue is refilled by a Claude session.
