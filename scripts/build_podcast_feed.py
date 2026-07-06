#!/usr/bin/env python3
"""Milk the podcast for audio: extract MP3 from each episode + build an RSS feed
(iTunes/Spotify-ready) at site/podcast/feed.xml. Submit that URL once to Spotify
for Podcasters + Apple Podcasts Connect; after that every new episode auto-syndicates."""
import datetime as dt, html, json, os, subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
POD = os.path.join(ROOT, "site", "podcast")
BASE = "https://booked-job.com"
FEED = os.path.join(POD, "feed.xml")

SHOW = {
    "title": "Get Booked, Not F***ed",
    "desc": ("Two tradesmen and the real math behind contractor marketing. Is Angi worth it? "
             "How many Google reviews do you actually need? What does a booked job really cost? "
             "No fluff, no sales pitch — just the numbers that get you booked. From Booked Job."),
    "author": "Booked Job",
    "email": "hello@booked-job.com",
    "cover": f"{BASE}/podcast/cover.png",
}


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        s = int(float(r.stdout.strip()))
    except Exception:
        s = 0
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


def rfc822(d):
    return d.strftime("%a, %d %b %Y %H:%M:%S +0000")


def main():
    eps = json.load(open(os.path.join(ROOT, "content", "podcast_queue.json")))["episodes"]
    base_date = dt.datetime(2026, 7, 1, 9, 0, 0)
    items = []
    for i, e in enumerate(eps):
        mp4 = os.path.join(ROOT, e["video"])
        if not os.path.exists(mp4):
            continue
        mp3 = os.path.join(POD, f"{e['id']}.mp3")
        if not os.path.exists(mp3) or os.path.getmtime(mp3) < os.path.getmtime(mp4):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vn",
                            "-c:a", "libmp3lame", "-q:a", "4", mp3], check=True)
        size = os.path.getsize(mp3)
        dur = probe_dur(mp3)
        pub = base_date + dt.timedelta(days=i)
        title = e["title"].split("|")[0].strip()
        items.append(f"""    <item>
      <title>{html.escape(title)}</title>
      <description>{html.escape(e['description'])}</description>
      <enclosure url="{BASE}/podcast/{e['id']}.mp3" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{e['id']}</guid>
      <pubDate>{rfc822(pub)}</pubDate>
      <itunes:author>{SHOW['author']}</itunes:author>
      <itunes:duration>{dur}</itunes:duration>
      <itunes:episode>{i+1}</itunes:episode>
      <itunes:explicit>true</itunes:explicit>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{html.escape(SHOW['title'])}</title>
    <link>{BASE}</link>
    <language>en-us</language>
    <description>{html.escape(SHOW['desc'])}</description>
    <itunes:author>{SHOW['author']}</itunes:author>
    <itunes:summary>{html.escape(SHOW['desc'])}</itunes:summary>
    <itunes:type>episodic</itunes:type>
    <itunes:explicit>true</itunes:explicit>
    <itunes:image href="{SHOW['cover']}"/>
    <image><url>{SHOW['cover']}</url><title>{html.escape(SHOW['title'])}</title><link>{BASE}</link></image>
    <itunes:category text="Business"><itunes:category text="Marketing"/></itunes:category>
    <itunes:owner><itunes:name>{SHOW['author']}</itunes:name><itunes:email>{SHOW['email']}</itunes:email></itunes:owner>
{chr(10).join(reversed(items))}
  </channel>
</rss>
"""
    open(FEED, "w").write(xml)
    print(f"feed.xml: {len(items)} episodes -> {BASE}/podcast/feed.xml")


if __name__ == "__main__":
    main()
