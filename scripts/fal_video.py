#!/usr/bin/env python3
"""
fal.ai image-to-video — animate a still into a moving clip (the character-motion
engine). Reads FAL_KEY from secrets/fal.env. Submits to the fal queue, polls,
downloads the mp4. Image is sent as a base64 data URI (no hosting needed).

  python3 scripts/fal_video.py --model wan/v2.6/image-to-video \
      --image scene.png --prompt "the contractor gestures and talks" --out clip.mp4

Default model = Wan (cheapest). Swap --model fal-ai/kling-video/v2.1/standard/image-to-video
for higher-quality stylized motion.
"""
import argparse, base64, json, os, subprocess, sys, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def key():
    for line in open(os.path.join(ROOT, "secrets", "fal.env")):
        if line.startswith("FAL_KEY="):
            return line.strip().split("=", 1)[1]
    sys.exit("FAL_KEY missing")


def curl(*args):
    r = subprocess.run(["curl", "-s", *args], capture_output=True, text=True)
    return r.stdout, r.returncode


def data_uri(path):
    # downscale to <=1280 wide jpeg to keep the request small
    tmp = path + ".u.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
                    "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", tmp], check=True)
    b = base64.b64encode(open(tmp, "rb").read()).decode()
    return "data:image/jpeg;base64," + b


def submit(model, image, prompt, extra):
    K = key()
    body = {"prompt": prompt, "image_url": data_uri(image)}
    body.update(extra or {})
    bf = image + ".body.json"; open(bf, "w").write(json.dumps(body))
    out, _ = curl("-X", "POST", f"https://queue.fal.run/{model}",
                  "-H", f"Authorization: Key {K}", "-H", "Content-Type: application/json",
                  "--data-binary", f"@{bf}")
    try:
        d = json.loads(out)
    except Exception:
        sys.exit(f"submit: bad response: {out[:300]}")
    if not d.get("request_id"):
        sys.exit(f"submit error: {out[:400]}")
    return d


def run(model, image, prompt, out, extra=None, timeout=900):
    K = key(); t0 = time.time()
    j = submit(model, image, prompt, extra)
    rid = j["request_id"]
    status_url = j.get("status_url") or f"https://queue.fal.run/{model}/requests/{rid}/status"
    resp_url = j.get("response_url") or f"https://queue.fal.run/{model}/requests/{rid}"
    print(f"submitted {rid}")
    while True:
        s, _ = curl(status_url, "-H", f"Authorization: Key {K}")
        try:
            st = json.loads(s).get("status", "?")
        except Exception:
            st = "?"
        print(f"  [{time.time()-t0:5.0f}s] {st}")
        if st == "COMPLETED":
            break
        if st in ("FAILED", "ERROR") or time.time()-t0 > timeout:
            sys.exit(f"generation {st}: {s[:300]}")
        time.sleep(8)
    r, _ = curl(resp_url, "-H", f"Authorization: Key {K}")
    d = json.loads(r)
    vurl = (d.get("video") or {}).get("url") or (d.get("videos") or [{}])[0].get("url")
    if not vurl:
        sys.exit(f"no video url in result: {json.dumps(d)[:400]}")
    curl(vurl, "-o", out)
    ok = os.path.exists(out) and os.path.getsize(out) > 1000
    print(f"  {'downloaded '+out if ok else 'download FAILED'} ({time.time()-t0:.0f}s)")
    if not ok:
        sys.exit("download failed")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="wan/v2.6/image-to-video")
    ap.add_argument("--image", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra", default=None, help="JSON of extra model params")
    a = ap.parse_args()
    run(a.model, a.image, a.prompt, a.out, json.loads(a.extra) if a.extra else None)
