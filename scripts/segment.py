#!/usr/bin/env python3
"""
Generic podcast-segment builder. Script lines are one of:
    SPEAKER: text        (NARR / MARSH / DOM / CODY)
    [SFX:name]           (stinger | ding | buzzer | roll)  -> synthesized
    [PAUSE:1.8]          -> silence (for the audience to play along)
Voices via ElevenLabs v3 (fallback v2). Output mastered to -16 LUFS.

    python3 scripts/segment.py content/podcast/porno-or-plumbing.txt content/podcast/porno-or-plumbing.mp3
"""
import os, re, json, subprocess, sys, tempfile, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOICES = {"NARR": "S6Pqw2uh7xzH6i4w17QB", "ANN": "S6Pqw2uh7xzH6i4w17QB",
          "MARSH": "IL22Ke355hck2I2lwmNi", "DOM": "q4ZWePOqOlCczfm45cgu", "CODY": "s9qPEcNDdWZC4ab7A4mk"}
SET = {"NARR": dict(stability=0.42, style=0.70), "MARSH": dict(stability=0.42, style=0.55),
       "DOM": dict(stability=0.32, style=0.66), "CODY": dict(stability=0.24, style=0.85)}
# game-show SFX -> (lavfi source, extra filter chain). source must be a single lavfi source.
SFX = {
 "stinger": ("aevalsrc='0.5*sin(2*PI*(520+760*t)*t)*exp(-1.6*t)':d=0.7:s=44100", ""),
 "ding":    ("aevalsrc='0.6*sin(2*PI*1318.5*t)*exp(-4*t)+0.4*sin(2*PI*1975.5*t)*exp(-5*t)':d=0.9:s=44100", ""),
 "buzzer":  ("aevalsrc='0.5*sin(2*PI*138*t)+0.45*sin(2*PI*146*t)':d=0.85:s=44100", ""),
 "roll":    ("anoisesrc=d=1.0:c=pink:a=0.85:r=44100", "highpass=f=240,tremolo=f=18:d=0.8"),
}


def key():
    return [l.strip().split("=", 1)[1] for l in open(os.path.join(ROOT, "secrets", "elevenlabs.env"))
            if l.startswith("ELEVENLABS_API_KEY=")][0]


def tts(text, vid, vs, out):
    for m in ("eleven_v3", "eleven_multilingual_v2"):
        try:
            body = json.dumps({"text": text, "model_id": m,
                               "voice_settings": {**vs, "similarity_boost": 0.85, "use_speaker_boost": True}}).encode()
            req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                                         data=body, method="POST",
                                         headers={"xi-api-key": key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
            open(out, "wb").write(urllib.request.urlopen(req, timeout=180).read()); return
        except urllib.error.HTTPError:
            continue
    raise SystemExit("tts failed")


def sfx(name, tmp):
    out = os.path.join(tmp, f"sfx_{name}.wav")
    if not os.path.exists(out):
        source, filt = SFX[name]
        af = (filt + "," if filt else "") + "loudnorm=I=-15:TP=-1.5"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", source,
                        "-t", "1.2", "-af", af, out], check=True)
    return out


def main():
    src, out = sys.argv[1], sys.argv[2]
    tmp = tempfile.mkdtemp(prefix="seg_")
    gap = os.path.join(tmp, "gap.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.14", gap], check=True)
    segs = []
    i = 0
    for ln in open(src):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        sm = re.match(r"\[SFX:(\w+)\]", ln)
        pm = re.match(r"\[PAUSE:([\d.]+)\]", ln)
        vm = re.match(r"(NARR|ANN|MARSH|DOM|CODY):\s*(.+)", ln)
        if sm:
            segs.append(sfx(sm.group(1), tmp))
        elif pm:
            p = os.path.join(tmp, f"p{i}.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", pm.group(1), p], check=True)
            segs.append(p)
        elif vm:
            spk, txt = vm.group(1), vm.group(2)
            seg = os.path.join(tmp, f"v{i}.mp3")
            tts(txt, VOICES[spk], SET.get(spk, {"stability": 0.4, "style": 0.6}), seg)
            segs.append(seg); segs.append(gap)
        i += 1
        print(f"  {i}")
    inp = []
    for s in segs:
        inp += ["-i", s]
    fc = "".join(f"[{j}:a]aresample=44100[a{j}];" for j in range(len(segs))) + \
         "".join(f"[a{j}]" for j in range(len(segs))) + \
         f"concat=n={len(segs)}:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inp, "-filter_complex", fc, "-map", "[a]",
                    "-ac", "2", "-b:a", "192k", out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                         capture_output=True, text=True).stdout.strip()
    print(f"built {out} ({float(dur):.0f}s)")


if __name__ == "__main__":
    main()
