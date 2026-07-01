# Connect UX — Multi-Tenant Posting-Engine Onboarding Spec

Turns the per-site credential/approval gauntlet into a ~20-minute wizard. Grounded
in the exact scopes, endpoints, and error codes proven out on Booked Job.

## Core principle: master apps, per-site assets
App Reviews / access grants attach to an **app or cloud project**, not a website.
One Meta app + one Google Cloud project can manage many pages / IG accounts / GBP
locations. So: do the heavy reviews ONCE on master apps; each new site = "add asset
+ OAuth consent" (no new review). The UX is built around this.

---

## Data model

```
tenant            id, name, domain, timezone, secret_sync{type:github, repo}, status
app_credential    id, provider, client_id, client_secret(vault),           # the MASTER apps
                  review_status{capability: approved|pending|na}            # shared across tenants
connection        id, tenant_id, provider, platform, account_ref,          # e.g. account_ref = IG user id
                  auth_type[oauth2|app_password|bot_token|api_key|system_user],
                  status[none|connecting|connected|expired|error|needs_reauth],
                  scopes[], last_verified_at
capability        connection_id, key[post|insights|dms|video|carousel|doc|poll|story],
                  state[live|blocked|pending_review|na], detail, checked_at, remediation
secret            connection_id, key, value(vault, encrypted), expires_at, rotates:bool
approval_request  tenant_id, platform, capability, form_type, prefill{}, submitted_at,
                  status[draft|submitted|approved|denied], external_ref, next_check_at
channel_config    tenant_id, platform, enabled, daily_cap, windows[], exclude_rules[]  # == the runner PLATFORMS dict
```

## Connection state machine
`none → connecting → connected → {healthy | expired | error | needs_reauth}`
Capability: `unknown → live | blocked(pending_review) | na`

---

## OAuth / auth-strategy registry
One hosted callback service (`connect.<agency>.com/oauth/callback/:provider`).
Per-provider strategy handles the flow + token exchange + refresh:

| Provider | auth_type | notes / gotcha |
|---|---|---|
| Meta (FB+IG) | system_user token | long-lived; scopes via `/debug_token`; App Review gates insights + messaging |
| Google (YT/Blogger/GBP) | oauth2 + refresh | one project, many scopes; GBP needs access-request (quota 0→300) |
| Bluesky | app_password | `createSession` → JWT; video via `uploadBlob` |
| Mastodon | oauth2 / token | per-instance |
| Threads | oauth2 | insights limited |
| Telegram | bot_token | `getMe` + channel id |
| Tumblr | oauth2 + **rotating** refresh | MUST persist rotated refresh token or 400 next run |
| Buffer | api key + org | free plan = 10-post queue cap → detect + surface |

Flow: wizard **Connect** → build auth URL from provider config → user approves →
callback exchanges code → store token in vault → **run capability probes** → update
connection + capabilities → **sync secret to tenant store** (GitHub secret API / env).

---

## Capability probe registry (the gold — read-only classify calls)
Each probe returns `{state, detail, remediation}`. These are the exact calls proven today.

| Platform · capability | Probe (read-only) | live | blocked → remediation |
|---|---|---|---|
| Meta · token/scopes | `GET /debug_token` | scopes list | — |
| Meta · post | `GET /{page}?fields=name` | 200 | invalid token → reconnect |
| IG · insights | `GET /{ig}/insights?metric=reach&period=day&metric_type=total_value` | 200 | `#10` → App Review (Advanced Access) |
| IG · dms | `GET /{ig}/conversations?platform=instagram` | 200 | `#3` → App Review (messaging) |
| GBP · post | `GET mybusinessaccountmanagement/v1/accounts` | 200 | `PERMISSION_DENIED`/quota 0 → access request |
| YouTube · stats | `GET channels?part=statistics&mine=true` | 200 | reconnect |
| Bluesky · post/video | `createSession` ok | JWT | bad app pw → reconnect |
| Buffer · post | `channels` + attempt; watch `LimitReachedError` | queued | free-plan cap → upgrade |
| Tumblr · post | token refresh + `user/info` | blog name | `invalid_grant` → re-auth |
| Telegram · post | `getMe` + `getChat(channel)` | ok | bad token/channel → fix |

The probe results render as a **capability matrix** (the auth version of the content
coverage matrix): rows = platforms, cells = live ✅ / blocked 🔒 / pending ⏳ / na —.

---

## Token-health daemon
Scheduled job: for each connection with a refresh token, refresh (Google, Tumblr
rotate-persist, FB long-lived exchange), re-run probes, flip to `needs_reauth` +
alert on failure → one-click reconnect in the UX. (Solves the Tumblr-rotation class
of bug centrally.)

## Approval tracker
`approval_request` rows carry **auto-prefilled** form text (templated per
platform+capability from tenant fields — we already drafted the GBP + IG-insights
justifications). `next_check_at` re-runs the capability probe and auto-flips
`pending → live` when access lands (exactly how IG insights was detected turning on).

---

## Wizard flow (screens)
1. **Create tenant** — name, domain, timezone, connect GitHub repo for secret sync.
2. **Assets** — enter/auto-list the page / IG / GBP / handle refs from the master app.
3. **Connections** — grid of platforms; each **Connect** → OAuth popup → auto-probe → badges.
4. **Capability matrix** — green/red/pending per capability, with remediation links (prefilled forms).
5. **Cadence** — per-platform daily caps + windows + exclude rules (edits `channel_config`).
6. **Readiness score** → **Go live** — enables the engine's GitHub Actions workflow for the tenant.

---

## Maps to what already exists (Booked Job)
| Spec component | Existing code |
|---|---|
| auth-strategy registry | `*_oauth.py` (tumblr/gbp/blogger), hosted `/oauth/callback` |
| capability probe registry | the `debug_token` / insights / conversations / quota probes written this session |
| secret vault + sync | `secrets/*.env` + `gh secret set ENV_*` |
| channel_config | `video_pool_runner.py` `PLATFORMS` dict |
| capability matrix UI | `fetch_stats.coverage()` + dashboard coverage panel |
| engine runtime | `run_all.py` + `.github/workflows/automation.yml` |

## Security
- Tokens in an encrypted vault (KMS/sealed secrets), never in plaintext logs.
- Least-privilege scopes per capability; per-tenant isolation.
- Secret sync one-way to the tenant's runtime (GitHub secret), rotated on reconnect.

## Net onboarding cost after this
Add asset (5 min, no review) → Connect wizard (10 min OAuth) → auto-test+store
(instant) → rare per-site approval (prefilled form + wait, tracked) → green board.
**Multi-week gauntlet → ~20 min of clicking + amortized one-time reviews.**
