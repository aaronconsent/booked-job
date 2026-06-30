#!/usr/bin/env python3
"""
ANIMATED-INFOGRAPHIC renderer for Marketing 101 lessons — the "tells a story"
look (vs the slide/PowerPoint look of make_lesson.py). True frame-by-frame 30fps
motion graphics with eased tweens: the funnel fills, nodes spread, a phone search
assembles, checklists tick, an arrow draws into the next-lesson card.

Reuses the SAME scripts (content/course/lessons.json) and the SAME cached
ElevenLabs "Torque Marshal" VO as make_lesson.py — so re-rendering costs zero
TTS credits. Each scene maps to a motion WIDGET via its `motion` field (or a
kind-based default); unknown widgets fall back to sliding chips.

Usage:
  python3 scripts/make_lesson_motion.py --lesson lesson-01 [--out ...] [--dry-run] [--fps 30]
"""
import argparse, hashlib, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_lesson as ML            # reuse base_canvas/chrome/wrap/F/colors/segments/silence
import elevenlabs_tts as TTS

W, H = ML.W, ML.H
HI, HI2, ASPHALT, CARD = ML.HI, ML.HI2, ML.ASPHALT, ML.CARD
WHITE, YELLOW, MUTED, GREEN, LINE = ML.WHITE, ML.YELLOW, ML.MUTED, ML.GREEN, ML.LINE
CAP = (208, 212, 220)
F = ML.F
INTRO, GAP, TAIL = ML.INTRO, ML.GAP, ML.TAIL


# ---------- easing ----------
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease(t):                         # easeOutCubic
    return 1 - (1 - clamp01(t)) ** 3


def ease_io(t):                      # easeInOut
    t = clamp01(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def item_p(p, i, n, win=0.42):
    start = (i / max(1, n)) * (1 - win)
    return ease((p - start) / win)


# ---------- shared layout ----------
def draw_heading(d, scene, p):
    head = scene.get("heading", "")
    kind = scene["kind"]
    LX = 150
    label = ML._seg_label(kind)
    if label:
        ML.eyebrow(d, LX, 150, label, ML._seg_color(kind))
    if not head:
        return 300
    a = ease(clamp01(p * 4)); rise = int((1 - a) * 22)
    hf = F("Arial Black.ttf", 60); hy = 208
    for ln in ML.wrap(d, head, hf, W - 300):
        d.text((LX, hy - rise), ln, font=hf, fill=YELLOW if kind == "action" else WHITE)
        hy += 70
    return hy + 18


def caption_slim(d, segs, t):
    cur = ""
    for s in segs:
        if s["start"] <= t:
            cur = s["text"]
    if not cur:
        return
    cf = F("Arial Bold.ttf", 33)
    lines = ML.wrap(d, cur, cf, W - 460)
    y = H - 116 - len(lines) * 40
    for ln in lines:
        d.text((W / 2, y), ln, font=cf, fill=CAP, anchor="ma"); y += 40


def rrect(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)


# ---------- motion widgets: fn(d, p, scene, cy0) ----------
def w_chips(d, p, scene, y0):
    items = scene.get("bullets", []) or ["—"]
    cf = F("Arial Black.ttf", 46)
    for i, b in enumerate(items):
        ip = item_p(p, i, len(items))
        if ip <= 0:
            continue
        x = int(150 - (1 - ip) * 520)
        y = y0 + i * 116
        tw = d.textlength(b, font=cf)
        rrect(d, [x, y, x + tw + 96, y + 84], 14, fill=CARD, outline=HI, width=3)
        d.ellipse([x + 26, y + 32, x + 46, y + 52], fill=HI)
        d.text((x + 64, y + 14), b, font=cf, fill=WHITE)


def w_pillars(d, p, scene, y0):
    labels = ["FINDABLE", "TRUSTABLE"]
    base_y, top_y = 840, 430
    full = base_y - top_y
    bw, gap = 300, 120
    total = len(labels) * bw + (len(labels) - 1) * gap
    x0 = (W - total) // 2
    for i, lab in enumerate(labels):
        ip = ease(clamp01((p - i * 0.18) / 0.5))
        h = int(full * ip)
        x = x0 + i * (bw + gap)
        rrect(d, [x, base_y - h, x + bw, base_y], 16,
              fill=HI if i == 0 else HI2)
        d.text((x + bw / 2, base_y - h - 52), lab, font=F("Arial Black.ttf", 40),
               fill=WHITE, anchor="ma")
    # "= they call you" appears after both rise
    if p > 0.75:
        a = ease((p - 0.75) / 0.25)
        d.text((W / 2, base_y + 28), "= THEY CALL YOU",
               font=F("Arial Black.ttf", 38), fill=GREEN, anchor="ma")


def w_funnel(d, p, scene, y0):
    stages = ["STRANGER", "VISITOR", "LEAD", "BOOKED JOB"]
    counts = ["1,000", "300", "80", "12"]
    widths = [880, 660, 440, 240]
    cx = 720
    band_h, gap = 92, 34
    top = 330
    for i, st in enumerate(stages):
        y = top + i * (band_h + gap)
        w = widths[i]
        box = [cx - w // 2, y, cx + w // 2, y + band_h]
        rrect(d, box, 14, outline=LINE, width=3)
        rev = ease(clamp01((p - i * 0.22) / 0.26))
        if rev > 0:
            fw = int(w * rev)
            rrect(d, [cx - w // 2, y, cx - w // 2 + fw, y + band_h], 14,
                  fill=HI if i < 3 else GREEN)
        d.text((cx, y + band_h / 2 - 22), st, font=F("Arial Black.ttf", 38),
               fill=WHITE, anchor="ma")
        # count label to the right
        if rev > 0.4:
            d.text((cx + w // 2 + 30, y + band_h / 2 - 20), counts[i],
                   font=F("Arial Bold.ttf", 34), fill=HI2)
    # flowing dots top->bottom
    span = (band_h + gap) * 3 + band_h
    for k in range(7):
        ph = (p * 2.2 + k / 7.0) % 1.0
        dy = top + ph * span
        nw = widths[0] + (widths[3] - widths[0]) * (ph)
        d.ellipse([cx - 7, dy - 7, cx + 7, dy + 7], fill=YELLOW)


def w_network(d, p, scene, y0):
    cx, cy = 560, 600
    # central YOU node
    a = ease(clamp01(p * 3))
    R = int(76 * a)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=HI)
    if a > 0.5:
        d.text((cx, cy - 22), "YOU", font=F("Arial Black.ttf", 40), fill=ASPHALT, anchor="ma")
    n = 7
    for i in range(n):
        ang = -math.pi / 2 + i * (2 * math.pi / n)
        ip = item_p(p, i, n, 0.5)
        if ip <= 0:
            continue
        dist = 230 * ease(ip)
        nx, ny = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
        d.line([cx, cy, nx, ny], fill=LINE, width=4)
        r = int(34 * ip)
        d.ellipse([nx - r, ny - r, nx + r, ny + r], fill=CARD, outline=HI2, width=3)
    if p > 0.6:
        d.text((cx + 320, cy - 20), "referrals\nspread", font=F("Arial Black.ttf", 40),
               fill=WHITE)


def w_phone_search(d, p, scene, y0):
    px, py, pw, ph = 470, 300, 440, 560
    rrect(d, [px, py, px + pw, py + ph], 36, fill=CARD, outline=LINE, width=4)
    rrect(d, [px, py, px + pw, py + 64], 36, fill=ASPHALT)
    d.text((px + pw / 2, py + 20), "7:00 AM", font=F("Arial Bold.ttf", 30), fill=GREEN, anchor="ma")
    # search bar typing
    sb = [px + 28, py + 96, px + pw - 28, py + 158]
    rrect(d, sb, 12, fill=ASPHALT, outline=HI, width=2)
    full = "plumber near me"
    chars = int(len(full) * ease(clamp01(p / 0.4)))
    d.text((sb[0] + 18, sb[1] + 14), full[:chars] + ("|" if chars < len(full) else ""),
           font=F("Arial Bold.ttf", 32), fill=WHITE)
    # results slide in
    rows = ["YOUR SHOP  ★★★★★", "Competitor A  ★★★★", "Competitor B  ★★★"]
    for i, r in enumerate(rows):
        ip = item_p(p, i, len(rows) + 2, 0.4)
        if ip <= 0:
            continue
        ry = py + 190 + i * 110
        rx = int(px + 28 - (1 - ip) * 200)
        col = HI if i == 0 else CARD
        rrect(d, [rx, ry, px + pw - 28, ry + 90], 12, fill=col, outline=LINE, width=2)
        d.text((rx + 20, ry + 24), r, font=F("Arial Black.ttf", 30),
               fill=ASPHALT if i == 0 else WHITE)
    # caption on right
    if p > 0.55:
        d.text((px + pw + 90, py + 200), "You win it…\nor you're\ninvisible.",
               font=F("Arial Black.ttf", 48), fill=WHITE)


def w_trade_cards(d, p, scene, y0):
    cards = [("HVAC", "no-cool call", "☀"), ("ROOFING", "after the hail", "⛆"),
             ("TREE", "limb on the roof", "🌲")]
    bullets = scene.get("bullets", [])
    cw, gap = 460, 60
    total = len(cards) * cw + (len(cards) - 1) * gap
    x0 = (W - total) // 2
    y = 430
    for i, (t, sub, _) in enumerate(cards):
        ip = item_p(p, i, len(cards), 0.5)
        if ip <= 0:
            continue
        yy = int(y + (1 - ease(ip)) * 80)
        x = x0 + i * (cw + gap)
        rrect(d, [x, yy, x + cw, yy + 300], 20, fill=CARD, outline=HI, width=3)
        d.text((x + cw / 2, yy + 50), t, font=F("Arial Black.ttf", 56), fill=HI2, anchor="ma")
        line = bullets[i] if i < len(bullets) else sub
        wy = yy + 140
        for ln in ML.wrap(d, line, F("Arial Bold.ttf", 34), cw - 60):
            d.text((x + cw / 2, wy), ln, font=F("Arial Bold.ttf", 34), fill=WHITE, anchor="ma"); wy += 44


def w_checklist(d, p, scene, y0):
    items = scene.get("bullets", []) or ["—"]
    cf = F("Arial Black.ttf", 46)
    for i, b in enumerate(items):
        ip = item_p(p, i, len(items), 0.45)
        y = y0 + i * 116
        box = [150, y, 210, y + 60]
        rrect(d, box, 10, outline=HI, width=4,
              fill=GREEN if ip > 0.6 else None)
        if ip > 0.6:                     # draw a check
            d.line([162, y + 32, 178, y + 48], fill=ASPHALT, width=7)
            d.line([178, y + 48, 202, y + 14], fill=ASPHALT, width=7)
        col = WHITE if ip > 0.6 else MUTED
        d.text((240, y + 6), b, font=cf, fill=col)


def w_bridge(d, p, scene, y0):
    # arrow draws across into a NEXT card that pops
    ay = 560
    x0, x1 = 200, 1180
    cur = x0 + (x1 - x0) * ease(clamp01(p / 0.6))
    d.line([x0, ay, cur, ay], fill=HI, width=10)
    if cur > x1 - 4:
        d.polygon([(x1, ay - 22), (x1 + 40, ay), (x1, ay + 22)], fill=HI)
    if p > 0.55:
        a = ease((p - 0.55) / 0.45)
        cw, ch = int(560 * a), int(220 * a)
        cx, cyy = 1480, ay
        rrect(d, [cx - cw // 2, cyy - ch // 2, cx + cw // 2, cyy + ch // 2], 20,
              fill=CARD, outline=GREEN, width=4)
        if a > 0.6:
            d.text((cx, cyy - 56), "NEXT", font=F("Arial Bold.ttf", 30), fill=GREEN, anchor="ma")
            nxt = scene.get("heading", "Lesson 2").split("—")[-1].strip()
            for j, ln in enumerate(ML.wrap(d, nxt, F("Arial Black.ttf", 40), cw - 40)):
                d.text((cx, cyy - 10 + j * 46), ln, font=F("Arial Black.ttf", 40),
                       fill=WHITE, anchor="ma")


def w_money_drain(d, p, scene, y0):
    # downward trend line + coins falling out of a wallet
    ax0, ax1, ay0, ay1 = 220, 1080, 420, 800
    d.line([ax0, ay0, ax1, ay1], fill=HI, width=10)
    d.polygon([(ax1, ay1 - 22), (ax1 + 40, ay1 + 6), (ax1 - 6, ay1 + 30)], fill=HI)
    for k in range(8):
        ph = (p * 1.6 + k / 8.0) % 1.0
        x = 1150 + (k % 3) * 70
        yy = 380 + ph * 460
        r = 26
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=YELLOW, outline=(180, 150, 30), width=3)
        d.text((x, yy - 18), "$", font=F("Arial Black.ttf", 34), fill=(120, 90, 10), anchor="ma")
    if p > 0.3:
        d.text((300, 470), "money you\ncan't see", font=F("Arial Black.ttf", 56), fill=WHITE)


WIDGETS = {"chips": w_chips, "pillars": w_pillars, "funnel": w_funnel,
           "network": w_network, "phone_search": w_phone_search,
           "trade_cards": w_trade_cards, "checklist": w_checklist,
           "bridge": w_bridge, "money_drain": w_money_drain}
DEFAULT = {"hook": "money_drain", "learn": "chips", "teach": "pillars",
           "example": "phone_search", "cutaway": "trade_cards",
           "action": "checklist", "bridge": "bridge"}


def widget_for(scene):
    name = scene.get("motion") or DEFAULT.get(scene["kind"], "chips")
    return WIDGETS.get(name, w_chips)


# ---------- title card (animated) ----------
def title_frame(bg, lesson, p):
    img = bg.copy(); d = ML.chrome(img, lesson, 0.0)
    a = ease(clamp01(p / 0.5))
    d.text((W / 2, 300), f"LESSON {lesson['number']}", font=F("Arial Bold.ttf", 54),
           fill=HI2, anchor="ma")
    rise = int((1 - a) * 30)
    tf = F("Arial Black.ttf", 110); y = 380
    for ln in ML.wrap(d, lesson["title"].upper(), tf, W - 360):
        d.text((W / 2, y - rise), ln, font=tf, fill=WHITE, anchor="ma"); y += 122
    if p > 0.5:
        d.text((W / 2, y + 20), "MARKETING 101 · FOR SERVICE PROS",
               font=F("Arial Bold.ttf", 32), fill=MUTED, anchor="ma")
    return img


def build(lesson, out, voice=None, dry=False, fps=30):
    scenes = lesson["scenes"]
    words_est = sum(len(s["vo"].split()) for s in scenes)
    print(f"Lesson {lesson['number']} (MOTION): {lesson['title']} — "
          f"{len(scenes)} scenes · ~{words_est/150:.1f} min VO")
    if dry:
        for i, s in enumerate(scenes):
            print(f"   [{i}] {s['kind']:8} motion={s.get('motion') or DEFAULT.get(s['kind'],'chips'):12} "
                  f"{s.get('heading','')[:48]}")
        return None, 0

    voice = voice or TTS.DEFAULT_VOICE
    tmp = tempfile.mkdtemp(prefix="lessonmo_")
    cache = os.path.join(ROOT, "content", "course", ".tts_cache")
    os.makedirs(cache, exist_ok=True)
    parts = []
    for i, s in enumerate(scenes):
        key = hashlib.md5((voice + "\n" + s["vo"]).encode()).hexdigest()
        cmp3, cmeta = os.path.join(cache, key + ".mp3"), os.path.join(cache, key + ".json")
        if os.path.exists(cmp3) and os.path.exists(cmeta):
            words = json.load(open(cmeta))["words"]; hit = "cached"
        else:
            _, _, words = TTS.generate_speech(s["vo"], voice, cmp3)
            json.dump({"words": words}, open(cmeta, "w")); hit = "TTS"
        real = ML.ffprobe_dur(cmp3) or 1.0
        parts.append({"mp3": cmp3, "dur": real, "words": words, "scene": s})
        print(f"  ✓ scene {i} ({s['kind']}) {real:.1f}s [{hit}]")

    total = INTRO + TAIL + GAP * len(scenes) + sum(p["dur"] for p in parts)
    bg = ML.base_canvas()
    frames_dir = os.path.join(tmp, "f"); os.makedirs(frames_dir)
    idx = 0
    def save(img):
        nonlocal idx
        img.save(os.path.join(frames_dir, f"{idx:06d}.png")); idx += 1

    # intro (animated title)
    for f in range(int(INTRO * fps)):
        save(title_frame(bg, lesson, f / max(1, INTRO * fps)))

    offset = INTRO
    for pi, part in enumerate(parts):
        s, dur, words = part["scene"], part["dur"], part["words"]
        segs = ML.segments(words)
        widget = widget_for(s)
        nf = max(1, int(dur * fps))
        for f in range(nf):
            t = f / fps
            p = clamp01(t / dur)
            img = bg.copy(); d = ML.chrome(img, lesson, (offset + t) / total)
            cy0 = draw_heading(d, s, p)
            widget(d, p, s, max(360, cy0))
            # citation chip for data/cutaway scenes
            if s.get("cite"):
                cf = F("Arial Bold.ttf", 26); cw = d.textlength("SOURCE: " + s["cite"], font=cf)
                rrect(d, [W - 150 - cw - 40, H - 150, W - 150, H - 104], 9, fill=ASPHALT, outline=LINE)
                d.text((W - 150 - cw - 20, H - 144), "SOURCE: " + s["cite"], font=cf, fill=MUTED)
            caption_slim(d, segs, t)
            save(img)
        # gap: hold last frame
        last = Image.open(os.path.join(frames_dir, f"{idx-1:06d}.png"))
        for _ in range(int(GAP * fps)):
            save(last.copy())
        offset += dur + GAP
        print(f"  ✦ rendered scene {pi} ({widget.__name__})  frames→{idx}")
    # tail
    last = Image.open(os.path.join(frames_dir, f"{idx-1:06d}.png"))
    for _ in range(int(TAIL * fps)):
        save(last.copy())

    # audio: INTRO sil + (scene + GAP sil)* + TAIL sil
    si, sg, st = os.path.join(tmp, "si.mp3"), os.path.join(tmp, "sg.mp3"), os.path.join(tmp, "st.mp3")
    ML.silence(si, INTRO); ML.silence(sg, GAP); ML.silence(st, TAIL)
    alist = [si]
    for part in parts:
        alist += [part["mp3"], sg]
    alist += [st]
    aconcat = os.path.join(tmp, "a.txt")
    open(aconcat, "w").write("\n".join(f"file '{a}'" for a in alist) + "\n")
    audio = os.path.join(tmp, "a.m4a")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", aconcat,
                        "-c:a", "aac", "-b:a", "176k", audio], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("audio error:\n" + r.stderr[-1000:])

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "%06d.png"),
           "-i", audio, "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium",
           "-crf", "20", "-c:a", "aac", "-b:a", "176k", "-shortest", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg error:\n" + r.stderr[-1500:])
    print(f"  built {out}  ({idx} frames, ~{idx/fps:.0f}s)")
    return out, total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", required=True)
    ap.add_argument("--lessons", default=os.path.join(ROOT, "content", "course", "lessons.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.lessons))
    lesson = next((l for l in data["lessons"] if l["id"] == a.lesson), None)
    if not lesson:
        sys.exit(f"lesson {a.lesson} not found")
    out = a.out or os.path.join(ROOT, "content", "course", f"{a.lesson}-motion.mp4")
    build(lesson, out, a.voice, a.dry_run, a.fps)
