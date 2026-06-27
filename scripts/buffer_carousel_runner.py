#!/usr/bin/env python3
"""LinkedIn PDF document-carousel posting via Buffer (launchd, weekly). Generates a
branded multi-slide PDF per article (make_carousel), hosts it at booked-job.com/docs/,
and posts the next live one to LinkedIn as a document (highest-engagement LinkedIn
format). Decoupled hosting (generate -> deploy -> post when live).
State: content/buffer_state.json['linkedin_carousel']"""
import argparse, datetime as dt, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_carousel, variants

CFG = os.path.join(ROOT, "content", "linkedin_carousels.json")
STATE = os.path.join(ROOT, "content", "buffer_state.json")
LOG = os.path.join(ROOT, "content", "buffer_carousel.log")
DOCS = os.path.join(ROOT, "site", "docs")
BASE = "https://booked-job.com/docs"


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
    state = load(STATE, {}); done = set(state.get("linkedin_carousel", []))
    # 1) generate any missing carousels (so they deploy)
    gen = []
    for slug, c in cfg.items():
        if not os.path.exists(os.path.join(DOCS, f"{slug}.pdf")):
            make_carousel.make(slug, c["title"], c["slides"]); gen.append(slug)
    if gen:
        log(f"generated carousels: {', '.join(gen)} — will post once deployed/live")
    if a.status:
        print(json.dumps({"done": list(done), "carousels": list(cfg)}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "buffer.env")):
        log("Buffer not connected — skipping."); return
    # 2) post next un-posted whose PDF + thumbnail are live
    import buffer_publish
    e = buffer_publish.env()
    for slug, c in cfg.items():
        if slug in done:
            continue
        pdf_url, thumb_url = f"{BASE}/{slug}.pdf", f"{BASE}/{slug}.png"
        if not (is_live(pdf_url) and is_live(thumb_url)):
            log(f"'{slug}' carousel not live yet — will retry next run"); continue
        caption = variants.get("linkedin", slug) or c["title"]
        try:
            buffer_publish.queue_document(e["BUFFER_LINKEDIN_CHANNEL"], caption, pdf_url, c["title"], thumb_url)
        except Exception as ex:
            log(f"carousel post failed for '{slug}': {ex}"); return
        done.add(slug); state["linkedin_carousel"] = list(done)
        json.dump(state, open(STATE, "w"), indent=2)
        log(f"POSTED carousel '{slug}' to LinkedIn via Buffer -> {pdf_url}")
        return
    log("no new live carousels to post.")


if __name__ == "__main__":
    main()
