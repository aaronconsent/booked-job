#!/usr/bin/env python3
"""
Blog drip runner (launchd, daily). Publishes only the staged articles whose
go-live date has arrived — so a big batch trickles onto the live site a few a
day instead of all at once (natural-looking growth, not a content dump).

Reads content/schedule.json + content/staged/<slug>.json, renders the due ones
via render_branch.wire_articles(), marks them live, and git-pushes so Cloudflare
deploys. State lives in schedule.json. Log: content/blog_drip.log.

Flags: --status, --dry-run, --force (publish all currently-due ignoring the cap).
"""
import argparse, datetime as dt, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import render_branch as RB

SCHEDULE = os.path.join(ROOT, "content", "schedule.json")
STAGED = os.path.join(ROOT, "content", "staged")
LOG = os.path.join(ROOT, "content", "blog_drip.log")
MAX_PER_RUN = 3          # safety cap so a backlog still drips, never dumps


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(SCHEDULE):
        log("no content/schedule.json — nothing staged."); return
    sched = json.load(open(SCHEDULE))
    items = sched["items"]
    today = dt.date.today()
    pending = [it for it in items if it["status"] == "pending"]
    due = [it for it in pending if dt.date.fromisoformat(it["go_live"]) <= today]

    if a.status:
        nxt = sorted(p["go_live"] for p in pending)[:3]
        print(json.dumps({"pending": len(pending), "live": sum(1 for i in items if i["status"] == "live"),
                          "due_now": len(due), "next_dates": nxt}, indent=2)); return

    if not due:
        nxt = min((p["go_live"] for p in pending), default="—")
        log(f"nothing due today ({len(pending)} still scheduled, next {nxt})."); return

    batch = due if a.force else due[:MAX_PER_RUN]
    arts = []
    for it in batch:
        p = os.path.join(STAGED, f"{it['slug']}.json")
        if os.path.exists(p):
            arts.append(json.load(open(p)))
        else:
            log(f"WARN staged file missing for {it['slug']} — skipping"); it["status"] = "missing"
    arts = [x for x in arts if x]
    if not arts:
        log("nothing to publish (staged files missing)."); json.dump(sched, open(SCHEDULE, "w"), indent=2); return

    if a.dry_run:
        log(f"DRY-RUN would publish {len(arts)}: {', '.join(x['slug'] for x in arts)}"); return

    built = RB.wire_articles(arts)
    for it in batch:
        if it["slug"] in built:
            it["status"] = "live"; it["published"] = today.isoformat()
    json.dump(sched, open(SCHEDULE, "w"), indent=2)
    log(f"PUBLISHED {len(built)} staged articles: {', '.join(built)}")

    # deploy
    os.chdir(ROOT)
    subprocess.run(["git", "add", "site/blog", "site/sitemap.xml", "content/syndication_queue.json",
                    "content/channel_variants.json", "content/queue.json", "content/schedule.json"], check=False)
    msg = f"blog drip: publish {len(built)} ({today.isoformat()})"
    if subprocess.run(["git", "commit", "-q", "-m", msg]).returncode == 0:
        subprocess.run(["git", "push", "-q"], check=False)
        log("pushed — Cloudflare deploying.")
    else:
        log("nothing to commit.")


if __name__ == "__main__":
    main()
