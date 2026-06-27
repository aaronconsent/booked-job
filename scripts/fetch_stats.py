#!/usr/bin/env python3
"""
Pull live Booked Job stats from the Graph API + local state and write
site/dashboard/data.json (read by the dashboard; no token ever in the client).
Run by launchd a few times a day.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GRAPH = "https://graph.facebook.com/v21.0"


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "fb.env")):
        if "=" in line:
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def get(path, params, tok):
    params["access_token"] = tok
    try:
        with urllib.request.urlopen(f"{GRAPH}/{path}?" + urllib.parse.urlencode(params), timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_err": str(e)}


def jload(p, d):
    try:
        return json.load(open(os.path.join(ROOT, p)))
    except Exception:
        return d


# --- Self-updating agent list: derived from the worker/*.plist files, so any
# --- new channel/agent automatically appears on the dashboard. (SOP: add a
# --- channel -> add its com.bookedjob.<x>.plist -> it shows up here for free.)
WEEKDAY = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
AGENT_NAMES = {
    "publisher": "Posts", "reels": "FB Reels", "youtube": "YouTube Shorts",
    "instagram": "Instagram Reels", "engage": "Engage", "report": "Weekly Report",
    "stats": "Stats Refresh", "blogger": "Blogger", "tumblr": "Tumblr",
    "pinterest": "Pinterest", "newsletter": "Newsletter",
    "telegraph": "Telegraph", "bluesky": "Bluesky", "mastodon": "Mastodon",
    "threads": "Threads", "telegram": "Telegram", "ghpages": "GitHub Pages",
    "blueskyengage": "Bluesky Engage", "youtubeengage": "YouTube CTA",
    "threadsengage": "Threads Surfacing", "igengage": "IG Inbound",
    "buffer": "LinkedIn (Buffer)", "buffertiktok": "TikTok (Buffer)", "telegrampoll": "Telegram Polls", "emaildrip": "Email Drip", "buffercarousel": "LinkedIn Carousels",
}


def _sched(sci):
    if not sci:
        return "scheduled"
    items = sci if isinstance(sci, list) else [sci]
    days, times = set(), []
    for it in items:
        if "Weekday" in it:
            days.add(int(it["Weekday"]))
        times.append(f"{int(it.get('Hour', 0))}:{int(it.get('Minute', 0)):02d}")
    daystr = ", ".join(WEEKDAY[d] for d in sorted(days)) if days else "Daily"
    return f"{daystr} · {' / '.join(sorted(set(times)))}"


def enumerate_agents():
    import glob, plistlib
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "worker", "com.bookedjob.*.plist"))):
        try:
            d = plistlib.load(open(p, "rb"))
        except Exception:
            continue
        key = d.get("Label", "").split(".")[-1]
        out.append({"name": AGENT_NAMES.get(key, key.title()),
                    "schedule": _sched(d.get("StartCalendarInterval")), "on": True})
    return out


def readenv(fname):
    p = os.path.join(ROOT, "secrets", fname)
    e = {}
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); e[k] = v
    return e


def _jget(url, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}


def social_followers():
    """Best-effort follower/subscriber counts for channels with no scoreboard card."""
    f = {}
    bs = readenv("bluesky.env")
    if bs.get("BLUESKY_HANDLE"):
        d = _jget(f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={bs['BLUESKY_HANDLE']}")
        if "followersCount" in d:
            f["Bluesky"] = d["followersCount"]
    ms = readenv("mastodon.env")
    if ms.get("MASTODON_TOKEN") and ms.get("MASTODON_INSTANCE"):
        d = _jget(f"{ms['MASTODON_INSTANCE'].rstrip('/')}/api/v1/accounts/verify_credentials",
                  {"Authorization": f"Bearer {ms['MASTODON_TOKEN']}"})
        if "followers_count" in d:
            f["Mastodon"] = d["followers_count"]
    th = readenv("threads.env")
    if th.get("THREADS_USER_ID") and th.get("THREADS_TOKEN"):
        d = _jget(f"https://graph.threads.net/v1.0/{th['THREADS_USER_ID']}/threads_insights?metric=followers_count&access_token={th['THREADS_TOKEN']}")
        try:
            f["Threads"] = d["data"][0]["total_value"]["value"]
        except Exception:
            pass
    tg = readenv("telegram.env")
    if tg.get("TELEGRAM_BOT_TOKEN") and tg.get("TELEGRAM_CHAT_ID"):
        d = _jget(f"https://api.telegram.org/bot{tg['TELEGRAM_BOT_TOKEN']}/getChatMemberCount?chat_id={tg['TELEGRAM_CHAT_ID']}")
        if d.get("ok"):
            f["Telegram"] = d.get("result")
    return f


def channels(email_subs=0, followers=None):
    """Distribution panel: every channel with connection status + activity."""
    followers = followers or {}
    # (name, secret file, state file, state key, unit, kind-when-connected)
    reg = [
        ("Facebook", "fb.env", "state.json", "posted", "posts", "live"),
        ("Instagram", "fb.env", "instagram_state.json", "done", "reels", "live"),
        ("YouTube", "youtube.env", "youtube_state.json", "done", "shorts", "live"),
        ("Blogger", "blogger.env", "blogger_state.json", "done", "posts", "live"),
        ("Tumblr", "tumblr.env", "tumblr_state.json", "done", "posts", "live"),
        ("Telegraph", "telegraph.env", "telegraph_state.json", "done", "posts", "live"),
        ("Bluesky", "bluesky.env", "bluesky_state.json", "done", "posts", "live"),
        ("Mastodon", "mastodon.env", "mastodon_state.json", "done", "posts", "live"),
        ("Threads", "threads.env", "threads_state.json", "done", "posts", "live"),
        ("Telegram", "telegram.env", "telegram_state.json", "done", "posts", "live"),
        ("GitHub Pages", "github.env", "ghpages_state.json", "done", "mirrors", "live"),
        ("Pinterest", "pinterest.env", "pinterest_state.json", "done", "pins", "sandbox"),
    ]
    out = []
    for name, sec, stf, key, unit, kind in reg:
        connected = os.path.exists(os.path.join(ROOT, "secrets", sec))
        cnt = len(jload(os.path.join(ROOT, "content", stf), {}).get(key, [])) if connected else 0
        entry = {"name": name, "status": kind if connected else "off", "count": cnt, "unit": unit}
        if followers.get(name) is not None:
            entry["followers"] = followers[name]
        out.append(entry)
    # Blog (always live — it's our own site); count = published articles
    arts = len(jload(os.path.join(ROOT, "content", "syndication_queue.json"), {}).get("items", []))
    out.insert(0, {"name": "Blog", "status": "live", "count": arts, "unit": "articles"})
    # Email (Resend)
    em = os.path.exists(os.path.join(ROOT, "secrets", "resend.env"))
    out.append({"name": "Email", "status": "live" if em else "off", "count": email_subs, "unit": "subs"})
    # LinkedIn + TikTok via Buffer (interim) — with engagement metrics from Buffer
    buf = os.path.exists(os.path.join(ROOT, "secrets", "buffer.env"))
    bs = jload(os.path.join(ROOT, "content", "buffer_state.json"), {})
    li_m = tt_m = {}
    if buf:
        try:
            sys.path.insert(0, HERE); import buffer_publish as BP
            be = BP.env()
            li_m = BP.metrics([be["BUFFER_LINKEDIN_CHANNEL"]])
            tt_m = BP.metrics([be["BUFFER_TIKTOK_CHANNEL"]])
        except Exception:
            pass
    li = {"name": "LinkedIn", "status": "live" if buf else "pending",
          "count": len(bs.get("linkedin", [])), "unit": "posts (Buffer)"}
    if li_m:
        li["stat"] = f"{int(li_m.get('reach', 0))} reach · {int(li_m.get('reactions', 0))} reactions"
    out.append(li)
    tt = {"name": "TikTok", "status": "live" if buf else "off",
          "count": len(bs.get("tiktok", [])), "unit": "videos (Buffer)"}
    if tt_m:
        tt["stat"] = f"{int(tt_m.get('views', 0))} views · {int(tt_m.get('reactions', 0))} reactions"
    out.append(tt)
    # Pending channels (built/ready, waiting on an external gate)
    out.append({"name": "Google Business", "status": "pending", "count": 0, "unit": "verifying"})
    return out


def main():
    E = env()
    page, ptok, stok = E["FB_PAGE_ID"], E["FB_PAGE_TOKEN"], E.get("FB_SYSTEM_TOKEN", E["FB_LONGLIVED_USER_TOKEN"])
    acct = E.get("FB_AD_ACCOUNT", "")

    pi = get(page, {"fields": "name,fan_count,followers_count"}, ptok)
    posts = get(f"{page}/posts", {"fields": "shares,reactions.summary(true),comments.summary(true)", "limit": 50}, ptok)
    rx = cm = sh = 0
    pdata = posts.get("data", [])
    for p in pdata:
        rx += p.get("reactions", {}).get("summary", {}).get("total_count", 0)
        cm += p.get("comments", {}).get("summary", {}).get("total_count", 0)
        sh += p.get("shares", {}).get("count", 0)

    # queues
    q = jload("content/queue.json", {"posts": []})["posts"]
    st = jload("content/state.json", {"posted": []})
    rq = jload("content/reels_queue.json", {"reels": []})["reels"]
    rst = jload("content/reels_state.json", {"done": []})

    # ads insights
    ads = {"status": "—", "daily_budget": None, "spend": "0", "impressions": 0, "reach": 0, "video_views": 0}
    if acct:
        camps = get(f"{acct}/campaigns", {"fields": "name,effective_status,daily_budget", "limit": 5}, stok).get("data", [])
        if camps:
            c = camps[0]
            ads["status"] = c.get("effective_status", "—")
        ins = get(f"{acct}/insights", {"fields": "spend,impressions,reach,actions", "date_preset": "maximum"}, stok).get("data", [])
        if ins:
            i = ins[0]
            ads["spend"] = i.get("spend", "0"); ads["impressions"] = int(i.get("impressions", 0) or 0)
            ads["reach"] = int(i.get("reach", 0) or 0)
            for a in i.get("actions", []):
                if "video_view" in a.get("action_type", ""):
                    ads["video_views"] = int(float(a.get("value", 0)))
        # daily budget from active adset
        asets = get(f"{acct}/adsets", {"fields": "daily_budget,effective_status", "limit": 5}, stok).get("data", [])
        for a in asets:
            if a.get("daily_budget"):
                ads["daily_budget"] = int(a["daily_budget"]) / 100
                break

    # YouTube stats (if connected)
    yt = {"connected": False, "subscribers": 0, "views": 0, "videos": 0}
    yp = os.path.join(ROOT, "secrets", "youtube.env")
    if os.path.exists(yp):
        try:
            ye = {}
            for line in open(yp):
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1); ye[k] = v
            tbody = urllib.parse.urlencode({
                "client_id": ye["YT_CLIENT_ID"], "client_secret": ye["YT_CLIENT_SECRET"],
                "refresh_token": ye["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
            at = json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://oauth2.googleapis.com/token", data=tbody), timeout=30).read().decode())["access_token"]
            cr = urllib.request.Request("https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true")
            cr.add_header("Authorization", f"Bearer {at}")
            stt = json.loads(urllib.request.urlopen(cr, timeout=30).read().decode())["items"][0]["statistics"]
            yt = {"connected": True, "subscribers": int(stt.get("subscriberCount", 0)),
                  "views": int(stt.get("viewCount", 0)), "videos": int(stt.get("videoCount", 0))}
        except Exception:
            pass
    yt_done = len(jload("content/yt_state.json", {"done": []}).get("done", []))

    # Instagram stats (if connected)
    ig = {"connected": False, "followers": 0, "media": 0}
    if E.get("FB_IG_ID"):
        d = get(E["FB_IG_ID"], {"fields": "followers_count,media_count"}, stok)
        if "followers_count" in d or "media_count" in d:
            ig = {"connected": True, "followers": int(d.get("followers_count", 0)),
                  "media": int(d.get("media_count", 0))}

    # Email subscribers (Resend)
    email_subs = 0
    rp = os.path.join(ROOT, "secrets", "resend.env")
    if os.path.exists(rp):
        try:
            re_env = {}
            for line in open(rp):
                if "=" in line:
                    k, v = line.strip().split("=", 1); re_env[k] = v
            req = urllib.request.Request(
                f"https://api.resend.com/audiences/{re_env['RESEND_AUDIENCE_ID']}/contacts")
            req.add_header("Authorization", f"Bearer {re_env['RESEND_API_KEY']}")
            req.add_header("User-Agent", "curl/8.4.0")
            email_subs = len(json.loads(urllib.request.urlopen(req, timeout=30).read().decode()).get("data", []))
        except Exception:
            pass

    eng_total = rx + cm + sh
    reels_done = len(rst.get("done", []))
    posts_done = len(st.get("posted", [])) + 1

    # ---- project the upcoming schedule from the real posting rules ----
    created = dt.date.fromisoformat(st.get("page_created", dt.date.today().isoformat()))
    remaining_posts = [p for p in q if p["id"] not in set(st.get("posted", []))]
    remaining_reels = [r for r in rq if r["id"] not in set(rst.get("done", []))]
    upcoming, pi_, ri_ = [], 0, 0
    d = dt.date.today() + dt.timedelta(days=1)
    for _ in range(45):
        age = (d - created).days
        post_days = {1, 2, 3} if age < 14 else {0, 1, 2, 3, 4}
        if d.weekday() in post_days and pi_ < len(remaining_posts):
            p = remaining_posts[pi_]; pi_ += 1
            upcoming.append({"date": d.isoformat(), "type": "post", "icon": "📝",
                             "title": p["caption"][:60].split("\n")[0],
                             "sub": p["archetype"].replace("-", " ")})
        if d.weekday() in {1, 4} and ri_ < len(remaining_reels):
            r = remaining_reels[ri_]; ri_ += 1
            upcoming.append({"date": d.isoformat(), "type": "reel", "icon": "🎬",
                             "title": r["hook"], "sub": "Reel"})
        if pi_ >= len(remaining_posts) and ri_ >= len(remaining_reels):
            break
        d += dt.timedelta(days=1)
    upcoming.sort(key=lambda x: (x["date"], x["type"]))
    upcoming = upcoming[:12]

    # ---- goals vs target with pace ----
    goals_cfg = jload("content/goals.json", {"period": {}, "targets": []})
    per = goals_cfg.get("period", {})
    today = dt.date.today()
    actuals = {"followers": pi.get("followers_count", 0), "likes": pi.get("fan_count", 0),
               "engagement": eng_total, "posts_published": posts_done,
               "reels_published": reels_done, "video_views": ads["video_views"],
               "yt_shorts": max(yt_done, yt["videos"]), "yt_subscribers": yt["subscribers"],
               "yt_views": yt["views"], "ig_followers": ig["followers"],
               "email_subscribers": email_subs}
    g_items = []
    try:
        gs = dt.date.fromisoformat(per["start"]); ge = dt.date.fromisoformat(per["end"])
        total_days = max(1, (ge - gs).days); elapsed = max(0, min(total_days, (today - gs).days))
        days_left = max(0, (ge - today).days)
    except Exception:
        total_days, elapsed, days_left = 30, 0, 30
    for t in goals_cfg.get("targets", []):
        cur = actuals.get(t["key"], 0); tgt = t["target"] or 1
        pct = min(100, round(100 * cur / tgt))
        expected = tgt * elapsed / total_days
        g_items.append({"label": t["label"], "icon": t["icon"], "current": cur, "target": t["target"],
                        "pct": pct, "on_track": cur >= expected})

    data = {
        "updated": dt.datetime.now().isoformat(timespec="minutes"),
        "goals": {"label": per.get("label", "Sprint"), "end": per.get("end", ""),
                  "days_left": days_left, "rationale": goals_cfg.get("rationale", ""), "items": g_items},
        "strategist": jload("content/strategist.json", {}),
        "upcoming": upcoming,
        "page": {"name": pi.get("name", "Booked Job"),
                 "followers": pi.get("followers_count", 0), "likes": pi.get("fan_count", 0)},
        "content": {
            "posts_published": len(st.get("posted", [])) + 1,  # +1 manual intro
            "reactions": rx, "comments": cm, "shares": sh,
            "reels_published": len(rst.get("done", [])),
            "posts_remaining": max(0, len(q) - len(st.get("posted", []))),
            "reels_remaining": max(0, len(rq) - len(rst.get("done", []))),
        },
        "ads": ads,
        "youtube": {**yt, "shorts": max(yt_done, yt["videos"])},
        "instagram": ig,
        "email": {"subscribers": email_subs},
        "agents": enumerate_agents(),
        "channels": channels(email_subs, social_followers()),
    }
    out = os.path.join(ROOT, "site", "dashboard", "data.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, "w"), indent=2)
    print(f"wrote {os.path.relpath(out)} — followers={data['page']['followers']} likes={data['page']['likes']} "
          f"posts={data['content']['posts_published']} reels={data['content']['reels_published']} spend=${ads['spend']}")


if __name__ == "__main__":
    main()
