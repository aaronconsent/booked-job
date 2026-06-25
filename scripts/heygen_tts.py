#!/usr/bin/env python3
"""
HeyGen audio-only TTS (Starfish). Generates voiceover WAV + word timestamps.

Reads the API key from secrets/heygen.env (HEYGEN_API_KEY=...), gitignored.

    from heygen_tts import generate_speech
    wav, dur, words = generate_speech("Hello", voice_id="...", out="vo.wav")
"""
import json, os, sys, urllib.request

API = "https://api.heygen.com/v3/voices/speech"
DEFAULT_VOICE = "01f98ed43e6140349f47dbd37a416827"  # "Cody" — male English (swappable)


def _key():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "heygen.env")
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("HEYGEN_API_KEY="):
                return line.strip().split("=", 1)[1]
    k = os.environ.get("HEYGEN_API_KEY")
    if not k:
        sys.exit("HEYGEN_API_KEY missing — add secrets/heygen.env")
    return k


def generate_speech(text, voice_id=DEFAULT_VOICE, out="voiceover.wav", speed=1.0):
    body = json.dumps({"text": text, "voice_id": voice_id, "speed": speed}).encode()
    req = urllib.request.Request(API, data=body, method="POST", headers={
        "X-Api-Key": _key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())["data"]
    audio_url, duration = d["audio_url"], d.get("duration")
    words = [w for w in d.get("word_timestamps", []) if not w["word"].startswith("<")]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    urllib.request.urlretrieve(audio_url, out)
    json.dump({"duration": duration, "words": words}, open(out + ".json", "w"), indent=2)
    return out, duration, words


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--out", default="voiceover.wav")
    a = ap.parse_args()
    wav, dur, words = generate_speech(a.text, a.voice, a.out)
    print(f"wrote {wav}  ({dur:.1f}s, {len(words)} words)")
