#!/usr/bin/env python3
"""Generate Booked Job page graphics: profile picture + Facebook cover banner."""
import os
from PIL import Image, ImageDraw, ImageFont

HI = (255, 106, 0); ASPHALT = (21, 23, 26); WHITE = (255, 255, 255); YELLOW = (255, 210, 63)
FD = "/System/Library/Fonts/Supplemental"
def F(n, s): return ImageFont.truetype(os.path.join(FD, n), s)
OUT = os.path.join(os.path.dirname(__file__), "..", "content", "brand")
os.makedirs(OUT, exist_ok=True)


def profile():
    S = 1000
    img = Image.new("RGB", (S, S), ASPHALT); d = ImageDraw.Draw(img)
    # caution tape arc top
    for x in range(-40, S + 40, 90):
        d.polygon([(x, 0), (x + 45, 0), (x + 45 - 38, 38), (x - 38, 38)], fill=YELLOW)
    # big skewed B tile
    tile = Image.new("RGBA", (520, 520), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    td.rounded_rectangle([0, 0, 520, 520], radius=70, fill=HI)
    td.text((150, 70), "B", font=F("Arial Black.ttf", 400), fill=ASPHALT)
    tile = tile.transform((520, 520), Image.AFFINE, (1, -0.12, 30, 0, 1, 0), resample=Image.BICUBIC)
    img.paste(tile, (240, 150), tile)
    # wordmark
    d.text((S/2, 770), "BOOKED", font=F("Arial Black.ttf", 96), fill=WHITE, anchor="mm")
    d.text((S/2, 870), "JOB", font=F("Arial Black.ttf", 96), fill=HI, anchor="mm")
    p = os.path.join(OUT, "profile.png"); img.save(p); return p


def cover():
    W, H = 1640, 624
    img = Image.new("RGB", (W, H), ASPHALT); d = ImageDraw.Draw(img)
    # glow
    glow = Image.new("RGB", (W, H), ASPHALT); gd = ImageDraw.Draw(glow)
    for r in range(520, 0, -10):
        a = int(22 * (r / 520))
        gd.ellipse([W*0.72 - r, H*0.2 - r, W*0.72 + r, H*0.2 + r],
                   fill=(min(ASPHALT[0]+a, 255), min(ASPHALT[1]+a//3, 255), ASPHALT[2]))
    img = Image.blend(img, glow, 0.6); d = ImageDraw.Draw(img)
    # caution tape left rail
    for y in range(-40, H + 40, 80):
        d.polygon([(0, y), (0, y + 40), (40, y + 40 - 34), (40, y - 34)], fill=YELLOW)
    # headline
    d.text((90, 150), "STAY BOOKED.", font=F("Arial Black.ttf", 130), fill=WHITE)
    d.text((90, 290), "RUN A BETTER SHOP.", font=F("Arial Black.ttf", 96), fill=HI)
    d.text((96, 430), "FOR PLUMBERS · ROOFERS · HVAC · ELECTRICIANS",
           font=F("Arial Bold.ttf", 34), fill=(170, 175, 182))
    d.rectangle([96, 412, 96 + 220, 420], fill=HI)
    p = os.path.join(OUT, "cover.png"); img.save(p); return p


if __name__ == "__main__":
    print(profile()); print(cover())
