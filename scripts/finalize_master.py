#!/usr/bin/env python3
"""Stage 4 (polish): wrap the assembled dialogue video into a production master —
branded title card + end card, an ElevenLabs music bed (looped, sidechain-ducked
under the voices), a whoosh at the open, and -14 LUFS loudness. Outputs the master.

  python3 scripts/finalize_master.py --in lesson-01-dialogue.mp4 --out lesson-01-MASTER.mp4
"""
import argparse, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_lesson as ML

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H, FPS = 1920, 1080, 30
F = ML.F
CREAM = (243, 240, 233); INK = (28, 32, 44); HI = ML.HI; HI2 = ML.HI2


def key():
    for line in open(os.path.join(ROOT, "secrets", "elevenlabs.env")):
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.strip().split("=", 1)[1]


def el(endpoint, payload, out):
    import json
    bf = out + ".req.json"; open(bf, "w").write(json.dumps(payload))
    subprocess.run(["curl", "-s", "-X", "POST", f"https://api.elevenlabs.io/v1/{endpoint}",
                    "-H", f"xi-api-key: {key()}", "-H", "Content-Type: application/json",
                    "--data-binary", f"@{bf}", "-o", out], check=False)
    return os.path.exists(out) and os.path.getsize(out) > 2000


def lockup(d, cx, y):
    d.rounded_rectangle([cx-150, y, cx-106, y+44], radius=9, fill=HI)
    d.text((cx-141, y), "B", font=F("Arial Black.ttf", 33), fill=CREAM)
    d.text((cx-96, y+4), "BOOKED", font=F("Arial Black.ttf", 30), fill=INK)
    bw = d.textlength("BOOKED", font=F("Arial Black.ttf", 30))
    d.text((cx-96+bw+6, y+4), "JOB", font=F("Arial Black.ttf", 30), fill=HI)


def title_card(path):
    img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img)
    for x in range(-40, W+40, 92):  # caution tape
        d.polygon([(x, 0), (x+44, 0), (x+44-30, 26), (x-30, 26)], fill=(255, 210, 63))
    d.text((W/2, 300), "MARKETING 101", font=F("Arial Bold.ttf", 50), fill=HI2, anchor="ma")
    tf = F("Arial Black.ttf", 96); y = 380
    for ln in ML.wrap(d, "WHAT MARKETING ACTUALLY IS", tf, W-360):
        d.text((W/2, y), ln, font=tf, fill=INK, anchor="ma"); y += 108
    d.text((W/2, y+24), "Lesson 1 · for service pros", font=F("Arial Bold.ttf", 34), fill=(120, 126, 140), anchor="ma")
    lockup(d, W/2+90, H-150)
    img.save(path)


def end_card(path):
    img = Image.new("RGB", (W, H), INK); d = ImageDraw.Draw(img)
    d.text((W/2, 300), "THAT'S LESSON 1.", font=F("Arial Black.ttf", 84), fill=CREAM, anchor="ma")
    d.text((W/2, 430), "NEXT — LESSON 2: KNOW YOUR NUMBERS", font=F("Arial Bold.ttf", 40), fill=(255, 196, 60), anchor="ma")
    d.rounded_rectangle([W/2-260, 560, W/2+260, 640], radius=14, fill=HI)
    d.text((W/2, 575), "FOLLOW BOOKED JOB", font=F("Arial Black.ttf", 36), fill=INK, anchor="ma")
    d.text((W/2, 720), "booked-job.com", font=F("Arial Bold.ttf", 34), fill=(150, 156, 170), anchor="ma")
    img.save(path)


def card_clip(png, secs, tmp, name):
    out = os.path.join(tmp, name+".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png,
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{secs}",
                    "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "176k",
                    "-shortest", out], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=os.path.join(ROOT, "content", "course", "lesson-01-dialogue.mp4"))
    ap.add_argument("--out", default=os.path.join(ROOT, "content", "course", "lesson-01-MASTER.mp4"))
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="master_")
    # 1) cards
    tpng, epng = os.path.join(tmp, "t.png"), os.path.join(tmp, "e.png")
    title_card(tpng); end_card(epng)
    tclip = card_clip(tpng, 2.4, tmp, "title"); eclip = card_clip(epng, 3.2, tmp, "end")
    # normalize main to same params
    mainn = os.path.join(tmp, "main.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.inp,
                    "-vf", f"scale={W}:{H},fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "18", "-c:a", "aac", "-b:a", "176k", "-ar", "48000", mainn], check=True)
    # 2) concat title + main + end
    cl = os.path.join(tmp, "concat.txt")
    open(cl, "w").write("".join(f"file '{c}'\n" for c in (tclip, mainn, eclip)))
    combined = os.path.join(tmp, "combined.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", cl,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "176k", combined], check=True)
    total = ML.ffprobe_dur(combined) or 90
    # 3) music bed (ElevenLabs) + whoosh
    music = os.path.join(tmp, "music.mp3")
    have_music = el("music", {"prompt": "gentle upbeat acoustic indie-folk background music, ukulele and light percussion, warm, positive, motivational, instrumental", "music_length_ms": min(295000, int(total*1000)+2000)}, music)
    whoosh = os.path.join(tmp, "whoosh.mp3")
    have_w = el("sound-generation", {"text": "clean cinematic whoosh transition", "duration_seconds": 1.2}, whoosh)
    # 4) mix: dialogue + ducked music (+ whoosh at title->main)
    out = a.out
    if have_music:
        inputs = ["-i", combined, "-stream_loop", "-1", "-i", music]
        fc = ("[1:a]volume=0.30,aresample=48000[bed];"
              "[0:a]aresample=48000,asplit=2[vo][sc];"
              "[bed][sc]sidechaincompress=threshold=0.045:ratio=11:attack=12:release=320[duck];")
        if have_w:
            inputs += ["-i", whoosh]
            fc += "[2:a]adelay=2200|2200,volume=0.6[wh];[vo][duck][wh]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1:LRA=11[a]"
        else:
            fc += "[vo][duck]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1:LRA=11[a]"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc,
                        "-map", "0:v", "-map", "[a]", "-t", f"{total}", "-c:v", "libx264", "-preset", "slow",
                        "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                        "-movflags", "+faststart", out], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", combined,
                        "-af", "loudnorm=I=-14:TP=-1:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                        "-movflags", "+faststart", out], check=True)
    print(f"built MASTER {out} ({ML.ffprobe_dur(out):.0f}s, music={'yes' if have_music else 'no'})")


if __name__ == "__main__":
    main()
