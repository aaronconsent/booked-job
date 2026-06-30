#!/usr/bin/env python3
"""Stage 2: animate every beat's scene via fal i2v in PARALLEL. Hero beats ->
Kling (premium stylized motion), rest -> Wan (cheap). Submits all jobs to the fal
queue, then polls/downloads each. Reuses cached clips (skips beats already done).

  python3 scripts/fal_batch.py
"""
import base64, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CC = os.path.join(ROOT, "content", "course", ".recraft_cache")
CLIPS = os.path.join(ROOT, "content", "course", ".clip_cache")
KLING = "fal-ai/kling-video/v2.1/standard/image-to-video"
WAN = "wan/v2.6/image-to-video"


def key():
    for line in open(os.path.join(ROOT, "secrets", "fal.env")):
        if line.startswith("FAL_KEY="):
            return line.strip().split("=", 1)[1]
    sys.exit("FAL_KEY missing")


def curl(*a):
    return subprocess.run(["curl", "-s", *a], capture_output=True, text=True).stdout


def data_uri(png):
    jpg = png + ".u.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", png,
                    "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", jpg], check=True)
    return "data:image/jpeg;base64," + base64.b64encode(open(jpg, "rb").read()).decode()


def submit(model, png, prompt):
    K = key()
    body = {"prompt": prompt, "image_url": data_uri(png), "duration": "5"}
    bf = png + ".fb.json"; open(bf, "w").write(json.dumps(body))
    out = curl("-X", "POST", f"https://queue.fal.run/{model}",
               "-H", f"Authorization: Key {K}", "-H", "Content-Type: application/json",
               "--data-binary", f"@{bf}")
    try:
        d = json.loads(out)
    except Exception:
        print(f"  submit bad resp: {out[:200]}"); return None
    if not d.get("request_id"):
        print(f"  submit err: {out[:200]}"); return None
    return {"model": model, "rid": d["request_id"],
            "status": d.get("status_url") or f"https://queue.fal.run/{model}/requests/{d['request_id']}/status",
            "resp": d.get("response_url") or f"https://queue.fal.run/{model}/requests/{d['request_id']}"}


def main():
    os.makedirs(CLIPS, exist_ok=True)
    K = key()
    d = json.load(open(os.path.join(ROOT, "content", "course", "lesson_dialogue.json")))
    jobs = {}
    for b in d["beats"]:
        out = os.path.join(CLIPS, f"{b['id']}.mp4")
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f"  {b['id']}: cached clip"); continue
        png = os.path.join(CC, f"dlg_{b['id']}.png")
        if not os.path.exists(png):
            print(f"  {b['id']}: scene PNG missing (Recraft) — skipping for now"); continue
        model = KLING if b.get("hero") else WAN
        j = submit(model, png, b["motion"])
        if j:
            j["out"] = out; jobs[b["id"]] = j
            print(f"  submitted {b['id']} -> {'Kling' if b.get('hero') else 'Wan'} ({j['rid'][:12]})")
        time.sleep(1)
    # poll all
    t0 = time.time(); pending = set(jobs)
    while pending and time.time() - t0 < 1500:
        time.sleep(10)
        for bid in list(pending):
            j = jobs[bid]
            try:
                st = json.loads(curl(j["status"], "-H", f"Authorization: Key {K}")).get("status", "?")
            except Exception:
                st = "?"
            if st == "COMPLETED":
                r = json.loads(curl(j["resp"], "-H", f"Authorization: Key {K}"))
                vurl = (r.get("video") or {}).get("url") or (r.get("videos") or [{}])[0].get("url")
                if vurl:
                    curl(vurl, "-o", j["out"]); print(f"  ✓ {bid} done ({int(time.time()-t0)}s)")
                else:
                    print(f"  ✗ {bid} no url: {json.dumps(r)[:160]}")
                pending.discard(bid)
            elif st in ("FAILED", "ERROR"):
                print(f"  ✗ {bid} {st}"); pending.discard(bid)
        if pending:
            print(f"  …waiting on {len(pending)}: {sorted(pending)}")
    print(f"done. {len([b for b in d['beats'] if os.path.exists(os.path.join(CLIPS, b['id']+'.mp4'))])}/{len(d['beats'])} clips.")


if __name__ == "__main__":
    main()
