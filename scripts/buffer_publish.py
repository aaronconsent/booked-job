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


def queue_video(channel_id, text, video_url, title=None, thumbnail_url=None):
    """Queue a video post (TikTok). video_url must be a PUBLIC, reachable URL."""
    asset = {"video": {"url": video_url, "metadata": {"title": (title or "")[:100]}}}
    if thumbnail_url:
        asset["video"]["thumbnailUrl"] = thumbnail_url
    inp = {"channelId": channel_id, "text": text, "assets": [asset],
           "schedulingType": "automatic", "mode": "addToQueue"}
    d = gql("mutation($input: CreatePostInput!){ createPost(input:$input){ __typename } }", {"input": inp})
    tn = d.get("createPost", {}).get("__typename")
    if tn != "PostActionSuccess":
        raise RuntimeError(f"Buffer createPost(video) returned {tn}: {json.dumps(d)[:300]}")
    return True


def metrics(channel_ids, days=30):
    """Aggregated post metrics for the given channels over the last `days`.
    Returns {metricType: value} e.g. {'reach': N, 'reactions': N, 'views': N}."""
    import datetime as dt
    e = env()
    end = dt.datetime.utcnow(); start = end - dt.timedelta(days=days)
    q = "query($i: AggregatedPostMetricsInput!){ aggregatedPostMetrics(input:$i){ metrics { type value unit } } }"
    v = {"i": {"organizationId": e["BUFFER_ORG"],
               "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "channelIds": channel_ids}}
    try:
        d = gql(q, v)
        return {m["type"]: m["value"] for m in d["aggregatedPostMetrics"]["metrics"]}
    except Exception:
        return {}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", action="store_true")
    ap.add_argument("--metrics", action="store_true")
    ap.add_argument("--text"); ap.add_argument("--channel")
    a = ap.parse_args()
    if a.channels:
        for c in channels():
            print(f"  {c['service']:10} {c.get('displayName')}  id={c['id']}  disconnected={c['isDisconnected']}")
    elif a.metrics:
        e = env()
        print(json.dumps(metrics([e["BUFFER_LINKEDIN_CHANNEL"], e["BUFFER_TIKTOK_CHANNEL"]]), indent=2))
    elif a.text and a.channel:
        print("queued:", queue_text(a.channel, a.text))
