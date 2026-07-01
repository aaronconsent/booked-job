# Content Setup Wizard — Strategy + Production Onboarding Spec

Third layer of the engine. `connect-ux-spec.md` = auth; `operations-console-spec.md`
= runtime; **this = strategy + production capability.** The goal: an operator
setting up a new site walks a wizard, nails the content strategy, wires the media
pipeline, and launches — with **provable coverage of every content type on every
connected channel.**

Grounded in the tooling in use: Recraft, OpenAI `gpt-image-1`, ElevenLabs, HeyGen,
ffmpeg + PIL (make_statcard/make_reel/make_carousel/make_story), segment.py.

---

## Coverage is the spine
A channel is **launch-ready** only when, for every post type it supports:
`channel connected (Connect) × pipeline can PRODUCE this type (this wizard) × a content SOURCE exists`.
The wizard blocks "go live" on a channel until every supported post-type cell is
green **or explicitly deferred**. This is the setup-time enforcement of the runtime
coverage matrix.

---

## Wizard steps

### 1. ICP definition
Capture (AI-assisted: seed a draft by reading the site URL, operator refines):
- niche, persona(s), pains, buying triggers, objections, competitors
- **channel priority** — where the ICP actually is (drives which channels to push)
→ feeds topic generation + voice + channel weighting.

### 2. Voice wizard  (two voices)
- **Written brand voice** — interview (tone slider: blunt↔polished, reading level,
  emoji policy, do's/don'ts, banned words) **+ paste 3–5 samples → auto-extract a
  voice profile**. Injected into every generation prompt (booked-job's "blunt,
  numbers-first" is exactly this, hardcoded — here it's captured per tenant).
- **Spoken voice** — pick or clone an **ElevenLabs** voice → `voice_id`; optional
  **HeyGen** avatar (accepts the ElevenLabs voice_id). Used by reels/podcast.

### 3. Media / Image API layer
Provider abstraction — connect keys, probe capability, set defaults + brand assets
(logo, colors, fonts):
| Kind | Providers | Notes / known gotchas |
|---|---|---|
| Image gen | **Recraft** (branded illustration), **OpenAI gpt-image-1** | not dall-e-3; watch Recraft credits |
| Composite / overlay | **PIL** (stat cards, text) | ffmpeg has **no drawtext** — text via PIL |
| Video render | **ffmpeg** (local), reel/story compositors | *.mp4 gitignored; host public for URL posting |
| TTS | **ElevenLabs** | credits metered per reel |
| Avatar | **HeyGen** | route-#2 photo-avatar look; takes ElevenLabs voice_id |

**Combos = recipes** (a `media_recipe`): e.g. Recraft bg → PIL headline overlay →
ElevenLabs VO → ffmpeg assemble = a reel. Engine ships the recipes; tenant supplies
brand assets. Each recipe declares which **post types** it can produce (feeds coverage).

### 4. Blog / content hub
The hub content publishes to, then syndicates to social:
- **Create** a new static blog (Cloudflare Pages, the booked-job/render_branch pattern), **or**
- **Connect** existing (WordPress API / Ghost / an existing Cloudflare site like aaron.chat).
Capture: type, creds, URL pattern, template. This is the source the syndication +
video pool draw from.

### 5. Coverage plan  (the gate)
Auto-generate the **content-type × channel matrix** and, per cell, verify all three
legs: channel connected · a `media_recipe` can produce this type · content source wired.
Render green / gap / deferred. Fix blockers inline (connect a channel, add a recipe,
add a media key). **Launch is gated on this board.**

### 6. Content plan + launch
From ICP + voice + coverage: seed **pillars/topic clusters**, set **cadence targets**
(goals.yaml — per-channel per-type/day, matching your spec), kick off the **starter
content batch** (the fact-checked content workflow) → **Go live** enables the tenant's
GitHub Actions.

---

## Data model
```
icp             tenant_id, niche, personas[], pains[], triggers[], objections[], channel_priority[]
voice_profile   tenant_id, written{tone, reading_level, dos[], donts[], banned[], examples[], emoji},
                spoken{provider, voice_id, avatar_id?}
media_provider  tenant_id, kind[image|composite|video|tts|avatar], provider, key(vault),
                defaults{}, status[live|no_credits|error]           # capability-probed like auth
media_recipe    key, produces[post_type…], steps[](provider chain), brand_assets_ref
content_hub     tenant_id, type[static-cf|wordpress|ghost|existing], connection, url_pattern, template
coverage_target tenant_id, channel, post_type, producible:bool, source_ok:bool, blockers[]
content_plan    tenant_id, pillars[], cadence_targets[], starter_batch_status
```

## Media-capability probes (mirror the auth probes)
| Provider | Probe | live | blocked |
|---|---|---|---|
| Recraft | account/credits endpoint | credits>0 | no key / 0 credits |
| OpenAI | tiny `gpt-image-1` test or models list | 200 | bad key |
| ElevenLabs | `/v1/user` (credit balance) | balance>0 | no key / 0 credits |
| HeyGen | account/quota | ok | no key |
| ffmpeg/PIL | local binary + font presence | present | missing fonts (map macOS→Linux) |

---

## How the three layers compose into COVERAGE
```
COVERAGE(tenant, channel, post_type) =
    Connect:  channel connected & capability live
  × Content:  a media_recipe produces post_type  &  content source wired
  × Cadence:  channel_config has this type enabled (Ops Console)
```
Green in all three → the runner posts it. The wizard proves this at **setup**; the
Operations Console monitors it at **runtime**. Same matrix, two moments.

## Maps to existing code
| Wizard piece | Existing |
|---|---|
| Written voice → prompts | booked-job's hardcoded voice in the content workflow |
| Spoken voice | `segment.py` (ElevenLabs), HeyGen pipeline |
| Media recipes | `make_statcard` / `make_reel` / `make_carousel` / `make_story` (PIL+ffmpeg) |
| Image gen | Recraft + gpt-image-1 integrations |
| Blog hub | `render_branch` + `blog_drip_runner` (create) or a WP/Ghost adapter (connect) |
| Coverage gate | `fetch_stats.coverage()` extended with produce-capability + source legs |
| Starter batch | the fact-checked content workflow |
| Cadence targets | `goals.json` / `channel_config` |

## Net: the full three-layer onboarding
1. **Connect** — auth every channel (shared master apps → fast).
2. **Content Setup** (this) — ICP, voice, media APIs, blog, **coverage gate**, starter batch.
3. **Operations Console** — Robots/Channels/Tasks/Strategy monitor the running tenant.
Green coverage board across all three → a fully-launched autonomous site, every
content type covered on every connected network.
