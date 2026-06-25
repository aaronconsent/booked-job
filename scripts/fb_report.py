#!/usr/bin/env python3
"""
Booked Job weekly report. Pulls page + recent-post metrics from the Graph API
and writes a Markdown digest to content/reports/. Run weekly by launchd.

Tracks the scoreboard that matters for a from-zero page: followers, reach,
engagement, and which archetypes are landing — so the strategy can be tuned.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import fb_post

GRAPH = "https://graph.facebook.com/v21.0"


def get(path, params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": e.read().decode()}


def main():
    env = fb_post.load_env()
    page, token = env["FB_PAGE_ID"], env["FB_PAGE_TOKEN"]

    page_info = get(page, {"fields": "name,fan_count,followers_count", "access_token": token})
    posts = get(f"{page}/posts", {
        "fields": "id,message,created_time,permalink_url,shares,"
                  "reactions.summary(true),comments.summary(true)",
        "limit": 25, "access_token": token})

    rows = []
    for p in posts.get("data", []):
        rx = p.get("reactions", {}).get("summary", {}).get("total_count", 0)
        cm = p.get("comments", {}).get("summary", {}).get("total_count", 0)
        sh = p.get("shares", {}).get("count", 0)
        rows.append({"id": p["id"], "when": p.get("created_time", "")[:10],
                     "msg": (p.get("message", "") or "").replace("\n", " ")[:70],
                     "rx": rx, "cm": cm, "sh": sh, "score": rx + cm * 3 + sh * 5,
                     "url": p.get("permalink_url", "")})
    rows.sort(key=lambda r: r["score"], reverse=True)

    today = dt.date.today().isoformat()
    out_dir = os.path.join(ROOT, "content", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"report-{today}.md")

    fans = page_info.get("fan_count", "?")
    foll = page_info.get("followers_count", "?")
    tot_rx = sum(r["rx"] for r in rows); tot_cm = sum(r["cm"] for r in rows); tot_sh = sum(r["sh"] for r in rows)

    with open(out, "w") as f:
        f.write(f"# Booked Job — weekly report ({today})\n\n")
        f.write(f"**Followers:** {foll}  ·  **Page likes:** {fans}\n\n")
        f.write(f"**Last {len(rows)} posts:** {tot_rx} reactions · {tot_cm} comments · {tot_sh} shares\n\n")
        f.write("## Top posts (score = reactions + 3×comments + 5×shares)\n\n")
        f.write("| When | Post | 👍 | 💬 | ↗ | Score |\n|---|---|--:|--:|--:|--:|\n")
        for r in rows[:10]:
            f.write(f"| {r['when']} | {r['msg']} | {r['rx']} | {r['cm']} | {r['sh']} | {r['score']} |\n")
        f.write("\n## Next-step prompts for the strategist\n")
        f.write("- Which archetypes are in the top posts? Make more of those.\n")
        f.write("- Are comments outpacing reactions? Good — discussion drives reach. Double down on questions.\n")
        f.write("- Refill content/queue.json if < 5 posts remain (run seed_content.py or add posts).\n")
        if page_info.get("_error") or posts.get("_error"):
            f.write(f"\n> NOTE: partial data — API error: {page_info.get('_error') or posts.get('_error')}\n")

    print(f"wrote {os.path.relpath(out)}  (followers={foll}, likes={fans}, posts={len(rows)})")


if __name__ == "__main__":
    main()
