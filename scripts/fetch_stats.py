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
               "reels_published": reels_done, "video_views": ads["video_views"]}
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
        "agents": [
            {"name": "Publisher", "schedule": "Tue–Thu · 3 windows/day", "on": True},
            {"name": "Reels", "schedule": "Tue & Fri · 7:30am", "on": True},
            {"name": "YouTube Shorts", "schedule": "Mon/Wed/Fri · 8:30am", "on": True},
            {"name": "Engage", "schedule": "Daily · 9 / 2:30 / 8:15", "on": True},
            {"name": "Report", "schedule": "Mon · 8am", "on": True},
            {"name": "Stats refresh", "schedule": "Daily · 6 / 12 / 6 / 10", "on": True},
        ],
    }
    out = os.path.join(ROOT, "site", "dashboard", "data.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, "w"), indent=2)
    print(f"wrote {os.path.relpath(out)} — followers={data['page']['followers']} likes={data['page']['likes']} "
          f"posts={data['content']['posts_published']} reels={data['content']['reels_published']} spend=${ads['spend']}")


if __name__ == "__main__":
    main()
