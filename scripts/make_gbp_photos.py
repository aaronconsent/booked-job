#!/usr/bin/env python3
"""Generate 8 branded 1200x1200 photos for the Booked Job Google Business Profile gallery."""
import os
from PIL import Image, ImageDraw, ImageFont

HI = (255, 106, 0); HI2 = (255, 138, 43); ASPHALT = (21, 23, 26); WHITE = (255, 255, 255)
YEL = (255, 210, 63); MUT = (160, 166, 174)
FD = "/System/Library/Fonts/Supplemental"
def F(n, s): return ImageFont.truetype(os.path.join(FD, n), s)
OUT = os.path.join(os.path.dirname(__file__), "..", "content", "brand")
S = 1200


def base():
    img = Image.new("RGB", (S, S), ASPHALT); d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (S, S), ASPHALT); gd = ImageDraw.Draw(glow)
    for r in range(520, 0, -10):
        a = int(20 * (r / 520))
        gd.ellipse([S//2 - r, 300 - r, S//2 + r, 300 + r],
                   fill=(min(ASPHALT[0]+a, 255), min(ASPHALT[1]+a//3, 255), ASPHALT[2]))
    img = Image.blend(img, glow, 0.5); d = ImageDraw.Draw(img)
    for x in range(-40, S + 40, 84):
        d.polygon([(x, 0), (x + 42, 0), (x + 42 - 30, 30), (x - 30, 30)], fill=YEL)
    return img, d


def lockup(d):
    d.rounded_rectangle([S/2 - 150, S - 120, S/2 - 96, S - 66], radius=10, fill=HI)
    d.text((S/2 - 137, S - 116), "B", font=F("Arial Black.ttf", 40), fill=ASPHALT)
    bf = F("Arial Black.ttf", 34)
    d.text((S/2 - 82, S - 113), "BOOKED", font=bf, fill=WHITE)
    bw = d.textlength("BOOKED", font=bf)
    d.text((S/2 - 82 + bw + 7, S - 113), "JOB", font=bf, fill=HI)


def wrap(d, t, f, mw):
    out, cur = [], ""
    for w in t.split():
        s = (cur + " " + w).strip()
        if d.textlength(s, font=f) <= mw: cur = s
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


def headline(eyebrow, text, sub, fn):
    img, d = base()
    d.text((S/2, 150), eyebrow.upper(), font=F("Arial Bold.ttf", 34), fill=HI, anchor="ma")
    size = 110
    while size > 56:
        f = F("Arial Black.ttf", size); lines = wrap(d, text.upper(), f, S - 150)
        if len(lines) <= 4: break
        size -= 6
    th = len(lines) * (size + 12); y = (S - th)//2 - 20
    for ln in lines:
        d.text((S/2, y), ln, font=f, fill=WHITE, anchor="ma"); y += size + 12
    d.rectangle([S/2 - 70, y + 14, S/2 + 70, y + 24], fill=HI)
    if sub:
        sy = y + 56
        for ln in wrap(d, sub, F("Arial.ttf", 36) if os.path.exists(os.path.join(FD, "Arial.ttf")) else F("Arial Bold.ttf", 34), S - 180):
            d.text((S/2, sy), ln, font=F("Arial.ttf", 36), fill=MUT, anchor="ma"); sy += 46
    lockup(d); img.save(os.path.join(OUT, fn))


def listcard(title, items, fn):
    img, d = base()
    d.text((S/2, 150), "WHAT WE COVER", font=F("Arial Bold.ttf", 34), fill=HI, anchor="ma")
    d.text((S/2, 210), title.upper(), font=F("Arial Black.ttf", 64), fill=WHITE, anchor="ma")
    y = 360
    for it in items:
        d.rectangle([200, y + 16, 232, y + 24], fill=HI)
        d.text((260, y), it, font=F("Arial Bold.ttf", 44), fill=WHITE); y += 86
    lockup(d); img.save(os.path.join(OUT, fn))


def statcard(big, label, fn):
    img, d = base()
    d.text((S/2, 280), big, font=F("Arial Black.ttf", 150), fill=HI, anchor="ma")
    y = 470
    for ln in wrap(d, label, F("Arial Black.ttf", 56), S - 160):
        d.text((S/2, y), ln, font=F("Arial Black.ttf", 56), fill=WHITE, anchor="ma"); y += 66
    lockup(d); img.save(os.path.join(OUT, fn))


headline("For the trades", "Stay booked. Run a better shop.", "Real talk for plumbers, roofers, HVAC & electricians.", "gbp-01.png")
listcard("We cover", ["More booked jobs", "Pricing that wins work", "Getting paid faster", "Slow-season survival", "The truth on lead sites"], "gbp-02.png")
headline("Who it's for", "Plumbers · Roofers · HVAC · Electricians", "Home-service business owners who'd rather be working.", "gbp-03.png")
statcard("$290", "What an organic job costs — vs $1,430+ on Angi", "gbp-04.png")
headline("The hard truth", "Stop renting your leads.", "Shared-lead sites resell you the same homeowner.", "gbp-05.png")
headline("Free tool", "True cost of an Angi lead calculator", "Plug in your close rate. See what a lead really costs.", "gbp-06.png")
headline("Pricing", "Quote so you win the job.", "Stop leaving money on the table.", "gbp-07.png")
headline("The promise", "No pitch. No fluff. Just what works in the field.", "", "gbp-08.png")
print("wrote 8 GBP photos to content/brand/gbp-01..08.png")
