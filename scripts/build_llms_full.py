#!/usr/bin/env python3
"""Build site/llms-full.txt — the llms.txt convention's full-content companion:
every LIVE article's full text (headings, answers, FAQ) in one plain-markdown
file so AI answer engines can ingest the whole content moat in a single fetch.
Runs in run_all after blog_drip, so new articles appear the hour they publish."""
import html, json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "site", "llms-full.txt")
B = "https://booked-job.com"


def strip(s):
    return html.unescape(re.sub("<[^>]+>", "", s or "")).strip()


def main():
    sched = json.load(open(os.path.join(ROOT, "content", "schedule.json")))["items"]
    live = [it["slug"] for it in sched if it["status"] == "live"]
    parts = ["# Booked Job — full content",
             "",
             "Free, no-fluff marketing education for home-service contractors. "
             "Every numeric claim below is sourced inline. Canonical URLs on each article.",
             ""]
    n = 0
    for slug in live:
        p = os.path.join(ROOT, "content", "staged", f"{slug}.json")
        if not os.path.exists(p):
            continue
        a = json.load(open(p))
        parts += [f"## {strip(a['title'])}", f"URL: {B}/blog/{slug}/", "",
                  f"**Short answer:** {strip(a['short'])}", ""]
        for s in a.get("body", []):
            parts.append(f"### {strip(s['h2'])}")
            if s.get("answer"):
                parts.append(f"*{strip(s['answer'])}*")
            parts += [strip(s.get("html", "")), ""]
        if a.get("faq"):
            parts.append("### FAQ")
            for f in a["faq"]:
                parts += [f"**Q: {strip(f['q'])}**", f"A: {strip(f['a'])}", ""]
        parts.append("---")
        n += 1
    open(OUT, "w").write("\n".join(parts) + "\n")
    print(f"llms-full.txt: {n} articles, {os.path.getsize(OUT)//1024}KB")


if __name__ == "__main__":
    main()
