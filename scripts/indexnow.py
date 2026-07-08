#!/usr/bin/env python3
"""IndexNow pings — tell Bing (which feeds ChatGPT search, Copilot, and other AI
answer engines) about new/updated URLs the moment they publish, instead of waiting
days for a crawl. The key is PUBLIC by protocol design (it's served at the site
root as proof of ownership), so it lives here, not in secrets/.

  python3 scripts/indexnow.py --all          # submit every URL in the sitemap
  python3 scripts/indexnow.py URL [URL ...]  # submit specific URLs

`submit(urls)` is importable — blog_drip_runner calls it after each publish."""
import json, os, re, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KEY = "bd9118e55980402a869f0d965da0b71c"          # public — also served at /<KEY>.txt
HOST = "booked-job.com"


def submit(urls):
    if not urls:
        return 0
    body = json.dumps({"host": HOST, "key": KEY,
                       "keyLocation": f"https://{HOST}/{KEY}.txt",
                       "urlList": urls[:10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def sitemap_urls():
    sm = open(os.path.join(ROOT, "site", "sitemap.xml")).read()
    return re.findall(r"<loc>(.*?)</loc>", sm)


if __name__ == "__main__":
    urls = sitemap_urls() if "--all" in sys.argv else [a for a in sys.argv[1:] if a.startswith("http")]
    code = submit(urls)
    print(f"IndexNow: submitted {len(urls)} URLs -> HTTP {code}")
