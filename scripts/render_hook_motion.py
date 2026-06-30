#!/usr/bin/env python3
"""
Quality-bar slice for the full-motion cartoon explainer (autonomous, Path A+).
Proves real character motion via layered compositing + the 12 principles:
 - separate background (parallax drift + slow zoom) and hue-keyed CHARACTER layer
 - character is ALIVE: breathing (squash/stretch), idle sway (rotate+shift), bob
 - eased, anticipated motion graphics (coins pop with squash/stretch + overshoot)
 - kinetic word-pop captions synced to Torque Marshal VO
30fps. Renders ~the hook beat to content/course/hook_motion.mp4.
"""
import hashlib, json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_lesson as ML
import elevenlabs_tts as TTS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CC = os.path.join(ROOT, "content", "course", ".recraft_cache")
W, H, FPS = 1920, 1080, 30
HI, YELLOW, WHITE = ML.HI, ML.YELLOW, ML.WHITE
F = ML.F
VO = ("Let's cut the shit. You're a damn good tradesman, and you're still broke "
      "some months. Nobody ever taught you the one thing that fills the schedule.")


def ease(t): return 1 - (1 - max(0, min(1, t))) ** 3
def eio(t):
    t = max(0, min(1, t)); return 4*t*t*t if t < .5 else 1-(-2*t+2)**3/2
def back(t):
    t = max(0, min(1, t)); c = 2.70158
    return 1 + (c+1)*(t-1)**3 + 1.70158*(t-1)**2


def tightcrop(im):
    a = np.array(im)[..., 3]; ys, xs = np.where(a > 12)
    return im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))


def cover(im, scale=1.0):
    iw, ih = im.size; s = max(W/iw, H/ih)*scale
    return im.resize((int(iw*s)+2, int(ih*s)+2), Image.LANCZOS)


def cues(words):
    out, line, ls = [], [], None
    for w in words:
        if w.get("start") is None: continue
        if ls is None: ls = w["start"]
        line.append(w)
        if len(line) >= 4 or w["word"][-1:] in ".,!?":
            out.append((ls, w["end"], " ".join(x["word"] for x in line))); line, ls = [], None
    if line: out.append((ls, words[-1]["end"], " ".join(x["word"] for x in line)))
    return out


def kinetic(d, cs, t):
    cur = None
    for s, e, txt in cs:
        if s <= t <= e+0.2: cur = (s, txt)
    if not cur: return
    s, txt = cur
    pop = max(0.1, min(1.18, back((t-s)/0.18) if t-s < 0.18 else 1.0))
    cf = F("Arial Black.ttf", max(1, int(62*pop)))
    lines = ML.wrap(d, txt.upper(), cf, W-440); lh = max(1, int(72*pop))
    y = H-110-len(lines)*lh
    # caption shadow plate
    for ln in lines:
        d.text((W/2, y), ln, font=cf, fill=WHITE, anchor="ma", stroke_width=9, stroke_fill=(20, 24, 40)); y += lh


def coin(d, cx, cy, r, sq):
    w = max(2, int(r*sq))
    d.ellipse([cx-w, cy-r, cx+w, cy+r], fill=YELLOW, outline=(30, 34, 50), width=5)
    if w > 10:
        d.text((cx, cy-r*0.72), "$", font=F("Arial Black.ttf", int(r*1.1)), fill=(30, 34, 50), anchor="ma")


def main():
    out = os.path.join(ROOT, "content", "course", "hook_motion.mp4")
    bg = cover(Image.open(os.path.join(CC, "m_bg_hook.png")).convert("RGB"), 1.12)
    char = tightcrop(Image.open(os.path.join(CC, "m_char_hook_key.png")).convert("RGBA"))
    # scale character to ~84% frame height
    sc = int(H*0.84); char = char.resize((int(char.width*sc/char.height), sc), Image.LANCZOS)

    cache = os.path.join(ROOT, "content", "course", ".tts_cache")
    k = hashlib.md5((TTS.DEFAULT_VOICE+"\n"+VO).encode()).hexdigest()
    mp3, meta = os.path.join(cache, k+".mp3"), os.path.join(cache, k+".json")
    words = json.load(open(meta))["words"] if os.path.exists(meta) else \
        TTS.generate_speech(VO, TTS.DEFAULT_VOICE, mp3)[2]
    dur = ML.ffprobe_dur(mp3) or 8.0
    cs = cues(words)
    LEAD, TAIL = 0.3, 0.6; total = LEAD+dur+TAIL
    tmp = tempfile.mkdtemp(prefix="hookmo_"); fr = os.path.join(tmp, "f"); os.makedirs(fr)
    nframes = int(total*FPS)
    bw, bh = bg.size
    for fi in range(nframes):
        t = fi/FPS; p = t/total
        # --- background: parallax drift + slow zoom (ease) ---
        z = 1.0 + 0.05*eio(min(1, t/total))
        zw, zh = int(W*z), int(H*z)
        bgz = bg.resize((int(bw*zw/W), int(bh*zh/W)), Image.LANCZOS)
        ox = int((bgz.width-W)/2 + 26*math.sin(t*0.5))
        oy = int((bgz.height-H)/2 + 12*math.sin(t*0.4))
        ox = max(0, min(bgz.width-W, ox)); oy = max(0, min(bgz.height-H, oy))
        frame = bgz.crop((ox, oy, ox+W, oy+H)).convert("RGBA")
        # subtle vignette
        vg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); vd = ImageDraw.Draw(vg)
        vd.ellipse([-260, -180, W+260, H+180], fill=(0, 0, 0, 0), outline=None)
        # --- character: breathing (squash/stretch), sway, bob ---
        breathe = 1 + 0.022*math.sin(t*2*math.pi*0.55)       # vertical
        squashx = 1 - 0.012*math.sin(t*2*math.pi*0.55)        # volume-ish preserve
        cw2, ch2 = int(char.width*squashx), int(char.height*breathe)
        c = char.resize((cw2, ch2), Image.LANCZOS)
        ang = 1.6*math.sin(t*0.7)                              # idle sway rotation
        c = c.rotate(ang, resample=Image.BICUBIC, expand=True)
        bobx = int(8*math.sin(t*0.7)); boby = int(5*math.sin(t*2*math.pi*0.55+1.0))
        cx = (W-c.width)//2 + bobx; cy = H-ch2+ (c.height-ch2)//1 - 6 + boby
        frame.alpha_composite(c, (cx, H-ch2-8+boby))
        d = ImageDraw.Draw(frame)
        # --- coins (eased, squash/stretch, anticipation) ---
        if t > 0.9:
            for kk in range(9):
                ph = ((kk*0.137) + (t-0.9)*0.5) % 1.0
                pe = ease(ph)
                cxn = int(W*(0.6+0.36*(kk/9)) + 30*math.sin(ph*6))
                cyn = int(150 + pe*(H-60)); coin(d, cxn, cyn, 22+(kk % 3)*7, abs(math.cos(ph*7))*0.6+0.6)
        kinetic(d, cs, t-LEAD)
        # lockup
        d.rounded_rectangle([W-250, H-64, W-206, H-20], radius=9, fill=HI, outline=(20, 24, 40), width=3)
        d.text((W-241, H-63), "B", font=F("Arial Black.ttf", 33), fill=(20, 24, 40))
        d.text((W-196, H-60), "BOOKED", font=F("Arial Black.ttf", 29), fill=WHITE)
        bw2 = d.textlength("BOOKED", font=F("Arial Black.ttf", 29))
        d.text((W-196+bw2+6, H-60), "JOB", font=F("Arial Black.ttf", 29), fill=YELLOW)
        frame.convert("RGB").save(os.path.join(fr, f"{fi:04d}.png"))
    print(f"rendered {nframes} frames")
    sil = os.path.join(tmp, "sil.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=stereo", "-t", str(LEAD), sil], check=True)
    al = os.path.join(tmp, "a.txt"); open(al, "w").write(f"file '{sil}'\nfile '{mp3}'\n")
    audio = os.path.join(tmp, "a.m4a")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", al,
                    "-c:a", "aac", "-b:a", "176k", audio], check=True)
    r = subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(fr, "%04d.png"),
                        "-i", audio, "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "17", "-c:a", "aac", "-b:a", "176k", "-shortest",
                        "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode != 0: sys.exit("mux failed:\n"+r.stderr[-1000:])
    print(f"built {out} (~{total:.0f}s)")


if __name__ == "__main__":
    main()
