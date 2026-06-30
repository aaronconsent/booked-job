#!/usr/bin/env python3
"""
Doodle Explainer ENGINE (no Node; SVG assets -> PIL composite -> ffmpeg).
Implements the format-dna/build-foundations spec:
 - rigged Character (separable parts rotated about correct joint pivots)
 - 6 primitives: slideIn, popIn, drawOn(wipe), headBob, armRaise, buildSequence
 - VO word-timestamps (ElevenLabs) -> per-word text reveal + tick SFX + head-bob
   on the SAME frame  (sync is the product)
 - element-by-element assembly, hard cuts, SFX kit, -14 LUFS master.

Drives off content/course/doodle_script.json. Run: python3 scripts/doodle_engine.py
"""
import hashlib, json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doodle_assets as DA
import elevenlabs_tts as TTS
import make_lesson as ML

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "doodle", "assets")
SFXDIR = os.path.join(ROOT, "doodle", "sfx")
TC = os.path.join(ROOT, "content", "course", ".tts_cache")
W, H, FPS = int(os.environ.get("DOODLE_W", "1920")), int(os.environ.get("DOODLE_H", "1080")), 30
INK = (20, 20, 20)
PAPER = (250, 249, 245)            # warm off-white (v2 §1), not pure white
PAL_ACCENT = (255, 106, 0)         # marker emphasis (brand orange)


def ground_line(d, y=None):
    if y is None: y = H - 112
    """One hand-drawn baseline per scene (gravity)."""
    pts = [(80, y), (W // 2, y + 6), (W - 80, y - 2)]
    d.line([(80, y)] + [(x, y + int(5 * math.sin(x / 230))) for x in range(120, W - 80, 60)] + [(W - 80, y)],
           fill=(208, 206, 198), width=6)


def draw_env(img, kind="city"):
    """Faint location doodle ILLUSTRATION behind the foreground (no geometric shapes).
    Uses the real Recraft doodle bg props rendered light-gray + low opacity."""
    prop = {"city": "citybg", "street": "citybg", "yard": "suburbbg", "house": "suburbbg"}.get(kind)
    if not prop:
        return img
    im = raster(prop, 1500)
    a = im.split()[3].point(lambda v: int(v * 0.42))      # faint
    faint = Image.new("RGBA", im.size, (206, 204, 196, 0)); faint.putalpha(a)
    img.alpha_composite(faint, ((W - im.width) // 2, 944 - im.height))
    return img


def draw_wash(img, color="blue"):
    """Pale section-change wash behind ONE scene at a topic shift (art-direction §1)."""
    tint = {"blue": (210, 232, 244), "yellow": (252, 244, 214)}.get(color, (235, 235, 235))
    panel = Image.new("RGBA", (W, H), tint + (120,))
    return Image.alpha_composite(img, panel)


def apply_camera(frame, t, total, push=0.05, shake=0.0):
    """Subtle constant motion: slow push-in + idle 'boil' jitter (+ optional shake).
    Always crops INWARD so the off-white edges never show."""
    import random
    z = 1.0 + push * ease(min(1.0, t / max(0.01, total)))
    cw, chh = int(W / z), int(H / z)
    jx = int(2 * math.sin(t * 33)) + (random.randint(-1, 1))      # boil
    jy = int(2 * math.cos(t * 29)) + (random.randint(-1, 1))
    if shake:
        jx += random.randint(-int(shake), int(shake)); jy += random.randint(-int(shake), int(shake))
    cx = (W - cw) // 2 + jx; cy = (H - chh) // 2 + jy
    cx = max(0, min(W - cw, cx)); cy = max(0, min(H - chh, cy))
    return frame.crop((cx, cy, cx + cw, cy + chh)).resize((W, H), Image.BILINEAR)
FONT = os.path.join(ROOT, "doodle", "assets", "PermanentMarker.ttf")
NARRATOR = "IL22Ke355hck2I2lwmNi"   # Torque Marshal
_raster = {}


def ease(t): return 1 - (1 - max(0, min(1, t))) ** 3
def back(t):
    t = max(0, min(1, t)); c = 2.70158
    return 1 + (c + 1) * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def raster(name, w):
    """Load an asset at width w. Recraft PNG props (doodle/assets/<id>.png) take
    priority; otherwise rasterize the SVG (character rig parts) via rsvg."""
    k = (name, w)
    if k in _raster: return _raster[k]
    pngp = os.path.join(ASSETS, name + ".png")
    if os.path.exists(pngp):
        im = Image.open(pngp).convert("RGBA")
        if im.width != w:
            im = im.resize((w, max(1, int(im.height * w / im.width))), Image.LANCZOS)
    else:
        png = os.path.join(tempfile.gettempdir(), f"dr_{name}_{w}.png")
        subprocess.run(["rsvg-convert", "-w", str(w), "-o", png, os.path.join(ASSETS, name + ".svg")], check=True)
        im = Image.open(png).convert("RGBA")
    _raster[k] = im; return im


# ---------- character rig ----------
PARTS = ["legs", "armBack", "torso", "neck", "head", "armFront"]
def render_char(scale=1.0, head=0.0, armF=0.0, armB=0.0, sway=0.0, tag="", mood="neutral",
                hat="hardhat", tool=None):
    """Rigged character. Trade-swap via hat=<trade hat> + tool=<trade tool> slots."""
    cw = int(DA.CW * scale)
    canvas = Image.new("RGBA", (cw, int(DA.CH * scale)), (0, 0, 0, 0))
    headpiv = (DA.PIVOTS["head"][0] * scale, DA.PIVOTS["head"][1] * scale)
    for part in PARTS:
        name = (f"head_{mood}" if part == "head" else part) + tag
        im = raster(name, cw)
        piv = DA.PIVOTS.get(part)
        ang = {"head": head, "armFront": armF, "armBack": armB, "torso": sway}.get(part, 0.0)
        if ang and piv:
            im = im.rotate(ang, resample=Image.BICUBIC, center=(piv[0] * scale, piv[1] * scale))
        canvas.alpha_composite(im)
        if part == "head" and hat:                      # hat slot rides with the head bob
            him = raster(f"hat_{hat}", cw)
            if head:
                him = him.rotate(head, resample=Image.BICUBIC, center=headpiv)
            canvas.alpha_composite(him)
    if tool:                                            # tool slot (in the front hand)
        canvas.alpha_composite(raster(f"tool_{tool}", cw))
    return canvas


# ---------- SFX kit (SYNTHESIZED with ffmpeg — punchy, distinct, audible) ----------
# ElevenLabs text-to-SFX produced near-silent clips; synth is reliable + controllable.
SFX_SYNTH = {
    # key: (lavfi source, post filter) — each peak-normalized to -3 dBFS after
    "tick":  ("aevalsrc=0.6*sin(2*PI*1750*t)*exp(-60*t):d=0.05:s=48000", "highpass=f=900"),
    "pop":   ("aevalsrc=0.7*sin(2*PI*640*t)*exp(-20*t):d=0.18:s=48000", "aresample=48000"),
    "whoosh":("anoisesrc=d=0.42:c=pink:a=0.8:r=48000", "bandpass=f=1500:width_type=h:w=1800,volume=volume='sin(t/0.42*3.14159)':eval=frame"),
    "zip":   ("anoisesrc=d=0.24:c=pink:a=0.7:r=48000", "highpass=f=1700,volume=volume='1-exp(-t*14)':eval=frame"),
    "thunk": ("aevalsrc=0.8*sin(2*PI*132*t)*exp(-19*t):d=0.16:s=48000", "lowpass=f=400"),
    # diegetic (v2 §5) — the sound the object would actually make
    "rumble":("anoisesrc=d=0.8:c=brown:a=0.9:r=48000", "lowpass=f=220,volume=volume='sin(t/0.8*3.14159)':eval=frame"),
    "buzz":  ("aevalsrc='0.7*sin(2*PI*115*t)*(0.55+0.45*sin(2*PI*32*t))':d=0.4:s=48000", "aresample=48000"),
    "ping":  ("aevalsrc='0.7*sin(2*PI*1380*t)*exp(-7*t)':d=0.5:s=48000", "highpass=f=600"),
    "ding":  ("aevalsrc='0.5*sin(2*PI*1050*t)*exp(-6*t)+0.4*sin(2*PI*1560*t)*exp(-7*t)':d=0.6:s=48000", "aresample=48000"),
    "gush":  ("anoisesrc=d=1.6:c=pink:a=0.9:r=48000", "bandpass=f=900:width_type=h:w=1300,volume=volume='1-exp(-t*9)':eval=frame"),
}
# asset id -> diegetic sound (layered above UI SFX, under VO)
DIEGETIC = {"truck": "rumble", "phonemap": "ping", "coin": "ding", "dollarstack": "ding",
            "reviewstars": "pop", "megaphone": "pop", "housetruck": "rumble"}
def sfx_path(key):
    os.makedirs(SFXDIR, exist_ok=True)
    key = key if key in SFX_SYNTH else "pop"
    p = os.path.join(SFXDIR, key + ".wav")
    if not os.path.exists(p) or os.path.getsize(p) < 1500:
        src, post = SFX_SYNTH[key]
        raw = p + ".raw.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", src,
                        "-af", post + ",aformat=channel_layouts=stereo", raw], check=True)
        # peak-normalize to -3 dBFS
        det = subprocess.run(["ffmpeg", "-i", raw, "-af", "volumedetect", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        import re
        mx = re.search(r"max_volume:\s*(-?[\d.]+) dB", det)
        gain = (-3.0 - float(mx.group(1))) if mx else 0.0
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"volume={gain:.1f}dB", p], check=True)
        os.remove(raw)
    return p


# ---------- VO + word matching ----------
def vo_words(text):
    os.makedirs(TC, exist_ok=True)
    k = hashlib.md5((NARRATOR + "\n" + text).encode()).hexdigest()
    mp3, meta = os.path.join(TC, k + ".mp3"), os.path.join(TC, k + ".json")
    if os.path.exists(mp3) and os.path.exists(meta):
        words = json.load(open(meta))["words"]
    else:
        _, _, words = TTS.generate_speech(text, NARRATOR, mp3)
        json.dump({"words": words}, open(meta, "w"))
    return mp3, [w for w in words if w.get("start") is not None]


def match_phrase(phrase, words):
    """Time each on-screen phrase word to the VO word that says it (sequential match);
    fall back to even spacing across the VO if unmatched."""
    import re
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    out, wi = [], 0
    vo = [(norm(w["word"]), w["start"]) for w in words]
    total = words[-1]["end"] if words else 1.0
    for i, pw in enumerate(phrase.split()):
        n = norm(pw); t = None
        for j in range(wi, len(vo)):
            if n and (n in vo[j][0] or vo[j][0] in n):
                t = vo[j][1]; wi = j + 1; break
        if t is None:
            t = total * (i + 1) / (len(phrase.split()) + 1)
        out.append((pw, t))
    return out


# ---------- text ----------
def F(sz):
    return ImageFont.truetype(FONT, sz)
def draw_words(d, revealed, cy, emph=None):
    if not revealed: return
    txt = " ".join(revealed); fs = 84            # Permanent Marker is bold/wide
    f = F(fs)
    while d.textlength(txt, font=f) > W - 300 and fs > 44:
        fs -= 5; f = F(fs)
    tw = d.textlength(txt, font=f); x0 = W / 2 - tw / 2
    d.text((W / 2, cy), txt, font=f, fill=INK, anchor="mm")
    # marker underline on the emphasis word (once it's revealed)
    if emph and emph.upper() in [w.upper() for w in revealed]:
        words = txt.split(); pre = ""
        for w in words:
            if w.upper() == emph.upper(): break
            pre += w + " "
        ex0 = x0 + d.textlength(pre, font=f); ew = d.textlength(emph, font=f)
        uy = cy + fs * 0.42
        d.line([(ex0, uy), (ex0 + ew * 0.5, uy + 5), (ex0 + ew, uy - 2)], fill=PAL_ACCENT, width=8)


# ---------- transitions (art-direction §8) ----------
def blur_to_text(prev_png, next_png, text, outdir, idx, nfr):
    """Signature: blur the outgoing scene, float a marker-hand line over it, HOLD on it
    (stop-motion pause), then resolve sharp into the next scene."""
    from PIL import ImageFilter
    prev = Image.open(prev_png).convert("RGB"); nxt = Image.open(next_png).convert("RGB")
    pre = prev.filter(ImageFilter.GaussianBlur(18))
    for f in range(nfr):
        p = f / (nfr - 1) if nfr > 1 else 1.0
        if p < 0.26:                               # blur in + marker line draws on (stepped)
            q = p / 0.26
            base = prev.filter(ImageFilter.GaussianBlur(2 + q * 16)); ta = round(ease(q) * 4) / 4
        elif p < 0.62:                             # HOLD — the stop-motion pause
            base = pre; ta = 1.0
        else:                                      # resolve sharp into next
            q = (p - 0.62) / 0.38
            base = Image.blend(pre, nxt, ease(q)); ta = max(0, 1 - q * 1.5)
        base = base.convert("RGBA")
        if text and ta > 0:
            jx = int(2 * math.sin(f * 0.7))        # tiny stop-motion jitter on the line
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).text((W / 2 + jx, H / 2), text, font=F(96),
                                    fill=(20, 20, 20, int(255 * ta)), anchor="mm")
            base = Image.alpha_composite(base, ov)
        base.convert("RGB").save(os.path.join(outdir, f"{idx + f:05d}.png"))
    return nfr


def whip_pan(prev_png, next_png, outdir, idx, nfr):
    """Fast horizontal whip between scenes."""
    prev = Image.open(prev_png).convert("RGB"); nxt = Image.open(next_png).convert("RGB")
    for f in range(nfr):
        p = ease(f / (nfr - 1) if nfr > 1 else 1.0); ox = int(p * W)
        frame = Image.new("RGB", (W, H), PAPER)
        frame.paste(prev, (-ox, 0)); frame.paste(nxt, (W - ox, 0))
        frame.save(os.path.join(outdir, f"{idx + f:05d}.png"))
    return nfr


# ---------- calendar hero scene (v2 §4 — the brand) ----------
def _stamp_img():
    im = Image.new("RGBA", (520, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 510, 210], radius=20, outline=(208, 40, 30), width=12)
    d.text((260, 110), "BOOKED!", font=F(110), fill=(208, 40, 30), anchor="mm")
    return im.rotate(11, expand=True, resample=Image.BICUBIC)


def render_calendar(scene, tmp, sidx, beats_dir):
    mp3, words = vo_words(scene["vo"]); dur = ML.ffprobe_dur(mp3) or 4.0
    total = dur + 0.45
    cols, rows, cell = 6, 4, 150
    gw, gh = cols * cell, rows * cell
    gx, gy = W // 2 - gw // 2, H // 2 - gh // 2 + 40
    n = cols * rows
    fill_end = max(0.4, dur - 0.9)
    stamps = [0.35 + (fill_end - 0.35) * (i / max(1, n - 1)) for i in range(n)]   # one block at a time
    booked_t = dur - 0.4
    sfx = [(s, "thunk") for s in stamps] + [(booked_t, "thunk"), (booked_t, "ding")]
    beats = [{"t": round(s, 3), "type": "build", "target": "jobblock", "anim": "stamp", "sfx": "thunk"} for s in stamps]
    beats.append({"t": round(booked_t, 3), "type": "stamp", "target": "BOOKED", "sfx": "ding"})
    json.dump({"id": scene["id"], "vo": os.path.basename(mp3), "assets": ["calendar", "jobblock", "BOOKED"], "beats": beats},
              open(os.path.join(beats_dir, scene["id"] + ".beats.json"), "w"), indent=2)
    stamp = _stamp_img()
    fdir = os.path.join(tmp, f"s{sidx}"); os.makedirs(fdir); nf = int(total * FPS)
    for fi in range(nf):
        t = fi / FPS
        img = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(img)
        ground_line(d)
        d.text((W / 2, 120), "AND YOUR CALENDAR FILLS UP", font=F(82), fill=INK, anchor="mm")
        # calendar grid + header
        d.rounded_rectangle([gx - 14, gy - 92, gx + gw + 14, gy + gh + 14], radius=18, outline=INK, width=7, fill=(255, 255, 255))
        d.rounded_rectangle([gx - 14, gy - 92, gx + gw + 14, gy - 30], radius=18, fill=(63, 167, 214))
        for c in range(cols + 1):
            d.line([(gx + c * cell, gy), (gx + c * cell, gy + gh)], fill=INK, width=4)
        for r in range(rows + 1):
            d.line([(gx, gy + r * cell), (gx + gw, gy + r * cell)], fill=INK, width=4)
        for i, st in enumerate(stamps):
            if t < st: continue
            r, c = divmod(i, cols); bx, by = gx + c * cell + 16, gy + r * cell + 16
            pop = back(min(1.0, (t - st) / 0.18)); s = 1 + 0.25 * (1 - pop)   # impact
            m = int((cell - 32) * (s - 1) / 2)
            d.rounded_rectangle([bx - m, by - m, bx + cell - 32 + m, by + cell - 32 + m], radius=12,
                                fill=(255, 196, 60), outline=INK, width=4)
            d.line([bx + 22, by + 58, bx + 44, by + 82], fill=INK, width=7)
            d.line([bx + 44, by + 82, bx + 90, by + 30], fill=INK, width=7)
        shake = 0.0
        if t >= booked_t:                            # BOOKED stamp + flash + shake payoff
            bp = back(min(1.0, (t - booked_t) / 0.16)); ss = 1.6 - 0.6 * bp
            si = stamp.resize((int(stamp.width * ss), int(stamp.height * ss)))
            img.alpha_composite(si, (W // 2 - si.width // 2, H // 2 - si.height // 2 + 30))
            fa = max(0, 1 - (t - booked_t) / 0.18)
            if fa > 0:
                fl = Image.new("RGBA", (W, H), (255, 255, 255, int(150 * fa))); img = Image.alpha_composite(img, fl)
            shake = 7 if (t - booked_t) < 0.2 else 0
        cam = apply_camera(img.convert("RGB"), t, total, push=0.04, shake=shake)
        cam.save(os.path.join(fdir, f"{fi:04d}.png"))
    return fdir, nf, mp3, total, sfx


# ---------- heightened pipe-burst scene (the emotional peak; spend time) ----------
def render_burst(scene, tmp, sidx, beats_dir):
    mp3, words = vo_words(scene["vo"]); dur = ML.ffprobe_dur(mp3) or 4.0
    total = max(dur, 4.6) + 0.4
    phrase_t = match_phrase(scene.get("text", ""), words)
    sfx = [(0.05, "thunk")] + [(t, "tick") for _, t in phrase_t]      # NO water sound (was distracting)
    json.dump({"id": scene["id"], "vo": os.path.basename(mp3), "assets": ["pipe", "customer"],
               "beats": [{"t": 0.05, "type": "build", "target": "pipe", "anim": "crack", "sfx": "thunk"}]},
              open(os.path.join(beats_dir, scene["id"] + ".beats.json"), "w"), indent=2)
    fdir = os.path.join(tmp, f"s{sidx}"); os.makedirs(fdir); nf = int(total * FPS)
    px1, px2, py, pr, cx = 250, 780, 350, 40, 560               # simple horizontal pipe + crack at cx
    for fi in range(nf):
        t = fi / FPS
        img = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(img)
        img = draw_env(img, "yard"); d = ImageDraw.Draw(img)
        ground_line(d)
        # panicked homeowner (frustrated, one arm up)
        cimg = render_char(scale=0.78, mood="frustrated", hat=None, armF=-34 + 6 * math.sin(t * 9), sway=2 * math.sin(t * 6))
        img.alpha_composite(cimg, (int(1300 - cimg.width / 2), 392))
        # SIMPLE PIPE with a crack
        d.rounded_rectangle([px1, py - pr, px2, py + pr], radius=pr, fill=(255, 255, 255), outline=INK, width=8)
        for fx in (px1 - 4, px2 - 24):
            d.rectangle([fx, py - pr - 12, fx + 28, py + pr + 12], fill=(255, 255, 255), outline=INK, width=8)
        d.line([(cx - 26, py + pr), (cx - 8, py + pr - 16), (cx + 8, py + pr + 2), (cx + 26, py + pr - 14)], fill=INK, width=6)
        # a few gentle drips falling from the crack into the rising water
        for k in range(5):
            ph = ((k * 0.2) + t * 0.8) % 1.0; dy = py + pr + 12 + ph * 520; r = 9
            d.ellipse([cx - r, dy - r * 1.3, cx + r, dy + r * 1.3], fill=(63, 167, 214), outline=INK, width=3)
        # RISING WATER — wavy blue level climbing the frame (the focus)
        wl = 944 - int(min(360, (t / total) * 440))
        wat = Image.new("RGBA", (W, H), (0, 0, 0, 0)); wd = ImageDraw.Draw(wat)
        top = [(x, wl + int(12 * math.sin(x / 90 + t * 4))) for x in range(0, W + 1, 30)]
        wd.polygon(top + [(W, 960), (0, 960)], fill=(63, 167, 214, 120))
        wd.line(top, fill=(40, 120, 170, 200), width=5)
        img = Image.alpha_composite(img, wat); d = ImageDraw.Draw(img)
        draw_words(d, [pw for (pw, pt) in phrase_t if t >= pt], scene.get("text_y", 120), scene.get("emph"))
        shake = max(0.0, 4 * (1 - t / 1.0))                 # mild settle, no hard shake
        apply_camera(img.convert("RGB"), t, total, push=0.03, shake=shake).save(os.path.join(fdir, f"{fi:04d}.png"))
    return fdir, nf, mp3, total, sfx


# ---------- branded outro card ----------
def render_outro(scene, tmp, sidx, beats_dir):
    mp3, words = vo_words(scene["vo"]); dur = ML.ffprobe_dur(mp3) or 4.0
    total = max(dur, 4.0) + 0.6
    sfx = [(0.3, "pop"), (1.2, "pop"), (2.0, "tick"), (2.8, "ding")]
    json.dump({"id": scene["id"], "vo": os.path.basename(mp3), "assets": ["brand"],
               "beats": [{"t": 0.3, "type": "brand", "sfx": "pop"}]},
              open(os.path.join(beats_dir, scene["id"] + ".beats.json"), "w"), indent=2)
    fdir = os.path.join(tmp, f"s{sidx}"); os.makedirs(fdir); nf = int(total * FPS)
    O = PAL_ACCENT
    for fi in range(nf):
        t = fi / FPS
        img = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(img)
        ground_line(d)
        if t >= 0.3:                                   # brand lockup: [B] BOOKED JOB
            dy = int((1 - ease(min(1, (t - 0.3) / 0.4))) * -30)
            d.rounded_rectangle([660, 340 + dy, 780, 460 + dy], radius=20, fill=O)
            d.text((720, 398 + dy), "B", font=F(88), fill=PAPER, anchor="mm")
            d.text((802, 400 + dy), "BOOKED", font=F(72), fill=INK, anchor="lm")
            bw = d.textlength("BOOKED", font=F(72))
            d.text((802 + bw + 16, 400 + dy), "JOB", font=F(72), fill=O, anchor="lm")
        if t >= 1.2:
            d.text((W / 2, 565), "GET FOUND. GET PICKED. GET BOOKED.", font=F(54), fill=INK, anchor="mm")
        if t >= 2.0:
            d.text((W / 2, 660), scene.get("url", "booked-job.com"), font=F(56), fill=O, anchor="mm")
        if t >= 2.8:
            txt = "NEXT — " + scene.get("next_label", "COURSE 2: KNOW YOUR NUMBERS"); cf = F(40); tw = d.textlength(txt, font=cf)
            d.rounded_rectangle([W / 2 - tw / 2 - 42, 792, W / 2 + tw / 2 + 42, 864], radius=18, outline=INK, width=6, fill=(255, 255, 255))
            d.text((W / 2, 828), txt, font=cf, fill=INK, anchor="mm")
        apply_camera(img.convert("RGB"), t, total, push=0.02).save(os.path.join(fdir, f"{fi:04d}.png"))
    return fdir, nf, mp3, total, sfx


# ---------- scene render ----------
def render_scene(scene, tmp, sidx, beats_dir):
    if scene.get("calendar"):
        return render_calendar(scene, tmp, sidx, beats_dir)
    if scene.get("burst"):
        return render_burst(scene, tmp, sidx, beats_dir)
    if scene.get("outro"):
        return render_outro(scene, tmp, sidx, beats_dir)
    vo_text = scene["vo"]; mp3, words = vo_words(vo_text)
    dur = (ML.ffprobe_dur(mp3) or 3.0)
    total = dur + 0.35                                   # tight tail (no dead air)
    phrase_t = match_phrase(scene.get("text", ""), words)
    headbob_times = [t for (_, t) in phrase_t]
    beats = [{"t": round(t, 3), "type": "word", "text": pw, "anim": "headBob", "sfx": "tick"}
             for (pw, t) in phrase_t]
    sfx_events = [(t, "tick") for (_, t) in phrase_t]
    # assets: entrance keyed to a phrase-word index or explicit t; FIRST visible at t~0
    assets = scene.get("assets", [])
    # keep props out of the top title band and above the ground line (fix text overlap)
    TEXT_BOTTOM = scene.get("text_y", 130) + 150     # generous clearance under the title
    GROUND = H - 136
    for a in assets:
        a["_t"] = phrase_t[a["at_word"]][1] if ("at_word" in a and a["at_word"] < len(phrase_t)) else a.get("t", 0.05)
        h = raster(a["id"], int(a.get("w", 480))).height
        avail = GROUND - TEXT_BOTTOM
        if h > avail:                                  # too tall -> shrink to fit the content band
            a["w"] = max(60, int(a.get("w", 480) * avail / h)); h = raster(a["id"], a["w"]).height
        cy0 = a.get("y", H // 2)
        a["y"] = int(min(max(cy0, TEXT_BOTTOM + h // 2 + 10), GROUND - h // 2))
    ch = scene.get("char")
    if assets:                                           # no dead air: the primary prop draws in early
        e = min(assets, key=lambda x: x["_t"])           # (char scenes too — host never just waits)
        e["_t"] = min(e["_t"], 0.6 if ch else 0.05)
        if e.get("anim") in (None, "popIn"):
            e["anim"] = "drawOn"                          # marker sketches it in to fill the space
    for a in assets:
        sfx_events.append((a["_t"], a.get("sfx", "pop")))
        if a["id"] in DIEGETIC:                       # layer the diegetic sound on entrance
            sfx_events.append((a["_t"], DIEGETIC[a["id"]]))
        beats.append({"t": round(a["_t"], 3), "type": "build", "target": a["id"], "anim": a.get("anim", "popIn"),
                      "sfx": a.get("sfx", "pop"), "diegetic": DIEGETIC.get(a["id"])})
    # character cues: slideIn entrance @0, armRaise gesture
    cent = 0.0
    if ch:
        gest_t = phrase_t[min(ch.get("gesture_at", 0), len(phrase_t)-1)][1] if phrase_t else 0.4
        sfx_events.append((0.0, "whoosh")); beats.append({"t": 0.0, "type": "enter", "target": "character", "anim": "slideIn", "sfx": "whoosh"})
        sfx_events.append((round(gest_t, 3), "pop")); beats.append({"t": round(gest_t, 3), "type": "gesture", "target": "character.armFront", "anim": "armRaise", "sfx": "pop"})
    if scene.get("trades"):                                  # pop on each trade swap
        tr = scene["trades"]
        for i in range(len(tr)):
            sfx_events.append((round(i * total / len(tr), 3), "pop"))
    if scene.get("char2"):
        sfx_events.append((0.05, "whoosh"))
    # write the beat track (the contract)
    beats.sort(key=lambda b: b["t"])
    json.dump({"id": scene["id"], "vo": os.path.basename(mp3), "assets": [a["id"] for a in assets], "beats": beats},
              open(os.path.join(beats_dir, scene["id"] + ".beats.json"), "w"), indent=2)

    frames_dir = os.path.join(tmp, f"s{sidx}"); os.makedirs(frames_dir)
    nf = int(total * FPS)
    mood = scene.get("mood", "neutral")
    for fi in range(nf):
        t = fi / FPS
        img = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(img)
        if scene.get("wash"):
            img = draw_wash(img, scene["wash"]); d = ImageDraw.Draw(img)
        ground_line(d)
        if scene.get("env"):
            img = draw_env(img, scene["env"]); d = ImageDraw.Draw(img)
        for a in assets:
            lt = t - a["_t"]
            if lt < 0: continue
            im = raster(a["id"], int(a.get("w", 480)))
            if a.get("flip"):
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            x, y = a.get("x", W // 2), a.get("y", H // 2)
            y += int(3 * math.sin((lt + a["_t"]) * 2.2))          # continuous idle bob (never frozen)
            anim = a.get("anim", "popIn"); p = min(1.0, lt / 0.38)
            if anim == "popIn":
                s = back(p); iw, ih = max(1, int(im.width * s)), max(1, int(im.height * s))
                img.alpha_composite(im.resize((iw, ih)), (int(x - iw / 2), int(y - ih / 2)))
            elif anim == "slideIn":
                off = int((1 - ease(p)) * 760); img.alpha_composite(im, (int(x - im.width / 2 - off), int(y - im.height / 2)))
            elif anim == "dropIn":
                yoff = int((1 - back(p)) * -300); img.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2 + yoff)))
            elif anim == "dropFade":
                pf = lt / 0.95
                if pf > 1.0: continue                       # fully faded -> gone
                yy = y - 140 + ease(pf) * 430               # descend through the funnel
                al = max(0.0, 1.0 - pf)                     # fade as it sinks
                ach = im.split()[3].point(lambda v: int(v * al))
                im2 = im.copy(); im2.putalpha(ach)
                img.alpha_composite(im2, (int(x - im.width / 2), int(yy - im.height / 2)))
            elif anim == "drawOn":
                rev = ease(min(1.0, lt / 0.55)); crop = im.crop((0, 0, im.width, max(1, int(im.height * rev))))
                img.alpha_composite(crop, (int(x - im.width / 2), int(y - im.height / 2)))
            else:
                img.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
            if a.get("mark") and lt > 0.12:                  # ✓ / ✗ stamped over the prop
                mp = ease(min(1.0, (lt - 0.12) / 0.25))
                if a["mark"] == "check":
                    c = (45, 160, 70); pts = [(x - 46, y), (x - 12, y + 40), (x + 52, y - 44)]
                    seg = max(2, int(len(pts) * mp))
                    d.line(pts[:seg] if mp < 1 else pts, fill=c, width=16, joint="curve")
                else:
                    c = (214, 48, 48); r = int(48 * mp)
                    d.line([(x - r, y - r), (x + r, y + r)], fill=c, width=15)
                    d.line([(x - r, y + r), (x + r, y - r)], fill=c, width=15)
            if a.get("label") and lt > 0.1:                  # small marker caption under the prop
                lf = F(40)
                d.text((x, y + im.height // 2 + 36), a["label"].upper(), font=lf, fill=INK, anchor="mm")
            if a["id"] == "bubble" and a.get("say") and lt > 0.18:   # supporting text inside bubble
                bf = F(46); inner = int(a.get("w", 360) * 0.74)
                lines = ML.wrap(d, a["say"].upper(), bf, inner)
                ty = y - im.height * 0.16 - (len(lines) - 1) * 28
                for ln in lines:
                    d.text((x, ty), ln, font=bf, fill=INK, anchor="mm"); ty += 56
        if ch:
            # entrance slideIn (first 0.4s) + word head-bobs + continuous idle sway/breathe
            ent = 1 - ease(min(1.0, t / 0.4)); ent_x = -int(ent * 700)
            bob = 2.6 * math.sin(t * 1.5)
            for ht in headbob_times:
                d2 = t - ht
                if 0 <= d2 < 0.32: bob += -7 * math.sin(d2 / 0.32 * math.pi)
            gest_t = phrase_t[min(ch.get("gesture_at", 0), len(phrase_t)-1)][1] if phrase_t else 0.4
            gp = (t - gest_t) / 0.55
            armF = -26 * math.sin(gp * math.pi) if 0 <= gp <= 1 else 0.0
            sway = 1.6 * math.sin(t * 1.2)
            hat_i, tool_i, lab = ch.get("hat", "hardhat"), ch.get("tool"), None
            trades = scene.get("trades")               # trade-swap demo: cycle hat+tool
            if trades:
                idx = min(len(trades) - 1, int(t / (total / len(trades))))
                hat_i, tool_i, lab = trades[idx]
            cimg = render_char(scale=ch.get("scale", 1.1), head=bob, armF=armF, sway=sway, tag=ch.get("tag", ""),
                               mood=mood, hat=hat_i, tool=tool_i)
            img.alpha_composite(cimg, (int(ch.get("x", 360) - cimg.width / 2 + ent_x), max(int(ch.get("y", 300)), TEXT_BOTTOM)))
            if lab:
                d.text((int(ch.get("x", 360)), 470), lab, font=F(70), fill=PAL_ACCENT, anchor="mm")
        c2 = scene.get("char2")                          # second character (e.g. the customer)
        if c2:
            e2 = 1 - ease(min(1.0, t / 0.4)); e2x = int(e2 * 700)   # enters from the right
            b2 = 2.6 * math.sin(t * 1.5 + 1.1); s2 = 1.6 * math.sin(t * 1.2 + 0.7)
            c2img = render_char(scale=c2.get("scale", 0.8), head=b2, sway=s2, tag=c2.get("tag", ""),
                                mood=c2.get("mood", "neutral"), hat=c2.get("hat"), tool=c2.get("tool"))
            img.alpha_composite(c2img, (int(c2.get("x", 1420) - c2img.width / 2 + e2x), max(int(c2.get("y", 320)), TEXT_BOTTOM)))
        revealed = [pw for (pw, pt) in phrase_t if t >= pt]
        draw_words(d, revealed, scene.get("text_y", 130), scene.get("emph"))
        if scene.get("sub") and revealed:                    # small subtitle under the title
            d.text((W / 2, scene.get("text_y", 130) + 78), scene["sub"].upper(), font=F(46), fill=PAL_ACCENT, anchor="mm")
        cam = apply_camera(img.convert("RGB"), t, total, push=scene.get("push", 0.05))
        cam.save(os.path.join(frames_dir, f"{fi:04d}.png"))
    return frames_dir, nf, mp3, total, sfx_events


# UI SFX quietest, diegetic a clear step under VO (v2 §5 mix rule)
SFX_VOL = {"tick": 0.4, "pop": 0.55, "whoosh": 0.6, "zip": 0.55,
           "thunk": 0.7, "rumble": 0.55, "buzz": 0.6, "ping": 0.6, "ding": 0.7, "gush": 0.5}


def build_music(total, tmp):
    """ElevenLabs music bed (instrumental), or None on failure."""
    try:
        kf = None
        for line in open(os.path.join(ROOT, "secrets", "elevenlabs.env")):
            if line.startswith("ELEVENLABS_API_KEY="): kf = line.strip().split("=", 1)[1]
        m = os.path.join(tmp, "music_src.mp3")
        body = json.dumps({"prompt": "gentle minimal upbeat acoustic background, soft ukulele and light percussion, positive, low-key, instrumental",
                           "music_length_ms": min(295000, int(total * 1000) + 1500)})
        bf = m + ".req"; open(bf, "w").write(body)
        subprocess.run(["curl", "-s", "-X", "POST", "https://api.elevenlabs.io/v1/music",
                        "-H", f"xi-api-key: {kf}", "-H", "Content-Type: application/json",
                        "--data-binary", f"@{bf}", "-o", m], check=False)
        return m if os.path.exists(m) and os.path.getsize(m) > 4000 else None
    except Exception:
        return None


def build_audio(scene_mp3s, starts, all_sfx, total, tmp, music=True):
    """VO + every SFX (each on its frame) + a ducked music bed -> two-pass loudnorm
    to exactly -14 LUFS / -1 dBTP, 48 kHz stereo."""
    inputs, filt, lbls, idx = [], [], [], 0
    for si, mp3 in enumerate(scene_mp3s):
        inputs += ["-i", mp3]; dly = int(starts[si] * 1000)
        filt.append(f"[{idx}:a]adelay={dly}|{dly}[a{idx}]"); lbls.append(f"[a{idx}]"); idx += 1
    for (gt, key) in all_sfx:
        inputs += ["-i", sfx_path(key)]; dly = int(max(0, gt) * 1000)
        filt.append(f"[{idx}:a]adelay={dly}|{dly},volume={SFX_VOL.get(key,0.6)}[a{idx}]"); lbls.append(f"[a{idx}]"); idx += 1
    vs = os.path.join(tmp, "vs.wav")
    fc = ";".join(filt) + ";" + "".join(lbls) + f"amix=inputs={idx}:normalize=0:duration=longest[a]"
    bf = os.path.join(tmp, "fc.txt"); open(bf, "w").write(fc)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex_script", bf,
                    "-map", "[a]", "-ar", "48000", "-ac", "2", vs], check=True)
    # duck a music bed under the voice (~-12 dB via low gain + sidechain)
    pre = vs
    mus = build_music(total, tmp) if music else None
    if mus:
        pre = os.path.join(tmp, "premaster.wav")
        duck = ("[1:a]aresample=48000,volume=0.10[bed];[0:a]asplit=2[v][sc];"
                "[bed][sc]sidechaincompress=threshold=0.05:ratio=10:attack=15:release=320[d];"
                "[v][d]amix=inputs=2:normalize=0:duration=first[pm]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vs, "-stream_loop", "-1", "-i", mus,
                        "-filter_complex", duck, "-map", "[pm]", "-ar", "48000", "-ac", "2", "-t", f"{total}", pre], check=True)
    # two-pass loudnorm -> exact -14 LUFS / -1 dBTP
    meas = subprocess.run(["ffmpeg", "-i", pre, "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    import re
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", meas, re.S)
    out = os.path.join(tmp, "audio.m4a")
    af = "loudnorm=I=-14:TP=-1.5:LRA=11"   # TP=-1.5 target so true peak lands <= -1 dBTP
    if m:
        j = json.loads(m.group(0))
        af += (f":measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
               f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    af += ",alimiter=limit=0.74:level=disabled"   # hard-cap peaks (~-2.6 dBFS) -> true peak comfortably <= -1 dBTP
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pre, "-af", af,
                    "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "256k", out], check=True)
    return out


def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "content", "course", "doodle_script.json")
    script = json.load(open(script_path))
    tmp = tempfile.mkdtemp(prefix="doodle_")
    seq_dir = os.path.join(tmp, "seq"); os.makedirs(seq_dir)
    beats_dir = os.path.join(ROOT, "content", "course", "doodle_beats"); os.makedirs(beats_dir, exist_ok=True)
    scenes = []
    for si, scene in enumerate(script["scenes"]):
        fdir, nf, mp3, total, sfx_events = render_scene(scene, tmp, si, beats_dir)
        scenes.append({"fdir": fdir, "nf": nf, "mp3": mp3, "total": total, "sfx": sfx_events, "id": scene["id"], "cfg": scene})
        print(f"  scene {si} ({scene['id']}) {total:.1f}s, {nf}f")
    # HARD CUTS (no transition frames, no dead air) + a soft thunk on each cut
    gidx = 0; starts = []; all_sfx = []; gt = 0.0
    INTER = 0.25; gnf = int(INTER * FPS)        # breathing gap between scenes
    for si, s in enumerate(scenes):
        starts.append(gt)
        all_sfx += [(gt + lt, key) for (lt, key) in s["sfx"]]
        for fi in range(s["nf"]):
            os.link(os.path.join(s["fdir"], f"{fi:04d}.png"), os.path.join(seq_dir, f"{gidx:05d}.png")); gidx += 1
        gt += s["total"]
        if si < len(scenes) - 1:
            nxt = scenes[si + 1]; tin = nxt["cfg"].get("transition_in")
            prev_last = os.path.join(s["fdir"], f"{s['nf']-1:04d}.png")
            next_first = os.path.join(nxt["fdir"], "0000.png")
            if tin == "blur":                   # signature blur-to-text with stop-motion hold
                nfr = int(1.3 * FPS); all_sfx.append((gt, "whoosh")); all_sfx.append((gt + 0.34, "tick"))
                gidx += blur_to_text(prev_last, next_first, nxt["cfg"].get("transition_text", ""), seq_dir, gidx, nfr)
                gt += 1.3
            elif tin == "whip":                 # fast whip-pan
                nfr = int(0.22 * FPS); all_sfx.append((gt, "whoosh"))
                gidx += whip_pan(prev_last, next_first, seq_dir, gidx, nfr)
                gt += 0.22
            else:                               # default: micro-pause hold + cut thunk
                all_sfx.append((gt, "thunk"))
                for _ in range(gnf):
                    os.link(prev_last, os.path.join(seq_dir, f"{gidx:05d}.png")); gidx += 1
                gt += INTER
    audio = build_audio([s["mp3"] for s in scenes], starts, all_sfx, gt, tmp)
    print(f"  beat tracks -> {beats_dir}")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "content", "course", "doodle-lesson-01.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", os.path.join(seq_dir, "%05d.png"), "-i", audio, "-vf", "format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "200k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"built {out} ({ML.ffprobe_dur(out):.0f}s)")


if __name__ == "__main__":
    main()
