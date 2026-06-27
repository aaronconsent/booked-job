#!/usr/bin/env python3
"""TikTok photo-carousel posting via Buffer (launchd). Posts an article's slide
images as a TikTok photo carousel (native, underused, strong saves). Reuses the
same rendered slides as IG/FB carousels. State: content/buffer_state.json['tiktok_carousel']"""
import argparse, datetime as dt, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_carousel

CFG = os.path.join(ROOT, "content", "linkedin_carousels.json")
STATE = os.path.join(ROOT, "content", "buffer_state.json")
LOG = os.path.join(ROOT, "content", "buffer_tiktok_carousel.log")
IMGDIR = os.path.join(ROOT, "site", "img")
BASE = "https://booked-job.com/img"
TAGS = "#contractor #trades #plumber #roofer #hvac #electrician #smallbusiness #contractorlife"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    cfg = load(CFG, {"carousels": {}})["carousels"]
    state = load(STATE, {}); done = set(state.get("tiktok_carousel", []))
    for slug, c in cfg.items():
        if not os.path.exists(os.path.join(IMGDIR, f"{slug}-1.png")):
            make_carousel.make_images(slug, c["title"], c["slides"])
    if a.status:
        print(json.dumps({"done": list(done)}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "buffer.env")):
        log("Buffer not connected — skipping."); return
    q = load(os.path.join(ROOT, "content", "syndication_queue.json"), {"items": []})["items"]
    import buffer_publish
    e = buffer_publish.env()
    for slug, c in cfg.items():
        if slug in done:
            continue
        n = len(c["slides"])
        urls = [f"{BASE}/{slug}-{i+1}.png" for i in range(n)]
        if not all(is_live(u) for u in urls):
            log(f"'{slug}' images not all live — retry next run"); continue
        item = next((i for i in q if i["id"] == slug), {})
        hook = (item.get("blurb", "") or c["title"]).split(". ")[0][:120]
        caption = f"{c['title']} — swipe 👉\n\n{hook}.\n\n{TAGS}"
        try:
            buffer_publish.queue_images(e["BUFFER_TIKTOK_CHANNEL"], caption, urls)
        except Exception as ex:
            log(f"TikTok carousel failed for '{slug}': {ex}"); return
        done.add(slug); state["tiktok_carousel"] = list(done)
        json.dump(state, open(STATE, "w"), indent=2)
        log(f"QUEUED TikTok photo carousel '{slug}' to Buffer")
        return
    log("no new live carousels for TikTok.")


if __name__ == "__main__":
    main()
