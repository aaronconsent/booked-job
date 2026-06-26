#!/usr/bin/env python3
"""Generate site/feed.xml (RSS 2.0) from the published articles in
content/syndication_queue.json. Used by LinkedIn (via RSS tool), Flipboard,
NewsBreak, and any reader. Regenerate whenever content changes."""
import datetime as dt, email.utils, html, json, os

ROOT = os.path.join(os.path.dirname(__file__), "..")
SITE = "https://booked-job.com"


def main():
    items = json.load(open(os.path.join(ROOT, "content", "syndication_queue.json")))["items"]
    # strip emoji / non-BMP chars — some RSS importers (and LinkedIn) reject them
    def clean(s):
        return "".join(c for c in (s or "") if ord(c) <= 0xFFFF).strip()
    rows = ""
    for it in items:
        it = {**it, "title": clean(it["title"]), "blurb": clean(it.get("blurb", ""))}
        rows += f"""
    <item>
      <title>{html.escape(it['title'])}</title>
      <link>{it['url']}</link>
      <guid isPermaLink="true">{it['url']}</guid>
      <description>{html.escape(it.get('blurb',''))}</description>
      <pubDate>{email.utils.format_datetime(dt.datetime.now())}</pubDate>
    </item>"""
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Booked Job — for the trades</title>
    <link>{SITE}/blog/</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Real talk for service pros — more booked jobs, better pricing, getting paid, and dodging the lead-reseller traps.</description>
    <language>en-us</language>{rows}
  </channel>
</rss>
"""
    out = os.path.join(ROOT, "site", "feed.xml")
    open(out, "w").write(feed)
    print(f"wrote site/feed.xml ({len(items)} items)")


if __name__ == "__main__":
    main()
