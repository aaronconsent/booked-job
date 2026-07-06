#!/usr/bin/env python3
"""Shared cadence gate for the otherwise-ungated syndication runners.

run_all.py fires every runner once per hour. Without a gate, a runner posts one
queue item every run and drains its whole backlog in a day. `due()` enforces a
minimum gap between posts (a soft daily cap) via a `last_iso` timestamp kept in
the runner's own state dict; `stamp()` records a successful post. --force runs
(the nightly push-everywhere) bypass the gate at the call site."""
import datetime as dt


def due(state, gap_hours):
    """True if enough time has passed since this runner's last post."""
    last = state.get("last_iso")
    if not last:
        return True
    try:
        elapsed = (dt.datetime.now() - dt.datetime.fromisoformat(last)).total_seconds() / 3600
    except Exception:
        return True
    return elapsed >= gap_hours


def stamp(state):
    """Record a successful post so the next `due()` respects the gap."""
    state["last_iso"] = dt.datetime.now().isoformat(timespec="seconds")
    return state
