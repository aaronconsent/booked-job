#!/usr/bin/env python3
"""
Commit files to the Booked Job GitHub Pages repo via the Contents API, and
enable Pages. Reads secrets/github.env:
    GITHUB_TOKEN=...     (fine-grained PAT: Contents write + Pages write)
    GITHUB_OWNER=aaronconsent
    GITHUB_REPO=booked-job-articles
"""
import base64, json, os, sys, urllib.request

API = "https://api.github.com"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "github.env")
    if not os.path.exists(p):
        sys.exit("secrets/github.env missing — add the GitHub PAT first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _req(method, path, tok, body=None):
    req = urllib.request.Request(f"{API}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "booked-job-bot")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as ex:
        return ex.code, {"_err": ex.read().decode()[:400]}


def put_file(path, content_str, message):
    e = env()
    repo = f"/repos/{e['GITHUB_OWNER']}/{e['GITHUB_REPO']}/contents/{path}"
    # need the existing sha to update
    code, cur = _req("GET", repo, e["GITHUB_TOKEN"])
    body = {"message": message, "content": base64.b64encode(content_str.encode()).decode(), "branch": "main"}
    if code == 200 and "sha" in cur:
        body["sha"] = cur["sha"]
    code, res = _req("PUT", repo, e["GITHUB_TOKEN"], body)
    if code not in (200, 201):
        sys.exit(f"GitHub put failed {code}: {res.get('_err', res)}")
    return res.get("content", {}).get("html_url")


def enable_pages():
    e = env()
    base = f"/repos/{e['GITHUB_OWNER']}/{e['GITHUB_REPO']}/pages"
    code, res = _req("POST", base, e["GITHUB_TOKEN"], {"source": {"branch": "main", "path": "/"}})
    if code in (201, 204):
        return "enabled"
    if code == 409:  # already exists
        return "already-enabled"
    return f"pages status {code}: {res.get('_err', res)}"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--enable-pages", action="store_true")
    a = ap.parse_args()
    if a.enable_pages:
        print(enable_pages())
