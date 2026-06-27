#!/usr/bin/env python3
"""Facebook multi-photo carousel posting (launchd). Posts the article's slide images
as a swipeable multi-photo feed post (FB's saveable/shareable format), link in the
first comment. Reuses the same rendered slide images as the IG carousel.
State: content/fb_carousel_state.json"""
import argparse, datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_carousel

GRAPH = "https://graph.facebook.com/v21.0"
CFG = os.path.join(ROOT, "content", "linkedin_carousels.json")
STATE = os.path.join(ROOT, "content", "fb_carousel_state.json")
LOG = os.path.join(ROOT, "content", "fb_carousel.log")
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
    cfg = load(CFG, {"carousels": {}})["carousels"]
    state = load(STATE, {"done": []}); done = set(state["done"])
    for slug, c in cfg.items():
        if not os.path.exists(os.path.join(IMGDIR, f"{slug}-1.png")):
            make_carousel.make_images(slug, c["title"], c["slides"])
    if a.status:
        print(json.dumps({"done": list(done)}, indent=2)); return
    e = env(); page = e["FB_PAGE_ID"]; tok = e["FB_PAGE_TOKEN"]
    q = load(os.path.join(ROOT, "content", "syndication_queue.json"), {"items": []})["items"]
    for slug, c in cfg.items():
        if slug in done:
            continue
        n = len(c["slides"])
        urls = [f"{BASE}/{slug}-{i+1}.png" for i in range(n)]
        if not all(is_live(u) for u in urls):
            log(f"'{slug}' images not all live — retry next run"); continue
        try:
            # 1) upload each photo unpublished
            fbids = [_post(f"{page}/photos", {"url": u, "published": "false", "access_token": tok})["id"] for u in urls]
            # 2) feed post with attached_media + share CTA
            item = next((i for i in q if i["id"] == slug), {})
            hook = (item.get("blurb", "") or c["title"]).split(". ")[0][:180]
            msg = f"{c['title']}\n\n{hook}.\n\nSwipe through 👉 and send this to the contractor who needs it. 🛠️"
            params = [("message", msg), ("access_token", tok)]
            for i, fid in enumerate(fbids):
                params.append((f"attached_media[{i}]", json.dumps({"media_fbid": fid})))
            post = _post(f"{page}/feed", params)
            # 3) link in first comment
            url = item.get("url", "https://booked-job.com/blog/")
            _post(f"{post['id']}/comments", {"message": f"Full breakdown 👉 {url}", "access_token": tok})
        except Exception as ex:
            log(f"FB carousel failed for '{slug}': {ex}"); return
        done.add(slug); state["done"] = list(done)
        json.dump(state, open(STATE, "w"), indent=2)
        log(f"POSTED FB carousel '{slug}' -> {post.get('id')}")
        return
    log("no new live carousels to post to FB.")


if __name__ == "__main__":
    main()
