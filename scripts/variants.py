#!/usr/bin/env python3
"""Unique-content engine: look up a channel's native content variant for an item.
Returns None if no variant exists (runner falls back to its generic copy)."""
import json, os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "channel_variants.json")


def get(channel, item_id):
    try:
        return json.load(open(PATH)).get(item_id, {}).get(channel)
    except Exception:
        return None
