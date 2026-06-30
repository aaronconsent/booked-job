#!/usr/bin/env python3
"""
Stat-card engine — turns one sourced stat from content/stats.json into a branded
card (hazard look) with the SOURCE printed on it (the "real numbers" moat).
Aspects: sq (1080x1080 FB/IG), pin (1000x1500 Pinterest), story (1080x1920).

    python3 scripts/make_statcard.py            # render all stats, all aspects -> content/cards/
    from make_statcard import render            # render(stat_dict, aspect, out)
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ORANGE = (255, 106, 0); BLACK = (17, 17, 17); WHITE = (248, 247, 243); GREY = (150, 150, 150)
IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
BLACKF = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
MARKER = os.path.join(ROOT, "doodle", "assets", "PermanentMarker.ttf")
DIMS = {"sq": (1080, 1080), "pin": (1000, 1500), "story": (1080, 1920)}


def f(p, s): return ImageFont.truetype(p, int(s))


def fit(d, t, p, tw, start):
    s = start
    while s > 24:
        ft = f(p, s)
        if d.textlength(t, font=ft) <= tw: return ft
        s -= 4
    return f(p, 24)


def wrap(d, t, ft, tw):
    words, lines, cur = t.split(), [], ""
    for w in words:
        if d.textlength((cur + " " + w).strip(), font=ft) <= tw: cur = (cur + " " + w).strip()
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def hazard(img, x0, y0, x1, y1):
    d = ImageDraw.Draw(img); d.rectangle([x0, y0, x1, y1], fill=BLACK)
    H = y1 - y0; w = int(H * 0.45); x = x0 - H
    while x < x1 + H:
        d.polygon([(x, y0), (x + w, y0), (x + w - H, y1), (x - H, y1)], fill=ORANGE); x += 2 * w


def render(stat, aspect, out):
    W, H = DIMS[aspect]
    img = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(img)
    band = int(H * 0.055)
    hazard(img, 0, 0, W, band); hazard(img, 0, H - band, W, H)
    d.rectangle([0, 0, W - 1, H - 1], outline=ORANGE, width=max(6, W // 150))
    cx = W / 2
    # kicker
    d.text((cx, band + 70), "REAL TRADE NUMBERS", font=f(BLACKF, W * 0.038), fill=ORANGE, anchor="mm")
    # value — split composite values (·) onto their own lines, sized to fit a band
    val = stat["value"]
    parts = [p.strip() for p in val.split("·")] if "·" in val else [val]
    y_top, y_bot = H * 0.22, H * 0.60                          # value zone
    if len(parts) == 1 and len(parts[0]) <= 7:                 # short, punchy → huge
        ft = fit(d, parts[0], IMPACT, W - 160, W * 0.42)
        d.text((cx, (y_top + y_bot) / 2), parts[0], font=ft, fill=ORANGE, anchor="mm")
        label_y = y_bot + H * 0.02
    else:
        lh = (y_bot - y_top) / len(parts)
        for i, p in enumerate(parts):
            ft = fit(d, p, IMPACT, W - 140, min(W * 0.13, lh * 0.78))
            d.text((cx, y_top + lh * (i + 0.5)), p, font=ft, fill=ORANGE, anchor="mm")
        label_y = y_bot + H * 0.04
    # metric label (white, wrapped)
    lf = f(BLACKF, W * 0.048)
    for ln in wrap(d, stat["metric"], lf, W - 150):
        d.text((cx, label_y), ln, font=lf, fill=WHITE, anchor="mm"); label_y += W * 0.06
    # source line (the moat)
    src = f"SOURCE: {stat['source_name'].upper()} · {stat['date']}"
    d.text((cx, H - band - 95), src, font=f(BLACKF, W * 0.026), fill=GREY, anchor="mm")
    # brand
    bs = int(W * 0.07); bx = cx - bs - 90
    d.rounded_rectangle([bx, H - band - 70, bx + bs, H - band - 70 + bs], radius=bs * 0.22, fill=ORANGE)
    d.text((bx + bs / 2, H - band - 70 + bs / 2), "B", font=f(MARKER, bs * 0.8), fill=WHITE, anchor="mm")
    d.text((bx + bs + 16, H - band - 70 + bs / 2), "BOOKED-JOB.COM", font=f(MARKER, W * 0.04), fill=WHITE, anchor="lm")
    img.save(out, quality=92)
    return out


def main():
    stats = json.load(open(os.path.join(ROOT, "content", "stats.json")))["stats"]
    out_dir = os.path.join(ROOT, "content", "cards"); os.makedirs(out_dir, exist_ok=True)
    aspects = sys.argv[1:] or ["sq", "pin", "story"]
    n = 0
    for s in stats:
        for asp in aspects:
            render(s, asp, os.path.join(out_dir, f"{s['id']}-{asp}.png")); n += 1
    print(f"rendered {n} cards -> content/cards/ ({len(stats)} stats x {len(aspects)} aspects)")


if __name__ == "__main__":
    main()
