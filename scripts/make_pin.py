#!/usr/bin/env python3
"""Generate a branded 1000x1500 (2:3) Pinterest pin image for a post."""
import os
from PIL import Image, ImageDraw, ImageFont

HI = (255, 106, 0); ASPHALT = (21, 23, 26); WHITE = (255, 255, 255); YEL = (255, 210, 63); MUT = (150, 156, 164)
FD = "/System/Library/Fonts/Supplemental"
def F(n, s): return ImageFont.truetype(os.path.join(FD, n), s)
W, H = 1000, 1500


def _wrap(d, text, fnt, maxw):
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


def make(title, teaser, out, eyebrow="FOR SERVICE PROS"):
    img = Image.new("RGB", (W, H), ASPHALT); d = ImageDraw.Draw(img)
    # caution tape top
    for x in range(-40, W + 40, 84):
        d.polygon([(x, 0), (x + 42, 0), (x + 42 - 30, 30), (x - 30, 30)], fill=YEL)
    # eyebrow
    ef = F("Arial Bold.ttf", 30)
    d.text((W/2, 130), eyebrow, font=ef, fill=HI, anchor="ma")
    # title (big)
    size = 96
    while size > 52:
        tf = F("Arial Black.ttf", size)
        lines = _wrap(d, title.upper(), tf, W - 120)
        if len(lines) <= 6:
            break
        size -= 6
    y = 240
    for ln in lines:
        d.text((W/2, y), ln, font=tf, fill=WHITE, anchor="ma"); y += size + 14
    # accent rule
    d.rectangle([W/2 - 90, y + 18, W/2 + 90, y + 30], fill=HI)
    # teaser
    qf = F("Arial.ttf", 38) if os.path.exists(os.path.join(FD, "Arial.ttf")) else F("Arial Bold.ttf", 36)
    ty = y + 70
    for ln in _wrap(d, teaser, qf, W - 150):
        d.text((W/2, ty), ln, font=qf, fill=MUT, anchor="ma"); ty += 52
    # brand lockup bottom
    d.rounded_rectangle([W/2 - 175, H - 150, W/2 - 105, H - 80], radius=12, fill=HI)
    d.text((W/2 - 158, H - 146), "B", font=F("Arial Black.ttf", 52), fill=ASPHALT)
    bf = F("Arial Black.ttf", 46)
    d.text((W/2 - 90, H - 142), "BOOKED", font=bf, fill=WHITE)
    bw = d.textlength("BOOKED", font=bf)
    d.text((W/2 - 90 + bw + 10, H - 142), "JOB", font=bf, fill=HI)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out, "PNG")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True); ap.add_argument("--teaser", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(make(a.title, a.teaser, a.out))
