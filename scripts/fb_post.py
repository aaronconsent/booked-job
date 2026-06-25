#!/usr/bin/env python3
"""
Publish to the Booked Job Facebook Page via the Graph API.

Reads secrets/fb.env (written by fb_setup_token.py). Supports the
link-in-first-comment pattern: the post body carries NO external link
(avoids the 2-links/month Page penalty); any link is dropped as the
first comment instead.

Usage:
    python3 scripts/fb_post.py --message "..." [--link https://booked-job.com/...] \
        [--comment "link in comments 👇"] [--photo path_or_url] [--dry-run]

Exit codes: 0 ok, 1 error. Prints the new post id (and comment id) as JSON.
"""
import argparse, json, os, sys, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


def load_env():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "fb.env")
    if not os.path.exists(p):
        sys.exit("secrets/fb.env not found — run fb_setup_token.py first.")
    env = {}
    for line in open(p):
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v
    return env


def _post(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{GRAPH}/{path}", data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"Graph API error {e.code}: {e.read().decode()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", required=True)
    ap.add_argument("--link", help="external link — posted as first COMMENT, not in body")
    ap.add_argument("--comment", help="first-comment text (link appended). Default if --link given.")
    ap.add_argument("--photo", help="local path or URL of an image to attach")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    env = load_env()
    page_id = env["FB_PAGE_ID"]
    token = env["FB_PAGE_TOKEN"]

    if a.dry_run:
        print(json.dumps({"dry_run": True, "page": page_id, "message": a.message,
                          "photo": a.photo, "first_comment_link": a.link}, indent=2))
        return

    # 1) main post (photo post if --photo, else feed post). NO link in body.
    if a.photo:
        data = {"caption": a.message, "access_token": token}
        if a.photo.startswith("http"):
            data["url"] = a.photo
            res = _post(f"{page_id}/photos", data)
        else:
            # multipart upload for local files
            res = _upload_photo(page_id, a.photo, a.message, token)
        post_id = res.get("post_id") or res.get("id")
    else:
        res = _post(f"{page_id}/feed", {"message": a.message, "access_token": token})
        post_id = res.get("id")

    out = {"post_id": post_id}

    # 2) link / first comment
    if a.link or a.comment:
        ctext = a.comment or "Link in comments 👇"
        if a.link:
            ctext = f"{ctext}\n{a.link}"
        c = _post(f"{post_id}/comments", {"message": ctext, "access_token": token})
        out["comment_id"] = c.get("id")

    print(json.dumps(out, indent=2))


def _upload_photo(page_id, path, caption, token):
    import mimetypes, uuid
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        content = f.read()
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    parts = []
    for k, v in {"caption": caption, "access_token": token}.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"; "
        f"filename=\"{os.path.basename(path)}\"\r\nContent-Type: {mime}\r\n\r\n".encode()
        + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(f"{GRAPH}/{page_id}/photos", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"Graph API photo error {e.code}: {e.read().decode()}")


if __name__ == "__main__":
    main()
