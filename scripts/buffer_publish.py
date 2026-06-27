#!/usr/bin/env python3
"""Buffer GraphQL API (api.buffer.com) — interim poster for the channels we can't
do natively yet: LinkedIn + TikTok. Free plan, so we queue (addToQueue) and Buffer
auto-publishes on each channel's schedule. Reads secrets/buffer.env.

NOTE: Buffer's API exposes posting + limited metrics, NOT full engagement/reach
analytics (dashboard-only as of 2026)."""
import json, os, sys, urllib.request

ENDPOINT = "https://api.buffer.com"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "buffer.env")
    if not os.path.exists(p):
        sys.exit("secrets/buffer.env missing.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def gql(query, variables=None):
    e = env()
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {e['BUFFER_TOKEN']}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Buffer HTTP {ex.code}: {ex.read().decode()[:300]}")
    if d.get("errors"):
        raise RuntimeError(json.dumps(d["errors"])[:400])
    return d["data"]


def channels():
    e = env()
    d = gql("query($i: ChannelsInput!){ channels(input:$i){ id service displayName isDisconnected } }",
            {"i": {"organizationId": e["BUFFER_ORG"]}})
    return d["channels"]


def queue_text(channel_id, text, assets=None):
    """Queue a post (text, optional media assets). schedulingType=automatic so Buffer
    publishes it on the channel's schedule."""
    inp = {"channelId": channel_id, "text": text, "assets": assets or [],
           "schedulingType": "automatic", "mode": "addToQueue"}
    d = gql("mutation($input: CreatePostInput!){ createPost(input:$input){ __typename } }", {"input": inp})
    tn = d.get("createPost", {}).get("__typename")
    if tn != "PostActionSuccess":
        raise RuntimeError(f"Buffer createPost returned {tn}: {json.dumps(d)[:300]}")
    return True


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", action="store_true")
    ap.add_argument("--text"); ap.add_argument("--channel")
    a = ap.parse_args()
    if a.channels:
        for c in channels():
            print(f"  {c['service']:10} {c.get('displayName')}  id={c['id']}  disconnected={c['isDisconnected']}")
    elif a.text and a.channel:
        print("queued:", queue_text(a.channel, a.text))
