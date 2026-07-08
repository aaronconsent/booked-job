#!/usr/bin/env python3
"""Zero-account link/citation signals, fired per published URL:
- Wayback Machine save (web.archive.org/save/) — archived copies are a citation
  surface AI engines + fact-checkers resolve to, and SPN needs no auth.
- WebSub ping (Google's open hub) — pushes feed updates to RSS aggregators the
  moment they change instead of waiting for polls.
Importable: archive(urls), websub(). blog_drip calls both after each publish."""
import urllib.parse, urllib.request

FEEDS = ["https://booked-job.com/feed.xml", "https://booked-job.com/podcast/feed.xml"]


def archive(urls):
    """Ask the Wayback Machine to snapshot each URL. Best-effort, returns #ok."""
    ok = 0
    for u in urls:
        try:
            req = urllib.request.Request("https://web.archive.org/save/" + u,
                                         headers={"User-Agent": "bookedjob-archiver/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                ok += (r.status in (200, 302))
        except Exception:
            pass
    return ok


def websub():
    """Ping Google's WebSub hub for our feeds. Best-effort, returns #accepted."""
    ok = 0
    for f in FEEDS:
        try:
            data = urllib.parse.urlencode({"hub.mode": "publish", "hub.url": f}).encode()
            req = urllib.request.Request("https://pubsubhubbub.appspot.com/", data=data, method="POST")
            with urllib.request.urlopen(req, timeout=30) as r:
                ok += (r.status in (200, 204))
        except Exception:
            pass
    return ok


if __name__ == "__main__":
    import sys
    urls = [a for a in sys.argv[1:] if a.startswith("http")]
    print(f"archived {archive(urls)}/{len(urls)}; websub {websub()}/{len(FEEDS)}")
