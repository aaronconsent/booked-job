# Posting Engine — Consolidated Build Spec (v1)

Supersedes and merges `connect-ux-spec.md`, `content-setup-wizard-spec.md`,
`operations-console-spec.md` into one buildable system. Includes an audit of gaps
in those three and the decisions that resolve them, plus the concrete plan to apply
it to a second site (aaron.chat).

---

## PART A — Audit of the three specs (gaps → resolutions)

| # | Gap / problem | Severity | Resolution (baked into Part B) |
|---|---|---|---|
| 1 | **Runtime model inherited from booked-job** (per-repo GitHub Actions) never reconciled to multi-tenant | 🔴 High | **Central scheduler/worker + shared DB.** Drop GitHub Actions for the product. |
| 2 | **No deployment stack** — "how to build" undefined | 🔴 High | Pinned stack in Part B (web app + Postgres + worker + vault + object store). |
| 3 | **Secret vault hand-waved**, and "sync to GitHub secret" contradicts multi-tenant | 🔴 High | Central encrypted vault; worker reads at runtime. No per-repo secrets. |
| 4 | **Content boundary contradictory** — "out of scope" yet the wizard's starter batch + recipes need it | 🔴 High | Define a pluggable **`ContentSource` interface**; generation is one implementation. |
| 5 | **Content-source adapter for non-blog sites** treated as a checkbox (breaks on aaron.chat = pages) | 🟠 Med | Formal adapter contract; ship `BlogAdapter`, `PageAdapter`, `BuiltinGenerator`. |
| 6 | **No runtime post sequence** — only static data models | 🟠 Med | The post loop is specified in Part B. |
| 7 | **State (posted-ids, cadence counters) is per-JSON-file** in booked-job | 🟠 Med | Move all runtime state into the DB. |
| 8 | **Auth sourcing undecided** (own verified app vs aggregator, from the Buffer talk) | 🟠 Med | `channel_config.backend = own_app \| aggregator`; publisher registry routes on it. |
| 9 | **No fleet-level alerting** in the Console | 🟡 Low | Tenant Health + on-call hooks. |
| 10 | **aaron.chat mismatch** — specs default to the aggressive 12-channel model; aaron.chat is founder-led (LinkedIn/X) + page content, greenfield | 🟠 Med | Part C: aaron.chat gets a narrow config + `PageAdapter`, not the booked-job blast. |

---

## PART B — The consolidated build

### Architecture: one central multi-tenant service
```
web app (wizard + console)  ─┐
   Next.js + tRPC            │
API / domain services       ├─ Postgres (all tables)  ── Vault (KMS envelope enc.)
   Node/TS                   │
OAuth callback service      ─┘
Scheduler ── Runner workers ── Publisher registry ── {own verified apps | aggregators}
Media workers (ffmpeg/PIL/Recraft/ElevenLabs/HeyGen) ── Object store + CDN (public media URLs)
```
- **Scheduler** wakes per tenant × channel × post_type on cadence (replaces booked-job's GitHub Actions). Use a durable queue (Temporal or BullMQ+cron).
- **Runner worker** = the generic version of booked-job's runners, driven entirely by `channel_config` rows (no per-runner scripts).
- **Publisher registry** = booked-job's `*_publish` modules as a `@engine/publishers` package; each declares `{platform, post_types, backend}`.
- **Media workers** run the recipes; output to object storage with public CDN URLs (what IG/TikTok/Bluesky require).
- **Vault**: envelope encryption (KMS or Infisical/Doppler). Workers fetch per-tenant tokens at run time. No plaintext, no GitHub secrets.

### Data model (unified — from all three specs, DB tables)
```
tenant, app_credential(master apps), connection, capability, secret(vault ref),
channel_config(tenant,platform,post_type,enabled,daily_cap,windows,backend,exclude),
icp, voice_profile, media_provider, media_recipe(produces[post_type]), content_hub,
content_item(the queue — normalized across sources), post_state(idempotency+cadence),
runner, run, run_step, channel_metric, coverage_cell, cadence_target, task, approval_request
```
All runtime state (posted ids, per-day counters, last_iso) lives in `post_state`, not files.

### The content boundary — resolved
```
interface ContentSource {
  next(tenant, platform, post_type): ContentItem | null   // {text, mediaSpec?, link?}
}
```
Ship three implementations; a tenant picks one+ per source:
- **BuiltinGenerator** — the fact-checked content workflow (AI articles/posts).
- **BlogAdapter** — pull from an existing blog (render_branch / WordPress / Ghost) → variants.
- **PageAdapter** — transform existing site *pages* (landing/pillar) into social posts. ← aaron.chat.

The engine is content-agnostic; **generation is optional**, plugged behind this interface.

### The runtime post loop (per scheduler tick)
```
for (tenant, platform, post_type) due now:
  gate:   window ok && post_state.day.count < channel_config.daily_cap && spacing ok
  item  = ContentSource.next(tenant, platform, post_type)          // coverage-driven pick
  media = MediaPipeline.ensure(item, post_type)                    // run recipe if needed → CDN url
  res   = PublisherRegistry.route(platform, backend).post(item, media)
  record run_step + channel_metric; bump post_state counters; on-fail → health/alert
```

### Coverage = the invariant (enforced setup-time, monitored runtime)
```
green(tenant, platform, post_type) =
    connection.capability == live                (Connect)
  & exists media_recipe.produces[post_type]      (Content Setup)
  & ContentSource.can(platform, post_type)       (source wired)
  & channel_config.enabled                        (Ops)
```
Wizard blocks launch of a channel until every supported type is green or deferred.

### Auth sourcing (per platform, decided at build)
`channel_config.backend`:
- **own_app** — your verified app (FB/IG, Google/YouTube, Bluesky, Mastodon, Telegram, X*).
- **aggregator** — Buffer/Ayrshare for partner-gated networks (LinkedIn, TikTok, Pinterest).
(*X API is paid-tier; treat as optional/own_app.)

### Build order (each phase shippable; booked-job is tenant #1 = the test harness)
1. **Extract `@engine/publishers` + generic runner + `ContentSource`** from booked-job; run booked-job through it unchanged (proves parity).
2. **Postgres + move state** (post_state, channel_config) off JSON files.
3. **Central scheduler + runner/media workers** (retire GitHub Actions).
4. **Vault + OAuth callback service** (Connect layer) + capability probes.
5. **Wizards (Connect + Content Setup) + Operations Console** UIs on the DB.
6. **Onboard tenant #2 = aaron.chat** (Part C) — the real portability test.

---

## PART C — Applying it to aaron.chat

**Reality:** aaron.chat is a greenfield-for-posting static SEO site (pages + a blog in
the `firstbyte` repo). No connected channels, no secrets, no runners. Its social
intent is **founder-led LinkedIn + X**, not a 12-channel blast.

**So its config is deliberately narrow, not booked-job's:**
- `tenant`: aaron.chat, professional/agency voice, timezone.
- **Channels**: LinkedIn + X first (founder), optionally FB/IG. Each `channel_config`
  with modest caps (e.g. LinkedIn 1/day, X 2–3/day) — quality over blast.
- **Auth sourcing**: LinkedIn via **aggregator**; X via own_app (paid tier) or aggregator;
  FB/IG via **shared master app with booked-job** → near-zero new approvals.
- **ContentSource**: `PageAdapter` over the firstbyte blog + pillar/combo pages
  (existing SEO content → LinkedIn/X posts + carousels), plus optional BuiltinGenerator
  for founder takes.
- **Voice**: run the voice wizard on Aaron's existing LinkedIn/site copy → agency voice
  profile (NOT booked-job's edgy tone).
- **Media**: reuse recipes (statcard/carousel) with aaron.chat brand assets; reels
  optional (founder video later).
- **Coverage gate**: only the post types those 2–4 networks support — green board is
  small and achievable, no pressure to fill TikTok/Pinterest it doesn't want.

**Gotchas specific to aaron.chat**
- Its content is *pages*, so `PageAdapter` is real work — the one genuinely new piece.
- Social is *secondary* to SEO there; cadence should be conservative and on-brand.
- Do **not** reuse booked-job's voice/curation defaults — professional brand.

**Net:** aaron.chat validates the engine as portable — same publishers, runner,
console, coverage invariant; only the config, the `PageAdapter`, and the voice/brand
differ. That's the intended ~80/20 split, proven on a real second site.
