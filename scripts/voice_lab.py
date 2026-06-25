#!/usr/bin/env python3
"""Generate the same line across candidate ElevenLabs voices so Aaron can pick by ear.
Outputs MP3s to content/voicelab/. Open them and listen."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from elevenlabs_tts import generate_speech

SAMPLE = ("Found this behind the drywall today. The last guy used a garden hose as a P-trap. "
          "Rate it one to ten. I'll start. It's on fire.")

CANDIDATES = [
    ("torque-marshal", "IL22Ke355hck2I2lwmNi"),
    ("midwest",        "q4ZWePOqOlCczfm45cgu"),
    ("nacho-man-handy","s9qPEcNDdWZC4ab7A4mk"),
    ("bill-wise",      "pqHfZKP75CvOlQylNhV4"),
    ("chris-downtoearth","iP95p4xoKVk53GoZ742B"),
    ("adam-firm",      "pNInz6obpgDQGcFmaJgB"),
]

OUT = os.path.join(HERE, "..", "content", "voicelab")
for name, vid in CANDIDATES:
    try:
        p, dur, words = generate_speech(SAMPLE, vid, os.path.join(OUT, f"{name}.mp3"))
        print(f"  {name:18s} -> {os.path.relpath(p)}  ({(dur or 0):.1f}s)")
    except SystemExit as e:
        print(f"  {name:18s} FAILED: {e}")
print("\nListen in content/voicelab/ and tell me which voice.")
