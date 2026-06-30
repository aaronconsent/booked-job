#!/usr/bin/env python3
"""
Build a faceless LONG-FORM 16:9 lesson video (1920x1080) for the Marketing 101
course — the channel's flagship teaching format (separate from the vertical
Shorts pipeline in make_reel.py).

  ElevenLabs "Torque Marshal" VO (per-scene, word-timed)
    -> branded motion-text scenes (building bullets, data lower-thirds,
       citation chips, word-synced caption band)
    -> ffmpeg concat -> chaptered MP4.

A lesson is a list of SCENES, each with narration (`vo`) + on-screen content.
Scene kinds: title | hook | learn | teach | example | cutaway | action | bridge.
The `cutaway` kind is the per-trade DATA slot (shows a stat + a citation chip);
v1 renders the generic version, trade versions swap in later from the stats DB.

Usage:
  python3 scripts/make_lesson.py --lesson lesson-01 \
      [--lessons content/course/lessons.json] [--out content/course/lesson-01.mp4]
      [--voice <id>] [--dry-run]

--dry-run prints the scene plan + estimated runtime WITHOUT calling TTS (free).
"""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import elevenlabs_tts as TTS

# ---- brand palette (matches make_reel.py) ----
HI = (255, 106, 0); HI2 = (255, 138, 43); ASPHALT = (15, 17, 19)
CARD = (26, 30, 34); WHITE = (244, 242, 238); YELLOW = (255, 210, 63)
MUTED = (138, 143, 151); GREEN = (34, 197, 94); LINE = (42, 47, 54)
W, H = 1920, 1080
FD = "/System/Library/Fonts/Supplemental"
INTRO, GAP, TAIL = 2.2, 0.32, 1.6   # seconds of held-frame padding


def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)


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


def segments(words, max_words=4):
    segs, cur = [], []
    for w in words:
        if w.get("start") is None:
            continue
        cur.append(w)
        if len(cur) >= max_words or re.search(r"[.,!?;:]$", w["word"]):
            segs.append({"text": " ".join(x["word"] for x in cur),
                         "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur = []
    if cur:
        segs.append({"text": " ".join(x["word"] for x in cur),
                     "start": cur[0]["start"], "end": cur[-1]["end"]})
    return segs


# ---------- background + persistent chrome ----------
def base_canvas():
    img = Image.new("RGB", (W, H), ASPHALT)
    glow = Image.new("RGB", (W, H), ASPHALT); gd = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.32), int(H * 0.42)
    for r in range(760, 0, -16):
        a = int(26 * (r / 760))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(min(ASPHALT[0] + a, 255), min(ASPHALT[1] + a // 3, 255), ASPHALT[2]))
    img = Image.blend(img, glow, 0.6)
    return img


def chrome(img, lesson, gprog):
    d = ImageDraw.Draw(img)
    # caution tape top edge
    for x in range(-50, W + 50, 96):
        d.polygon([(x, 0), (x + 48, 0), (x + 48 - 34, 26), (x - 34, 26)], fill=YELLOW)
    # course chip top-left
    cf = F("Arial Bold.ttf", 26)
    chip = f"MARKETING 101 · LESSON {lesson['number']}"
    tw = d.textlength(chip, font=cf)
    d.rounded_rectangle([54, 52, 54 + tw + 40, 96], radius=10, fill=CARD, outline=LINE)
    d.text((74, 60), chip, font=cf, fill=HI2)
    # brand lockup bottom-right
    bx, by = W - 340, H - 78
    d.rounded_rectangle([bx, by, bx + 46, by + 46], radius=9, fill=HI)
    d.text((bx + 9, by + 2), "B", font=F("Arial Black.ttf", 36), fill=ASPHALT)
    bf = F("Arial Black.ttf", 32)
    d.text((bx + 60, by + 6), "BOOKED", font=bf, fill=WHITE)
    bw = d.textlength("BOOKED", font=bf)
    d.text((bx + 60 + bw + 7, by + 6), "JOB", font=bf, fill=HI)
    # global progress bar (very bottom)
    d.rectangle([0, H - 8, W, H], fill=(40, 44, 50))
    d.rectangle([0, H - 8, int(W * max(0, min(1, gprog))), H], fill=HI)
    return d


def caption_band(d, text):
    if not text:
        return
    cf = F("Arial Black.ttf", 52)
    lines = wrap(d, text.upper(), cf, W - 360)
    bh = len(lines) * 64 + 36
    by = H - 150 - bh
    d.rounded_rectangle([160, by, W - 160, by + bh], radius=16,
                        fill=(0, 0, 0))  # solid band for legibility
    d.rounded_rectangle([160, by, W - 160, by + bh], radius=16, outline=LINE, width=2)
    y = by + 18
    for ln in lines:
        d.text((W / 2, y), ln, font=cf, fill=WHITE, anchor="ma"); y += 64


def eyebrow(d, x, y, text, color=HI):
    ef = F("Arial Bold.ttf", 30)
    d.text((x, y), text.upper(), font=ef, fill=color)
    tw = d.textlength(text.upper(), font=ef)
    d.rectangle([x, y + 42, x + min(tw, 220), y + 47], fill=color)


def bullet_block(d, x, y, bullets, shown, drift):
    bf = F("Arial Black.ttf", 56)
    yy = y + drift
    for b in bullets[:shown]:
        lines = wrap(d, b, bf, W - x - 300)
        d.ellipse([x, yy + 20, x + 18, yy + 38], fill=HI)
        for ln in lines:
            d.text((x + 42, yy), ln, font=bf, fill=WHITE); yy += 60
        yy += 26   # gap between bullets, advances by actual wrapped-line count


# ---------- per-scene visual ----------
def scene_static(scene, drift, reveal):
    """Compose the persistent (non-caption) visual for a scene at a given reveal
    fraction (0..1 across the scene) — bullets build, drift gives subtle motion."""
    img = base_canvas()
    return img  # chrome + content added in compose()


def compose(scene, lesson, caption, scene_prog, gprog):
    img = base_canvas()
    d = chrome(img, lesson, gprog)
    drift = int(scene_prog * 26)            # subtle Ken-Burns-ish vertical drift
    kind = scene["kind"]
    head = scene.get("heading", "")
    bullets = scene.get("bullets", [])
    LX = 150

    if kind in ("title",):
        # big centered lesson title card (intro hold)
        d.text((W / 2, 300), f"LESSON {lesson['number']}", font=F("Arial Bold.ttf", 56),
               fill=HI2, anchor="ma")
        tf = F("Arial Black.ttf", 116)
        y = 380
        for ln in wrap(d, lesson["title"].upper(), tf, W - 360):
            d.text((W / 2, y), ln, font=tf, fill=WHITE, anchor="ma"); y += 128
        d.text((W / 2, y + 30), "MARKETING 101 · FOR SERVICE PROS",
               font=F("Arial Bold.ttf", 34), fill=MUTED, anchor="ma")
        return img

    if head:
        eyebrow(d, LX, 150, _seg_label(kind), _seg_color(kind))
        hf = F("Arial Black.ttf", 66)
        hy = 210
        for ln in wrap(d, head, hf, W - 300):
            d.text((LX, hy), ln, font=hf, fill=WHITE if kind != "action" else YELLOW); hy += 76
        body_y = hy + 28
    else:
        body_y = 320

    if kind == "cutaway":
        # data lower-third panel + citation chip
        py = 440
        d.rounded_rectangle([LX, py, W - 150, py + 360], radius=20, fill=CARD, outline=HI, width=3)
        d.text((LX + 40, py + 30), "SAME MOMENT — YOUR TRADE", font=F("Arial Bold.ttf", 30), fill=HI2)
        yy = py + 90
        shown = max(1, min(len(bullets), int(scene_prog * len(bullets)) + 1))
        for b in bullets[:shown]:
            d.text((LX + 40, yy), "› " + b, font=F("Arial Black.ttf", 50), fill=WHITE); yy += 78
        cite = scene.get("cite", "")
        if cite:
            cf = F("Arial Bold.ttf", 26)
            cw = d.textlength("SOURCE: " + cite, font=cf)
            d.rounded_rectangle([W - 150 - cw - 40, py + 360 - 56, W - 150 - 14, py + 360 - 14],
                                radius=9, fill=ASPHALT, outline=LINE)
            d.text((W - 150 - cw - 22, py + 360 - 50), "SOURCE: " + cite, font=cf, fill=MUTED)
    elif bullets:
        shown = max(1, min(len(bullets), int(scene_prog * len(bullets)) + 1))
        bullet_block(d, LX, body_y, bullets, shown, drift)

    if kind == "action":
        d.rounded_rectangle([LX, 150, LX + 300, 200], radius=8, fill=HI)
        d.text((LX + 20, 158), "DO THIS NOW", font=F("Arial Black.ttf", 32), fill=ASPHALT)

    caption_band(d, caption)
    return img


def _seg_label(kind):
    return {"hook": "THE PROBLEM", "learn": "WHAT YOU'LL LEARN", "teach": "THE TEACHING",
            "example": "WORKED EXAMPLE", "cutaway": "YOUR TRADE",
            "action": "", "bridge": "UP NEXT"}.get(kind, "")


def _seg_color(kind):
    return {"example": YELLOW, "cutaway": HI2, "bridge": GREEN}.get(kind, HI)


# ---------- audio helpers ----------
def ffprobe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def silence(path, secs):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    "anullsrc=r=44100:cl=stereo", "-t", f"{secs:.3f}",
                    "-q:a", "9", path], capture_output=True, text=True)


# ---------- build ----------
def build(lesson, out, voice=None, dry=False):
    scenes = lesson["scenes"]
    words_est = sum(len(s["vo"].split()) for s in scenes)
    est_min = words_est / 150.0
    print(f"Lesson {lesson['number']}: {lesson['title']}")
    print(f"  {len(scenes)} scenes · ~{words_est} words · ~{est_min:.1f} min VO "
          f"(+{INTRO+TAIL+GAP*len(scenes):.1f}s padding)")
    reels = [i for i, s in enumerate(scenes) if s.get("reel")]
    print(f"  reel chop points: scenes {reels}")
    if dry:
        for i, s in enumerate(scenes):
            print(f"   [{i}] {s['kind']:8} {len(s['vo'].split()):3}w  {s.get('heading','')[:60]}")
        return None, est_min * 60

    voice = voice or TTS.DEFAULT_VOICE
    tmp = tempfile.mkdtemp(prefix="lesson_")
    cache = os.path.join(ROOT, "content", "course", ".tts_cache")
    os.makedirs(cache, exist_ok=True)
    # Pass 1: TTS each scene (cached by voice+text so re-renders don't re-spend credits)
    parts = []
    for i, s in enumerate(scenes):
        key = hashlib.md5((voice + "\n" + s["vo"]).encode()).hexdigest()
        cmp3, cmeta = os.path.join(cache, key + ".mp3"), os.path.join(cache, key + ".json")
        if os.path.exists(cmp3) and os.path.exists(cmeta):
            meta = json.load(open(cmeta)); words = meta["words"]; hit = "cached"
        else:
            _, _, words = TTS.generate_speech(s["vo"], voice, cmp3)
            json.dump({"words": words}, open(cmeta, "w")); hit = "TTS"
        real = ffprobe_dur(cmp3) or 1.0
        parts.append({"mp3": cmp3, "dur": real, "words": words, "scene": s})
        print(f"  ✓ scene {i} ({s['kind']}) {real:.1f}s [{hit}]")
    total = INTRO + TAIL + GAP * len(scenes) + sum(p["dur"] for p in parts)

    # title/intro card frame
    intro_img = compose({"kind": "title", "vo": ""}, lesson, "", 0.0, 0.0)
    concat_lines, idx = [], 0
    def emit(img, secs):
        nonlocal idx
        fp = os.path.join(tmp, f"f{idx:04d}.png"); idx += 1
        img.save(fp)
        concat_lines.append(f"file '{fp}'\nduration {max(0.10, secs):.3f}")
    emit(intro_img, INTRO)

    # Pass 2: render scene frames (word-synced caption + building visual)
    offset = INTRO
    for p in parts:
        s, dur, words = p["scene"], p["dur"], p["words"]
        segs = segments(words)
        if not segs:
            segs = [{"text": "", "start": 0.0, "end": dur}]
        timeline = []
        if segs[0]["start"] > 0.05:
            timeline.append({"cap": "", "start": 0.0})
        for sg in segs:
            timeline.append({"cap": sg["text"], "start": sg["start"]})
        for j, t in enumerate(timeline):
            end = timeline[j + 1]["start"] if j + 1 < len(timeline) else dur
            sp = min(1.0, t["start"] / dur) if dur else 0
            gp = (offset + t["start"]) / total
            emit(compose(s, lesson, t["cap"], sp, gp), max(0.12, end - t["start"]))
        # inter-scene gap: hold last frame
        emit(compose(s, lesson, timeline[-1]["cap"], 1.0, (offset + dur) / total), GAP)
        offset += dur + GAP

    concat_lines.append(f"file '{os.path.join(tmp, f'f{idx-1:04d}.png')}'")  # repeat last
    concat = os.path.join(tmp, "frames.txt")
    open(concat, "w").write("\n".join(concat_lines) + "\n")

    # Build audio track: INTRO sil + (scene + GAP sil)* + TAIL sil
    sil_intro = os.path.join(tmp, "sil_intro.mp3"); silence(sil_intro, INTRO)
    sil_gap = os.path.join(tmp, "sil_gap.mp3"); silence(sil_gap, GAP)
    sil_tail = os.path.join(tmp, "sil_tail.mp3"); silence(sil_tail, TAIL)
    alist = [sil_intro]
    for p in parts:
        alist += [p["mp3"], sil_gap]
    alist += [sil_tail]
    aconcat = os.path.join(tmp, "audio.txt")
    open(aconcat, "w").write("\n".join(f"file '{a}'" for a in alist) + "\n")
    full_audio = os.path.join(tmp, "audio.m4a")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", aconcat,
                        "-c:a", "aac", "-b:a", "176k", full_audio], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("audio concat error:\n" + r.stderr[-1200:])

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-i", full_audio,
           "-vf", "scale=1920:1080,format=yuv420p,fps=30",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "176k", "-shortest", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg error:\n" + r.stderr[-1500:])
    print(f"  built {out}  (~{total:.0f}s)")
    return out, total


def chapters(lesson):
    """YouTube chapter list from scene headings (first must be 00:00)."""
    return lesson  # placeholder; mega-cut tooling computes real timestamps


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", required=True, help="lesson id, e.g. lesson-01")
    ap.add_argument("--lessons", default=os.path.join(ROOT, "content", "course", "lessons.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.lessons))
    lesson = next((l for l in data["lessons"] if l["id"] == a.lesson), None)
    if not lesson:
        sys.exit(f"lesson {a.lesson} not found in {a.lessons}")
    out = a.out or os.path.join(ROOT, "content", "course", f"{a.lesson}.mp4")
    build(lesson, out, a.voice, a.dry_run)
