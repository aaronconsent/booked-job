#!/usr/bin/env python3
"""
Post-process Branch Series workflow output: render each article to the blog
(same template/schema as build_blog), and wire it into the machine —
syndication_queue (-> 9 channels + carousels + pins + tiktok), channel_variants,
sitemap, blog index, and 1 FB/IG post each.

    python3 scripts/render_branch.py clean   # only fact-check-passed articles (default)
    python3 scripts/render_branch.py all
    python3 scripts/render_branch.py slug1 slug2 ...
"""
import json, os, re, sys, html

ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG = os.path.join(ROOT, "site", "blog")
RESULT = os.path.join(ROOT, "content", "_branch_result.json")
SYND = os.path.join(ROOT, "content", "syndication_queue.json")
VAR = os.path.join(ROOT, "content", "channel_variants.json")
SITEMAP = os.path.join(ROOT, "site", "sitemap.xml")
IDX = os.path.join(ROOT, "site", "blog", "index.html")
QUEUE = os.path.join(ROOT, "content", "queue.json")
TODAY = "2026-06-30"
B = "https://booked-job.com"


def render(a):
    slug = a["slug"]; url = f"{B}/blog/{slug}/"
    h1 = html.unescape(a["h1"])
    plain_h1 = re.sub("<[^>]+>", "", h1).replace("&amp;", "&")
    faq_ld = ",".join('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
                      % (json.dumps(f["q"]), json.dumps(f["a"])) for f in a["faq"])
    secs = ""
    for s in a["body"]:
        ans = html.unescape(s.get("answer", "") or "")
        abox = f'<div class="answer">{ans}</div>' if ans.strip() else ""
        secs += f"\n  <h2>{html.unescape(s['h2'])}</h2>{abox}\n  {html.unescape(s['html'])}"
    faq_html = "".join(f'\n  <h3>{f["q"]}</h3>\n  <p>{f["a"]}</p>' for f in a["faq"])
    lead = re.sub("<[^>]+>", "", a["body"][0]["html"]) if a["body"] else ""
    lead = html.unescape(lead).strip()
    lead = (lead[:300].rsplit(".", 1)[0] + ".") if len(lead) > 300 else lead
    big, lab = a["statBig"], a["statLabel"]
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{a['title']}</title>
<meta name="description" content="{a['meta']}" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="article" /><meta property="og:title" content="{a['title']}" />
<meta property="og:description" content="{a['meta']}" /><meta property="og:url" content="{url}" />
<meta name="theme-color" content="#15171A" />
<link rel="stylesheet" href="/assets/article.css" />
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Article","headline":{json.dumps(plain_h1)},"description":{json.dumps(a['meta'])},
"datePublished":"{TODAY}","dateModified":"{TODAY}",
"author":{{"@type":"Person","name":"Aaron Phillips","jobTitle":"Founder, Booked Job","url":"https://booked-job.com/about/"}},
"publisher":{{"@type":"Organization","name":"Booked Job","url":"https://booked-job.com/"}},
"mainEntityOfPage":"{url}"}},
{{"@type":"BreadcrumbList","itemListElement":[
{{"@type":"ListItem","position":1,"name":"Booked Job","item":"https://booked-job.com/"}},
{{"@type":"ListItem","position":2,"name":"Blog","item":"https://booked-job.com/blog/"}},
{{"@type":"ListItem","position":3,"name":{json.dumps(plain_h1)},"item":"{url}"}}]}},
{{"@type":"FAQPage","mainEntity":[{faq_ld}]}}]}}
</script></head><body>
<header><div class="nav">
  <a class="logo" href="/"><span class="mark">B</span><b>BOOKED<span>JOB</span></b></a>
  <a class="cta" href="https://www.facebook.com/bookedjob" target="_blank" rel="noopener">Follow</a>
</div></header><div class="tape"></div>
<article class="wrap">
  <p class="crumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › {plain_h1}</p>
  <h1>{h1}</h1>
  <div class="meta"><span class="av">AP</span> By Aaron Phillips · Booked Job · Updated June 2026</div>
  <div class="answer"><b>Short answer:</b> {a['short']}</div>
  <p class="lead">{lead}</p>
  <div class="stat"><div class="big">{big}</div><div class="lab">{lab}</div></div>{secs}
  <h2>Frequently asked questions</h2>{faq_html}
  <div class="answer"><b>Next step:</b> Get the free Marketing 101 course + tools at <a href="https://booked-job.com/">booked-job.com</a>. Get found. Get picked. Get booked.</div>
</article>
<footer style="text-align:center;padding:40px;color:#888;font-size:14px">© Booked Job · Honest marketing for the trades · <a href="https://booked-job.com/">booked-job.com</a></footer>
</body></html>"""


def main():
    res = json.load(open(RESULT)); arts = res["articles"]
    arg = sys.argv[1:] or ["clean"]
    if arg == ["clean"]:
        picks = [a for a in arts if a.get("_verdict", {}).get("allNumbersSourced")]
    elif arg == ["all"]:
        picks = arts
    else:
        picks = [a for a in arts if a["slug"] in arg]

    synd = json.load(open(SYND)); sids = {i["id"] for i in synd["items"]}
    cv = json.load(open(VAR))
    q = json.load(open(QUEUE)); qids = {p["id"] for p in q["posts"]}
    sm = open(SITEMAP).read(); idx = open(IDX).read()
    new_cards = ""; new_sm = ""; built = []
    for a in picks:
        slug = a["slug"]; url = f"{B}/blog/{slug}/"
        d = os.path.join(BLOG, slug); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(render(a)); built.append(slug)
        if slug not in sids:
            synd["items"].append({"id": slug, "title": a["title"], "labels": a["labels"],
                                  "short_title": a["_series"], "blurb": a["short"], "url": url, "posted": {}})
        cv[slug] = a["variants"]
        if f"/blog/{slug}/" not in sm:
            new_sm += f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
        new_cards += (f'\n    <a class="post" href="/blog/{slug}/">\n      <span class="tag">{a["_series"]}</span>'
                      f'\n      <h2>{html.unescape(a["title"])}</h2>\n      <p>{a["short"][:160]}</p>\n    </a>')
        pid = f"art2-{slug[:24]}"
        if pid not in qids and a.get("fbPosts"):
            q["posts"].append({"id": pid, "archetype": "branch-series", "caption": a["fbPosts"][0],
                               "image": None, "link": url, "comment": "Full breakdown 👇"})
    json.dump(synd, open(SYND, "w"), indent=2)
    json.dump(cv, open(VAR, "w"), indent=1, ensure_ascii=False)
    json.dump(q, open(QUEUE, "w"), indent=2)
    open(SITEMAP, "w").write(sm.replace("</urlset>", new_sm + "</urlset>"))
    open(IDX, "w").write(idx.replace('<div class="grid">', '<div class="grid">' + new_cards, 1))
    # validate
    import xml.dom.minidom; xml.dom.minidom.parse(SITEMAP)
    print(f"rendered + wired {len(built)} articles: {', '.join(built)}")
    print(f"syndication now {len(synd['items'])} · variants {len([k for k in cv if k!='_doc'])} · FB/IG queue {len(q['posts'])}")


if __name__ == "__main__":
    main()
