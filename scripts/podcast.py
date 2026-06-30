#!/usr/bin/env python3
"""
Multi-voice podcast generator for "Get Booked, Not F***ed".
Script lines 'SPEAKER: text' -> ElevenLabs per-voice (tries the expressive v3
model w/ audio tags, falls back to multilingual_v2) -> stitched tight -> -16 LUFS.

    python3 scripts/podcast.py content/podcast/ep01-angi.txt content/podcast/ep01.mp3
"""
import os, re, subprocess, sys, tempfile, urllib.request, urllib.error, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# cast -> voice id + per-character delivery (lower stability = wilder, more varied)
CAST = {
    "MARSH": ("IL22Ke355hck2I2lwmNi", dict(stability=0.40, similarity_boost=0.85, style=0.55, use_speaker_boost=True)),
    "DOM":   ("q4ZWePOqOlCczfm45cgu", dict(stability=0.30, similarity_boost=0.85, style=0.70, use_speaker_boost=True)),
    "CODY":  ("s9qPEcNDdWZC4ab7A4mk", dict(stability=0.22, similarity_boost=0.80, style=0.85, use_speaker_boost=True)),
}
GAP = 0.13   # tight, conversational


def key():
    for line in open(os.path.join(ROOT, "secrets", "elevenlabs.env")):
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.strip().split("=", 1)[1]


def tts(text, vid, vs, model, out):
    body = json.dumps({"text": text, "model_id": model, "voice_settings": vs}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
        data=body, method="POST",
        headers={"xi-api-key": key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=120) as r:
        open(out, "wb").write(r.read())


def parse(path, keep_tags):
    out = []
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"([A-Z]+):\s*(.+)", ln)
        if m and m.group(1) in CAST:
            txt = m.group(2)
            words_only = re.sub(r"\[[^\]]+\]", "", txt)
            if not re.sub(r"[^A-Za-z0-9]", "", words_only):   # no actual words -> skip (v3 rejects bare tags)
                continue
            if not keep_tags:
                txt = words_only
            txt = re.sub(r"\s+", " ", txt).strip(" -")
            out.append((m.group(1), txt))
    return out


def main():
    src, out = sys.argv[1], sys.argv[2]
    tmp = tempfile.mkdtemp(prefix="pod_")
    # pick model: try v3 (expressive), else multilingual_v2
    model = "eleven_v3"
    try:
        tts("Testing, one two.", CAST["MARSH"][0], CAST["MARSH"][1], model, os.path.join(tmp, "t.mp3"))
        print("using ElevenLabs v3 (expressive, audio tags on)")
    except urllib.error.HTTPError:
        model = "eleven_multilingual_v2"
        print("v3 unavailable -> using eleven_multilingual_v2 (tags stripped)")
    lines = parse(src, keep_tags=(model == "eleven_v3"))
    sil = os.path.join(tmp, "sil.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=mono", "-t", str(GAP), sil], check=True)
    print(f"generating {len(lines)} lines…")
    segs = []
    for i, (spk, txt) in enumerate(lines):
        vid, vs = CAST[spk]
        seg = os.path.join(tmp, f"{i:03d}.mp3")
        try:
            tts(txt, vid, vs, model, seg)
        except urllib.error.HTTPError as e:
            sys.exit(f"line {i} ({spk}) failed {e.code}: {e.read().decode()[:200]}")
        segs.append(seg)
        if i < len(lines) - 1:
            segs.append(sil)
        if i % 8 == 0:
            print(f"  …{i+1}/{len(lines)}")
    inputs = []
    for s in segs:
        inputs += ["-i", s]
    fc = "".join(f"[{j}:a]" for j in range(len(segs))) + \
         f"concat=n={len(segs)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc,
                    "-map", "[a]", "-ac", "2", "-b:a", "192k", out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    print(f"built {out}  ({float(dur):.0f}s, model={model})")


if __name__ == "__main__":
    main()
