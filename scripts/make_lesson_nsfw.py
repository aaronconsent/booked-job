#!/usr/bin/env python3
"""
NSFW / uncensored cut of a Marketing 101 lesson — AI hero images (gpt-image-1)
with Ken Burns + meme cards + profane motion-text. NOT for the main YouTube
channel (age-restricted/demonetized); social / separate-channel only. No auto-upload.

Reuses the TTS cache (different profane script => its own VO) and the funnel
widget from make_lesson_motion. Frame-by-frame 30fps for real Ken Burns motion.

  python3 scripts/make_lesson_nsfw.py --lesson lesson-01 [--out ...] [--dry-run] [--img-quality medium]
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_lesson as ML
import make_lesson_motion as MO
import elevenlabs_tts as TTS
import openai_image

W, H = ML.W, ML.H
HI, HI2, ASPHALT, CARD = ML.HI, ML.HI2, ML.ASPHALT, ML.CARD
WHITE, YELLOW, MUTED, GREEN, LINE = ML.WHITE, ML.YELLOW, ML.MUTED, ML.GREEN, ML.LINE
F = ML.F
INTRO, GAP, TAIL, FPS = ML.INTRO, ML.GAP, ML.TAIL, 30
FD = "/System/Library/Fonts/Supplemental"


def impact(size):
    try:
        return ML.ImageFont.truetype(os.path.join(FD, "Impact.ttf"), size)
    except Exception:
        return F("Arial Black.ttf", size)


# ---- dark legibility overlay (stronger at bottom) ----
def _overlay():
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(H):
        a = int(70 + 120 * (y / H) ** 1.6)      # 70 top -> ~190 bottom
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    return ov
OVERLAY = _overlay()


def cover(im):
    iw, ih = im.size
    s = max(W / iw, H / ih)
    return im.resize((int(iw * s) + 2, int(ih * s) + 2), Image.LANCZOS)


def ken_burns(cov, kp):
    scale = 1.06 + 0.12 * kp
    sw, sh = int(W * scale), int(H * scale)
    big = cov.resize((sw, sh), Image.LANCZOS)
    maxdx, maxdy = sw - W, sh - H
    dx = int(maxdx * (0.35 + 0.30 * kp)); dy = int(maxdy * (0.30 + 0.30 * kp))
    dx = max(0, min(maxdx, dx)); dy = max(0, min(maxdy, dy))
    return big.crop((dx, dy, dx + W, dy + H)).convert("RGB")


def photo_bg(cov, kp):
    img = ken_burns(cov, kp).convert("RGBA")
    img = Image.alpha_composite(img, OVERLAY)
    return img.convert("RGB")


def stroked(d, xy, text, font, fill=WHITE, anchor=None, sw=4):
    d.text(xy, text, font=font, fill=fill, anchor=anchor,
           stroke_width=sw, stroke_fill=(0, 0, 0))


def draw_heading_photo(d, scene, p):
    head = scene.get("heading", "")
    if not head:
        return
    LX = 150
    label = ML._seg_label(scene["kind"])
    if label:
        ef = F("Arial Bold.ttf", 30)
        stroked(d, (LX, 150), label.upper(), ef, fill=ML._seg_color(scene["kind"]), sw=3)
    a = MO.ease(min(1, p * 4)); rise = int((1 - a) * 22)
    hf = F("Arial Black.ttf", 64); hy = 206
    for ln in ML.wrap(d, head, hf, W - 300):
        stroked(d, (LX, hy - rise), ln, hf,
                fill=YELLOW if scene["kind"] == "action" else WHITE, sw=4); hy += 74
    # bullets (if any) under heading
    bl = scene.get("bullets", [])
    if bl:
        bf = F("Arial Black.ttf", 50); by = hy + 20
        for i, b in enumerate(bl):
            ip = MO.item_p(p, i, len(bl))
            if ip <= 0:
                continue
            x = int(LX - (1 - ip) * 300)
            d.ellipse([x, by + 18, x + 18, by + 36], fill=HI)
            stroked(d, (x + 40, by), b, bf, sw=3); by += 74


def meme_text(d, scene, p):
    m = scene["meme"]
    a = MO.ease(min(1, p * 3))
    if a <= 0:
        return
    if m.get("top"):
        ft = impact(76)
        y = 70
        for ln in ML.wrap(d, m["top"].upper(), ft, W - 200):
            stroked(d, (W / 2, y), ln, ft, anchor="ma", sw=6); y += 84
    if m.get("bottom"):
        fb = impact(82)
        lines = ML.wrap(d, m["bottom"].upper(), fb, W - 180)
        y = H - 130 - len(lines) * 92
        for ln in lines:
            stroked(d, (W / 2, y), ln, fb, anchor="ma", sw=6); y += 92


def caption_photo(d, segs, t):
    cur = ""
    for s in segs:
        if s["start"] <= t:
            cur = s["text"]
    if not cur:
        return
    cf = F("Arial Black.ttf", 38)
    lines = ML.wrap(d, cur.upper(), cf, W - 420)
    y = H - 116 - len(lines) * 46
    for ln in lines:
        stroked(d, (W / 2, y), ln, cf, anchor="ma", sw=4); y += 46


def title_frame(bg, lesson, p):
    img = bg.copy(); d = ML.chrome(img, lesson, 0.0)
    a = MO.ease(min(1, p / 0.5))
    d.text((W / 2, 290), f"LESSON {lesson['number']} · UNCUT", font=F("Arial Bold.ttf", 50),
           fill=HI2, anchor="ma")
    rise = int((1 - a) * 30); tf = F("Arial Black.ttf", 108); y = 370
    for ln in ML.wrap(d, lesson["title"].upper(), tf, W - 360):
        d.text((W / 2, y - rise), ln, font=tf, fill=WHITE, anchor="ma"); y += 120
    return img


def build(lesson, out, dry=False, img_quality="medium"):
    scenes = lesson["scenes"]
    print(f"Lesson {lesson['number']} (NSFW): {lesson['title']} — {len(scenes)} scenes")
    imgs = [(i, s.get("image") or (s.get("meme") or {}).get("img"))
            for i, s in enumerate(scenes)]
    imgs = [(i, p) for i, p in imgs if p]
    print(f"  AI images needed: {len(imgs)}")
    if dry:
        for i, s in enumerate(scenes):
            tag = "meme" if s.get("meme") else ("photo" if s.get("image") else
                  (s.get("motion") or "text"))
            print(f"   [{i}] {s['kind']:8} {tag:6} {s.get('heading','')[:46]}")
        return None, 0

    # Pre-generate AI images (cached)
    covers = {}
    for i, prompt in imgs:
        path, how = openai_image.generate(prompt, quality=img_quality)
        covers[i] = cover(Image.open(path).convert("RGB"))
        print(f"  🖼  scene {i} image [{how}]")

    voice = TTS.DEFAULT_VOICE
    tmp = tempfile.mkdtemp(prefix="lessonsx_")
    cache = os.path.join(ROOT, "content", "course", ".tts_cache"); os.makedirs(cache, exist_ok=True)
    parts = []
    for i, s in enumerate(scenes):
        key = hashlib.md5((voice + "\n" + s["vo"]).encode()).hexdigest()
        cmp3, cmeta = os.path.join(cache, key + ".mp3"), os.path.join(cache, key + ".json")
        if os.path.exists(cmp3) and os.path.exists(cmeta):
            words = json.load(open(cmeta))["words"]; hit = "cached"
        else:
            _, _, words = TTS.generate_speech(s["vo"], voice, cmp3)
            json.dump({"words": words}, open(cmeta, "w")); hit = "TTS"
        parts.append({"mp3": cmp3, "dur": ML.ffprobe_dur(cmp3) or 1.0, "words": words, "scene": s})
        print(f"  ✓ scene {i} ({s['kind']}) {parts[-1]['dur']:.1f}s [{hit}]")

    total = INTRO + TAIL + GAP * len(scenes) + sum(p["dur"] for p in parts)
    brand_bg = ML.base_canvas()
    frames = os.path.join(tmp, "f"); os.makedirs(frames)
    idx = 0
    def save(img):
        nonlocal idx
        img.save(os.path.join(frames, f"{idx:06d}.png")); idx += 1

    for f in range(int(INTRO * FPS)):
        save(title_frame(brand_bg, lesson, f / max(1, INTRO * FPS)))

    offset = INTRO
    for pi, part in enumerate(parts):
        s, dur, words = part["scene"], part["dur"], part["words"]
        segs = ML.segments(words)
        nf = max(1, int(dur * FPS))
        cov = covers.get(pi)
        for f in range(nf):
            t = f / FPS; p = min(1, t / dur)
            bg = photo_bg(cov, p) if cov is not None else brand_bg.copy()
            d = ML.chrome(bg, lesson, (offset + t) / total)
            if s.get("meme"):
                meme_text(d, s, p)
            else:
                draw_heading_photo(d, s, p)
                if s.get("motion") == "funnel" and cov is None:
                    MO.w_funnel(d, p, s, 360)
            if s.get("cite"):
                cf = F("Arial Bold.ttf", 26); cw = d.textlength("SOURCE: " + s["cite"], font=cf)
                MO.rrect(d, [W - 150 - cw - 40, H - 150, W - 150, H - 104], 9, fill=ASPHALT, outline=LINE)
                d.text((W - 150 - cw - 20, H - 144), "SOURCE: " + s["cite"], font=cf, fill=MUTED)
            if not s.get("meme"):
                caption_photo(d, segs, t)
            save(bg)
        last = Image.open(os.path.join(frames, f"{idx-1:06d}.png"))
        for _ in range(int(GAP * FPS)):
            save(last.copy())
        offset += dur + GAP
        print(f"  ✦ scene {pi} ({s['kind']}) frames→{idx}")
    last = Image.open(os.path.join(frames, f"{idx-1:06d}.png"))
    for _ in range(int(TAIL * FPS)):
        save(last.copy())

    si, sg, st = os.path.join(tmp, "si.mp3"), os.path.join(tmp, "sg.mp3"), os.path.join(tmp, "st.mp3")
    ML.silence(si, INTRO); ML.silence(sg, GAP); ML.silence(st, TAIL)
    alist = [si]
    for part in parts:
        alist += [part["mp3"], sg]
    alist += [st]
    open(os.path.join(tmp, "a.txt"), "w").write("\n".join(f"file '{a}'" for a in alist) + "\n")
    audio = os.path.join(tmp, "a.m4a")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "a.txt"),
                        "-c:a", "aac", "-b:a", "176k", audio], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("audio error:\n" + r.stderr[-1000:])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    r = subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(frames, "%06d.png"),
                        "-i", audio, "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "20", "-c:a", "aac", "-b:a", "176k", "-shortest",
                        "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg error:\n" + r.stderr[-1500:])
    print(f"  built {out}  ({idx} frames, ~{idx/FPS:.0f}s)")
    return out, total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", required=True)
    ap.add_argument("--lessons", default=os.path.join(ROOT, "content", "course", "lessons_nsfw.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--img-quality", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.lessons))
    lesson = next((l for l in data["lessons"] if l["id"] == a.lesson), None)
    if not lesson:
        sys.exit(f"lesson {a.lesson} not found")
    out = a.out or os.path.join(ROOT, "content", "course", f"{a.lesson}-nsfw.mp4")
    build(lesson, out, a.dry_run, a.img_quality)
