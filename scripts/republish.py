#!/usr/bin/env python3
"""
Re-publish the corrected Marketing 101 lessons:
  1) set the 8 old (wrong-domain) unlisted uploads -> PRIVATE (reversible, NOT deleted)
  2) upload the corrected 10 lessons (unlisted)
  3) clear the Marketing 101 playlist and add the new 10 in order
  4) re-title the new 10 with the lesson-number tags
Reuses publish_all (upload + creds) and yt_organize (titles + playlist id).
"""
import json, urllib.parse, urllib.request, urllib.error
import publish_all as P
import yt_organize as YO

V = "https://www.googleapis.com/youtube/v3"
PL = "PLQVb1V1iNPtg"
OLD = dict(YO.IDS)  # {lesson: old_video_id}


def api(url, tok, data=None, method="GET"):
    req = urllib.request.Request(url, data=(json.dumps(data).encode() if data is not None else None), method=method)
    req.add_header("Authorization", f"Bearer {tok}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode()
        return json.loads(body) if body else {}


def main():
    tok = P.token(P.env())

    # 1) old -> private
    for n, vid in OLD.items():
        try:
            cur = api(f"{V}/videos?part=status&id={vid}", tok)
            st = cur["items"][0]["status"]; st["privacyStatus"] = "private"
            api(f"{V}/videos?part=status", tok, {"id": vid, "status": st}, "PUT")
            print(f"old L{n} ({vid}) -> private")
        except urllib.error.HTTPError as e:
            print(f"old L{n} private FAILED {e.code}: {e.read().decode()[:120]}")

    # 2) upload corrected 10
    newids = {}
    for n in range(1, 11):
        try:
            res = P.upload(tok, n, "unlisted")
            newids[n] = res["video_id"]
            print(f"uploaded corrected L{n} -> https://youtu.be/{res['video_id']} ({res['privacy']})")
        except urllib.error.HTTPError as e:
            print(f"upload L{n} FAILED {e.code}: {e.read().decode()[:160]}")

    # 3) clear playlist, then add new in order
    try:
        items = api(f"{V}/playlistItems?part=id&playlistId={PL}&maxResults=50", tok)
        for it in items.get("items", []):
            api(f"{V}/playlistItems?id={it['id']}", tok, method="DELETE")
        print(f"cleared {len(items.get('items', []))} old playlist items")
    except urllib.error.HTTPError as e:
        print(f"playlist clear note {e.code}")
    for n in range(1, 11):
        if n not in newids:
            continue
        try:
            api(f"{V}/playlistItems?part=snippet", tok,
                {"snippet": {"playlistId": PL, "position": n - 1,
                             "resourceId": {"kind": "youtube#video", "videoId": newids[n]}}}, "POST")
        except urllib.error.HTTPError as e:
            print(f"playlist add L{n} FAILED {e.code}")

    # 4) re-title with lesson tags
    for n in range(1, 11):
        if n not in newids:
            continue
        try:
            cur = api(f"{V}/videos?part=snippet&id={newids[n]}", tok)
            sn = cur["items"][0]["snippet"]; sn["title"] = YO.title_for(n)
            api(f"{V}/videos?part=snippet", tok, {"id": newids[n], "snippet": sn}, "PUT")
        except urllib.error.HTTPError as e:
            print(f"retitle L{n} FAILED {e.code}")

    print("\nNEW VIDEO IDS:", json.dumps(newids))
    print(f"Playlist: https://www.youtube.com/playlist?list={PL}")


if __name__ == "__main__":
    main()
