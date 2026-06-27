#!/usr/bin/env python3
"""Instagram carousel posting (launchd). Renders an article's slides as images,
hosts them at booked-job.com/img/, and posts the next live one as an IG carousel
(saveable teaching content — IG's highest-save format). Reuses the LinkedIn
carousel slide content. State: content/ig_carousel_state.json"""
import argparse, datetime as dt, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_carousel

CFG = os.path.join(ROOT, "content", "linkedin_carousels.json")
STATE = os.path.join(ROOT, "content", "ig_carousel_state.json")
LOG = os.path.join(ROOT, "content", "ig_carousel.log")
IMGDIR = os.path.join(ROOT, "site", "img")
BASE = "https://booked-job.com/img"
TAGS = "#contractor #plumber #roofer #hvac #electrician #homeservice #trades #contractorlife #smallbusiness"


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def is_live(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def caption_for(slug, c):
    q = load(os.path.join(ROOT, "content", "syndication_queue.json"), {"items": []})["items"]
    blurb = next((i.get("blurb", "") for i in q if i["id"] == slug), "")
    hook = blurb.split(". ")[0][:160] if blurb else c["title"]
    return f"{c['title']}\n\n{hook}.\n\nSave this for your next slow week 🛠️ and DM it to whoever runs your numbers.\n\n{TAGS}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    cfg = load(CFG, {"carousels": {}})["carousels"]
    state = load(STATE, {"done": []}); done = set(state["done"])
    # 1) render slide images for any not yet rendered
    for slug, c in cfg.items():
        if not os.path.exists(os.path.join(IMGDIR, f"{slug}-1.png")):
            make_carousel.make_images(slug, c["title"], c["slides"]); log(f"rendered IG slides for {slug}")
    if a.status:
        print(json.dumps({"done": list(done), "carousels": list(cfg)}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "fb.env")):
        log("FB/IG not connected — skipping."); return
    # 2) post next un-posted whose images are all live
    import ig_publish
    for slug, c in cfg.items():
        if slug in done:
            continue
        n = len(c["slides"])
        urls = [f"{BASE}/{slug}-{i+1}.png" for i in range(n)]
        if not all(is_live(u) for u in urls):
            log(f"'{slug}' images not all live yet — retry next run"); continue
        try:
            res = ig_publish.publish_carousel(urls, caption_for(slug, c))
        except Exception as ex:
            log(f"IG carousel failed for '{slug}': {ex}"); return
        done.add(slug); state["done"] = list(done)
        json.dump(state, open(STATE, "w"), indent=2)
        log(f"POSTED IG carousel '{slug}' -> {res.get('id')}")
        try:
            import log_change
            log_change.add("site", f"Posted IG carousel: {c['title']}")
        except Exception:
            pass
        return
    log("no new live carousels to post to IG.")


if __name__ == "__main__":
    main()
