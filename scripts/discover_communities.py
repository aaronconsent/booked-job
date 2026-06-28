#!/usr/bin/env python3
"""Community-discovery agent (the "where is the audience already gathered?" robot).

Discovery is task #1 for any social channel. Facebook killed its Groups API in
2024 (no list-my-groups, no search, no post) — that side is handled manually via
the FB roster on the Tasks page. But Reddit / Mastodon / Bluesky still expose
discovery, so this finds the highest-value communities + accounts there and writes
site/dashboard/discovery.json for the Tasks page to render with join/follow links.

  Reddit   : public subreddits/search.json (no app needed; just a real UA)
  Mastodon : authed /api/v2/search (hashtags) + /api/v1/accounts/search
  Bluesky  : authed app.bsky.actor.searchActors

Read-only — surfaces leads for a human to join/follow. Never auto-joins.
launchd: weekly.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "site", "dashboard", "discovery.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

UA = "booked-job-discovery/1.0 (+https://booked-job.com)"
KEYWORDS = ["HVAC", "plumbing", "roofing", "electricians", "contractor",
            "handyman", "home improvement", "small business owners"]
# Relevance gate for noisy keyword matches (Bluesky actor search casts wide).
TRADE_TOKENS = ["hvac", "plumb", "roof", "electric", "contractor", "handyman",
                "remodel", "construction", "home service", "home improvement",
                "trades", "tradesman", "builder", "renovat", "small business",
                "entrepreneur", "marketing", "local seo"]

# Hand-picked, verified Reddit communities — Reddit's API blocks server IPs without
# an OAuth app, so we ship a curated roster (the discovery work done for the human).
REDDIT_SEED = [
    {"name": "r/HVAC", "members": 290000, "desc": "Pros & techs — heating/cooling trade talk.", "link": "https://www.reddit.com/r/HVAC/"},
    {"name": "r/Plumbing", "members": 230000, "desc": "Plumbers and DIYers; homeowners asking for help.", "link": "https://www.reddit.com/r/Plumbing/"},
    {"name": "r/electricians", "members": 360000, "desc": "Licensed electricians and apprentices.", "link": "https://www.reddit.com/r/electricians/"},
    {"name": "r/Construction", "members": 320000, "desc": "Trades & GCs across construction.", "link": "https://www.reddit.com/r/Construction/"},
    {"name": "r/Roofing", "members": 70000, "desc": "Roofers and homeowners pricing roofs.", "link": "https://www.reddit.com/r/Roofing/"},
    {"name": "r/Contractor", "members": 60000, "desc": "Contractors running the business side.", "link": "https://www.reddit.com/r/Contractor/"},
    {"name": "r/smallbusiness", "members": 2000000, "desc": "Owners — marketing, leads, pricing.", "link": "https://www.reddit.com/r/smallbusiness/"},
    {"name": "r/Entrepreneur", "members": 4000000, "desc": "Broad SMB growth; service-biz threads.", "link": "https://www.reddit.com/r/Entrepreneur/"},
    {"name": "r/HomeImprovement", "members": 3000000, "desc": "Homeowners — the 'who do I call' audience.", "link": "https://www.reddit.com/r/HomeImprovement/"},
    {"name": "r/Plumbingrepair", "members": 30000, "desc": "Higher-intent repair questions.", "link": "https://www.reddit.com/r/Plumbingrepair/"},
    {"name": "r/AskElectricians", "members": 90000, "desc": "Homeowners asking pros directly.", "link": "https://www.reddit.com/r/AskElectricians/"},
    {"name": "r/handyman", "members": 60000, "desc": "Handyman trade + business.", "link": "https://www.reddit.com/r/handyman/"},
]


def _get_json(url, headers=None, timeout=25):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ---------- Reddit (public JSON, no OAuth) ----------
def discover_reddit():
    seen, out = set(), []
    blocked = False
    for kw in KEYWORDS:
        url = "https://www.reddit.com/subreddits/search.json?" + urllib.parse.urlencode(
            {"q": kw, "limit": 15, "sort": "relevance"})
        try:
            data = _get_json(url)
        except Exception as e:
            print(f"  reddit '{kw}': {e}")
            blocked = True
            continue
        for c in data.get("data", {}).get("children", []):
            d = c.get("data", {})
            name = d.get("display_name_prefixed") or ("r/" + d.get("display_name", ""))
            subs = d.get("subscribers") or 0
            if name in seen or subs < 1500 or d.get("over18"):
                continue
            seen.add(name)
            out.append({"name": name, "members": subs,
                        "desc": (d.get("public_description") or "").strip()[:140],
                        "link": "https://www.reddit.com" + (d.get("url") or "/" + name + "/")})
    if blocked and not out:
        print("  reddit API blocked (no OAuth app) → using curated seed roster")
        return list(REDDIT_SEED)
    out.sort(key=lambda x: -x["members"])
    return out[:14]


# ---------- Mastodon (authed) ----------
def discover_mastodon():
    p = os.path.join(ROOT, "secrets", "mastodon.env")
    if not os.path.exists(p):
        return {"tags": [], "accounts": []}
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    inst = e.get("MASTODON_INSTANCE", "").rstrip("/")
    tok = e.get("MASTODON_TOKEN", "")
    if not (inst and tok):
        return {"tags": [], "accounts": []}
    H = {"Authorization": "Bearer " + tok}
    tags, accts, tseen, aseen = [], [], set(), set()
    for kw in KEYWORDS:
        try:
            res = _get_json(f"{inst}/api/v2/search?" + urllib.parse.urlencode(
                {"q": kw, "type": "hashtags", "limit": 5}), H)
        except Exception as e2:
            print(f"  mastodon tag '{kw}': {e2}"); res = {}
        for t in res.get("hashtags", []):
            name = t.get("name", "")
            if not name or name.lower() in tseen:
                continue
            tseen.add(name.lower())
            wk = sum(int(d.get("uses", 0)) for d in (t.get("history") or [])[:7])
            tags.append({"tag": "#" + name, "uses": wk,
                         "link": f"{inst}/tags/{name}"})
        try:
            res = _get_json(f"{inst}/api/v1/accounts/search?" + urllib.parse.urlencode(
                {"q": kw, "limit": 4, "resolve": "false"}), H)
        except Exception as e2:
            print(f"  mastodon acct '{kw}': {e2}"); res = []
        for a in (res or []):
            acct = a.get("acct", "")
            if not acct or acct in aseen or a.get("followers_count", 0) < 200:
                continue
            aseen.add(acct)
            accts.append({"handle": "@" + acct, "followers": a.get("followers_count", 0),
                          "link": a.get("url", "")})
    tags.sort(key=lambda x: -x["uses"]); accts.sort(key=lambda x: -x["followers"])
    return {"tags": tags[:12], "accounts": accts[:10]}


# ---------- Bluesky (authed) ----------
def discover_bluesky():
    if not os.path.exists(os.path.join(ROOT, "secrets", "bluesky.env")):
        return []
    try:
        import bluesky_publish as B
        e = B.env(); jwt = B.session(e)["accessJwt"]
    except Exception as ex:
        print(f"  bluesky session: {ex}"); return []
    H = {"Authorization": "Bearer " + jwt}
    # 1) searchActors gives handles/DIDs but no follower counts…
    dids, seen = [], set()
    for kw in KEYWORDS:
        url = "https://bsky.social/xrpc/app.bsky.actor.searchActors?" + urllib.parse.urlencode(
            {"q": kw, "limit": 8})
        try:
            res = _get_json(url, H)
        except Exception as ex:
            print(f"  bluesky '{kw}': {ex}"); continue
        for a in res.get("actors", []):
            did = a.get("did", "")
            if did and did not in seen:
                seen.add(did); dids.append(did)
    # 2) …getProfiles (batches of 25) returns followersCount + description
    out = []
    for i in range(0, len(dids), 25):
        batch = dids[i:i + 25]
        url = "https://bsky.social/xrpc/app.bsky.actor.getProfiles?" + urllib.parse.urlencode(
            [("actors", d) for d in batch])
        try:
            res = _get_json(url, H)
        except Exception as ex:
            print(f"  bluesky getProfiles: {ex}"); continue
        for a in res.get("profiles", []):
            if (a.get("followersCount") or 0) < 150:
                continue
            blob = ((a.get("displayName") or "") + " " + (a.get("description") or "") + " "
                    + (a.get("handle") or "")).lower()
            if not any(t in blob for t in TRADE_TOKENS):
                continue
            h = a.get("handle", "")
            out.append({"handle": "@" + h, "display": a.get("displayName") or h,
                        "followers": a.get("followersCount") or 0,
                        "desc": (a.get("description") or "").strip().replace("\n", " ")[:120],
                        "link": "https://bsky.app/profile/" + h})
    out.sort(key=lambda x: -x["followers"])
    return out[:14]


def main():
    data = {"updated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"}
    print("Reddit…");   data["reddit"] = discover_reddit()
    print("Mastodon…"); data["mastodon"] = discover_mastodon()
    print("Bluesky…");  data["bluesky"] = discover_bluesky()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"wrote discovery.json — reddit:{len(data['reddit'])} "
          f"masto-tags:{len(data['mastodon']['tags'])} masto-accts:{len(data['mastodon']['accounts'])} "
          f"bsky:{len(data['bluesky'])}")


if __name__ == "__main__":
    main()
