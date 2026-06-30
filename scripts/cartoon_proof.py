#!/usr/bin/env python3
"""
1-beat ANIMATED CARTOON proof (Path A): Recraft flat illustration + code-driven
motion. Shows the look + motion before building the full engine. Renders the hook
beat: on-brand cartoon contractor scene with a living camera (pop-in + push + bob),
tumbling cartoon coins draining away, and a kinetic word-pop caption, over the
Torque Marshal VO. 30fps frame-by-frame.
"""
import hashlib, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_lesson as ML
import recraft_image as RC
import elevenlabs_tts as TTS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H, FPS = 1920, 1080, 30
HI, HI2, ASPHALT, WHITE, YELLOW = ML.HI, ML.HI2, ML.ASPHALT, ML.WHITE, ML.YELLOW
F = ML.F
BRAND = [[255, 106, 0], [21, 23, 26], [255, 210, 63], [244, 242, 238], [42, 47, 54]]
VO = ("Let's cut the shit. You're a damn good tradesman, and you're still broke "
      "some months. Nobody ever taught you the one thing that fills the schedule.")


def ease(t):
    return 1 - (1 - max(0, min(1, t))) ** 3


def back(t):  # ease-out-back (overshoot) for pops
    t = max(0, min(1, t)); c = 1.70158 + 1
    return 1 + (c + 1) * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def cover(im):
    iw, ih = im.size; s = max(W / iw, H / ih)
    return im.resize((int(iw * s) + 2, int(ih * s) + 2), Image.LANCZOS)


def cam(covimg, scale, dy):
    sw, sh = int(W * scale), int(H * scale)
    big = covimg.resize((sw, sh), Image.LANCZOS)
    x = (sw - W) // 2; y = (sh - H) // 2 + dy
    x = max(0, min(sw - W, x)); y = max(0, min(sh - H, y))
    return big.crop((x, y, x + W, y + H)).convert("RGBA")


def draw_coin(d, cx, cy, r, squash):
    w = int(r * squash)
    d.ellipse([cx - w, cy - r, cx + w, cy + r], fill=(255, 210, 63), outline=(180, 140, 20), width=4)
    if w > 8:
        d.text((cx, cy - r * 0.7), "$", font=F("Arial Black.ttf", int(r * 1.1)),
               fill=(150, 110, 10), anchor="ma")


def cues_from_words(words):
    out, line, lstart = [], [], None
    for w in words:
        if w.get("start") is None:
            continue
        if lstart is None:
            lstart = w["start"]
        line.append(w)
        if len(line) >= 4 or w["word"][-1:] in ".,!?":
            out.append((lstart, w["end"], " ".join(x["word"] for x in line))); line, lstart = [], None
    if line:
        out.append((lstart, words[-1]["end"], " ".join(x["word"] for x in line)))
    return out


def kinetic_caption(d, cues, t):
    cur = None
    for s, e, txt in cues:
        if s <= t <= e + 0.25:
            cur = (s, txt)
    if not cur:
        return
    s, txt = cur
    raw = back((t - s) / 0.22) if (t - s) < 0.22 else 1.0
    pop = max(0.05, min(1.25, raw))
    cf = F("Arial Black.ttf", max(1, int(76 * pop)))
    lines = ML.wrap(d, txt.upper(), cf, W - 360)
    lh = max(1, int(84 * pop))
    y = H - 150 - len(lines) * lh
    for ln in lines:
        d.text((W / 2, y), ln, font=cf, fill=WHITE, anchor="ma",
               stroke_width=6, stroke_fill=(0, 0, 0)); y += lh


def main():
    out = os.path.join(ROOT, "content", "course", "cartoon_proof.mp4")
    tmp = tempfile.mkdtemp(prefix="cartoon_")
    # 1) Recraft scene (on-brand cartoon), cached
    scene_prompt = ("A stylized flat cartoon contractor wearing a yellow hard hat and orange "
                    "hi-vis vest, sitting in a pickup truck at dawn, looking stressed and tired "
                    "holding a phone. Modern flat explainer illustration, bold clean shapes, "
                    "subtle grain, dark slate background, empty space at top for a title.")
    webp, how = RC.generate(scene_prompt, style="digital_illustration", substyle="2d_art_poster_2",
                            size="1820x1024", colors=BRAND)
    print(f"scene image [{how}]")
    scene_png = os.path.join(tmp, "scene.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", webp, scene_png], check=True)
    cov = cover(Image.open(scene_png).convert("RGB"))

    # 2) VO (Torque Marshal, cached)
    cache = os.path.join(ROOT, "content", "course", ".tts_cache"); os.makedirs(cache, exist_ok=True)
    k = hashlib.md5((TTS.DEFAULT_VOICE + "\n" + VO).encode()).hexdigest()
    mp3 = os.path.join(cache, k + ".mp3"); meta = os.path.join(cache, k + ".json")
    if os.path.exists(mp3) and os.path.exists(meta):
        words = json.load(open(meta))["words"]
    else:
        _, _, words = TTS.generate_speech(VO, TTS.DEFAULT_VOICE, mp3)
        json.dump({"words": words}, open(meta, "w"))
    dur = ML.ffprobe_dur(mp3) or 8.0
    cues = cues_from_words(words)
    LEAD, TAIL = 0.3, 0.6
    total = LEAD + dur + TAIL
    print(f"vo {dur:.1f}s, {len(cues)} caption pops, total {total:.1f}s")

    # 3) frames
    fr = os.path.join(tmp, "f"); os.makedirs(fr)
    nframes = int(total * FPS)
    # coin field
    coins = [(0.08 + 0.84 * (i / 9), (i * 0.137) % 1.0, 26 + (i % 3) * 8) for i in range(10)]
    for fi in range(nframes):
        t = fi / FPS
        scale = (1.08 - 0.08 * ease(min(1, t / 0.5))) + 0.035 * (t / total)
        dy = int(3 * math.sin(t * 2.1))
        img = cam(cov, scale, dy); d = ImageDraw.Draw(img)
        # darken top for title legibility
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rectangle([0, 0, W, 250], fill=(10, 12, 14, 150)); img = Image.alpha_composite(img, ov)
        d = ImageDraw.Draw(img)
        # tumbling coins draining down-right (the "you're still broke" motif), after 1s
        if t > 1.0:
            for cx0, ph0, r in coins:
                ph = (ph0 + (t - 1.0) * 0.45) % 1.0
                cx = int(W * (cx0 * 0.5 + 0.45) + 40 * math.sin(ph * 6))
                cy = int(200 + ph * (H - 120))
                draw_coin(d, cx, cy, r, abs(math.cos(ph * 7)))
        kinetic_caption(d, cues, t - LEAD)
        # brand lockup
        d.rounded_rectangle([W - 250, H - 70, W - 204, H - 24], radius=9, fill=HI)
        d.text((W - 241, H - 70), "B", font=F("Arial Black.ttf", 34), fill=ASPHALT)
        d.text((W - 196, H - 66), "BOOKED", font=F("Arial Black.ttf", 30), fill=WHITE)
        bw = d.textlength("BOOKED", font=F("Arial Black.ttf", 30))
        d.text((W - 196 + bw + 6, H - 66), "JOB", font=F("Arial Black.ttf", 30), fill=HI)
        img.convert("RGB").save(os.path.join(fr, f"{fi:04d}.png"))
    print(f"rendered {nframes} frames")

    # 4) audio (lead silence + vo) + mux
    sil = os.path.join(tmp, "sil.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=stereo", "-t", str(LEAD), sil], check=True)
    al = os.path.join(tmp, "a.txt"); open(al, "w").write(f"file '{sil}'\nfile '{mp3}'\n")
    audio = os.path.join(tmp, "a.m4a")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", al,
                    "-c:a", "aac", "-b:a", "176k", audio], check=True)
    r = subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(fr, "%04d.png"),
                        "-i", audio, "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "18", "-c:a", "aac", "-b:a", "176k", "-shortest",
                        "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("mux failed:\n" + r.stderr[-1200:])
    print(f"built {out} (~{total:.0f}s)")


if __name__ == "__main__":
    main()
