#!/usr/bin/env python3
"""Autonomous Buffer syndication (launchd) — queues the next article to LinkedIn
(text + link) via Buffer, the interim path until direct API approval. Reuses
content/syndication_queue.json. TikTok (video) handled by buffer_tiktok later.
State: content/buffer_state.json"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "buffer_state.json")
LOG = os.path.join(ROOT, "content", "buffer.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"linkedin": []})
    done = set(state.get("linkedin", []))
    if a.status:
        print(json.dumps({"linkedin_done": len(done), "remaining": [i["id"] for i in items if i["id"] not in done]}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "buffer.env")):
        log("Buffer not connected — skipping."); return
    import variants, buffer_publish
    e = buffer_publish.env()
    queued = 0
    for _ in range(12):                                   # loop-to-fill: max out Buffer's queue
        nxt = next((i for i in items if i["id"] not in done), None)
        if not nxt:
            log("syndication queue empty — nothing new for Buffer/LinkedIn."); break
        v = variants.get("linkedin", nxt["id"])
        text = v if v else f"{(nxt.get('blurb', '') or '')[:600]}\n\n{nxt['url']}"
        try:
            buffer_publish.queue_text(e["BUFFER_LINKEDIN_CHANNEL"], text)
        except Exception as ex:
            if "LimitReached" in str(ex):
                log(f"LinkedIn Buffer queue full — topped up {queued} this run, retry next."); break
            log(f"LinkedIn queue failed: {str(ex)[:160]}"); break
        done.add(nxt["id"]); state["linkedin"] = list(done)
        json.dump(state, open(STATE, "w"), indent=2)
        log(f"QUEUED '{nxt['id']}' to LinkedIn via Buffer"); queued += 1
        try:
            import log_change; log_change.add("site", f"Queued to LinkedIn (Buffer): {nxt['title']}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
