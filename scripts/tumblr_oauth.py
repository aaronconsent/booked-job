#!/usr/bin/env python3
"""
Tumblr OAuth2 connect. Tumblr rejects localhost redirects, so we use a hosted
callback (https://booked-job.com/oauth/callback) that shows the code; you paste
it back and this exchanges it for a refresh token. Writes secrets/tumblr.env.

Two modes:
  1) print the auth URL:   python3 scripts/tumblr_oauth.py --client-id <K> --auth-url
  2) exchange the code:     python3 scripts/tumblr_oauth.py --client-id <K> --client-secret <S> --code <CODE>
"""
import argparse, json, os, sys, urllib.parse, urllib.request

REDIRECT = "https://booked-job.com/oauth/callback"
AUTH = "https://www.tumblr.com/oauth2/authorize"
TOKEN = "https://api.tumblr.com/v2/oauth2/token"
SCOPE = "basic write offline_access"


def auth_url(cid):
    return AUTH + "?" + urllib.parse.urlencode({"client_id": cid, "response_type": "code",
        "scope": SCOPE, "redirect_uri": REDIRECT, "state": "bookedjob"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret")
    ap.add_argument("--code")
    ap.add_argument("--auth-url", action="store_true")
    a = ap.parse_args()

    if a.auth_url or not a.code:
        print(auth_url(a.client_id))
        if not a.code:
            return

    if not a.client_secret:
        sys.exit("--client-secret required to exchange the code.")

    body = urllib.parse.urlencode({"grant_type": "authorization_code", "code": a.code,
        "client_id": a.client_id, "client_secret": a.client_secret, "redirect_uri": REDIRECT}).encode()
    req = urllib.request.Request(TOKEN, data=body)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"token exchange failed {ex.code}: {ex.read().decode()[:300]}")
    if "refresh_token" not in tok:
        sys.exit(f"No refresh_token: {tok}")

    blog = ""
    try:
        r = urllib.request.Request("https://api.tumblr.com/v2/user/info")
        r.add_header("Authorization", f"Bearer {tok['access_token']}")
        info = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
        blogs = info.get("response", {}).get("user", {}).get("blogs", [])
        if blogs:
            blog = blogs[0]["name"]
    except Exception as ex:
        print(f">>> (couldn't read blog name: {ex})")

    out = os.path.join(os.path.dirname(__file__), "..", "secrets", "tumblr.env")
    with open(out, "w") as f:
        f.write(f"TUMBLR_CLIENT_ID={a.client_id}\nTUMBLR_CLIENT_SECRET={a.client_secret}\n")
        f.write(f"TUMBLR_REFRESH_TOKEN={tok['refresh_token']}\nTUMBLR_BLOG={blog}\n")
    os.chmod(out, 0o600)
    print(f"\n✅ wrote secrets/tumblr.env")
    print(f">>> TUMBLR BLOG: '{blog}.tumblr.com'  ← confirm this is the Booked Job Tumblr.")


if __name__ == "__main__":
    main()
