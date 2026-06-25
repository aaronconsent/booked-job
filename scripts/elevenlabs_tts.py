#!/usr/bin/env python3
"""
ElevenLabs TTS with timestamps -> voiceover audio + word timings.
Drop-in replacement for heygen_tts.generate_speech (same return shape), so
make_reel.py can swap backends with one import change.

Reads ELEVENLABS_API_KEY from secrets/elevenlabs.env (gitignored).
"""
import base64, json, os, sys, urllib.request

BASE = "https://api.elevenlabs.io/v1/text-to-speech"
# Booked Job default voice (see scripts/voice_lab.py experiments). Swappable.
DEFAULT_VOICE = "IL22Ke355hck2I2lwmNi"   # "Torque Marshal" — custom trades voice
DEFAULT_MODEL = "eleven_multilingual_v2"  # reliable char timestamps + quality


def _key():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "elevenlabs.env")
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("ELEVENLABS_API_KEY="):
                return line.strip().split("=", 1)[1]
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("ELEVENLABS_API_KEY missing — add secrets/elevenlabs.env")
    return k


def _words_from_alignment(al):
    chars = al["characters"]
    starts = al["character_start_times_seconds"]
    ends = al["character_end_times_seconds"]
    words, cur, cs, ce = [], "", None, None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                words.append({"word": cur, "start": cs, "end": ce}); cur, cs = "", None
        else:
            if cs is None:
                cs = s
            cur += ch; ce = e
    if cur:
        words.append({"word": cur, "start": cs, "end": ce})
    return words


def generate_speech(text, voice_id=DEFAULT_VOICE, out="voiceover.mp3",
                    model=DEFAULT_MODEL, stability=0.40, similarity=0.80, style=0.35):
    body = json.dumps({
        "text": text, "model_id": model,
        "voice_settings": {"stability": stability, "similarity_boost": similarity,
                           "style": style, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(f"{BASE}/{voice_id}/with-timestamps", data=body,
                                 method="POST",
                                 headers={"xi-api-key": _key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code}: {e.read().decode()[:300]}")
    audio = base64.b64decode(d["audio_base64"])
    al = d.get("alignment") or d.get("normalized_alignment")
    words = _words_from_alignment(al) if al else []
    dur = al["character_end_times_seconds"][-1] if al else None
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as f:
        f.write(audio)
    json.dump({"duration": dur, "words": words}, open(out + ".json", "w"), indent=2)
    return out, dur, words


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", default="voiceover.mp3")
    a = ap.parse_args()
    out, dur, words = generate_speech(a.text, a.voice, a.out, a.model)
    print(f"wrote {out} ({(dur or 0):.1f}s, {len(words)} words)")
