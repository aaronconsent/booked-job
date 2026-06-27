#!/usr/bin/env python3
"""Render a branded LinkedIn-style document carousel: a list of slides -> portrait
1080x1350 PNGs -> a multi-page PDF + a cover thumbnail. Used by buffer_carousel_runner.
make(slug, title, slides) -> (pdf_path, thumb_path). slides = [{'kind','headline','body'}]."""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
ASPHALT = (21, 23, 26); ORANGE = (255, 106, 0); WHITE = (244, 242, 238); MUTE = (165, 170, 178); STEEL = (44, 49, 54)
ROOT = os.path.join(os.path.dirname(__file__), "..")
OUTDIR = os.path.join(ROOT, "site", "docs")


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


def logo(d):
    d.rounded_rectangle([60, 56, 100, 96], 8, fill=ORANGE)
    d.text((71, 59), "B", font=BLACK(30), fill=ASPHALT)
    d.text((114, 62), "BOOKED", font=BLACK(26), fill=WHITE)
    d.text((114 + d.textlength("BOOKED", font=BLACK(26)) + 7, 62), "JOB", font=BLACK(26), fill=ORANGE)


def slide(kind, headline, body, idx, total):
    img = Image.new("RGB", (W, H), ASPHALT); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ORANGE); logo(d)
    if kind == "cover":
        y = 360
        for ln in wrap(d, headline, BLACK(76), W - 130):
            d.text((65, y), ln, font=BLACK(76), fill=WHITE); y += 86
        if body:
            y += 24
            for ln in wrap(d, body, REG(34), W - 150):
                d.text((65, y), ln, font=REG(34), fill=MUTE); y += 46
        d.text((65, H - 110), "SWIPE →", font=BLACK(34), fill=ORANGE)
    else:
        d.text((65, 175), f"{idx:02d}", font=BLACK(120), fill=STEEL)
        y = 330
        for ln in wrap(d, headline, BLACK(58), W - 130):
            d.text((65, y), ln, font=BLACK(58), fill=WHITE); y += 68
        y += 26
        for ln in wrap(d, body, REG(38), W - 140):
            d.text((65, y), ln, font=REG(38), fill=(206, 210, 216)); y += 52
    d.text((W - 150, H - 70), f"{idx}/{total}", font=BOLD(26), fill=MUTE)
    return img


def make(slug, title, slides):
    os.makedirs(OUTDIR, exist_ok=True)
    total = len(slides)
    imgs = [slide(s.get("kind", "point"), s["headline"], s.get("body", ""), i + 1, total) for i, s in enumerate(slides)]
    pdf = os.path.join(OUTDIR, f"{slug}.pdf")
    imgs[0].save(pdf, save_all=True, append_images=imgs[1:], resolution=100.0)
    thumb = os.path.join(OUTDIR, f"{slug}.png")
    imgs[0].save(thumb)
    return pdf, thumb


def make_images(slug, title, slides, subdir="img"):
    """Render each slide as an individual PNG (for IG/FB carousels). Returns paths."""
    outdir = os.path.join(ROOT, "site", subdir)
    os.makedirs(outdir, exist_ok=True)
    total = len(slides)
    paths = []
    for i, s in enumerate(slides):
        img = slide(s.get("kind", "point"), s["headline"], s.get("body", ""), i + 1, total)
        p = os.path.join(outdir, f"{slug}-{i + 1}.png")
        img.save(p); paths.append(p)
    return paths


if __name__ == "__main__":
    import json, sys
    cfg = json.load(open(os.path.join(ROOT, "content", "linkedin_carousels.json")))["carousels"]
    slug = sys.argv[1] if len(sys.argv) > 1 else list(cfg.keys())[0]
    c = cfg[slug]
    p, t = make(slug, c["title"], c["slides"])
    print("wrote", p, "and", t)
