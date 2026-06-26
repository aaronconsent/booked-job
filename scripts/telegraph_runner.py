#!/usr/bin/env python3
"""
Autonomous Telegraph syndication (launchd, weekly). Posts a unique summary of
the next queued article to telegra.ph with a link back to booked-job.com.
Reuses content/syndication_queue.json. State: content/telegraph_state.json.
"""
import argparse, datetime as dt, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "telegraph_state.json")
LOG = os.path.join(ROOT, "content", "telegraph.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def nodes_from(item):
    nodes = []
    for block in re.findall(r"<p>(.*?)</p>", item.get("content_html", ""), re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", block)).strip()
        if text and "Read the full" not in text:
            nodes.append({"tag": "p", "children": [text]})
    if not nodes and item.get("blurb"):
        nodes.append({"tag": "p", "children": [item["blurb"]]})
    nodes.append({"tag": "p", "children": [
        {"tag": "a", "attrs": {"href": item["url"]},
         "children": ["Read the full breakdown on Booked Job →"]}]})
    nodes.append({"tag": "p", "children": [{"tag": "em", "children": [
        "Booked Job is a resource for home-service business owners — plumbers, roofers, HVAC techs and electricians."]}]})
    return nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"done": []})
    done = set(state["done"])

    if a.status:
        print(json.dumps({"done": len(done), "remaining": [i["id"] for i in items if i["id"] not in done]}, indent=2)); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "telegraph.env")):
        log("Telegraph not connected (no secrets/telegraph.env) — run telegraph_publish.py --setup."); return

    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for Telegraph."); return

    import telegraph_publish
    res = telegraph_publish.publish(nxt["title"], nodes_from(nxt))
    done.add(nxt["id"]); state["done"] = list(done)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PUBLISHED '{nxt['id']}' to Telegraph -> {res.get('url')}")
    try:
        import log_change
        log_change.add("site", f"Syndicated to Telegraph: {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
