#!/usr/bin/env python3
"""Render a 1080x1920 (9:16) branded Story card. make(slug, headline, sub) -> PNG path."""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ASPHALT = (21, 23, 26); ORANGE = (255, 106, 0); WHITE = (244, 242, 238); MUTE = (175, 180, 188)
ROOT = os.path.join(os.path.dirname(__file__), "..")
OUTDIR = os.path.join(ROOT, "site", "img")


def font(path, size, fb="/Library/Fonts/Arial Unicode.ttf"):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(fb, size)


BLACK = lambda s: font("/System/Library/Fonts/Supplemental/Arial Black.ttf", s)
BOLD = lambda s: font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", s)
REG = lambda s: font("/Library/Fonts/Arial Unicode.ttf", s)


def wrap(d, text, fnt, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out


def make(slug, headline, sub):
    os.makedirs(OUTDIR, exist_ok=True)
    img = Image.new("RGB", (W, H), ASPHALT); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=ORANGE)
    # logo
    d.rounded_rectangle([70, 110, 116, 156], 9, fill=ORANGE)
    d.text((83, 113), "B", font=BLACK(34), fill=ASPHALT)
    d.text((132, 116), "BOOKED", font=BLACK(30), fill=WHITE)
    d.text((132 + d.textlength("BOOKED", font=BLACK(30)) + 8, 116), "JOB", font=BLACK(30), fill=ORANGE)
    # headline (centered vertically-ish)
    lines = wrap(d, headline, BLACK(86), W - 150)
    y = 640
    for ln in lines:
        d.text((75, y), ln, font=BLACK(86), fill=WHITE); y += 98
    y += 40
    for ln in wrap(d, sub, REG(44), W - 160):
        d.text((75, y), ln, font=REG(44), fill=ORANGE); y += 60
    # footer
    d.text((75, H - 140), "booked-job.com", font=BOLD(40), fill=MUTE)
    out = os.path.join(OUTDIR, f"{slug}-story.png")
    img.save(out)
    return out


if __name__ == "__main__":
    import sys
    p = make(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    print("wrote", p)
