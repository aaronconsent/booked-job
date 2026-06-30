#!/usr/bin/env python3
"""
Customize the Booked Job YouTube channel via the Data API:
  - upload + set the channel BANNER (channelBanners.insert -> channels.update)
  - set the channel DESCRIPTION + KEYWORDS (brandingSettings)
Reuses secrets/youtube.env (refresh token). Avatar/profile pic is NOT settable
via the public API (Studio only).
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(__file__), "..")
BANNER = os.path.join(ROOT, "content", "course", "booked-job-youtube-banner.png")
TOKEN_URL = "https://oauth2.googleapis.com/token"
BANNER_UP = "https://www.googleapis.com/upload/youtube/v3/channelBanners/insert"
CH = "https://www.googleapis.com/youtube/v3/channels"

DESCRIPTION = (
    "Booked Job — honest, no-BS marketing for home-service contractors. "
    "Plumbers, HVAC, roofers, electricians, tree guys: it doesn't matter what you swing. "
    "We teach you the stuff nobody taught you, in plain English, so you can get found, "
    "get picked, and get booked — without getting fleeced by a guy in a vest.\n\n"
    "Start with the free Marketing 101 course. Get found. Get picked. Get booked.\n\n"
    "\U0001f517 booked-jobs.com")
KEYWORDS = ('"contractor marketing" "home services" "plumber marketing" "hvac marketing" '
            'roofing "lead generation" "local seo" "google business profile" "small business marketing" '
            '"trades business" "booked job"')


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "youtube.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def token(e):
    body = urllib.parse.urlencode({"client_id": e["YT_CLIENT_ID"], "client_secret": e["YT_CLIENT_SECRET"],
        "refresh_token": e["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=body), timeout=30).read())["access_token"]


def api(url, tok, data=None, method="GET", ctype="application/json"):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {tok}")
    if data is not None:
        req.add_header("Content-Type", ctype)
    return json.loads(urllib.request.urlopen(req, timeout=120).read().decode())


def main():
    e = env(); tok = token(e); cid = e["YT_CHANNEL_ID"]
    report = {}
    # 1) upload banner image -> get hosted URL
    try:
        res = api(BANNER_UP, tok, data=open(BANNER, "rb").read(), method="POST", ctype="image/png")
        banner_url = res.get("url")
        report["banner_upload"] = "ok"
    except urllib.error.HTTPError as ex:
        report["banner_upload"] = f"FAILED {ex.code}: {ex.read().decode()[:200]}"; banner_url = None
    # 2) read current brandingSettings (don't clobber title)
    cur = api(f"{CH}?part=brandingSettings&id={cid}", tok)
    bs = cur["items"][0].get("brandingSettings", {})
    bs.setdefault("channel", {})
    bs["channel"]["description"] = DESCRIPTION
    bs["channel"]["keywords"] = KEYWORDS
    if banner_url:
        bs["image"] = {"bannerExternalUrl": banner_url}
    # 3) update
    try:
        body = json.dumps({"id": cid, "brandingSettings": bs}).encode()
        api(f"{CH}?part=brandingSettings", tok, data=body, method="PUT")
        report["branding_update"] = "ok (banner + description + keywords set)"
    except urllib.error.HTTPError as ex:
        report["branding_update"] = f"FAILED {ex.code}: {ex.read().decode()[:300]}"
    report["channel"] = e.get("YT_CHANNEL_TITLE")
    report["note"] = "Avatar/profile pic must be set in Studio (not API-settable)."
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
