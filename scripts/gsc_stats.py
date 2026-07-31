#!/usr/bin/env python3
"""Google Search Console connector — pulls real Google organic traffic (clicks,
impressions, CTR, avg position, top queries) for booked-job.com into the
dashboard. This is THE authoritative source for Google SEO traffic.

Setup (one time):
  1. Google Cloud Console -> create a Service Account -> add a JSON key.
  2. Enable the "Search Console API" for that project.
  3. In Search Console -> Settings -> Users and permissions, add the service
     account's email (…@….iam.gserviceaccount.com) as a Restricted user.
  4. Save the JSON key as secrets/gsc.json (gitignored).
     Optional: add "site_url" to control the property; defaults to
     "sc-domain:booked-job.com" (domain property). For a URL-prefix property use
     "https://booked-job.com/".

  python3 scripts/gsc_stats.py --test

Auth uses a signed JWT -> OAuth token (needs `cryptography`, added to CI). If the
lib or key is missing this returns None and the dashboard just omits Google.
"""
import base64, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
KEYFILE = os.path.join(ROOT, "secrets", "gsc.json")
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def _access_token(sa):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    now = int(time.time())
    hdr = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64(json.dumps({"iss": sa["client_email"], "scope": SCOPE, "aud": TOKEN_URI,
                             "iat": now, "exp": now + 3600}).encode())
    signing_input = hdr + b"." + claim
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = _b64(key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256()))
    assertion = (signing_input + b"." + sig).decode()
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": assertion}).encode()
    req = urllib.request.Request(TOKEN_URI, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["access_token"]


def _query(token, site, payload):
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("rows", [])


def stats(days=28):
    """Return Google organic {clicks, impressions, ctr, position, top_queries[]} or None."""
    if not os.path.exists(KEYFILE):
        return None
    try:
        sa = json.load(open(KEYFILE))
        token = _access_token(sa)
    except ModuleNotFoundError:
        return {"error": "cryptography not installed"}
    except Exception as ex:
        return {"error": str(ex)[:140]}
    site = sa.get("site_url", "sc-domain:booked-job.com")
    end = dt.date.today() - dt.timedelta(days=2)          # GSC data lags ~2 days
    start = end - dt.timedelta(days=days)
    rng = {"startDate": start.isoformat(), "endDate": end.isoformat()}
    try:
        totals = _query(token, site, {**rng})
        byq = _query(token, site, {**rng, "dimensions": ["query"], "rowLimit": 10})
    except Exception as ex:
        return {"error": str(ex)[:140]}
    t = totals[0] if totals else {}
    top = [{"query": r["keys"][0], "clicks": r.get("clicks", 0), "impressions": r.get("impressions", 0),
            "position": round(r.get("position", 0), 1)} for r in byq]
    return {"clicks": int(t.get("clicks", 0)), "impressions": int(t.get("impressions", 0)),
            "ctr": round(100 * t.get("ctr", 0), 2), "position": round(t.get("position", 0), 1),
            "top_queries": top, "days": days}


if __name__ == "__main__":
    s = stats()
    if s is None:
        print("GSC not configured — add secrets/gsc.json (service-account key).")
    else:
        print(json.dumps(s, indent=2)[:1500])
