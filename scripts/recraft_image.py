#!/usr/bin/env python3
"""
Recraft V3 image generation with on-disk cache — the flat-cartoon ASSET layer for
the animated-explainer pipeline. Reads RECRAFT_API_KEY from secrets/recraft.env.
Cache: content/course/.recraft_cache/<hash>.png (keyed by all params) so re-renders
never re-bill ($0.04 raster / $0.08 vector per image).

  python3 scripts/recraft_image.py --prompt "..." --style vector_illustration \
      [--substyle ...] [--size 1820x1024] [--style-id <id>] [--out path]

remove_background(in_png) -> transparent PNG (for character/element layers).
"""
import argparse, hashlib, json, os, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BASE = "https://external.api.recraft.ai/v1"
CACHE = os.path.join(ROOT, "content", "course", ".recraft_cache")


def key():
    p = os.path.join(ROOT, "secrets", "recraft.env")
    for line in open(p):
        if line.startswith("RECRAFT_API_KEY="):
            return line.strip().split("=", 1)[1]
    sys.exit("RECRAFT_API_KEY missing")


def _curl_json(url, *args):
    out = subprocess.run(["curl", "-s", url, *args], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except Exception:
        sys.exit(f"bad response: {out[:400]}")


def generate(prompt, style="vector_illustration", substyle=None, size="1820x1024",
             style_id=None, out=None, colors=None):
    os.makedirs(CACHE, exist_ok=True)
    body = {"prompt": prompt, "size": size, "model": "recraftv3", "response_format": "url"}
    if style_id:
        body["style_id"] = style_id
    else:
        body["style"] = style
        if substyle:
            body["substyle"] = substyle
    if colors:   # brand-palette lock: list of [r,g,b]
        body["controls"] = {"colors": [{"rgb": c} for c in colors]}
    h = hashlib.md5(json.dumps(body, sort_keys=True).encode()).hexdigest()
    dest = out or os.path.join(CACHE, h + ".png")
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return dest, "cached"
    K = key()
    d = _curl_json(f"{BASE}/images/generations", "-H", "Content-Type: application/json",
                   "-H", f"Authorization: Bearer {K}", "-d", json.dumps(body))
    if d.get("data") and d["data"][0].get("url"):
        url = d["data"][0]["url"]
        subprocess.run(["curl", "-s", url, "-o", dest], check=False)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            return dest, "generated"
    sys.exit(f"recraft error: {json.dumps(d)[:400]}")


def create_style(reference_png, base_style="digital_illustration"):
    """Create a reusable custom Style from a reference image -> returns style_id.
    Lock a look once, then pass style_id to generate() for consistency across scenes."""
    K = key()
    d = _curl_json(f"{BASE}/styles", "-X", "POST", "-H", f"Authorization: Bearer {K}",
                   "-F", f"style={base_style}", "-F", f"file=@{reference_png};type=image/png")
    sid = d.get("id")
    if not sid:
        sys.exit(f"create_style error: {json.dumps(d)[:300]}")
    return sid


def remove_background(in_png, out=None):
    K = key()
    dest = out or in_png.replace(".png", "_cut.png")
    d = _curl_json(f"{BASE}/images/removeBackground", "-H", f"Authorization: Bearer {K}",
                   "-F", f"file=@{in_png};type=image/png", "-F", "response_format=url")
    if d.get("image", {}).get("url"):
        subprocess.run(["curl", "-s", d["image"]["url"], "-o", dest], check=False)
        return dest
    sys.exit(f"removeBackground error: {json.dumps(d)[:300]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--style", default="vector_illustration")
    ap.add_argument("--substyle", default=None)
    ap.add_argument("--size", default="1820x1024")
    ap.add_argument("--style-id", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    path, how = generate(a.prompt, a.style, a.substyle, a.size, a.style_id, a.out)
    print(f"{how}: {path}")
