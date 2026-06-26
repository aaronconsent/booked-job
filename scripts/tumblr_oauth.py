#!/usr/bin/env python3
"""
One-time Tumblr OAuth2 — captures a refresh token + your blog name, writes
secrets/tumblr.env. Run after registering an app at tumblr.com/oauth/apps with
OAuth2 redirect URL = http://127.0.0.1:8080.

    python3 scripts/tumblr_oauth.py --client-id <KEY> --client-secret <SECRET>
"""
import argparse, http.server, json, os, sys, threading, time, urllib.parse, urllib.request, webbrowser

SCOPE = "basic write offline_access"
REDIRECT = "http://127.0.0.1:8080"
AUTH = "https://www.tumblr.com/oauth2/authorize"
TOKEN = "https://api.tumblr.com/v2/oauth2/token"
_code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _code["code"] = p.get("code", [None])[0]; _code["error"] = p.get("error", [None])[0]
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        m = "Authorized — close this tab." if _code.get("code") else f"Error: {_code.get('error')}"
        self.wfile.write(f"<meta charset=utf-8><body style='font-family:sans-serif;background:#15171A;color:#fff;padding:60px;text-align:center'><h2>Booked Job · Tumblr</h2><p>{m}</p></body>".encode())

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    a = ap.parse_args()

    url = AUTH + "?" + urllib.parse.urlencode({"client_id": a.client_id, "response_type": "code",
        "scope": SCOPE, "redirect_uri": REDIRECT, "state": "bookedjob"})
    srv = http.server.HTTPServer(("127.0.0.1", 8080), Handler)
    threading.Thread(target=lambda: [srv.handle_request() for _ in iter(lambda: not (_code.get("code") or _code.get("error")), False)], daemon=True).start()
    print(">>> Open this URL signed in as the Booked Job Tumblr:\n\n" + url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    for _ in range(290):
        if _code.get("code") or _code.get("error"):
            break
        time.sleep(1)
    if not _code.get("code"):
        sys.exit(f"No code ({_code.get('error') or 'timeout'}).")

    body = urllib.parse.urlencode({"grant_type": "authorization_code", "code": _code["code"],
        "client_id": a.client_id, "client_secret": a.client_secret, "redirect_uri": REDIRECT}).encode()
    req = urllib.request.Request(TOKEN, data=body)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"token exchange failed {ex.code}: {ex.read().decode()[:300]}")
    if "refresh_token" not in tok:
        sys.exit(f"No refresh_token returned: {tok}")

    # get primary blog name
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
