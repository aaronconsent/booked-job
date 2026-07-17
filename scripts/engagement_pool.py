#!/usr/bin/env python3
"""Shared engagement-pool reader (pure-engagement play, 2026-07-17).

The FB engagement queue (content/queue.json, seeded by seed_content.py) is the
single source of native engagement content — no links. The follower feeds
(Threads, Bluesky, LinkedIn) all draw from it here, each tracking its own
posted-state so they don't post in lockstep. When a channel exhausts the pool it
wraps around to the least-recently-used post, so the feeds never run dry.
"""
import json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
QUEUE = os.path.join(ROOT, "content", "queue.json")


def posts():
    if not os.path.exists(QUEUE):
        return []
    return json.load(open(QUEUE)).get("posts", [])


def text_of(p):
    """Full native post text for a text-only channel (falls back to caption)."""
    return (p.get("text") or p.get("caption") or "").strip()


def next_unposted(done):
    """Next pool item this channel hasn't posted yet. Returns (item, reset):
    reset=True signals the caller to clear its done-set first — the pool was
    exhausted so we recycle from the top (archetypes are evergreen)."""
    pool = posts()
    if not pool:
        return None, False
    fresh = [p for p in pool if p["id"] not in set(done)]
    if fresh:
        return fresh[0], False
    return pool[0], True   # exhausted — recycle the whole pool
