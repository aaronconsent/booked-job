#!/usr/bin/env python3
"""One-shot: pre-render every TTS reel in the pool and bank it in site/reels/
(git-tracked -> deployed to Cloudflare = durable + public). After this, the daily
reel_runner posts a stored file instead of calling ElevenLabs each time.
Idempotent: skips any reel already banked. Safe to re-run."""
import json, os, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_reel

QUEUE = os.path.join(ROOT, "content", "reels_queue.json")
CREELS = os.path.join(ROOT, "content", "reels"); os.makedirs(CREELS, exist_ok=True)
SREELS = os.path.join(ROOT, "site", "reels"); os.makedirs(SREELS, exist_ok=True)
LOG = os.path.join(ROOT, "content", "batch_prerender.log")


def log(m):
    line = f"{time.strftime('%H:%M:%S')}  {m}"
    print(line, flush=True); open(LOG, "a").write(line + "\n")


def main():
    reels = json.load(open(QUEUE))["reels"]
    tts = [r for r in reels if r.get("script") and not r.get("video")]
    todo = [r for r in tts if not os.path.exists(os.path.join(SREELS, f"{r['id']}.mp4"))]
    log(f"pool: {len(reels)} reels · {len(tts)} TTS · {len(todo)} to render (rest already banked)")
    ok = fail = 0
    for i, r in enumerate(todo, 1):
        rid = r["id"]; out = os.path.join(CREELS, f"{rid}.mp4")
        try:
            if not os.path.exists(out):
                make_reel.build(r["hook"], r["script"], out, backend="elevenlabs")
            shutil.copy(out, os.path.join(SREELS, f"{rid}.mp4"))
            ok += 1; log(f"[{i}/{len(todo)}] ✅ {rid}")
        except SystemExit as e:
            fail += 1; log(f"[{i}/{len(todo)}] ❌ {rid}: {str(e)[:120]}")
        except Exception as e:
            fail += 1; log(f"[{i}/{len(todo)}] ❌ {rid}: {str(e)[:120]}")
    log(f"DONE — {ok} rendered+banked, {fail} failed. site/reels now has "
        f"{len([f for f in os.listdir(SREELS) if f.endswith('.mp4')])} mp4s.")


if __name__ == "__main__":
    main()
