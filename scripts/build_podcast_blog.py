#!/usr/bin/env python3
"""Milk the podcast for SEO: turn each episode transcript into an indexable
show-notes / transcript page at site/podcast/<ep>.html (title, meta, Q&A body,
CTA). Free organic + AI-search surface for every episode."""
import html, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MANIFEST = os.path.join(ROOT, "..", "remotion-studio", "public", "audio")
POD = os.path.join(ROOT, "site", "podcast")
BASE = "https://booked-job.com"
NAMES = {"marshall": "Marshall (The Foreman)", "ray": "Ray (The Skeptic)", "cody": "Cody"}


def page(ep, title, desc):
    m = json.load(open(os.path.join(MANIFEST, ep, "manifest.json")))
    clean_title = title.split("|")[0].strip()
    turns = "\n".join(
        f'<p class="turn"><b class="{l["speaker"]}">{NAMES.get(l["speaker"], l["speaker"])}:</b> {html.escape(l["text"])}</p>'
        for l in m)
    meta = html.escape(desc.split("\n")[0])
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(clean_title)} | Get Booked, Not F***ed</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{BASE}/podcast/{ep}.html">
<meta property="og:title" content="{html.escape(clean_title)}"><meta property="og:type" content="article">
<meta property="og:image" content="{BASE}/podcast/cover.png">
<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@type":"PodcastEpisode","name":clean_title,"description":meta,"url":f"{BASE}/podcast/{ep}.html","associatedMedia":{"@type":"MediaObject","contentUrl":f"{BASE}/podcast/{ep}.mp3"},"partOfSeries":{"@type":"PodcastSeries","name":"Get Booked, Not F***ed"}})}</script>
<style>body{{background:#15171A;color:#F4F2EE;font:17px/1.6 -apple-system,system-ui,sans-serif;max-width:760px;margin:0 auto;padding:28px}}
h1{{font-size:30px;line-height:1.15}}a{{color:#FF6A00}}.turn{{margin:14px 0}}.marshall{{color:#FF6A00}}.ray,.cody{{color:#5B8DB8}}
.cta{{background:rgba(255,106,0,.12);border:2px solid #FF6A00;border-radius:14px;padding:18px 22px;margin:26px 0;font-weight:700}}
audio,video,iframe{{width:100%;border-radius:12px;margin:14px 0}}.muted{{color:#A8A29E}}</style></head><body>
<p class="muted">🎙️ Get Booked, Not F***ed · The Podcast</p>
<h1>{html.escape(clean_title)}</h1>
<p class="muted">{meta}</p>
<audio controls preload="metadata" src="{BASE}/podcast/{ep}.mp3"></audio>
<p>🎧 <a href="{BASE}/podcast/feed.xml">Subscribe (Apple/Spotify RSS)</a> · 📺 <a href="{BASE}">Watch the full video</a></p>
<div class="cta">Want the free playbook behind these numbers? → <a href="{BASE}">booked-job.com</a></div>
<h2>Full transcript</h2>
{turns}
<div class="cta">Got a story or a number? That's what the show runs on — <a href="{BASE}">booked-job.com</a></div>
</body></html>"""


def main():
    eps = json.load(open(os.path.join(ROOT, "content", "podcast_queue.json")))["episodes"]
    n = 0
    for e in eps:
        mp = os.path.join(MANIFEST, e["id"], "manifest.json")
        if not os.path.exists(mp):
            continue
        open(os.path.join(POD, f"{e['id']}.html"), "w").write(page(e["id"], e["title"], e["description"]))
        n += 1
    print(f"built {n} podcast show-notes pages -> {BASE}/podcast/<ep>.html")


if __name__ == "__main__":
    main()
