#!/usr/bin/env python3
"""
Booked Job paid amplifier. Stages a campaign on the pinned ad account using the
ads-scoped USER token. ALWAYS creates everything PAUSED — real spend never starts
without Aaron flipping it live (or an explicit --activate).

Default play (research-backed for from-zero): a broad VIDEO-VIEW campaign on a
published Reel, to build a cheap retargeting pool of warm watchers. Every ad
promotes the Booked Job Page; spend is hard-pinned to act_600499776677891.

Usage:
    python3 scripts/fb_ads.py stage-video-views \
        --post 1272845059238799_122099492613372555 --daily 7 [--dry-run]
    python3 scripts/fb_ads.py list
"""
import argparse, json, os, sys, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


def env():
    e = {}
    for line in open(os.path.join(os.path.dirname(__file__), "..", "secrets", "fb.env")):
        if "=" in line:
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def api(path, params, method="GET"):
    E = env()
    params["access_token"] = E["FB_LONGLIVED_USER_TOKEN"]
    if method == "POST":
        req = urllib.request.Request(f"{GRAPH}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}?" + urllib.parse.urlencode(params))
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Ads API error {ex.code} on {method} {path}:\n{ex.read().decode()[:500]}")


def stage_video_views(post_id, daily_usd, activate, dry):
    E = env()
    acct = E["FB_AD_ACCOUNT"]; page = E["FB_PAGE_ID"]
    state = "ACTIVE" if activate else "PAUSED"
    budget = int(round(daily_usd * 100))  # cents

    plan = {
        "ad_account": acct, "promoted_page": page, "post": post_id,
        "daily_budget_usd": daily_usd, "status": state,
        "objective": "OUTCOME_AWARENESS", "optimization_goal": "THRUPLAY",
    }
    if dry:
        print(json.dumps({"dry_run": True, **plan}, indent=2)); return

    # 1) campaign
    camp = api(f"{acct}/campaigns", {
        "name": "BookedJob — Reel video views (retarget pool)",
        "objective": "OUTCOME_AWARENESS", "special_ad_categories": json.dumps([]),
        "is_adset_budget_sharing_enabled": "false", "status": state}, "POST")

    # 2) ad set — broad US, let creative qualify the audience
    targeting = {"geo_locations": {"countries": ["US"]}, "age_min": 25, "age_max": 65,
                 "targeting_automation": {"advantage_audience": 1}}
    adset = api(f"{acct}/adsets", {
        "name": "BookedJob — broad US 25-65", "campaign_id": camp["id"],
        "daily_budget": budget, "billing_event": "IMPRESSIONS",
        "optimization_goal": "THRUPLAY", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "targeting": json.dumps(targeting), "status": state}, "POST")

    # 3) creative from the existing Reel post
    creative = api(f"{acct}/adcreatives", {
        "name": "BookedJob — Reel creative", "object_story_id": post_id}, "POST")

    # 4) ad
    ad = api(f"{acct}/ads", {
        "name": "BookedJob — Reel ad", "adset_id": adset["id"],
        "creative": json.dumps({"creative_id": creative["id"]}), "status": state}, "POST")

    print(json.dumps({"status": state, "campaign": camp["id"], "adset": adset["id"],
                      "creative": creative["id"], "ad": ad["id"],
                      "daily_budget_usd": daily_usd}, indent=2))
    print(f"\nReview in Ads Manager: https://adsmanager.facebook.com/adsmanager/manage/campaigns?act={acct.replace('act_','')}")


def list_campaigns():
    acct = env()["FB_AD_ACCOUNT"]
    d = api(f"{acct}/campaigns", {"fields": "name,status,objective,daily_budget"})
    print(json.dumps(d.get("data", d), indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stage-video-views")
    s.add_argument("--post", required=True, help="PAGEID_POSTID of the Reel to promote")
    s.add_argument("--daily", type=float, default=7.0)
    s.add_argument("--activate", action="store_true", help="create ACTIVE (spends money) instead of PAUSED")
    s.add_argument("--dry-run", action="store_true")
    sub.add_parser("list")
    a = ap.parse_args()
    if a.cmd == "stage-video-views":
        stage_video_views(a.post, a.daily, a.activate, a.dry_run)
    else:
        list_campaigns()
