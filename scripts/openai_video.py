#!/usr/bin/env python3
"""
Sora-2 video generation (OpenAI /v1/videos) — create → poll → download.
Image-to-video when --ref is given (the reference image MUST match --size).
Reads OPENAI_API_KEY from secrets/openai.env. Uses curl for the multipart upload.

  python3 scripts/openai_video.py --prompt "..." --ref still.jpg \
      --model sora-2-pro --size 1920x1080 --seconds 8 --out clip.mp4

Prints the full job JSON (so cost/usage fields, if any, are visible) + wall time.
"""
import argparse, json, os, subprocess, sys, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BASE = "https://api.openai.com/v1/videos"


def key():
    p = os.path.join(ROOT, "secrets", "openai.env")
    for line in open(p):
        if line.startswith("OPENAI_API_KEY="):
            return line.strip().split("=", 1)[1]
    sys.exit("OPENAI_API_KEY missing")


def curl(*args):
    r = subprocess.run(["curl", "-s", *args], capture_output=True, text=True)
    return r.stdout, r.stderr, r.returncode


def create(prompt, model, size, seconds, ref=None):
    K = key()
    args = [BASE, "-H", f"Authorization: Bearer {K}",
            "-F", f"model={model}", "-F", f"prompt={prompt}",
            "-F", f"size={size}", "-F", f"seconds={seconds}"]
    if ref:
        mime = "image/jpeg" if ref.lower().endswith((".jpg", ".jpeg")) else "image/png"
        args += ["-F", f"input_reference=@{ref};type={mime}"]
    out, err, rc = curl(*args)
    try:
        d = json.loads(out)
    except Exception:
        sys.exit(f"create: bad response: {out[:400]} {err[:200]}")
    if d.get("error"):
        sys.exit(f"create error: {json.dumps(d['error'])}")
    return d


def poll(vid, every=10, timeout=1200):
    K = key(); t0 = time.time()
    while True:
        out, _, _ = curl(f"{BASE}/{vid}", "-H", f"Authorization: Bearer {K}")
        try:
            d = json.loads(out)
        except Exception:
            d = {"status": "?", "raw": out[:200]}
        st = d.get("status", "?")
        print(f"  [{time.time()-t0:5.0f}s] status={st} progress={d.get('progress','')}")
        if st in ("completed", "failed", "error"):
            return d
        if time.time() - t0 > timeout:
            return {"status": "timeout", **d}
        time.sleep(every)


def download(vid, out):
    K = key()
    _, err, rc = curl(f"{BASE}/{vid}/content", "-H", f"Authorization: Bearer {K}", "-o", out)
    return os.path.exists(out) and os.path.getsize(out) > 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--model", default="sora-2-pro")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--seconds", default="8")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    print(f"creating {a.model} {a.size} {a.seconds}s (ref={'yes' if a.ref else 'no'})…")
    job = create(a.prompt, a.model, a.size, a.seconds, a.ref)
    vid = job.get("id")
    print("job:", json.dumps(job)[:600])
    if not vid:
        sys.exit("no job id")
    final = poll(vid)
    print("final job:", json.dumps(final)[:800])
    if final.get("status") != "completed":
        sys.exit(f"generation did not complete: {final.get('status')}")
    if download(vid, a.out):
        print(f"  downloaded {a.out}  ({os.path.getsize(a.out)//1024} KB, {time.time()-t0:.0f}s wall)")
    else:
        sys.exit("download failed")


if __name__ == "__main__":
    main()
