#!/usr/bin/env python3
"""Parse the runner logs into a clean 'Recent Posts' feed for the dashboard.
Writes site/dashboard/recent.json = {updated, posts:[{ts, channel, item, url}]}."""
import glob, json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOGDIR = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "site", "dashboard", "recent.json")

# only these logs are posting logs (skip engage/fetch/report/poll logs)
SKIP = ("engage", "poll", "report", "review", "fetch", "discover", "inbox", "feed_refresh", "health")
TS = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
URL = r"(https?://\S+|at://\S+)"
PATTERNS = [
    re.compile(TS + r"\s+(\w+):\s+POSTED\s+'([^']+)'"),              # pool: "channel: POSTED 'item'"
    re.compile(TS + r"\s+(?:POSTED|PUBLISHED)[^']*'([^']+)'\s+to\s+(\w+)"),  # "POSTED 'item' to Channel"
    re.compile(TS + r"\s+PUBLISHED\s+Short\s+'([^']+)'"),            # youtube
    re.compile(TS + r"\s+PUBLISHED\s+reel\s+'([^']+)'\s+\((\w+)\)"),  # reels: "reel 'item' (FB)"
]


def parse_line(line, logname):
    url_m = re.search(URL, line)
    url = url_m.group(1) if url_m else None
    # 1) "channel: POSTED 'item'"
    m = PATTERNS[0].search(line)
    if m:
        return {"ts": m.group(1), "channel": m.group(2).lower(), "item": m.group(3), "url": url}
    # 2) "POSTED 'item' to Channel"
    m = PATTERNS[1].search(line)
    if m:
        return {"ts": m.group(1), "channel": m.group(3).lower(), "item": m.group(2), "url": url}
    # 3) youtube "PUBLISHED Short 'item'"
    m = PATTERNS[2].search(line)
    if m and "youtube" in logname:
        return {"ts": m.group(1), "channel": "youtube", "item": m.group(2), "url": url}
    # 4) reels "PUBLISHED reel 'item' (FB)"
    m = PATTERNS[3].search(line)
    if m:
        return {"ts": m.group(1), "channel": m.group(3).lower(), "item": m.group(2), "url": url}
    return None


def main():
    posts, seen = [], set()
    for f in glob.glob(os.path.join(LOGDIR, "*.log")):
        name = os.path.basename(f)
        if any(s in name for s in SKIP):
            continue
        try:
            lines = open(f, errors="ignore").read().splitlines()
        except Exception:
            continue
        for line in lines[-400:]:
            if "POSTED" not in line and "PUBLISHED" not in line:
                continue
            p = parse_line(line, name)
            if not p:
                continue
            key = (p["ts"], p["channel"], p["item"])
            if key in seen:
                continue
            seen.add(key); posts.append(p)
    posts.sort(key=lambda p: p["ts"], reverse=True)
    posts = posts[:60]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    import datetime as dt
    json.dump({"updated": dt.datetime.now().isoformat(timespec="minutes"), "posts": posts},
              open(OUT, "w"), indent=2)
    print(f"recent.json: {len(posts)} posts across {len({p['channel'] for p in posts})} channels")


if __name__ == "__main__":
    main()
