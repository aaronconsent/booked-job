#!/usr/bin/env python3
"""
Nightly review (launchd, ~23:15). Gathers analytics, measures actuals against the
daily/weekly/monthly goals in content/goals.json, fires gap triggers, and writes
COPY-PASTE PROMPTS Aaron can bring back to Claude to act on. Output ->
site/dashboard/goalsdata.json (the Goals tab reads it). History accrues in
content/goals_history.json so day/week/month deltas get accurate over time.

  python3 scripts/nightly_review.py            # full run (fetch stats, compute, write, push)
  python3 scripts/nightly_review.py --no-fetch # skip the stats refresh
  python3 scripts/nightly_review.py --dry-run  # compute + print, don't write/push
"""
import argparse, datetime as dt, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "site", "dashboard", "data.json")
GOALS = os.path.join(ROOT, "content", "goals.json")
HIST = os.path.join(ROOT, "content", "goals_history.json")
OUT = os.path.join(ROOT, "site", "dashboard", "goalsdata.json")
LOG = os.path.join(ROOT, "content", "nightly_review.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    try: return json.load(open(p))
    except Exception: return d


def counters(data):
    c = {}
    c["articles"] = len(glob.glob(os.path.join(ROOT, "site/blog/*/index.html")))
    c["reels"] = len(load(os.path.join(ROOT, "content/reels_state.json"), {}).get("done", []))
    total = 0
    for f, keys in [("buffer_state", ["linkedin", "tiktok"]), ("bluesky_state", ["done", "posted"]),
                    ("threads_state", ["done", "posted"]), ("mastodon_state", ["done", "posted"]),
                    ("tumblr_state", ["done", "posted"]), ("telegram_state", ["done", "posted"]),
                    ("blogger_state", ["done"]), ("ghpages_state", ["done"]), ("telegraph_state", ["done"]),
                    ("ig_state", ["done", "posted"]), ("pinterest_buffer_state", ["done"])]:
        d = load(os.path.join(ROOT, "content", f"{f}.json"), {})
        for k in keys:
            v = d.get(k)
            if isinstance(v, list): total += len(v)
    ps = load(os.path.join(ROOT, "content/state.json"), {})
    total += sum(ps.get("by_date", {}).values()) if isinstance(ps.get("by_date"), dict) else 0
    c["social_posts"] = total
    c["followers"] = sum((ch.get("followers") or 0) for ch in data.get("channels", []))
    cont = data.get("content", {}) or {}
    c["engagement"] = (cont.get("reactions", 0) or 0) + (cont.get("comments", 0) or 0) + (cont.get("shares", 0) or 0)
    yt = data.get("youtube", {}) or {}
    c["yt_views"] = yt.get("views", 0) or 0
    c["yt_shorts"] = yt.get("videos", yt.get("shorts", 0)) or 0
    em = data.get("email", {}) or {}
    c["email_subs"] = em.get("subs", em.get("subscribers", 0)) or 0
    c["traffic"] = 0  # no analytics source connected yet
    return c


def snap_at(history, on_or_before):
    elig = [h for h in history if h["date"] <= on_or_before]
    return elig[-1] if elig else None


def progress(goals, today_c, history, today, period_start, has_prior):
    """For each cadence goal, compute the windowed current vs target + status."""
    starts = {"daily": (today - dt.timedelta(days=1)).isoformat(),
              "weekly": (today - dt.timedelta(days=7)).isoformat(),
              "monthly": period_start}
    elapsed = {"daily": 1, "weekly": min(7, today.weekday() + 1),
               "monthly": max(1, (today - dt.date.fromisoformat(period_start)).days + 1)}
    span = {"daily": 1, "weekly": 7, "monthly": 30}
    out = {}
    for cad, items in goals.get("cadences", {}).items():
        rows = []
        for g in items:
            base = snap_at(history, starts.get(cad, period_start))
            cur = max(0, today_c.get(g["key"], 0) - base.get(g["key"], 0)) if base else 0
            if g.get("needs") == "analytics" or not has_prior:
                cur, status = None, "nodata"     # can't measure a window yet
            else:
                tgt = g["target"]; exp = tgt * (elapsed[cad] / span[cad])
                status = "green" if (cur >= tgt or cur >= exp) else ("yellow" if cur >= exp * 0.6 else "red")
            rows.append({"key": g["key"], "cat": g["cat"], "icon": g["icon"], "label": g["label"],
                         "current": cur, "target": g["target"], "status": status, "needs": g.get("needs")})
        out[cad] = rows
    return out


def queue_health():
    def rem(path, listkey, statefile, donekey):
        items = load(os.path.join(ROOT, path), {}).get(listkey, [])
        done = set(load(os.path.join(ROOT, statefile), {}).get(donekey, []))
        ids = [i.get("id") for i in items]
        return sum(1 for i in ids if i not in done), len(ids)
    fb = load(os.path.join(ROOT, "content/queue.json"), {}).get("posts", [])
    fbdone = set(load(os.path.join(ROOT, "content/state.json"), {}).get("posted", []))
    fb_rem = sum(1 for p in fb if p.get("id") not in fbdone)
    reels_rem, _ = rem("content/reels_queue.json", "reels", "content/reels_state.json", "done")
    staged = load(os.path.join(ROOT, "content/schedule.json"), {"items": []}).get("items", [])
    staged_pending = sum(1 for s in staged if s.get("status") == "pending")
    return {"fb_ig_posts": fb_rem, "reels": reels_rem, "staged_articles": staged_pending}


def build_prompts(prog, queues, has_prior):
    P = []
    def add(title, why, prompt): P.append({"title": title, "why": why, "prompt": prompt})

    if queues["fb_ig_posts"] < 12:
        add("📣 FB/IG queue running low", f"Only {queues['fb_ig_posts']} posts left (goal ~12/day).",
            "Top up the FB/IG queue — generate a batch of stat cards / quote-card variants from the stats DB and queue them.")
    if queues["reels"] < 5:
        add("🎬 Reels queue low", f"Only {queues['reels']} reels queued (need ~7/week).",
            "Cut more vertical clips from the podcast and course and add them to the reels queue.")
    if queues["staged_articles"] < 6:
        add("📝 Article pipeline thin", f"Only {queues['staged_articles']} articles staged to drip.",
            "Run another branch-series workflow batch and stage it to drip 2/day.")

    # traffic always-on until analytics connected
    add("🌐 Website traffic isn't tracked", "No analytics source is connected, so traffic goals show no data.",
        "Set up Cloudflare Web Analytics (I'll add a CF token) so website visits show on the Goals page and feed the nightly review.")

    # weekly gap triggers (only once we can actually measure a window)
    for r in (prog.get("weekly", []) if has_prior else []):
        if r["status"] == "red" and r["current"] is not None:
            behind = r["target"] - r["current"]
            tip = {"Content": "run a content workflow batch (staged)",
                   "Social": "refill the social queues / add more variant cards",
                   "Reels": "cut more podcast & course clips",
                   "Video": "produce more YouTube Shorts from the course/podcast"}.get(r["cat"], "produce more")
            add(f"{r['icon']} {r['label']} behind this week",
                f"{r['current']}/{r['target']} — {behind} short of pace.",
                f"We're behind on {r['label'].lower()} this week ({r['current']}/{r['target']}). {tip.capitalize()}.")

    top = P[0]["prompt"] if P else "On pace — keep the machine running and review channel winners."
    return P, top


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    today = dt.date.today()

    if not a.no_fetch:
        try:
            subprocess.run([sys.executable, os.path.join(HERE, "fetch_stats.py")], cwd=ROOT, timeout=300, check=False)
        except Exception as e:
            log(f"fetch_stats failed (continuing with cached): {str(e)[:120]}")

    data = load(DATA, {})
    goals = load(GOALS, {})
    period_start = goals.get("period", {}).get("start", today.isoformat())
    today_c = counters(data)

    history = load(HIST, [])
    has_prior = any(h.get("date", "") < today.isoformat() for h in history)
    history = [h for h in history if h.get("date") != today.isoformat()]
    history.append({"date": today.isoformat(), **today_c})
    history = sorted(history, key=lambda h: h["date"])[-120:]

    prog = progress(goals, today_c, history, today, period_start, has_prior)
    queues = queue_health()
    prompts, top = build_prompts(prog, queues, has_prior)

    out = {"generated": dt.datetime.now().isoformat(timespec="minutes"),
           "period": goals.get("period", {}), "rationale": goals.get("rationale", ""),
           "progress": prog, "queues": queues, "counters": today_c,
           "top_move": top, "prompts": prompts}

    if a.dry_run:
        print(json.dumps(out, indent=2)[:2500]); return

    json.dump(history, open(HIST, "w"), indent=2)
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"review written — {len(prompts)} prompts, top: {top[:70]}")

    os.chdir(ROOT)
    subprocess.run(["git", "add", "site/dashboard/goalsdata.json"], check=False)
    if subprocess.run(["git", "commit", "-q", "-m", f"nightly review {today.isoformat()}"]).returncode == 0:
        subprocess.run(["git", "push", "-q"], check=False); log("pushed.")


if __name__ == "__main__":
    main()
