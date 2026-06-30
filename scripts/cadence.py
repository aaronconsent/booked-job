#!/usr/bin/env python3
"""
A-cappella marine-cadence opener in the hosts' real voices.
Lines 'SPEAKER: text' (DOM calls, MARSH echoes, BOTH = layered shout) ->
shouted ElevenLabs (v3 if available) -> tight call/response timing -> -16 LUFS.

    python3 scripts/cadence.py content/podcast/intro-cadence.txt content/podcast/intro-cadence.mp3
"""
import os, re, subprocess, sys, tempfile, urllib.request, urllib.error, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOICES = {"DOM": "q4ZWePOqOlCczfm45cgu", "MARSH": "IL22Ke355hck2I2lwmNi"}
SET = dict(stability=0.20, similarity_boost=0.85, style=0.92, use_speaker_boost=True)  # forceful / shouted
GAP = 0.07   # tight chant


def key():
    for line in open(os.path.join(ROOT, "secrets", "elevenlabs.env")):
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.strip().split("=", 1)[1]


def tts(text, vid, model, out):
    body = json.dumps({"text": text, "model_id": model, "voice_settings": SET}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
        data=body, method="POST",
        headers={"xi-api-key": key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=120) as r:
        open(out, "wb").write(r.read())


def main():
    src, out = sys.argv[1], sys.argv[2]
    tmp = tempfile.mkdtemp(prefix="cad_")
    model = "eleven_v3"
    try:
        tts("Hut.", VOICES["DOM"], model, os.path.join(tmp, "t.mp3"))
    except urllib.error.HTTPError:
        model = "eleven_multilingual_v2"
    print(f"model={model}")
    lines = []
    for ln in open(src):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"(DOM|MARSH|BOTH):\s*(.+)", ln)
        if m:
            lines.append((m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()))
    sil = os.path.join(tmp, "sil.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", str(GAP), sil], check=True)
    segs = []
    for i, (spk, txt) in enumerate(lines):
        seg = os.path.join(tmp, f"{i:03d}.mp3")
        if spk == "BOTH":   # layer both voices for a group shout
            a, b = os.path.join(tmp, f"{i}a.mp3"), os.path.join(tmp, f"{i}b.mp3")
            tts(txt, VOICES["DOM"], model, a); tts(txt, VOICES["MARSH"], model, b)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-i", b,
                            "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0", seg], check=True)
        else:
            tts(txt, VOICES[spk], model, seg)
        segs.append(seg)
        if i < len(lines) - 1:
            segs.append(sil)
        print(f"  {i+1}/{len(lines)} {spk}")
    inputs = []
    for s in segs:
        inputs += ["-i", s]
    fc = "".join(f"[{j}:a]" for j in range(len(segs))) + \
         f"concat=n={len(segs)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc,
                    "-map", "[a]", "-ac", "2", "-b:a", "192k", out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    print(f"built {out} ({float(dur):.1f}s)")


if __name__ == "__main__":
    main()
