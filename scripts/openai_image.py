#!/usr/bin/env python3
"""
gpt-image-1 generator with on-disk cache. Returns a local PNG path for a prompt.
Used by make_lesson_nsfw.py for AI hero shots. Reads OPENAI_API_KEY from
secrets/openai.env (gitignored). Cache: content/course/.img_cache/<hash>.png
(keyed by prompt+size+quality) so re-renders never re-bill.

  python3 scripts/openai_image.py --prompt "a flooded garage at dawn" [--size 1536x1024]
"""
import argparse, base64, hashlib, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CACHE = os.path.join(ROOT, "content", "course", ".img_cache")
API = "https://api.openai.com/v1/images/generations"


def _key():
    p = os.path.join(ROOT, "secrets", "openai.env")
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("OPENAI_API_KEY="):
                return line.strip().split("=", 1)[1]
    k = os.environ.get("OPENAI_API_KEY")
    if not k:
        sys.exit("OPENAI_API_KEY missing — add secrets/openai.env")
    return k


def generate(prompt, size="1536x1024", quality="medium", style_suffix=True):
    os.makedirs(CACHE, exist_ok=True)
    full = prompt
    if style_suffix:
        full += (" — cinematic, gritty realistic photography, dramatic moody lighting, "
                 "high contrast, shallow depth of field, no text, no watermark, no logos")
    key = hashlib.md5(f"{full}|{size}|{quality}".encode()).hexdigest()
    out = os.path.join(CACHE, key + ".png")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out, "cached"
    body = json.dumps({"model": "gpt-image-1", "prompt": full,
                       "size": size, "quality": quality, "n": 1}).encode()
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"Authorization": "Bearer " + _key(),
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"OpenAI image error {e.code}: {e.read().decode()[:400]}")
    b64 = d["data"][0].get("b64_json")
    if not b64:
        sys.exit("no b64_json in response")
    open(out, "wb").write(base64.b64decode(b64))
    return out, "generated"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--size", default="1536x1024")
    ap.add_argument("--quality", default="medium")
    a = ap.parse_args()
    out, how = generate(a.prompt, a.size, a.quality)
    print(f"{how}: {out}")
