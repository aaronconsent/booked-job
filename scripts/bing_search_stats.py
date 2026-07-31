#!/usr/bin/env python3
"""Bing Webmaster Tools connector — pulls organic search traffic (clicks,
impressions, top queries) for booked-job.com so the dashboard can show real
SEO traffic instead of guesses. Bing also feeds ChatGPT Search + Copilot, so
this doubles as AEO visibility.

Setup — secrets/bing.env:
  BING_API_KEY=...        # Bing Webmaster Tools -> gear/Settings -> API access -> generate
  BING_SITE_URL=https://booked-job.com   # optional; must match the verified property

  python3 scripts/bing_search_stats.py --test
"""
import datetime as dt, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ENV = os.path.join(ROOT, "secrets", "bing.env")
BASE = "https://ssl.bing.com/webmaster/api.svc/json"


def env():
    if not os.path.exists(ENV):
        return None
    e = {}
    for l in open(ENV):
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k, v = l.split("=", 1); e[k.strip()] = v.strip()
    return e if e.get("BING_API_KEY") else None


def _get(method, key, site):
    url = f"{BASE}/{method}?" + urllib.parse.urlencode({"apikey": key, "siteUrl": site})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("d", [])


def _msdate(s):
    m = re.search(r"/Date\((\d+)", s or "")
    return dt.date.fromtimestamp(int(m.group(1)) / 1000).isoformat() if m else None


def stats(days=28):
    """Return Bing organic {clicks, impressions, ctr, series[], top_queries[]} or None."""
    e = env()
    if not e:
        return None
    site = e.get("BING_SITE_URL", "https://booked-job.com")
    try:
        traffic = _get("GetRankAndTrafficStats", e["BING_API_KEY"], site)
        queries = _get("GetQueryStats", e["BING_API_KEY"], site)
    except Exception as ex:
        return {"error": str(ex)[:140]}
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    series = []
    for row in traffic:
        d = _msdate(row.get("Date"))
        if d and d >= cutoff:
            series.append({"date": d, "clicks": row.get("Clicks", 0), "impressions": row.get("Impressions", 0)})
    clicks = sum(r["clicks"] for r in series); impr = sum(r["impressions"] for r in series)
    tq = sorted(queries, key=lambda q: -q.get("Clicks", 0))[:10]
    top = [{"query": q.get("Query", ""), "clicks": q.get("Clicks", 0),
            "impressions": q.get("Impressions", 0), "position": q.get("AvgImpressionPosition")} for q in tq]
    return {"clicks": clicks, "impressions": impr,
            "ctr": round(100 * clicks / impr, 2) if impr else 0,
            "series": series[-days:], "top_queries": top, "days": days}


if __name__ == "__main__":
    s = stats()
    if s is None:
        print("Bing not configured — add secrets/bing.env (BING_API_KEY).")
    else:
        print(json.dumps(s, indent=2)[:1500])
