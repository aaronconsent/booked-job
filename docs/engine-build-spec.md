# Posting Engine — Consolidated Build Spec (v1)

Supersedes and merges `connect-ux-spec.md`, `content-setup-wizard-spec.md`,
`operations-console-spec.md` into one buildable system. Includes an audit of gaps
in those three and the decisions that resolve them, plus the concrete plan to apply
it to a second site (aaron.chat).

---

## PART A — Audit of the three specs (gaps → resolutions)

| # | Gap / problem | Severity | Resolution (baked into Part B) |
|---|---|---|---|
| 1 | **Runtime model** — needed a decision | ✅ Decided | **Per-tenant GitHub Actions + Cloudflare IS the runtime** (Aaron's model). Keep the booked-job pattern, repeat it per account + a thin control plane. |
| 2 | **No deployment stack** — "how to build" undefined | 🔴 High | Per-tenant = GitHub repo + Cloudflare + **engine package**. Central = thin control-plane app (wizard/console/OAuth) driving the GitHub + Cloudflare APIs. |
| 3 | **Secret vault hand-waved** | ✅ Resolved | **GitHub Secrets per repo = the vault** (booked-job's `ENV_*`). OAuth service pushes tokens there via API. No central vault to run. |
| 4 | **Content boundary contradictory** — "out of scope" yet the wizard's starter batch + recipes need it | 🔴 High | Define a pluggable **`ContentSource` interface**; generation is one implementation. |
| 5 | **Content-source adapter for non-blog sites** treated as a checkbox (breaks on aaron.chat = pages) | 🟠 Med | Formal adapter contract; ship `BlogAdapter`, `PageAdapter`, `BuiltinGenerator`. |
| 6 | **No runtime post sequence** — only static data models | 🟠 Med | The post loop is specified in Part B. |
| 7 | **State (posted-ids, cadence counters) is per-JSON-file** | ✅ Fine as-is | Keep it — state stays in each tenant repo's committed JSON (booked-job pattern). Console reads it. No DB needed for runtime. |
| 11 | **NEW: engine-version drift across N independent repos** (the real cost of per-tenant) | 🔴 High | Engine ships as a **versioned package**; a control-plane bot bumps + PRs the version to every tenant repo. |
| 8 | **Auth sourcing undecided** (own verified app vs aggregator, from the Buffer talk) | 🟠 Med | `channel_config.backend = own_app \| aggregator`; publisher registry routes on it. |
| 9 | **No fleet-level alerting** in the Console | 🟡 Low | Tenant Health + on-call hooks. |
| 10 | **aaron.chat mismatch** — specs default to the aggressive 12-channel model; aaron.chat is founder-led (LinkedIn/X) + page content, greenfield | 🟠 Med | Part C: aaron.chat gets a narrow config + `PageAdapter`, not the booked-job blast. |

---

## PART B — The consolidated build

### Architecture: thin control plane + per-tenant GitHub/Cloudflare runtime
Aaron's model: **every account has its own GitHub account + Cloudflare.** So the runtime
is distributed (the booked-job pattern, per tenant), and a small central control plane
only *orchestrates* — it never runs the posting.

```
CONTROL PLANE (central, thin)                    PER-TENANT RUNTIME (distributed, one per account)
  web app: wizard + fleet console            ┌── GitHub repo  = engine package (pinned) + config + content + committed state
  OAuth callback service                     │     └── GitHub Actions (cron) → run_all → publishers → commit state
  orchestrator (GitHub API + Cloudflare API) ├── GitHub Secrets (ENV_*)  = the per-tenant vault
  fleet DB (tenants, statuses, approvals)    └── Cloudflare Pages/Workers = host site + serve data.json + media CDN
  version bot (bumps engine pkg across repos)
```

**Control plane** (one app you run):
- **Wizard** — Connect + Content Setup UIs. On finish it **provisions** the tenant:
  create GitHub repo from the engine template (GitHub API), set `ENV_*` secrets (GitHub API),
  create the Cloudflare Pages/Workers project + DNS (Cloudflare API), commit the tenant `config`.
- **OAuth callback service** — captures tokens centrally, then **pushes each to that tenant's GitHub Secrets** (never stored centrally long-term).
- **Fleet console** — federated reads: each tenant's committed `data.json`/`coverage.json` (served by their Cloudflare) + GitHub Actions run status (API) + Cloudflare Analytics (API). No shared runtime DB.
- **Version bot** — the answer to per-tenant drift: opens/auto-merges a PR bumping the engine package version across all tenant repos.

**Per-tenant runtime** (owned by the client, isolated):
- **GitHub repo** from the **engine template**: a thin `run_all` that imports `@engine` (pinned version) + the tenant's `config.yaml` + content + committed JSON state.
- **GitHub Actions** = the scheduler (cron), exactly like booked-job. No central worker.
- **GitHub Secrets** = the per-tenant vault (`ENV_*`). No central vault.
- **Cloudflare** = host + the public media/CDN URLs IG/TikTok/Bluesky require + analytics.
- **Publisher registry** = `@engine/publishers` (booked-job's `*_publish` modules); each declares `{platform, post_types, backend[own_app|aggregator]}`.
- **Media**: rendered inside the tenant's Actions run (ffmpeg/PIL) or a media step; output committed/hosted on the tenant's Cloudflare.

**Why this is better for your model:** full client isolation (separate repos/secrets/hosting, zero comingling), the client *owns* their repo + Cloudflare (clean handoff/billing), and infra cost ≈ $0 (GitHub Actions free minutes + Cloudflare free tier, per account). The one real tax is **engine-version propagation** — solved by the package + version bot, not by a central runtime.

### Data model — split by where it lives
**Control-plane DB** (central, small — orchestration only):
```
tenant(name, github_repo, cf_project, status), app_credential(master apps),
connection(status,scopes), capability(state), approval_request, fleet_metric(cache of tenant data.json)
```
**Per-tenant repo** (committed files, the booked-job pattern — no central DB):
```
config.yaml   channel_config(platform,post_type,enabled,daily_cap,windows,backend,exclude),
              icp, voice_profile, media_recipe(produces[post_type]), content_hub, cadence_target
content/      content_item queue + post_state (posted-ids, per-day counters, last_iso)
              run history / run_all.log, channel_metric (data.json), coverage.json, tasks
secrets       GitHub Secrets ENV_* (never committed)
```
Runtime state stays in the repo (idempotent, versioned, client-owned). The console reads
each tenant's committed `data.json`/`coverage.json`; the DB only caches it for fleet views.

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

### The runtime post loop (inside each tenant's GitHub Actions run — `run_all`)
```
for (platform, post_type) due now:
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

### Build order (each phase shippable; booked-job is tenant #1 = the reference)
1. **Extract the `@engine` package** — publishers + a generic runner driven by `config.yaml` + the `ContentSource` interface — out of booked-job; run booked-job on it unchanged (parity gate).
2. **Template repo** — package the tenant shape: thin `run_all` importing `@engine` (pinned) + `config.yaml` + the Actions workflow + `secrets` recreate step. booked-job becomes the reference tenant.
3. **Control-plane provisioning** — an app that, given a new client, creates their GitHub repo from the template, sets `ENV_*` secrets, spins up their Cloudflare Pages/Workers + DNS (GitHub + Cloudflare APIs).
4. **OAuth callback service** — capture tokens → push to that tenant's GitHub Secrets; + capability probes.
5. **Wizards (Connect + Content Setup)** driving provisioning; **fleet console** via federated reads (each tenant's `data.json` + Actions status + CF analytics).
6. **Version bot** — bump the `@engine` package across all tenant repos via PR.
7. **Onboard tenant #2 = aaron.chat** (Part C) — the real portability test.

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
