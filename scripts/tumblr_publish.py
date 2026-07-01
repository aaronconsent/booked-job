#!/usr/bin/env python3
"""Publish an NPF post (text + link block) to the Booked Job Tumblr (API v2,
OAuth2). Reads secrets/tumblr.env. Used by tumblr_runner.py for syndication."""
import json, os, sys, urllib.parse, urllib.request

TOKEN = "https://api.tumblr.com/v2/oauth2/token"


def env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "tumblr.env")
    if not os.path.exists(p):
        sys.exit("secrets/tumblr.env missing — run tumblr_oauth.py first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _save_refresh(new_rt):
    """Tumblr ROTATES the refresh token on every use — persist the new one or the
    next run gets invalid_grant (this was the HTTP 400 bug)."""
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "tumblr.env")
    lines = open(p).read().splitlines()
    for i, l in enumerate(lines):
        if l.startswith("TUMBLR_REFRESH_TOKEN="):
            lines[i] = "TUMBLR_REFRESH_TOKEN=" + new_rt
    open(p, "w").write("\n".join(lines) + "\n")


def access_token(e):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": e["TUMBLR_REFRESH_TOKEN"],
        "client_id": e["TUMBLR_CLIENT_ID"], "client_secret": e["TUMBLR_CLIENT_SECRET"]}).encode()
    req = urllib.request.Request(TOKEN, data=body)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    if d.get("refresh_token"):
        _save_refresh(d["refresh_token"])   # persist the rotated token
    return d["access_token"]


def publish(text, link, link_title, link_desc, tags=None):
    e = env()
    tok = access_token(e)
    blog = e["TUMBLR_BLOG"]
    payload = json.dumps({
        "content": [
            {"type": "text", "text": text},
            {"type": "link", "url": link, "title": link_title, "description": link_desc},
        ],
        "tags": ",".join(tags or []),
        "state": "published",
    }).encode()
    url = f"https://api.tumblr.com/v2/blog/{blog}.tumblr.com/posts"
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Tumblr publish failed {ex.code}: {ex.read().decode()[:400]}")


def _fetch_bytes(url):
    """Download the mp4 so it can be attached as a multipart file part. Tumblr
    NPF video blocks won't accept a plain remote URL in media.url — the binary
    must be uploaded and referenced by identifier (that was the HTTP 400 bug)."""
    req = urllib.request.Request(url, headers={"User-Agent": "booked-job/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _multipart(json_payload, ident, filename, filedata, mimetype="video/mp4"):
    """Encode a multipart/form-data body: a 'json' part (NPF payload) + the
    video file part named after the block's media identifier. Returns
    (content_type_header, body_bytes)."""
    boundary = "----bookedjob" + hex(abs(hash((ident, filename, len(filedata)))))[2:]
    crlf = b"\r\n"; buf = []
    # 'json' part — the NPF create payload
    buf.append(("--" + boundary).encode())
    buf.append(b'Content-Disposition: form-data; name="json"')
    buf.append(b"Content-Type: application/json")
    buf.append(b"")
    buf.append(json_payload if isinstance(json_payload, bytes) else json_payload.encode())
    # file part — name matches the block media identifier ("reel")
    buf.append(("--" + boundary).encode())
    buf.append(f'Content-Disposition: form-data; name="{ident}"; filename="{filename}"'.encode())
    buf.append(f"Content-Type: {mimetype}".encode())
    buf.append(b"")
    buf.append(filedata)
    buf.append(("--" + boundary + "--").encode())
    buf.append(b"")
    body = crlf.join(buf)
    return f"multipart/form-data; boundary={boundary}", body


def publish_video(text, video_url, tags=None):
    """Post a native video (NPF video block) + caption.

    Tumblr NPF requires the mp4 binary to be uploaded as a multipart file part,
    referenced from the block via {"identifier": ...}; a plain media.url is
    rejected with HTTP 400 ("Something broke")."""
    e = env(); tok = access_token(e); blog = e["TUMBLR_BLOG"]
    ident = "reel"
    filename = os.path.basename(urllib.parse.urlparse(video_url).path) or "reel.mp4"
    filedata = _fetch_bytes(video_url)
    payload = json.dumps({
        "content": [
            {"type": "video", "media": {"type": "video/mp4", "identifier": ident}},
            {"type": "text", "text": text},
        ],
        "tags": ",".join(tags or []), "state": "published",
    })
    ctype, body = _multipart(payload, ident, filename, filedata)
    req = urllib.request.Request(f"https://api.tumblr.com/v2/blog/{blog}.tumblr.com/posts", data=body, method="POST")
    req.add_header("Authorization", f"Bearer {tok}"); req.add_header("Content-Type", ctype)
    req.add_header("Content-Length", str(len(body)))
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        raise RuntimeError(f"Tumblr video failed {ex.code}: {ex.read().decode()[:300]}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--link", default=""); ap.add_argument("--video", default="")
    ap.add_argument("--title", default=""); ap.add_argument("--desc", default=""); ap.add_argument("--tags", default="")
    a = ap.parse_args()
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    if a.video:
        res = publish_video(a.text, a.video, tags)
    else:
        res = publish(a.text, a.link, a.title, a.desc, tags)
    print(json.dumps(res.get("response", res), indent=2))
