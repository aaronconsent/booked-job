#!/usr/bin/env python3
"""Refresh the Bluesky custom-feed skeleton (launchd, a few times/day). Does an
AUTHENTICATED searchPosts for trades/home-service terms and writes the matching
post URIs to site/feedskel.json, which the Worker serves as the feed. Commits+pushes
so it deploys. (The public AppView blocks unauthenticated search, hence this.)"""
import datetime as dt, json, os, subprocess, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import bluesky_publish as B

PDS = "https://bsky.social/xrpc"
OUT = os.path.join(ROOT, "site", "feedskel.json")
LOG = os.path.join(ROOT, "content", "bluesky_feed.log")
TERMS = ["contractor business", "home service business", "roofing business", "hvac business",
         "plumber business", "electrician business", "trades business", "contractor marketing"]


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def _get(path, jwt):
    req = urllib.request.Request(f"{PDS}/{path}")
    req.add_header("Authorization", f"Bearer {jwt}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    if not os.path.exists(os.path.join(ROOT, "secrets", "bluesky.env")):
        log("Bluesky not connected — skipping."); return
    e = B.env(); s = B.session(e); jwt = s["accessJwt"]
    seen, feed = set(), []
    for q in TERMS:
        try:
            res = _get("app.bsky.feed.searchPosts?" + urllib.parse.urlencode({"q": q, "limit": 20, "sort": "latest"}), jwt)
        except Exception as ex:
            log(f"search '{q}' failed: {ex}"); continue
        for p in res.get("posts", []):
            uri = p.get("uri")
            langs = p.get("record", {}).get("langs", ["en"])
            if uri and uri not in seen and "en" in langs:
                seen.add(uri); feed.append({"post": uri})
    feed = feed[:80]
    json.dump({"feed": feed, "updated": dt.datetime.now().isoformat(timespec="seconds")}, open(OUT, "w"))
    log(f"feed skeleton: {len(feed)} posts")
    try:
        subprocess.run(["git", "add", "site/feedskel.json"], cwd=ROOT, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "refresh bluesky feed skeleton"], cwd=ROOT, check=True, capture_output=True)
        subprocess.run(["git", "push"], cwd=ROOT, check=True, capture_output=True)
        log("pushed feedskel.json")
    except subprocess.CalledProcessError as ex:
        log(f"git push skipped: {ex.stderr.decode()[:120] if ex.stderr else ex}")


if __name__ == "__main__":
    main()
