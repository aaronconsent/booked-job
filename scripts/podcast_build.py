#!/usr/bin/env python3
"""
Booked Job podcast builder. Generates episode audio (ElevenLabs, same brand
voice) for the next un-produced episode, then rebuilds a valid podcast RSS feed
at site/podcast/feed.xml. Audio is hosted on booked-job.com (Cloudflare static
assets); submit the feed URL to Spotify/Apple ONCE and future episodes flow in.

State: content/podcast_state.json. Flags: --next (default), --rebuild, --all.
"""
import argparse, datetime as dt, email.utils, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from elevenlabs_tts import generate_speech, DEFAULT_VOICE

AUDIO = os.path.join(ROOT, "site", "podcast", "audio")
FEED = os.path.join(ROOT, "site", "podcast", "feed.xml")
STATE = os.path.join(ROOT, "content", "podcast_state.json")
SITE = "https://booked-job.com"
COVER = f"{SITE}/podcast/cover.png"
EMAIL = "hello@aaron.chat"


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def make_cover():
    out = os.path.join(ROOT, "site", "podcast", "cover.png")
    if os.path.exists(out):
        return
    from PIL import Image, ImageDraw, ImageFont
    FD = "/System/Library/Fonts/Supplemental"
    def F(n, s): return ImageFont.truetype(os.path.join(FD, n), s)
    S = 3000; HI = (255, 106, 0); ASPHALT = (21, 23, 26); WHITE = (255, 255, 255); YEL = (255, 210, 63)
    img = Image.new("RGB", (S, S), ASPHALT); d = ImageDraw.Draw(img)
    for x in range(-120, S + 120, 260):
        d.polygon([(x, 0), (x + 130, 0), (x + 130 - 110, 110), (x - 110, 110)], fill=YEL)
    tile = Image.new("RGBA", (1300, 1300), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    td.rounded_rectangle([0, 0, 1300, 1300], radius=180, fill=HI)
    td.text((360, 150), "B", font=F("Arial Black.ttf", 1050), fill=ASPHALT)
    tile = tile.transform((1300, 1300), Image.AFFINE, (1, -0.12, 80, 0, 1, 0), resample=Image.BICUBIC)
    img.paste(tile, (850, 560), tile)
    d.text((S/2, 2150), "BOOKED JOB", font=F("Arial Black.ttf", 300), fill=WHITE, anchor="mm")
    d.text((S/2, 2420), "FOR SERVICE PROS WHO'D RATHER BE WORKING", font=F("Arial Bold.ttf", 95), fill=(170, 175, 182), anchor="mm")
    img.save(out)


def rss_date(d):
    return email.utils.format_datetime(d)


def build_feed(state):
    eps = state.get("episodes", [])
    items = ""
    for e in eps:
        items += f"""
    <item>
      <title>{html.escape(e['title'])}</title>
      <description>{html.escape(e['summary'])}</description>
      <itunes:summary>{html.escape(e['summary'])}</itunes:summary>
      <link>{html.escape(e['link'])}</link>
      <guid isPermaLink="false">bookedjob-{e['id']}</guid>
      <pubDate>{e['pubDate']}</pubDate>
      <enclosure url="{SITE}/podcast/audio/{e['id']}.mp3" length="{e['bytes']}" type="audio/mpeg"/>
      <itunes:duration>{e['duration']}</itunes:duration>
      <itunes:author>Booked Job</itunes:author>
      <itunes:explicit>false</itunes:explicit>
    </item>"""
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Booked Job</title>
    <link>{SITE}/</link>
    <language>en-us</language>
    <description>Real talk for service pros who'd rather be working — plumbers, roofers, HVAC techs and electricians. How to get more booked jobs, price your work, get paid, and dodge the lead-reseller traps. No fluff.</description>
    <itunes:author>Booked Job</itunes:author>
    <itunes:summary>Real talk for service pros — more booked jobs, better pricing, and how to stop getting ripped off by lead resellers.</itunes:summary>
    <itunes:type>episodic</itunes:type>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{COVER}"/>
    <image><url>{COVER}</url><title>Booked Job</title><link>{SITE}/</link></image>
    <itunes:category text="Business"><itunes:category text="Entrepreneurship"/></itunes:category>
    <itunes:owner><itunes:name>Booked Job</itunes:name><itunes:email>{EMAIL}</itunes:email></itunes:owner>{items}
  </channel>
</rss>
"""
    os.makedirs(os.path.dirname(FEED), exist_ok=True)
    open(FEED, "w").write(feed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    os.makedirs(AUDIO, exist_ok=True)
    make_cover()
    queue = load(os.path.join(ROOT, "content", "podcast_queue.json"), {"episodes": []})["episodes"]
    state = load(STATE, {"episodes": []})
    produced = {e["id"] for e in state["episodes"]}

    if not a.rebuild:
        todo = [e for e in queue if e["id"] not in produced]
        if a.all is False and todo:
            todo = todo[:1]
        for e in todo:
            print(f"generating audio: {e['id']} …")
            out = os.path.join(AUDIO, f"{e['id']}.mp3")
            _, dur, _ = generate_speech(e["script"], DEFAULT_VOICE, out)
            mm, ss = divmod(int(dur or 0), 60)
            state["episodes"].insert(0, {
                "id": e["id"], "title": e["title"], "summary": e["summary"], "link": e["link"],
                "bytes": os.path.getsize(out), "duration": f"{mm}:{ss:02d}",
                "pubDate": rss_date(dt.datetime.now())})
            json.dump(state, open(STATE, "w"), indent=2)

    build_feed(state)
    print(f"feed: {os.path.relpath(FEED)} ({len(state['episodes'])} episodes)")


if __name__ == "__main__":
    main()
