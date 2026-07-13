#!/usr/bin/env python3
"""One-time (idempotent) injector: add the email-capture widget + script to every
already-rendered article and tool page. Future articles get it from render_branch's
template; this backfills the existing 100+ pages that were rendered without it."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_branch import CAPTURE_BLOCK

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SCRIPT = '<script src="/assets/capture.js" defer></script>'
targets = (glob.glob(os.path.join(ROOT, "site", "blog", "*", "index.html"))
           + glob.glob(os.path.join(ROOT, "site", "tools", "*", "index.html"))
           + [os.path.join(ROOT, "site", "tools", "index.html")])

done = skip = 0
for f in targets:
    if not os.path.exists(f):
        continue
    s = open(f, encoding="utf-8").read()
    if "capform" in s:
        skip += 1; continue
    if "</article>" in s:
        s = s.replace("</article>", f"  {CAPTURE_BLOCK}\n</article>", 1)
    else:
        continue
    if SCRIPT not in s:
        s = s.replace("</body>", f"{SCRIPT}\n</body>", 1)
    open(f, "w", encoding="utf-8").write(s)
    done += 1

print(f"capture injected: {done} pages, {skip} already had it")
