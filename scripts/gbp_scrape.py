#!/usr/bin/env python3
"""
GBP scrape engine — the proprietary-data moat (Branch Series Bible C2).
Runs Apify's Google Maps scraper for trade x market queries, then computes the
stats nobody publishes: % of contractors WITH a website, median review count,
and % under 4 stars — per trade. Writes raw rows to content/gbp_data.json and
appends aggregate, SOURCED stats to content/stats.json (source = our own scrape).

  python3 scripts/gbp_scrape.py --dry-run     # show queries + estimated cost, no API call
  python3 scripts/gbp_scrape.py --pilot        # tiny run (~free-tier) to verify data + cost
  python3 scripts/gbp_scrape.py --full         # the configured trade x market matrix

Cost: Apify Google Maps scraper ~ $4 / 1,000 places (basic). Each query pulls
MAX_PER places, so cost ≈ trades x markets x MAX_PER x $0.004. Keep it modest.
"""
import argparse, datetime as dt, json, os, statistics, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ACTOR = "compass~crawler-google-places"
DATA = os.path.join(ROOT, "content", "gbp_data.json")
STATS = os.path.join(ROOT, "content", "stats.json")

# search terms per trade (left of "in <city>")
TRADES = {
    "plumbing": "plumber", "HVAC": "hvac contractor", "roofing": "roofing contractor",
    "electrical": "electrician", "painting": "painting contractor",
}
# pilot vs full market lists — start tiny (free tier), expand for the real dataset
MARKETS_PILOT = ["Austin TX", "Dallas TX"]
MARKETS_FULL = ["Austin TX", "Dallas TX", "Houston TX", "San Antonio TX", "Phoenix AZ",
                "Denver CO", "Nashville TN", "Charlotte NC", "Tampa FL", "Columbus OH"]
MAX_PER = 30          # places per query — keep modest for cost


def token():
    p = os.path.join(ROOT, "secrets", "apify.env")
    if not os.path.exists(p):
        sys.exit("secrets/apify.env missing — add APIFY_TOKEN=...")
    for l in open(p):
        if l.startswith("APIFY_TOKEN="):
            return l.strip().split("=", 1)[1]
    sys.exit("APIFY_TOKEN not found in secrets/apify.env")


def run_actor(queries, tok):
    body = json.dumps({"searchStringsArray": queries, "maxCrawledPlacesPerSearch": MAX_PER,
                       "language": "en", "skipClosedPlaces": True}).encode()
    url = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?token={tok}"
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def aggregate(rows):
    out = {}
    for trade in TRADES:
        items = [x for x in rows if x.get("_trade") == trade]
        if not items:
            continue
        revs = [int(x.get("reviewsCount") or 0) for x in items]
        with_site = sum(1 for x in items if (x.get("website") or "").strip())
        under4 = sum(1 for x in items if isinstance(x.get("totalScore"), (int, float)) and x["totalScore"] < 4)
        out[trade] = {"n": len(items), "pct_website": round(100 * with_site / len(items)),
                      "median_reviews": int(statistics.median(revs)) if revs else 0,
                      "pct_under_4_stars": round(100 * under4 / len(items))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    markets = MARKETS_PILOT if a.pilot or a.dry_run else MARKETS_FULL
    queries = [(t, f"{term} in {city}") for t, term in TRADES.items() for city in markets]
    est = len(queries) * MAX_PER
    print(f"{len(queries)} queries x {MAX_PER} places = ~{est} places · est cost ~${est*0.004:.2f}")
    if a.dry_run:
        for t, q in queries[:8]:
            print(f"  [{t}] {q}")
        print("  …(dry run — no API call)"); return

    tok = token()
    rows = []
    for t, q in queries:
        try:
            items = run_actor([q], tok)
            for it in items:
                it["_trade"] = t
            rows.extend(items)
            print(f"  [{t}] {q}: {len(items)} places")
        except urllib.error.HTTPError as e:
            print(f"  [{t}] {q}: FAILED {e.code} {e.read().decode()[:160]}")
    if not rows:
        print("no rows returned — check token/actor."); return
    # save trimmed raw rows
    slim = [{"trade": x.get("_trade"), "title": x.get("title"), "reviews": x.get("reviewsCount"),
             "score": x.get("totalScore"), "has_website": bool((x.get("website") or "").strip()),
             "city": x.get("city")} for x in rows]
    json.dump({"scraped": dt.date.today().isoformat(), "markets": markets, "rows": slim},
              open(DATA, "w"), indent=2)
    agg = aggregate(rows)
    print("\n=== aggregates ===")
    for t, s in agg.items():
        print(f"  {t}: n={s['n']} · {s['pct_website']}% have a website · median {s['median_reviews']} reviews · {s['pct_under_4_stars']}% under 4★")
    # append SOURCED stats to the DB
    st = json.load(open(STATS)); ids = {x["id"] for x in st["stats"]}
    today = dt.date.today().isoformat(); src = "Booked Job GBP scrape"
    added = 0
    for t, s in agg.items():
        for key, metric, val in [
            ("website", f"% of {t} contractors with a website", f"{s['pct_website']}%"),
            ("reviews", f"Median Google review count, {t} contractors", str(s['median_reviews'])),
        ]:
            sid = f"gbp-{t.lower()}-{key}"
            if sid not in ids and s["n"] >= 10:
                st["stats"].append({"id": sid, "metric": metric, "trade": t, "channel": "GBP",
                                    "value": val, "source_name": src, "date": today,
                                    "note": f"From a scrape of {s['n']} {t} listings across {len(markets)} US markets.",
                                    "confidence": "high"}); added += 1
    json.dump(st, open(STATS, "w"), indent=2)
    print(f"\nwrote content/gbp_data.json + added {added} original sourced stats to the DB.")


if __name__ == "__main__":
    main()
