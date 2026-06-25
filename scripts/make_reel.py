#!/usr/bin/env python3
"""
Build a faceless vertical (1080x1920) Booked Job Reel:
  HeyGen Starfish voiceover  ->  word-synced captions (PIL)  ->  ffmpeg MP4.

Captions switch in time with the narration using HeyGen's word_timestamps.
No avatar, no stock footage required — brand-styled animated text + voice.

Usage:
    python3 scripts/make_reel.py --hook "3 ways shops bleed money" \
        --script "Three ways shops bleed money they never see. One..." \
        --out content/reels/money-leaks.mp4 [--voice <starfish_voice_id>]
"""
import argparse, json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _tts(backend):
    """Pick the TTS backend: 'elevenlabs' (best voice) or 'heygen' (fallback)."""
    if backend == "elevenlabs":
        import elevenlabs_tts as m
    else:
        import heygen_tts as m
    return m.generate_speech, m.DEFAULT_VOICE

HI = (255, 106, 0); ASPHALT = (21, 23, 26); WHITE = (255, 255, 255)
YELLOW = (255, 210, 63); MUTED = (150, 156, 164)
FD = "/System/Library/Fonts/Supplemental"
def F(n, s): return ImageFont.truetype(os.path.join(FD, n), s)
W, H = 1080, 1920


def wrap(draw, text, fnt, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out


def segments(words, max_words=3):
    """Group word timestamps into short caption chunks, breaking on punctuation."""
    segs, cur = [], []
    for w in words:
        cur.append(w)
        ends = re.search(r"[.,!?;:]$", w["word"])
        if len(cur) >= max_words or ends:
            segs.append({"text": " ".join(x["word"] for x in cur),
                         "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur = []
    if cur:
        segs.append({"text": " ".join(x["word"] for x in cur),
                     "start": cur[0]["start"], "end": cur[-1]["end"]})
    return segs


def frame(hook, caption, progress):
    img = Image.new("RGB", (W, H), ASPHALT); d = ImageDraw.Draw(img)
    # glow
    glow = Image.new("RGB", (W, H), ASPHALT); gd = ImageDraw.Draw(glow)
    for r in range(640, 0, -14):
        a = int(20 * (r / 640))
        gd.ellipse([W//2 - r, 360 - r, W//2 + r, 360 + r],
                   fill=(min(ASPHALT[0]+a, 255), min(ASPHALT[1]+a//3, 255), ASPHALT[2]))
    img = Image.blend(img, glow, 0.55); d = ImageDraw.Draw(img)
    # caution tape top
    for x in range(-40, W + 40, 84):
        d.polygon([(x, 0), (x + 42, 0), (x + 42 - 30, 30), (x - 30, 30)], fill=YELLOW)
    # hook title (top third)
    hf = F("Arial Black.ttf", 76)
    y = 180
    for ln in wrap(d, hook.upper(), hf, W - 150):
        d.text((W/2, y), ln, font=hf, fill=HI, anchor="ma"); y += 88
    d.rectangle([W/2 - 90, y + 18, W/2 + 90, y + 30], fill=WHITE)
    # caption (center) — big, white, current phrase
    if caption:
        cf = F("Arial Black.ttf", 96)
        lines = wrap(d, caption.upper(), cf, W - 150)
        ch = len(lines) * 108
        cy = (H - ch) // 2 + 80
        for ln in lines:
            d.text((W/2, cy), ln, font=cf, fill=WHITE, anchor="ma"); cy += 108
    # progress bar
    d.rectangle([0, H - 150, W, H - 144], fill=(45, 49, 55))
    d.rectangle([0, H - 150, int(W * progress), H - 144], fill=HI)
    # brand lockup bottom
    d.rounded_rectangle([W/2 - 165, H - 110, W/2 - 105, H - 50], radius=10, fill=HI)
    d.text((W/2 - 152, H - 106), "B", font=F("Arial Black.ttf", 46), fill=ASPHALT)
    bf = F("Arial Black.ttf", 40)
    d.text((W/2 - 90, H - 102), "BOOKED", font=bf, fill=WHITE)
    bw = d.textlength("BOOKED", font=bf)
    d.text((W/2 - 90 + bw + 8, H - 102), "JOB", font=bf, fill=HI)
    return img


def build(hook, script, out, voice=None, backend="heygen"):
    generate_speech, default_voice = _tts(backend)
    voice = voice or default_voice
    tmp = tempfile.mkdtemp(prefix="reel_")
    wav = os.path.join(tmp, "vo.wav")
    _, dur, words = generate_speech(script, voice, wav)
    if not words:
        sys.exit("no word timestamps returned")
    segs = segments(words)
    # timeline: lead-in (hook only) until first word, then each seg until next seg start
    timeline = []
    if segs[0]["start"] > 0.05:
        timeline.append({"cap": "", "start": 0.0})
    for s in segs:
        timeline.append({"cap": s["text"], "start": s["start"]})
    # render frames + durations
    concat = os.path.join(tmp, "concat.txt")
    lines = []
    for i, t in enumerate(timeline):
        end = timeline[i + 1]["start"] if i + 1 < len(timeline) else dur
        d = max(0.2, end - t["start"])
        p = min(1.0, t["start"] / dur) if dur else 0
        fp = os.path.join(tmp, f"f{i:03d}.png")
        frame(hook, t["cap"], p).save(fp)
        lines.append(f"file '{fp}'\nduration {d:.3f}")
    lines.append(f"file '{os.path.join(tmp, f'f{len(timeline)-1:03d}.png')}'")  # repeat last
    open(concat, "w").write("\n".join(lines) + "\n")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-i", wav,
           "-vf", "scale=1080:1920,format=yuv420p,fps=30",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg error:\n" + r.stderr[-1500:])
    return out, dur


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hook", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--backend", default="heygen", choices=["heygen", "elevenlabs"])
    a = ap.parse_args()
    out, dur = build(a.hook, a.script, a.out, a.voice, a.backend)
    print(f"built {out} ({dur:.1f}s)")
