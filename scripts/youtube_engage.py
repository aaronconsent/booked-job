#!/usr/bin/env python3
"""YouTube auto-CTA (launchd) — posts ONE pinned-style CTA comment on each new
upload, driving viewers to the blog + email list. Owner token, our own videos =
✅ ToS-safe. Needs the youtube.force-ssl scope on the OAuth token.
State: content/youtube_engage_state.json"""
import datetime as dt, json, os, random, sys, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATE = os.path.join(ROOT, "content", "youtube_engage_state.json")
LOG = os.path.join(ROOT, "content", "youtube_engage.log")
YT = "https://www.googleapis.com/youtube/v3"

CTAS = [
    "🔧 Full breakdown + free calculators (true cost per lead, pricing) over at booked-job.com — no-fluff business tips for the trades.",
    "Want the deep dive? booked-job.com has the full write-up + free tools for contractors. No pitch, just what works.",
    "More like this — getting more booked jobs, pricing right, getting paid — at booked-job.com 🛠️",
]


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "youtube.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def token(e):
    body = urllib.parse.urlencode({"client_id": e["YT_CLIENT_ID"], "client_secret": e["YT_CLIENT_SECRET"],
                                   "refresh_token": e["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", body, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def _get(path, tok):
    req = urllib.request.Request(f"{YT}/{path}"); req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    if not os.path.exists(os.path.join(ROOT, "secrets", "youtube.env")):
        log("YouTube not connected — skipping."); return
    e = env(); tok = token(e)
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}
    done = set(st["done"])
    try:
        up = _get("channels?part=contentDetails&mine=true", tok)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        vids = _get(f"playlistItems?part=snippet,contentDetails&playlistId={up}&maxResults=15", tok).get("items", [])
    except Exception as ex:
        log(f"list uploads failed: {ex}"); return
    posted = 0
    for v in vids:
        vid = v["contentDetails"]["videoId"]
        if vid in done:
            continue
        body = json.dumps({"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": random.choice(CTAS)}}}}).encode()
        req = urllib.request.Request(f"{YT}/commentThreads?part=snippet", data=body, method="POST")
        req.add_header("Authorization", f"Bearer {tok}"); req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                r.read()
            done.add(vid); posted += 1
            log(f"CTA comment posted on {vid}")
        except urllib.error.HTTPError as ex:
            log(f"comment failed on {vid} {ex.code}: {ex.read().decode()[:200]} (token may lack youtube.force-ssl scope)")
            break
    st["done"] = list(done)[-200:]; json.dump(st, open(STATE, "w"), indent=2)
    log(f"run: {posted} CTA comments posted")


if __name__ == "__main__":
    main()
