#!/usr/bin/env python3
"""IG + FB Stories (launchd) — daily-presence 9:16 cards. Renders a story card,
hosts it, and posts it as an Instagram Story + a Facebook photo Story. Cycles
through articles (stories vanish in 24h). State: content/story_state.json"""
import argparse, datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_story

GRAPH = "https://graph.facebook.com/v21.0"
CFG = os.path.join(ROOT, "content", "stories.json")
STATE = os.path.join(ROOT, "content", "story_state.json")
LOG = os.path.join(ROOT, "content", "story.log")
IMGDIR = os.path.join(ROOT, "site", "img")
BASE = "https://booked-job.com/img"


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "fb.env")):
        if "=" in line:
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _post(path, params):
    req = urllib.request.Request(f"{GRAPH}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def is_live(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    stories = load(CFG, {"stories": {}})["stories"]
    state = load(STATE, {"done": []}); done = set(state["done"])
    # render any missing cards
    for slug, s in stories.items():
        if not os.path.exists(os.path.join(IMGDIR, f"{slug}-story.png")):
            make_story.make(slug, s["headline"], s["sub"]); log(f"rendered story card for {slug}")
    if a.status:
        print(json.dumps({"done": list(done), "stories": list(stories)}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "fb.env")):
        log("FB/IG not connected — skipping."); return
    nxt = next((s for s in stories if s not in done), None)
    if not nxt:
        done = set(); nxt = next(iter(stories), None)  # cycle
    if not nxt:
        log("no stories configured."); return
    url = f"{BASE}/{nxt}-story.png"
    if not is_live(url):
        log(f"'{nxt}' story card not live yet — retry next run"); return
    e = env(); page = e["FB_PAGE_ID"]; ptok = e["FB_PAGE_TOKEN"]
    # IG story
    try:
        import ig_publish
        r = ig_publish.publish_story(url)
        log(f"IG story posted '{nxt}' -> {r.get('id')}")
    except Exception as ex:
        log(f"IG story failed '{nxt}': {ex}")
    # FB photo story
    try:
        fid = _post(f"{page}/photos", {"url": url, "published": "false", "access_token": ptok})["id"]
        r = _post(f"{page}/photo_stories", {"photo_id": fid, "access_token": ptok})
        log(f"FB story posted '{nxt}' -> {r.get('post_id') or r.get('id') or 'ok'}")
    except Exception as ex:
        log(f"FB story failed '{nxt}': {ex}")
    done.add(nxt); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)


if __name__ == "__main__":
    main()
