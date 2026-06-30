#!/usr/bin/env python3
"""
Organize the Marketing 101 course on YouTube:
  - re-title each uploaded lesson -> base + ' | Marketing 101 · Lesson N of 10' (<=100 chars)
  - create (or reuse) a 'Marketing 101' playlist and add the lessons in order
Uses secrets/youtube.env. Only touches the videos listed in IDS (the uploaded ones).
"""
import json, os, urllib.parse, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(__file__), "..")
V = "https://www.googleapis.com/youtube/v3"

IDS = {1: "hBaVKMFvXjE", 2: "QnECUMCpAbk", 3: "GjsJyDrICbk", 4: "gWpwCaxR4vM", 5: "9pT8tiLcnhc", 6: "xoxXFT7iRbE", 7: "7H-Oe8TIqiM", 8: "_Zrbjq-REJ0", 9: "PEoLZ0CMDF8", 10: "islbzITBJMU"}
BASE = {
 1: "What Marketing ACTUALLY Is — For Contractors Who Hate Marketing",
 2: "Why Cheap Leads Are Bankrupting Contractors (The 2 Numbers)",
 3: "The 5 Doors Every Customer Comes Through (Contractor Marketing)",
 4: "Get to the Top of Google for Free (Contractors: Your Map Pack)",
 5: "Why 98% of People Leave Your Contractor Website (Fix This)",
 6: "Why They Call the Other Guy: Reviews Decide It",
 7: "Should Contractors Pay for Leads? (Angi, Thumbtack, LSA)",
 8: "Stop Burning Money on Google Ads (Contractor's First Ad Dollar)",
 9: "Get Found by Google AND AI (The New Front Door)",
 10: "Your Marketing Scorecard — Run It Like an Owner",
}
PL_TITLE = "Marketing 101"
PL_DESC = ("The free, no-BS marketing course for home-service contractors — plumbers, HVAC, "
           "roofers, electricians, tree guys. Watch in order, Lesson 1 to 10. "
           "Get found. Get picked. Get booked.")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "youtube.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def token(e):
    body = urllib.parse.urlencode({"client_id": e["YT_CLIENT_ID"], "client_secret": e["YT_CLIENT_SECRET"],
        "refresh_token": e["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=body), timeout=30).read())["access_token"]


def api(url, tok, data=None, method="GET"):
    req = urllib.request.Request(url, data=(json.dumps(data).encode() if data is not None else None), method=method)
    req.add_header("Authorization", f"Bearer {tok}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())


def title_for(n):
    tag = f" | Marketing 101 · Lesson {n} of 10"
    base = BASE[n]
    if len(base) + len(tag) > 100:
        base = base[:100 - len(tag) - 1].rstrip() + "…"
    return base + tag


def main():
    e = env(); tok = token(e)
    # 1) re-title
    for n in sorted(IDS):
        cur = api(f"{V}/videos?part=snippet&id={IDS[n]}", tok)
        sn = cur["items"][0]["snippet"]
        sn["title"] = title_for(n)
        try:
            api(f"{V}/videos?part=snippet", tok, {"id": IDS[n], "snippet": sn}, "PUT")
            print(f"  retitled #{n}: {sn['title']}")
        except urllib.error.HTTPError as ex:
            print(f"  retitle #{n} FAILED {ex.code}: {ex.read().decode()[:160]}")
    # 2) playlist (reuse if one already named Marketing 101 exists)
    mine = api(f"{V}/playlists?part=snippet&mine=true&maxResults=50", tok)
    pid = next((p["id"] for p in mine.get("items", []) if p["snippet"]["title"] == PL_TITLE), None)
    if not pid:
        pl = api(f"{V}/playlists?part=snippet,status", tok,
                 {"snippet": {"title": PL_TITLE, "description": PL_DESC},
                  "status": {"privacyStatus": "unlisted"}}, "POST")
        pid = pl["id"]; print(f"  created playlist: {pid}")
    else:
        print(f"  reusing playlist: {pid}")
    # existing items (avoid dupes) — tolerate 404 on a freshly created/propagating playlist
    have = set()
    try:
        items = api(f"{V}/playlistItems?part=snippet&playlistId={pid}&maxResults=50", tok)
        for it in items.get("items", []):
            have.add(it["snippet"]["resourceId"].get("videoId"))
    except urllib.error.HTTPError:
        pass
    for n in sorted(IDS):
        if IDS[n] in have:
            print(f"  #{n} already in playlist"); continue
        try:
            api(f"{V}/playlistItems?part=snippet", tok,
                {"snippet": {"playlistId": pid, "position": n - 1,
                             "resourceId": {"kind": "youtube#video", "videoId": IDS[n]}}}, "POST")
            print(f"  added #{n} at position {n}")
        except urllib.error.HTTPError as ex:
            print(f"  add #{n} FAILED {ex.code}: {ex.read().decode()[:160]}")
    print(f"\nPlaylist: https://www.youtube.com/playlist?list={pid}")


if __name__ == "__main__":
    main()
