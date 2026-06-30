#!/usr/bin/env python3
"""
Rebuild a Marketing 101 lesson the *faceless-youtube-video skill* way — the
narrated-stills pipeline (per-beat oversampled Ken Burns → eased card overlay →
xfade crossfades → burned SRT captions → ducked/normalized 10-bit master).

This ORCHESTRATES the skill's bash scripts (~/.claude/skills/faceless-youtube-video/
scripts/*.sh); it does not reinvent them. Each lesson scene = one "beat". Reuses
the cached gpt-image-1 hero stills (openai_image.py) and the cached ElevenLabs
"Torque Marshal" narration. Branded beats get a procedurally-rendered still;
photo/meme beats use the AI image. Cards (chrome + heading/bullets/meme text /
funnel diagram) are pre-rendered transparent PNGs and faded in per the skill.

  python3 scripts/render_lesson_skill.py --lesson lesson-01 \
      [--lessons content/course/lessons_nsfw.json] [--out ...] [--res 1920x1080] [--music bed.mp3]

Note: gpt-image-1 caps at 1536px wide, so we master at 1080p (crisp) rather than
upscaling to a soft 4K — every other skill quality lever (oversampled KB, xfade,
captions, deband, 10-bit, aq-mode=3, -14 LUFS) is applied.
"""
import argparse, hashlib, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_lesson as ML
import make_lesson_motion as MO
import elevenlabs_tts as TTS
import openai_image

SKILL = os.path.expanduser("~/.claude/skills/faceless-youtube-video/scripts")
W, H = ML.W, ML.H
HI, HI2, ASPHALT, CARD = ML.HI, ML.HI2, ML.ASPHALT, ML.CARD
WHITE, YELLOW, MUTED, GREEN, LINE = ML.WHITE, ML.YELLOW, ML.MUTED, ML.GREEN, ML.LINE
F = ML.F
FD = "/System/Library/Fonts/Supplemental"
BREATH, XF, LEAD = 0.6, 0.6, 0.4          # skill: breathing room, crossfade, card-in delay
DIRS = ["in", "left", "out", "right"]


def impact(s):
    try:
        return ML.ImageFont.truetype(os.path.join(FD, "Impact.ttf"), s)
    except Exception:
        return F("Arial Black.ttf", s)


def sh(script, *args):
    cmd = ["bash", os.path.join(SKILL, script)] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[{script}] failed:\n{r.stderr[-1600:]}")
    return r


def overlay_card(base, card, out, at=0.4, fade=0.4):
    """Corrected replacement for the skill's overlay_card.sh — that script feeds the
    card PNG as a single t=0 frame, so its fade (st=0.4) renders the card at alpha 0
    and it never appears. Looping the still gives the eased fade real frames."""
    fc = (f"[1]format=rgba,fade=t=in:st={at}:d={fade}:alpha=1[c];"
          f"[0][c]overlay=0:0:shortest=1[v]")
    r = subprocess.run(["ffmpeg", "-y", "-i", base, "-loop", "1", "-i", card,
                        "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                        "-pix_fmt", "yuv420p", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("overlay_card failed:\n" + r.stderr[-1400:])


# ---------------- transparent card layers ----------------
def chrome_layer(d, minimal=False):
    for x in range(-50, W + 50, 96):
        d.polygon([(x, 0), (x + 48, 0), (x + 48 - 34, 26), (x - 34, 26)], fill=YELLOW + (255,))
    if not minimal:
        cf = F("Arial Bold.ttf", 26); chip = "MARKETING 101 · UNCUT"
        tw = d.textlength(chip, font=cf)
        d.rounded_rectangle([54, 52, 54 + tw + 40, 96], radius=10,
                            fill=ASPHALT + (235,), outline=LINE + (255,))
        d.text((74, 60), chip, font=cf, fill=HI2 + (255,))
    bx, by = W - 340, H - 78
    d.rounded_rectangle([bx, by, bx + 46, by + 46], radius=9, fill=HI + (255,))
    d.text((bx + 9, by + 2), "B", font=F("Arial Black.ttf", 36), fill=ASPHALT + (255,))
    bf = F("Arial Black.ttf", 32)
    d.text((bx + 60, by + 6), "BOOKED", font=bf, fill=WHITE + (255,))
    bw = d.textlength("BOOKED", font=bf)
    d.text((bx + 60 + bw + 7, by + 6), "JOB", font=bf, fill=HI + (255,))


def _stroke(d, xy, text, font, fill, anchor=None, sw=4):
    d.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=sw,
           stroke_fill=(0, 0, 0, 255))


def card_heading(scene, photo):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    chrome_layer(d)
    LX = 150
    label = ML._seg_label(scene["kind"])
    if label:
        _stroke(d, (LX, 150), label.upper(), F("Arial Bold.ttf", 30),
                ML._seg_color(scene["kind"]) + (255,), sw=3)
    hf = F("Arial Black.ttf", 64); hy = 206
    for ln in ML.wrap(d, scene.get("heading", ""), hf, W - 300):
        _stroke(d, (LX, hy), ln, hf,
                (YELLOW if scene["kind"] == "action" else WHITE) + (255,), sw=4); hy += 74
    by = hy + 18
    for b in scene.get("bullets", []):
        d.ellipse([LX, by + 20, LX + 18, by + 38], fill=HI + (255,))
        _stroke(d, (LX + 40, by), b, F("Arial Black.ttf", 48), WHITE + (255,), sw=3); by += 74
    if scene.get("cite"):
        cf = F("Arial Bold.ttf", 26); t = "SOURCE: " + scene["cite"]
        cw = d.textlength(t, font=cf)
        d.rounded_rectangle([W - 150 - cw - 40, H - 150, W - 150, H - 104], radius=9,
                            fill=ASPHALT + (235,), outline=LINE + (255,))
        d.text((W - 150 - cw - 20, H - 144), t, font=cf, fill=MUTED + (255,))
    return img


def card_meme(scene):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    chrome_layer(d, minimal=True)
    m = scene["meme"]
    if m.get("top"):
        ft = impact(78); y = 70
        for ln in ML.wrap(d, m["top"].upper(), ft, W - 200):
            _stroke(d, (W / 2, y), ln, ft, WHITE + (255,), anchor="ma", sw=6); y += 86
    if m.get("bottom"):
        fb = impact(84); lines = ML.wrap(d, m["bottom"].upper(), fb, W - 180)
        y = H - 150 - len(lines) * 94
        for ln in lines:
            _stroke(d, (W / 2, y), ln, fb, WHITE + (255,), anchor="ma", sw=6); y += 94
    return img


def card_funnel(scene):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    chrome_layer(d)
    _stroke(d, (150, 150), "THE TEACHING", F("Arial Bold.ttf", 30), HI + (255,), sw=3)
    hf = F("Arial Black.ttf", 60)
    _stroke(d, (150, 206), scene.get("heading", ""), hf, WHITE + (255,), sw=4)
    stages = ["STRANGER", "VISITOR", "LEAD", "PAID"]
    counts = ["1,000", "300", "80", "12"]
    widths = [880, 660, 440, 240]; cx = 720; band_h, gap, top = 92, 30, 360
    for i, st in enumerate(stages):
        y = top + i * (band_h + gap); w = widths[i]
        d.rounded_rectangle([cx - w // 2, y, cx + w // 2, y + band_h], radius=14,
                            fill=(HI if i < 3 else GREEN) + (255,))
        d.text((cx, y + band_h / 2 - 22), st, font=F("Arial Black.ttf", 38),
               fill=ASPHALT + (255,), anchor="ma")
        _stroke(d, (cx + w // 2 + 28, y + band_h / 2 - 20), counts[i],
                F("Arial Bold.ttf", 34), HI2 + (255,), sw=3)
    return img


def make_card(scene, photo):
    if scene.get("meme"):
        return card_meme(scene)
    if scene.get("motion") == "funnel":
        return card_funnel(scene)
    return card_heading(scene, photo)


# ---------------- captions (PIL strips composited via ffmpeg overlay) ----------------
# This ffmpeg build ships WITHOUT libass, so the subtitles/ass filters don't exist.
# Per the skill's own guidance ("render the layer, hand PNGs to ffmpeg to composite"),
# we render each caption line as a transparent PNG and overlay it in its time window.
def caption_cues(parts, starts):
    cues = []
    for p, st in zip(parts, starts):
        words = [w for w in p["words"] if w.get("start") is not None]
        line, lstart = [], None
        def flush(end):
            nonlocal line, lstart
            if line:
                cues.append((st + LEAD + lstart, st + LEAD + end,
                             " ".join(w["word"] for w in line).replace("\n", " ")))
                line.clear()
        for w in words:
            if lstart is None:
                lstart = w["start"]
            line.append(w)
            if len(line) >= 7 or (w["end"] - lstart) >= 3.2 or w["word"][-1:] in ".!?":
                flush(w["end"]); lstart = None
        if line:
            flush(words[-1]["end"])
    return cues


def render_caption_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    cf = F("Arial Black.ttf", 52)
    lines = ML.wrap(d, text, cf, W - 360)
    y = H - 80 - len(lines) * 62
    for ln in lines:
        d.text((W / 2, y), ln, font=cf, fill=(255, 255, 255, 255), anchor="ma",
               stroke_width=5, stroke_fill=(0, 0, 0, 255)); y += 62
    img.save(path)


def burn_captions(edit, cues, out, tmp):
    inputs = ["-i", edit]
    for i, (s, e, txt) in enumerate(cues):
        png = os.path.join(tmp, f"cap{i:03d}.png"); render_caption_png(txt, png)
        inputs += ["-i", png]
    chain, prev = [], "[0:v]"
    for i, (s, e, txt) in enumerate(cues):
        lbl = "[vout]" if i == len(cues) - 1 else f"[v{i}]"
        chain.append(f"{prev}[{i+1}:v]overlay=enable='between(t,{s:.2f},{e:.2f})'{lbl}")
        prev = lbl
    fc = ";".join(chain)
    r = subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                        "-pix_fmt", "yuv420p", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("caption overlay failed:\n" + r.stderr[-1600:])


# ---------------- build ----------------
def build(lesson, out, res, music=None, img_quality="medium", resume_edit=None, resume_kb=None):
    w, h = (int(x) for x in res.split("x"))
    global W, H
    if (w, h) != (W, H):
        W, H = w, h
    scenes = lesson["scenes"]
    print(f"Lesson {lesson['number']} via faceless-youtube-video skill — {len(scenes)} beats @ {W}x{H}")
    voice = TTS.DEFAULT_VOICE
    cache = os.path.join(ROOT, "content", "course", ".tts_cache"); os.makedirs(cache, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="skill_")

    # 1) narration (cached) + 2) stills + 3) cards + 4/5) ken burns + card overlay per beat
    parts, carded = [], []
    for i, s in enumerate(scenes):
        key = hashlib.md5((voice + "\n" + s["vo"]).encode()).hexdigest()
        mp3, meta = os.path.join(cache, key + ".mp3"), os.path.join(cache, key + ".json")
        if os.path.exists(mp3) and os.path.exists(meta):
            words = json.load(open(meta))["words"]; hit = "cached"
        else:
            _, _, words = TTS.generate_speech(s["vo"], voice, mp3)
            json.dump({"words": words}, open(meta, "w")); hit = "TTS"
        dur = ML.ffprobe_dur(mp3) or 1.0
        # kenburns.sh uses bash integer math (DUR*FPS) -> beat length must be a whole
        # number of seconds. Derive all sync offsets from this same integer.
        parts.append({"mp3": mp3, "dur": dur, "words": words, "beat": math.ceil(dur + BREATH)})

        if resume_edit:
            continue   # narration/captions only need parts[]; reuse the assembled edit
        prompt = s.get("image") or (s.get("meme") or {}).get("img")
        card = os.path.join(tmp, f"card{i}.png"); make_card(s, bool(prompt)).save(card)
        beat_dur = parts[-1]["beat"]
        kb = os.path.join(tmp, f"kb{i}.mp4")
        if resume_kb:
            kb = os.path.join(resume_kb, f"kb{i}.mp4"); how = "reuse-kb"
        else:
            still = os.path.join(tmp, f"still{i}.png")
            if prompt:
                p2, _ = openai_image.generate(prompt, quality=img_quality)
                Image.open(p2).convert("RGB").save(still); how = "ai"
            else:
                ML.base_canvas().save(still); how = "branded"
            sh("kenburns.sh", still, kb, beat_dur, 30, W, H, DIRS[i % 4])
        cd = os.path.join(tmp, f"cd{i}.mp4")
        overlay_card(kb, card, cd, LEAD, 0.4)        # corrected (skill's was broken)
        carded.append(cd)
        print(f"  ✓ beat {i:>2} ({s['kind']:8}) {dur:4.1f}s  still={how:8} kb={DIRS[i%4]:5} [{hit}]")

    # compute global beat starts (matches assemble.sh xfade offsets)
    starts = [0.0]
    for i in range(1, len(parts)):
        starts.append(round(starts[-1] + parts[i - 1]["beat"] - XF, 4))

    # 6) assemble crossfades (or reuse a prior assembled edit)
    edit = resume_edit or os.path.join(tmp, "edit.mp4")
    if not resume_edit:
        sh("assemble.sh", edit, XF, *carded)

    # narration track: place each VO at start+LEAD (adelay), amix without renormalizing
    inputs, filt, labels = [], [], []
    for i, p in enumerate(parts):
        inputs += ["-i", p["mp3"]]
        delay = int((starts[i] + LEAD) * 1000)
        filt.append(f"[{i}:a]adelay={delay}|{delay}[a{i}]"); labels.append(f"[a{i}]")
    narr = os.path.join(tmp, "narration.wav")
    fc = ";".join(filt) + ";" + "".join(labels) + f"amix=inputs={len(parts)}:normalize=0:duration=longest[a]"
    r = subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[a]", narr],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("narration mix failed:\n" + r.stderr[-1400:])

    # 7) burn captions — PIL strips composited via ffmpeg overlay (no libass in this build)
    cues = caption_cues(parts, starts)
    cc = os.path.join(tmp, "edit_cc.mp4")
    print(f"  burning {len(cues)} caption cues via overlay…")
    burn_captions(edit, cues, cc, tmp)

    # 8) finalize: normalize voice (+ ducked music if given), 10-bit master
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if music and os.path.exists(music):
        sh("finalize.sh", cc, narr, music, out)
    else:
        sh("finalize.sh", cc, narr, out)
    total = ML.ffprobe_dur(out)
    print(f"  built {out}  (~{total:.0f}s, 10-bit -14LUFS master{' + music' if music else ''})")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", required=True)
    ap.add_argument("--lessons", default=os.path.join(ROOT, "content", "course", "lessons_nsfw.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--music", default=None)
    ap.add_argument("--img-quality", default="medium")
    ap.add_argument("--resume-edit", default=None, help="reuse a prior assembled edit.mp4 (skip beat render)")
    ap.add_argument("--resume-kb", default=None, help="reuse prior kb*.mp4 Ken Burns clips (skip kenburns)")
    a = ap.parse_args()
    data = json.load(open(a.lessons))
    lesson = next((l for l in data["lessons"] if l["id"] == a.lesson), None)
    if not lesson:
        sys.exit(f"lesson {a.lesson} not found")
    out = a.out or os.path.join(ROOT, "content", "course", f"{a.lesson}-nsfw-skill.mp4")
    build(lesson, out, a.res, a.music, a.img_quality, a.resume_edit, a.resume_kb)
