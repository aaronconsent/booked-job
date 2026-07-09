#!/usr/bin/env python3
"""Shared Meta (Facebook/Instagram Graph) rate-limit cooldown.

When Meta returns 'Application request limit reached' / 'action is blocked'
(OAuthException code 4), the calling agent trips a cooldown; every Meta agent
then skips its Meta calls until it expires. This stops us from hammering an
already-blocked app every hour (which deepens the block and spams failures) and
lets Meta's app-level limit recover on its own."""
import datetime as dt, json, os

STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "meta_cooldown.json")
HOURS = 3


def in_cooldown():
    try:
        u = json.load(open(STATE)).get("until")
        return bool(u) and dt.datetime.now() < dt.datetime.fromisoformat(u)
    except Exception:
        return False


def trip():
    until = (dt.datetime.now() + dt.timedelta(hours=HOURS)).isoformat(timespec="seconds")
    try:
        json.dump({"until": until, "tripped": dt.datetime.now().isoformat(timespec="seconds")}, open(STATE, "w"))
    except Exception:
        pass
    return until


def is_rate_limit(err):
    s = str(err).lower()
    return ("request limit reached" in s or "action is blocked" in s
            or "reduce the amount" in s or '"code":4' in s or "(#4)" in s or "#4)" in s)
