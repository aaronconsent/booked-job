#!/usr/bin/env python3
"""
Animated CARTOON explainer renderer (Path A, the real engine). Per beat: a flat-
vector Recraft scene (locked style_id) + a living camera (push/bob) + a beat-
specific animated accent (coins/checks/bubbles/rain/ripple/arrow) + kinetic
word-pop captions synced to the Torque Marshal VO; meme beats get big kinetic
Impact text; the funnel beat is a code-drawn animated cartoon diagram. Beats are
crossfaded with quick slides (skill assemble.sh) and the VO is laid over the top.

  python3 scripts/render_cartoon_lesson.py [--lesson lesson-01] [--out ...]
"""
import hashlib, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_lesson as ML
import elevenlabs_tts as TTS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKILL = os.path.expanduser("~/.claude/skills/faceless-youtube-video/scripts")
W, H, FPS = 1920, 1080, 30
HI, HI2, ASPHALT, WHITE, YELLOW, GREEN = ML.HI, ML.HI2, ML.ASPHALT, ML.WHITE, ML.YELLOW, ML.GREEN
INK = (28, 30, 34); SLATE = (60, 66, 74)
F = ML.F
FD = "/System/Library/Fonts/Supplemental"
BREATH, XF, LEAD = 0.5, 0.35, 0.3
CACHE = os.path.join(ROOT, "content", "course", ".recraft_cache")

# beat index -> (scene file | "funnel", accent, kenburns dir)
PLAN = {
    0: ("scene_b0_hook.png", "coins", "in"),
    1: ("scene_b1_learn.png", "checks", "left"),
    2: ("scene_b2_dumpster.png", "embers", "in"),
    3: ("funnel", "none", "none"),
    4: ("scene_b4_wordmouth.png", "bubbles", "right"),
    5: ("lock14_garage.png", "ripple", "in"),
    6: ("scene_b6_storm.png", "rain", "left"),
    7: ("scene_b7_clipboard.png", "checks", "in"),
    8: ("scene_b8_calculator.png", "arrow", "out"),
}
SCRATCH = ("/private/tmp/claude-501/-Users-aaronphillips-GIT/"
           "0519c67f-1628-4c96-a207-073cceb75055/scratchpad")


def impact(s):
    try:
        return ML.ImageFont.truetype(os.path.join(FD, "Impact.ttf"), s)
    except Exception:
        return F("Arial Black.ttf", s)


def ease(t):
    return 1 - (1 - max(0, min(1, t))) ** 3


def back(t):
    t = max(0, min(1, t)); c = 2.70158
    return 1 + (c + 1) * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def cover(im):
    iw, ih = im.size; s = max(W / iw, H / ih)
    return im.resize((int(iw * s) + 2, int(ih * s) + 2), Image.LANCZOS)


def cam(cov, scale, dy):
    sw, sh = int(W * scale), int(H * scale)
    big = cov.resize((sw, sh), Image.LANCZOS)
    x = max(0, min(sw - W, (sw - W) // 2)); y = max(0, min(sh - H, (sh - H) // 2 + dy))
    return big.crop((x, y, x + W, y + H)).convert("RGBA")


# ---- accents (d, t, dur) ----
def _coin(d, cx, cy, r, sq):
    w = max(2, int(r * sq))
    d.ellipse([cx - w, cy - r, cx + w, cy + r], fill=YELLOW, outline=(40, 40, 40), width=4)
    if w > 9:
        d.text((cx, cy - r * 0.72), "$", font=F("Arial Black.ttf", int(r * 1.1)), fill=(40, 40, 40), anchor="ma")


def acc_coins(d, t, dur):
    if t < 0.8:
        return
    for k in range(9):
        ph = ((k * 0.137) + (t - 0.8) * 0.5) % 1.0
        cx = int(W * (0.55 + 0.4 * (k / 9)) + 36 * math.sin(ph * 6))
        cy = int(160 + ph * (H - 80)); _coin(d, cx, cy, 24 + (k % 3) * 7, abs(math.cos(ph * 7)))


def acc_embers(d, t, dur):
    for k in range(40):
        ph = ((k * 0.0731) + t * 0.6) % 1.0
        x = int(W * ((k * 37 % 100) / 100)); y = int(H - ph * H)
        r = 3 + (k % 3); a = int(220 * (1 - ph))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 150 + k % 80, 30))


def acc_checks(d, t, dur):
    for i in range(3):
        ip = back((t - 0.5 - i * 0.5) / 0.3)
        if ip <= 0:
            continue
        r = int(40 * min(1.2, ip)); cx, cy = W - 220, 230 + i * 150
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN, outline=(30, 30, 30), width=5)
        d.line([cx - r * 0.4, cy, cx - r * 0.05, cy + r * 0.4], fill=WHITE, width=9)
        d.line([cx - r * 0.05, cy + r * 0.4, cx + r * 0.5, cy - r * 0.4], fill=WHITE, width=9)


def acc_bubbles(d, t, dur):
    for k in range(5):
        ph = ((k * 0.2) + t * 0.25) % 1.0
        x = int(140 + k * 320); y = int(H * 0.78 - ph * 220); a = max(0, 1 - ph)
        if a <= 0:
            continue
        r = 30 + k % 3 * 6
        d.rounded_rectangle([x, y, x + r * 2.4, y + r * 1.5], radius=18, fill=WHITE, outline=(40, 40, 40), width=4)
        d.ellipse([x + 14, y + r * 0.55, x + 24, y + r * 0.55 + 10], fill=SLATE)
        d.ellipse([x + 40, y + r * 0.55, x + 50, y + r * 0.55 + 10], fill=SLATE)
        d.ellipse([x + 66, y + r * 0.55, x + 76, y + r * 0.55 + 10], fill=SLATE)


def acc_rain(d, t, dur):
    for k in range(70):
        ph = ((k * 0.041) + t * 1.1) % 1.0
        x = int((k * 53) % W); y = int(ph * H)
        d.line([x, y, x - 10, y + 34], fill=(150, 180, 210), width=3)


def acc_ripple(d, t, dur):
    cx, cy = int(W * 0.5), int(H * 0.82)
    for k in range(3):
        ph = ((t * 0.6) + k / 3) % 1.0; r = int(20 + ph * 240); a = int(180 * (1 - ph))
        if a <= 0:
            continue
        d.ellipse([cx - r, cy - r // 3, cx + r, cy + r // 3], outline=(120, 170, 210, a), width=5)


def acc_arrow(d, t, dur):
    p = ease(min(1, t / 1.0)); x0, x1, y = 220, 220 + int((W - 600) * p), int(H * 0.5)
    d.line([220, y, x1, y], fill=HI, width=12)
    if p > 0.95:
        d.polygon([(x1, y - 24), (x1 + 44, y), (x1, y + 24)], fill=HI)


def acc_none(d, t, dur):
    pass


ACC = {"coins": acc_coins, "embers": acc_embers, "checks": acc_checks, "bubbles": acc_bubbles,
       "rain": acc_rain, "ripple": acc_ripple, "arrow": acc_arrow, "none": acc_none}


def funnel_frame(t, dur):
    """Code-drawn animated cartoon funnel (matches the flat thick-outline style)."""
    img = Image.new("RGBA", (W, H), (245, 242, 236, 255)); d = ImageDraw.Draw(img)
    stages = [("STRANGER", "1,000", 820), ("VISITOR", "300", 600), ("LEAD", "80", 400), ("PAID", "12", 240)]
    cx, top, bh, gap = W // 2 - 120, 250, 120, 40
    for i, (lab, cnt, w) in enumerate(stages):
        y = top + i * (bh + gap)
        rev = ease((t - i * 0.5) / 0.4)
        col = (GREEN if i == 3 else HI)
        d.rounded_rectangle([cx - w // 2, y, cx + w // 2, y + bh], radius=18, outline=(30, 30, 30), width=6,
                            fill=(235, 235, 235))
        if rev > 0:
            fw = int(w * rev)
            d.rounded_rectangle([cx - w // 2, y, cx - w // 2 + fw, y + bh], radius=18, fill=col)
        d.text((cx, y + bh / 2 - 26), lab, font=F("Arial Black.ttf", 44), fill=(30, 30, 30), anchor="mm")
        if rev > 0.5:
            d.text((cx + w // 2 + 40, y + bh / 2), cnt, font=F("Arial Black.ttf", 40), fill=(30, 30, 30), anchor="lm")
    # flowing dots
    for k in range(6):
        ph = ((t * 2.0) + k / 6) % 1.0
        d.ellipse([cx - 9, top + ph * (3 * (bh + gap) + bh) - 9, cx + 9, top + ph * (3 * (bh + gap) + bh) + 9], fill=YELLOW, outline=(30, 30, 30), width=2)
    return img


def cues(words):
    out, line, ls = [], [], None
    for w in words:
        if w.get("start") is None:
            continue
        if ls is None:
            ls = w["start"]
        line.append(w)
        if len(line) >= 4 or w["word"][-1:] in ".,!?":
            out.append((ls, w["end"], " ".join(x["word"] for x in line))); line, ls = [], None
    if line:
        out.append((ls, words[-1]["end"], " ".join(x["word"] for x in line)))
    return out


def kinetic(d, cs, t):
    cur = None
    for s, e, txt in cs:
        if s <= t <= e + 0.2:
            cur = (s, txt)
    if not cur:
        return
    s, txt = cur
    pop = max(0.1, min(1.2, back((t - s) / 0.2) if t - s < 0.2 else 1.0))
    cf = F("Arial Black.ttf", max(1, int(60 * pop)))
    lines = ML.wrap(d, txt.upper(), cf, W - 420); lh = max(1, int(70 * pop))
    y = H - 120 - len(lines) * lh
    for ln in lines:
        d.text((W / 2, y), ln, font=cf, fill=WHITE, anchor="ma", stroke_width=8, stroke_fill=(20, 20, 20)); y += lh


def meme_text(d, top, bot, t):
    a = back(min(1, t / 0.25))
    if top:
        ft = impact(max(1, int(84 * max(0.1, a)))); y = 60
        for ln in ML.wrap(d, top.upper(), ft, W - 160):
            d.text((W / 2, y), ln, font=ft, fill=WHITE, anchor="ma", stroke_width=8, stroke_fill=(20, 20, 20)); y += 92
    if bot:
        fb = impact(88); lines = ML.wrap(d, bot.upper(), fb, W - 140); y = H - 150 - len(lines) * 96
        for ln in lines:
            d.text((W / 2, y), ln, font=fb, fill=YELLOW, anchor="ma", stroke_width=8, stroke_fill=(20, 20, 20)); y += 96


def lockup(d):
    bx, by = W - 250, H - 66
    d.rounded_rectangle([bx, by, bx + 44, by + 44], radius=9, fill=HI, outline=(20, 20, 20), width=3)
    d.text((bx + 9, by + 1), "B", font=F("Arial Black.ttf", 34), fill=(20, 20, 20))
    d.text((bx + 56, by + 5), "BOOKED", font=F("Arial Black.ttf", 30), fill=(30, 30, 30))
    bw = d.textlength("BOOKED", font=F("Arial Black.ttf", 30))
    d.text((bx + 56 + bw + 6, by + 5), "JOB", font=F("Arial Black.ttf", 30), fill=HI)


def find_scene(fn):
    for p in (os.path.join(CACHE, fn), os.path.join(SCRATCH, fn)):
        if os.path.exists(p):
            return p
    return None


def beat_clip(i, scene_fn, accent, kbdir, vo_words, dur, meme, tmp):
    fr = os.path.join(tmp, f"b{i}"); os.makedirs(fr)
    total = dur + BREATH
    cs = cues(vo_words)
    cov = None
    if scene_fn != "funnel":
        sp = find_scene(scene_fn)
        cov = cover(Image.open(sp).convert("RGB"))
    n = int(total * FPS)
    for f in range(n):
        t = f / FPS
        if scene_fn == "funnel":
            img = funnel_frame(t, dur).copy()
        else:
            sc = (1.07 - 0.07 * ease(min(1, t / 0.5))) + 0.03 * (t / total)
            dy = int(3 * math.sin(t * 2.0)) * (1 if kbdir != "out" else -1)
            img = cam(cov, sc, dy)
        d = ImageDraw.Draw(img)
        if meme:
            meme_text(d, meme.get("top"), meme.get("bottom"), t)
        else:
            ACC[accent](d, t, dur)
            kinetic(d, cs, t)
        lockup(d)
        img.convert("RGB").save(os.path.join(fr, f"{f:04d}.png"))
    out = os.path.join(tmp, f"clip{i}.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", os.path.join(fr, "%04d.png"), "-vf", "format=yuv420p",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"beat {i} encode failed:\n{r.stderr[-800:]}")
    return out


def main():
    out = os.path.join(ROOT, "content", "course", "lesson-01-cartoon.mp4")
    data = json.load(open(os.path.join(ROOT, "content", "course", "lessons_nsfw.json")))
    beats = data["lessons"][0]["scenes"]
    tmp = tempfile.mkdtemp(prefix="cartoon_")
    cache = os.path.join(ROOT, "content", "course", ".tts_cache")
    clips, parts = [], []
    for i, b in enumerate(beats):
        k = hashlib.md5((TTS.DEFAULT_VOICE + "\n" + b["vo"]).encode()).hexdigest()
        mp3, meta = os.path.join(cache, k + ".mp3"), os.path.join(cache, k + ".json")
        words = json.load(open(meta))["words"] if os.path.exists(meta) else \
            TTS.generate_speech(b["vo"], TTS.DEFAULT_VOICE, mp3)[2]
        dur = ML.ffprobe_dur(mp3) or 4.0
        scene_fn, accent, kbdir = PLAN[i]
        clip = beat_clip(i, scene_fn, accent, kbdir, words, dur, b.get("meme"), tmp)
        clips.append(clip); parts.append({"mp3": mp3, "clipdur": ML.ffprobe_dur(clip)})
        print(f"  beat {i} ({scene_fn.split('.')[0]}, {accent}) {dur:.1f}s")
    # assemble with quick slides (skill assemble.sh)
    edit = os.path.join(tmp, "edit.mp4")
    subprocess.run(["bash", os.path.join(SKILL, "assemble.sh"), edit, str(XF), *clips], check=True)
    # narration at clip offsets (matches assemble.sh xfade timing)
    starts, acc = [0.0], 0.0
    for p in parts[:-1]:
        acc += p["clipdur"] - XF; starts.append(round(acc, 3))
    inp, filt, lbl = [], [], []
    for i, p in enumerate(parts):
        inp += ["-i", p["mp3"]]; dly = int((starts[i] + LEAD) * 1000)
        filt.append(f"[{i}:a]adelay={dly}|{dly}[a{i}]"); lbl.append(f"[a{i}]")
    narr = os.path.join(tmp, "narr.m4a")
    fc = ";".join(filt) + ";" + "".join(lbl) + f"amix=inputs={len(parts)}:normalize=0:duration=longest[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inp, "-filter_complex", fc, "-map", "[a]",
                    "-c:a", "aac", "-b:a", "176k", narr], check=True)
    r = subprocess.run(["ffmpeg", "-y", "-i", edit, "-i", narr, "-map", "0:v", "-map", "1:a",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "176k", "-movflags", "+faststart", out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("final mux failed:\n" + r.stderr[-1000:])
    print(f"built {out} ({ML.ffprobe_dur(out):.0f}s)")


if __name__ == "__main__":
    main()
