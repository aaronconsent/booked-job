#!/usr/bin/env python3
"""One-time: publish the Bluesky custom feed record ("Home-Service Talk"). The feed
generator itself is served by the booked-job.com Worker (did:web:booked-job.com).
Run AFTER the Worker is deployed (so Bluesky can resolve the feed-gen DID).
Outputs the public feed URL."""
import datetime as dt, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bluesky_publish as B


def main():
    e = B.env(); s = B.session(e); jwt = s["accessJwt"]; did = s["did"]; handle = e["BLUESKY_HANDLE"]
    now = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    record = {"$type": "app.bsky.feed.generator", "did": "did:web:booked-job.com",
              "displayName": "Home-Service Talk",
              "description": "Live posts from contractors & home-service pros — running a trades business, pricing, leads, getting paid. Curated by Booked Job.",
              "createdAt": now}
    r = B._post("com.atproto.repo.createRecord",
                {"repo": did, "collection": "app.bsky.feed.generator", "rkey": "homeservice", "record": record}, jwt)
    print("feed record:", r.get("uri"))
    print(f"\n✅ CUSTOM FEED: https://bsky.app/profile/{handle}/feed/homeservice")


if __name__ == "__main__":
    main()
