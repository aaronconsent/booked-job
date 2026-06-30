#!/usr/bin/env python3
"""Stage 3: assemble the dialogue explainer. Per beat: the fal i2v clip (looped to
the beat's audio length) + speaker-colored kinetic captions + the beat's dialogue
audio (lines in order). Beats crossfade (quick slides); one narration track is laid
underneath. Processes whatever clips exist in .clip_cache (partial preview ok).

  python3 scripts/render_dialogue.py [--out ...]
"""
import argparse, hashlib, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_lesson as ML

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKILL = os.path.expanduser("~/.claude/skills/faceless-youtube-video/scripts")
TC = os.path.join(ROOT, "content", "course", ".tts_cache")
CLIPS = os.path.join(ROOT, "content", "course", ".clip_cache")
W, H, FPS = 1920, 1080, 30
XF, GAP, LEADTAIL = 0.3, 0.22, 0.4
F = ML.F
SPK = {"SAL": (255, 140, 30), "MIKE": (60, 190, 230)}   # speaker caption colors


def dur(p): return ML.ffprobe_dur(p) or 0.0


def line_audio(text, vid, tmp, tag):
    k = hashlib.md5((vid + "\n" + text).encode()).hexdigest()
    return os.path.join(TC, k + ".mp3"), json.load(open(os.path.join(TC, k + ".json")))["words"]


def cues_for_beat(beat, voices):
    """Return (cues, segments) where cues=[(start,end,text,speaker)] in beat-local time,
    and the ordered list of (mp3, start) for building the beat audio."""
    cues, audio, t = [], [], 0.0
    for ln in beat["lines"]:
        vid = voices[ln["speaker"]]
        k = hashlib.md5((vid + "\n" + ln["text"]).encode()).hexdigest()
        mp3 = os.path.join(TC, k + ".mp3")
        words = json.load(open(os.path.join(TC, k + ".json")))["words"]
        d = dur(mp3)
        # group words into ~5-word caption cues
        line, ls = [], None
        for w in words:
            if w.get("start") is None: continue
            if ls is None: ls = w["start"]
            line.append(w)
            if len(line) >= 5 or w["word"][-1:] in ".,!?":
                cues.append((t+ls, t+line[-1]["end"], " ".join(x["word"] for x in line), ln["speaker"]))
                line, ls = [], None
        if line:
            cues.append((t+ls, t+words[-1]["end"], " ".join(x["word"] for x in line), ln["speaker"]))
        audio.append((mp3, t)); t += d + 0.28
    return cues, audio, t


def caption_png(text, color, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    cf = F("Arial Black.ttf", 56)
    lines = ML.wrap(d, text.upper(), cf, W - 420); lh = 66
    y = H - 96 - len(lines) * lh
    for ln in lines:
        d.text((W/2, y), ln, font=cf, fill=color, anchor="ma", stroke_width=9, stroke_fill=(15, 18, 30)); y += lh
    img.save(path)


def lockup_png(path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    bx, by = W-250, H-64
    d.rounded_rectangle([bx, by, bx+44, by+44], radius=9, fill=ML.HI, outline=(15, 18, 30), width=3)
    d.text((bx+9, by), "B", font=F("Arial Black.ttf", 33), fill=(15, 18, 30))
    d.text((bx+56, by+4), "BOOKED", font=F("Arial Black.ttf", 29), fill=(245, 245, 245))
    bw = d.textlength("BOOKED", font=F("Arial Black.ttf", 29))
    d.text((bx+56+bw+6, by+4), "JOB", font=F("Arial Black.ttf", 29), fill=ML.HI)
    img.save(path)


def build_beat(beat, voices, tmp, i):
    clip = os.path.join(CLIPS, f"{beat.get('reuse_clip', beat['id'])}.mp4")
    cues, audio, adur = cues_for_beat(beat, voices)
    beatdur = round(adur + LEADTAIL, 2)
    # loop i2v clip to beat duration, normalize 1080p/30
    looped = os.path.join(tmp, f"loop{i}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", clip,
                    "-t", f"{beatdur}", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},fps={FPS}", "-an", looped], check=True)
    # overlay caption strips (speaker-colored) + lockup
    lk = os.path.join(tmp, "lockup.png");  lockup_png(lk)
    inputs = ["-i", looped, "-i", lk]; chain = []; prev = "[0:v]"
    chain.append(f"{prev}[1:v]overlay=0:0[vlk]"); prev = "[vlk]"
    for ci, (s, e, txt, spk) in enumerate(cues):
        png = os.path.join(tmp, f"c{i}_{ci}.png"); caption_png(txt, SPK.get(spk, (255,255,255)), png)
        inputs += ["-i", png]
        lbl = f"[vc{i}_{ci}]"
        chain.append(f"{prev}[{ci+2}:v]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'{lbl}"); prev = lbl
    out = os.path.join(tmp, f"beat{i}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain),
                    "-map", prev, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", out], check=True)
    return out, audio, beatdur


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(ROOT, "content", "course", "lesson-01-dialogue.mp4")); a = ap.parse_args()
    d = json.load(open(os.path.join(ROOT, "content", "course", "lesson_dialogue.json")))
    voices = d["voices"]
    beats = [b for b in d["beats"]
             if os.path.exists(os.path.join(CLIPS, f"{b.get('reuse_clip', b['id'])}.mp4"))]
    print(f"assembling {len(beats)}/{len(d['beats'])} beats")
    tmp = tempfile.mkdtemp(prefix="dlg_")
    bclips, baudios, bdurs = [], [], []
    for i, b in enumerate(beats):
        bc, au, bd = build_beat(b, voices, tmp, i); bclips.append(bc); baudios.append(au); bdurs.append(bd)
        print(f"  built {b['id']} ({bd:.1f}s)")
    edit = os.path.join(tmp, "edit.mp4")
    if len(bclips) > 1:
        subprocess.run(["bash", os.path.join(SKILL, "assemble.sh"), edit, str(XF), *bclips], check=True)
    else:
        subprocess.run(["cp", bclips[0], edit], check=True)
    # narration: place each line at its global offset (beat start + line offset + LEAD/2)
    starts, acc = [0.0], 0.0
    for bd in bdurs[:-1]:
        acc += bd - XF; starts.append(round(acc, 3))
    inp, filt, lbl = [], [], []; idx = 0
    for bi, au in enumerate(baudios):
        for (mp3, loff) in au:
            inp += ["-i", mp3]; dly = int((starts[bi] + 0.2 + loff) * 1000)
            filt.append(f"[{idx}:a]adelay={dly}|{dly}[a{idx}]"); lbl.append(f"[a{idx}]"); idx += 1
    narr = os.path.join(tmp, "narr.m4a")
    fc = ";".join(filt) + ";" + "".join(lbl) + f"amix=inputs={idx}:normalize=0:duration=longest[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inp, "-filter_complex", fc, "-map", "[a]",
                    "-c:a", "aac", "-b:a", "176k", narr], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", edit, "-i", narr, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "176k", "-movflags", "+faststart", a.out],
                   check=True)
    print(f"built {a.out} ({dur(a.out):.0f}s)")


if __name__ == "__main__":
    main()
