#!/usr/bin/env python3
"""Autonomous TikTok posting via Buffer (launchd). Hosts our vertical short videos
publicly (site/v/<id>.mp4) and queues the next un-posted one to TikTok via Buffer
with a caption. Decoupled hosting/posting: copies new videos into site/v (deploy
publishes them), and only posts videos whose public URL is already LIVE.
State: content/buffer_state.json['tiktok']"""
import argparse, datetime as dt, glob, json, os, shutil, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

VDIR = os.path.join(ROOT, "site", "v")
SHORTS = os.path.join(ROOT, "content", "shorts")
REELS = os.path.join(ROOT, "content", "reels")
STATE = os.path.join(ROOT, "content", "buffer_state.json")
QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
LOG = os.path.join(ROOT, "content", "buffer_tiktok.log")
BASE = "https://booked-job.com/v"
TAGS = "#contractor #trades #plumber #roofer #hvac #electrician #smallbusiness"


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def is_live(url):
    # Cloudflare blocks the default python-urllib UA — send a normal one.
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "curl/8.4.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def caption_for(vid):
    for it in load(QUEUE, {"items": []})["items"]:
        if it["id"] == vid:
            return (it.get("blurb", "") or it["title"]).split(". ")[0][:140] + "\n\n" + TAGS
    return f"{vid.replace('-', ' ').title()} — real talk for the trades.\n\n{TAGS}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    os.makedirs(VDIR, exist_ok=True)
    # 1) sync vertical videos into site/v (deploy publishes them)
    synced = []
    for src in sorted(glob.glob(f"{SHORTS}/*.mp4")) + sorted(glob.glob(f"{REELS}/*.mp4")):
        vid = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(VDIR, f"{vid}.mp4")
        if not os.path.exists(dst):
            shutil.copy(src, dst); synced.append(vid)
    if synced:
        log(f"hosted {len(synced)} new videos in site/v ({', '.join(synced)}) — will post once deployed/live")

    state = load(STATE, {}); done = set(state.get("tiktok", []))
    if a.status:
        print(json.dumps({"tiktok_done": list(done), "hosted": [os.path.basename(p)[:-4] for p in glob.glob(f'{VDIR}/*.mp4')]}, indent=2)); return
    if not os.path.exists(os.path.join(ROOT, "secrets", "buffer.env")):
        log("Buffer not connected — skipping."); return

    # 2) post the next un-posted video whose public URL is LIVE
    for src in sorted(glob.glob(f"{VDIR}/*.mp4")):
        vid = os.path.splitext(os.path.basename(src))[0]
        if vid in done:
            continue
        url = f"{BASE}/{vid}.mp4"
        if not is_live(url):
            log(f"'{vid}' not live yet at {url} — will retry next run"); continue
        import buffer_publish
        e = buffer_publish.env()
        try:
            buffer_publish.queue_video(e["BUFFER_TIKTOK_CHANNEL"], caption_for(vid), url, title=vid.replace("-", " ").title())
        except Exception as ex:
            log(f"TikTok queue failed for '{vid}': {ex}"); return
        done.add(vid); state["tiktok"] = list(done)
        json.dump(state, open(STATE, "w"), indent=2)
        log(f"QUEUED '{vid}' to TikTok via Buffer -> {url}")
        try:
            import log_change
            log_change.add("site", f"Queued to TikTok (Buffer): {vid}")
        except Exception:
            pass
        return
    log("no new live videos to post to TikTok.")


if __name__ == "__main__":
    main()
