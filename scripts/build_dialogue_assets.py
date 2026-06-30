#!/usr/bin/env python3
"""Stage 1 of the dialogue explainer: generate each beat's scene (Recraft locked
explainer style) + TTS every line in its speaker's voice (cached). Cheap; run
before the i2v spend."""
import hashlib, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recraft_image as RC
import elevenlabs_tts as TTS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CC = os.path.join(ROOT, "content", "course", ".recraft_cache")
TC = os.path.join(ROOT, "content", "course", ".tts_cache")
NT = (" Clean flat 2D explainer-video cartoon illustration, friendly characters, "
      "smooth solid colors, clean outlines, vibrant. No text, no words, no letters.")


def main():
    d = json.load(open(os.path.join(ROOT, "content", "course", "lesson_dialogue.json")))
    sid = json.load(open(os.path.join(ROOT, "content", "course", "recraft_style_explainer.json")))["style_id"]
    voices = d["voices"]
    os.makedirs(TC, exist_ok=True)
    for b in d["beats"]:
        # scene (skip if reusing another beat's clip, or already cached, or Recraft is out)
        scene_png = os.path.join(CC, f"dlg_{b['id']}.png")
        if not b.get("reuse_clip") and "scene" in b and not os.path.exists(scene_png):
            webp, _ = RC.generate(b["scene"] + NT, style_id=sid, size="1820x1024")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", webp, scene_png], check=True)
        # TTS each line
        for j, ln in enumerate(b["lines"]):
            vid = voices[ln["speaker"]]
            k = hashlib.md5((vid + "\n" + ln["text"]).encode()).hexdigest()
            mp3, meta = os.path.join(TC, k + ".mp3"), os.path.join(TC, k + ".json")
            if not (os.path.exists(mp3) and os.path.exists(meta)):
                _, _, words = TTS.generate_speech(ln["text"], vid, mp3)
                json.dump({"words": words}, open(meta, "w"))
        print(f"  {b['id']}: scene + {len(b['lines'])} line(s)")
    print("assets ready")


if __name__ == "__main__":
    main()
