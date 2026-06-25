#!/usr/bin/env python3
"""
Generate a branded 1080x1080 Booked Job quote/meme card (PNG) with PIL.

Used for the high-share text archetypes (pricing-drama one-liners, "stuff
homeowners say", trade humor) so they go out as IMAGE posts — which out-reach
bare text/link posts on Facebook.

Usage:
    python3 scripts/make_card.py --text "You want it fast, cheap, and perfect? Pick two." \
        --label "PRICING TRUTH" --out content/assets/card1.png
"""
import argparse, os, textwrap
from PIL import Image, ImageDraw, ImageFont

HI = (255, 106, 0)
HI2 = (255, 138, 43)
ASPHALT = (21, 23, 26)
ASPHALT2 = (30, 34, 39)
WHITE = (255, 255, 255)
YELLOW = (255, 210, 63)
MUTED = (170, 175, 182)

FONT_DIR = "/System/Library/Fonts/Supplemental"
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

W = H = 1080


def _wrap_to_width(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make(text, label, out, accent="orange"):
    img = Image.new("RGB", (W, H), ASPHALT)
    d = ImageDraw.Draw(img)

    # subtle radial glow top
    glow = Image.new("RGB", (W, H), ASPHALT)
    gd = ImageDraw.Draw(glow)
    for r in range(420, 0, -8):
        a = int(18 * (r / 420))
        gd.ellipse([W//2 - r, -160 - r, W//2 + r, -160 + r],
                   fill=(min(ASPHALT[0]+a, 255), min(ASPHALT[1]+a//3, 255), ASPHALT[2]))
    img = Image.blend(img, glow, 0.5)
    d = ImageDraw.Draw(img)

    # caution-tape strip top
    tape_h = 26
    for x in range(-tape_h, W + tape_h, 64):
        d.polygon([(x, 0), (x + 32, 0), (x + 32 - tape_h, tape_h), (x - tape_h, tape_h)], fill=YELLOW)

    # label pill
    accent_col = HI if accent == "orange" else YELLOW
    if label:
        lf = font("Arial Bold.ttf", 30)
        lw = d.textlength(label.upper(), font=lf)
        px, py = 70, 150
        d.rounded_rectangle([px, py, px + lw + 56, py + 58], radius=29, outline=accent_col, width=3)
        d.text((px + 28, py + 13), label.upper(), font=lf, fill=accent_col)

    # main quote — auto-size to fit
    size = 92
    while size > 44:
        qf = font("Arial Black.ttf", size)
        lines = _wrap_to_width(d, text, qf, W - 150)
        line_h = size + 16
        total = len(lines) * line_h
        if total <= 560 and len(lines) <= 7:
            break
        size -= 4
    y = (H - total) // 2 + 30
    for ln in lines:
        # highlight quoted words inside the line stay white; full line white with hi accent words optional
        d.text((75, y), ln, font=qf, fill=WHITE)
        y += line_h

    # accent underline
    d.rectangle([75, y + 14, 75 + 150, y + 24], fill=HI)

    # footer brand lockup
    bf = font("Arial Black.ttf", 38)
    d.rounded_rectangle([75, H - 130, 75 + 60, H - 70], radius=12, fill=HI)
    d.text((92, H - 126), "B", font=font("Arial Black.ttf", 44), fill=ASPHALT)
    d.text((150, H - 124), "BOOKED", font=bf, fill=WHITE)
    bw = d.textlength("BOOKED", font=bf)
    d.text((150 + bw + 8, H - 124), "JOB", font=bf, fill=HI)

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out, "PNG")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--label", default="")
    ap.add_argument("--accent", default="orange", choices=["orange", "yellow"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(make(a.text, a.label, a.out, a.accent))
