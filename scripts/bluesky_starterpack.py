#!/usr/bin/env python3
"""One-time: create a Bluesky STARTER PACK ("Trades & Home-Service Ops") from the
real trades accounts the engagement daemon has been following. Starter packs drive
~43% of new follows for accounts in them. Run once; re-run to refresh membership.
Outputs the shareable starter-pack URL (put it in the bio / pin it)."""
import datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import bluesky_publish as B

NAME = "Trades & Home-Service Ops"
DESC = "Contractors, trades pros, and home-service operators worth following — curated by Booked Job."
ENGAGE_STATE = os.path.join(ROOT, "content", "bluesky_engage_state.json")


def now():
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")


def main():
    e = B.env(); s = B.session(e); jwt = s["accessJwt"]; did = s["did"]
    handle = e["BLUESKY_HANDLE"]

    # members: our own account + accounts the daemon followed (trades-relevant)
    followed = []
    if os.path.exists(ENGAGE_STATE):
        followed = json.load(open(ENGAGE_STATE)).get("followed", [])
    members = [did] + [d for d in followed if d != did]
    members = members[:150]  # starter-pack list cap

    def create(collection, record):
        return B._post("com.atproto.repo.createRecord",
                       {"repo": did, "collection": collection, "record": record}, jwt)

    # 1) reference list
    lr = create("app.bsky.graph.list", {"$type": "app.bsky.graph.list",
        "purpose": "app.bsky.graph.defs#referencelist", "name": NAME, "description": DESC, "createdAt": now()})
    list_uri = lr["uri"]
    print(f"list: {list_uri}  ({len(members)} members)")

    # 2) add members
    added = 0
    for d in members:
        try:
            create("app.bsky.graph.listitem", {"$type": "app.bsky.graph.listitem",
                   "subject": d, "list": list_uri, "createdAt": now()}); added += 1
        except Exception as ex:
            print(f"  skip {d}: {ex}")
    print(f"added {added} members")

    # 3) starter pack
    sp = create("app.bsky.graph.starterpack", {"$type": "app.bsky.graph.starterpack",
        "name": NAME, "description": DESC, "list": list_uri, "createdAt": now()})
    rkey = sp["uri"].split("/")[-1]
    url = f"https://bsky.app/starter-pack/{handle}/{rkey}"
    print(f"\n✅ STARTER PACK: {url}")


if __name__ == "__main__":
    main()
