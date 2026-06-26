#!/usr/bin/env python3
"""
One-time YouTube OAuth — exchanges a browser consent for a long-lived refresh
token and writes secrets/youtube.env. Run ONCE after creating a Google Cloud
OAuth client (Desktop type).

Usage:
    python3 scripts/yt_oauth.py --client-id <ID> --client-secret <SECRET>

It opens your browser, you click "Allow" on the Booked Job YouTube channel's
Google account, and it captures the token automatically on localhost:8080.
"""
import argparse, http.server, json, os, sys, threading, urllib.parse, urllib.request, webbrowser

SCOPE = "https://www.googleapis.com/auth/youtube.upload"
REDIRECT = "http://localhost:8080"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"

_code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        _code["code"] = params.get("code", [None])[0]
        _code["error"] = params.get("error", [None])[0]
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
        msg = "Authorized — you can close this tab and return to the terminal. 🛠️" if _code.get("code") else f"Error: {_code.get('error')}"
        self.wfile.write(f"<html><body style='font-family:sans-serif;background:#15171A;color:#fff;padding:60px;text-align:center'><h2>Booked Job</h2><p>{msg}</p></body></html>".encode())

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", required=True)
    ap.add_argument("--client-secret", required=True)
    a = ap.parse_args()

    auth_url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": a.client_id, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent"})

    srv = http.server.HTTPServer(("localhost", 8080), Handler)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    print("Opening browser for YouTube authorization…")
    print("If it doesn't open, paste this URL:\n" + auth_url + "\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    import time
    for _ in range(180):
        if _code.get("code") or _code.get("error"):
            break
        time.sleep(1)
    if not _code.get("code"):
        sys.exit(f"No code received ({_code.get('error') or 'timeout'}).")

    body = urllib.parse.urlencode({
        "code": _code["code"], "client_id": a.client_id, "client_secret": a.client_secret,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN, data=body), timeout=30) as r:
            tok = json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"token exchange failed {ex.code}: {ex.read().decode()[:300]}")
    if "refresh_token" not in tok:
        sys.exit("No refresh_token returned. Revoke prior access at myaccount.google.com/permissions and retry.")

    out = os.path.join(os.path.dirname(__file__), "..", "secrets", "youtube.env")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(f"YT_CLIENT_ID={a.client_id}\n")
        f.write(f"YT_CLIENT_SECRET={a.client_secret}\n")
        f.write(f"YT_REFRESH_TOKEN={tok['refresh_token']}\n")
    os.chmod(out, 0o600)
    print(f"✅ wrote {os.path.relpath(out)} — YouTube is connected. Refresh token never expires.")


if __name__ == "__main__":
    main()
