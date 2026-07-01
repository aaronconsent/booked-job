# Operations Console — Multi-Tenant Posting-Engine Runtime Spec

Companion to `connect-ux-spec.md`. Connect *onboards* a tenant; this console
*monitors + steers* a live one. Covers the four dashboard tabs — **Robots,
Channels, Tasks, Strategy** — split along the engine/content line. Grounded in the
existing `run_all.py`, `fetch_stats.py`, and `nightly_review.py`.

Engine layers total: **Connect** (onboard) + **Operations Console** (this) = the
reusable engine. The **Content layer** (articles, reels, stats DB, fact-check
workflow) is scoped OUT and lives per-tenant.

---

## 1. ROBOTS — runner registry + run history + health  (✅ pure engine)

### Data model
```
runner       id, tenant_id|null(=template), key, category[Publishing|Visual|
             Engagement|Ops], schedule, enabled, media:bool, force_capable:bool
run          id, tenant_id, trigger[schedule|manual|force], started_at, finished_at,
             ok_count, fail_count, skip_count
run_step     run_id, runner_key, rc, tail, duration_ms, error        # one per agent per run
```
Health (derived): `last_success_at`, `consecutive_failures`,
`status[healthy|degraded|failing|idle]`, `success_rate_7d`.

### Views
- **Robots grid** — per runner: category · schedule · last run · status badge ·
  7-day success rate · [enable toggle] · [Run now → force].
- **Run history** — timeline of runs (ok/fail/skip); drill into `run_step` rows.
- **Alerts** — runner with `consecutive_failures ≥ N` → notify (SLA layer).

### Maps to existing code
`run_all.py` already emits per-agent `rc` + `tail` + a `"N ok, M failed, K skipped"`
summary → that is exactly `run` + `run_step`. `enumerate_agents()` → the `runner`
registry (name, category, schedule). `content/run_all.log` → `run_step` history.
The dashboard **Robots** tab renders this today.

---

## 2. CHANNELS — status + metrics + coverage  (✅ pure engine)

### Data model
```
channel        (== connection+capability from Connect spec) + display group[content|social]
channel_metric tenant_id, platform, date, metric[posts|views|likes|followers|reach], value
coverage_cell  tenant_id, platform, post_type, state[live|gap|soon|na], count
```

### Views
- **Scoreboard** — Content vs Social groups; social cards show Posts/Views/Likes/
  Followers (built today).
- **Coverage matrix** — post-type gaps per channel (built today).
- **Trends** — per-channel metric over time (from `channel_metric`).

### Maps to existing code
`fetch_stats.channels()` → channel rows + metrics; `fetch_stats.coverage()` →
`coverage_cell`; `content/metric_history.json` → `channel_metric` time series.
The dashboard **Channels** + scoreboard + coverage panels render this today.

---

## 3. TASKS — generic mechanism, per-tenant content  (🟡 mixed)

### Data model
```
cadence_target  tenant_id, key, label, category, period[daily|weekly|monthly], target
gap_rule        id, expr (compare actuals→target), severity, template_ref   # GENERIC engine
task            tenant_id, kind[gap|opportunity|manual], title, body, status
                [open|done|dismissed], source, created_at                    # PER-TENANT output
```

### The split
- **Engine ships:** the rule engine (actuals from `channel_metric` + run history vs
  `cadence_target` → emit gaps), the task store, the daily-review scheduler.
- **Tenant supplies:** the targets (`goals.yaml`) and the prompt *templates* the
  gaps render into (references that tenant's content/topics).

### Maps to existing code
`nightly_review.py` = the whole mechanism: computes progress vs `goals.json`, fires
gap triggers, writes copy-paste prompts → `goalsdata.json`. Generic engine; the
prompt bodies are the per-tenant content.

---

## 4. STRATEGY — mostly content, generic scaffolding  (🔴 content)

### Data model
```
strategy_doc  tenant_id, positioning, icp, pillars[], channel_priorities[]   # per-tenant content
              + structured cadence_targets (shared with Tasks)
strategist    tenant_id, headline, read, next_move, updated, next_review      # generated
```
- **Engine ships:** goals-progress rendering (bars, pace, on-track/behind) and the
  strategist card shell.
- **Tenant supplies:** the narrative (positioning, ICP, pillars) and target values.

### Maps to existing code
`goals.json` (targets + cadences) + `nightly_review` progress + `strategist.json`.
The **Strategy** tab renders progress bars + the strategist headline/next-move.

---

## Cross-cutting: unified Tenant Health
One score per tenant, engine-level, combining:
`connection_health (Connect) · runner_health (Robots) · coverage_completeness
(Channels) · goal_pace (Tasks)` → a single "is this site healthy + on track?" number
for an agency managing many tenants. Powers a portfolio view above the per-site console.

---

## What ports vs. what a tenant fills
| Layer | Ships in `engine/` | Tenant provides in `sites/<t>/` |
|---|---|---|
| Robots | runner registry, run/run_step, health, views | (nothing — auto) |
| Channels | metric pull, coverage calc, scoreboard/matrix views | (nothing — auto) |
| Tasks | rule engine, task store, scheduler, views | `goals.yaml`, prompt templates |
| Strategy | progress rendering, strategist shell | positioning/ICP/pillars narrative |

**Robots + Channels are ~100% engine (drop-in per tenant). Tasks + Strategy ship as
empty frameworks the content layer fills.** Combined with the Connect spec, this is
the complete reusable posting engine.
