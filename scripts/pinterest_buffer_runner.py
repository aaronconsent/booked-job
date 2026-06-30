#!/usr/bin/env python3
"""
Pinterest via Buffer (interim until direct pins:write API access is granted).
Tops up the Buffer Pinterest queue one pin at a time from the syndication queue.
Buffer's free plan caps each channel at 10 queued posts, so this self-paces:
when the queue is full Buffer returns LimitReachedError and we just retry next run.

State: content/pinterest_buffer_state.json (done ids). Log: content/pinterest_buffer.log.
Flags: --status, --dry-run, --force (ignored — always tries the next one).

    python3 scripts/pinterest_buffer_runner.py
"""
import argparse, datetime as dt, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import buffer_publish as BP, make_pin

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "pinterest_buffer_state.json")
LOG = os.path.join(ROOT, "content", "pinterest_buffer.log")
PINS = os.path.join(ROOT, "content", "pins")
SITE_PINS = os.path.join(ROOT, "site", "pins")
BASE = "https://booked-job.com/pins"


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def tags(labels):
    base = ["#contractor", "#trades", "#smallbusiness", "#contractormarketing"]
    extra = ["#" + "".join(w.capitalize() for w in l.split()) for l in (labels or [])[:3]]
    out = []
    for t in base + extra:
        if t.lower() not in [s.lower() for s in out]:
            out.append(t)
    return " ".join(out[:6])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"done": []})
    done = set(state["done"])

    if a.status:
        rem = [it["id"] for it in items if it["id"] not in done]
        print(json.dumps({"done": len(done), "remaining": rem}, indent=2)); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "buffer.env")):
        log("Buffer not connected — skipping."); return
    e = BP.env(); ch = e.get("BUFFER_PINTEREST_CHANNEL")
    if not ch:
        log("BUFFER_PINTEREST_CHANNEL not set in secrets/buffer.env — skipping."); return

    # Top up Buffer's Pinterest queue until it's full (LimitReached) or we run dry.
    queued = 0
    for _ in range(12):                                  # safety cap per run
        nxt = next((it for it in items if it["id"] not in done), None)
        if not nxt:
            log("all articles pinned — nothing new for Pinterest/Buffer."); break
        img = os.path.join(PINS, f"{nxt['id']}.png")
        if not os.path.exists(img):
            make_pin.make(nxt.get("short_title") or nxt["title"], nxt.get("blurb", ""), img)
        os.makedirs(SITE_PINS, exist_ok=True)
        hosted = os.path.join(SITE_PINS, f"{nxt['id']}.png")
        if not os.path.exists(hosted):
            shutil.copy(img, hosted)
            log(f"built pin '{nxt['id']}' -> push needed to make {BASE}/{nxt['id']}.png public")
        if a.dry_run:
            log(f"DRY-RUN next pin '{nxt['id']}', not queuing"); break
        text = f"{nxt.get('blurb', '').strip()} {nxt['url']} {tags(nxt.get('labels'))}"[:480]
        try:
            BP.queue_text(ch, text, assets=[{"image": {"url": f"{BASE}/{nxt['id']}.png"}}])
            done.add(nxt["id"]); state["done"] = list(done)
            json.dump(state, open(STATE, "w"), indent=2)
            log(f"QUEUED pin '{nxt['id']}' to Buffer (Pinterest)"); queued += 1
        except Exception as ex:
            if "LimitReached" in str(ex):
                log(f"Buffer Pinterest queue full — topped up {queued} this run, retry next."); break
            log(f"pin queue failed '{nxt['id']}': {str(ex)[:160]}"); break


if __name__ == "__main__":
    main()
