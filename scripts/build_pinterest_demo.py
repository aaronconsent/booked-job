#!/usr/bin/env python3
"""Build the Pinterest Standard-access demo video (1280x720 MP4) from real site
screenshots + the real generated Pin + the real API success output. Captioned
walkthrough for the App Review. Output: content/pinterest_demo.mp4"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
ASPHALT = (21, 23, 26); CARD = (30, 34, 39); ORANGE = (255, 106, 0)
WHITE = (244, 242, 238); MUTE = (168, 173, 181); STEEL = (44, 49, 54); GREEN = (74, 222, 128)
OUT = "/tmp/pinvid"; FR = os.path.join(OUT, "frames"); os.makedirs(FR, exist_ok=True)
ROOT = os.path.join(os.path.dirname(__file__), "..")


def font(path, size, fb="/Library/Fonts/Arial Unicode.ttf"):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(fb, size)


BLACK = lambda s: font("/System/Library/Fonts/Supplemental/Arial Black.ttf", s)
BOLD = lambda s: font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", s)
REG = lambda s: font("/Library/Fonts/Arial Unicode.ttf", s)
MONO = lambda s: font("/System/Library/Fonts/Menlo.ttc", s)


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


def base():
    img = Image.new("RGB", (W, H), ASPHALT); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=ORANGE)
    # logo mark + wordmark
    d.rounded_rectangle([40, 28, 74, 62], 7, fill=ORANGE)
    d.text((49, 30), "B", font=BLACK(26), fill=ASPHALT)
    d.text((84, 32), "BOOKED", font=BLACK(22), fill=WHITE)
    d.text((84 + d.textlength("BOOKED", font=BLACK(22)) + 6, 32), "JOB", font=BLACK(22), fill=ORANGE)
    return img, d


def caption(d, kicker, title):
    d.rectangle([0, H - 132, W, H], fill=(13, 15, 17))
    d.rectangle([0, H - 132, W, H - 128], fill=ORANGE)
    d.text((48, H - 112), kicker.upper(), font=BOLD(17), fill=ORANGE)
    for i, ln in enumerate(wrap(d, title, BOLD(27), W - 96)[:2]):
        d.text((48, H - 84 + i * 34), ln, font=BOLD(27), fill=WHITE)


def shot(img, d, path, kicker, title):
    s = Image.open(path).convert("RGB")
    maxw, maxh = W - 120, H - 230
    r = min(maxw / s.width, maxh / s.height); ns = s.resize((int(s.width * r), int(s.height * r)))
    x = (W - ns.width) // 2; y = 80 + (H - 210 - ns.height) // 2
    d.rectangle([x - 2, y - 2, x + ns.width + 2, y + ns.height + 2], outline=STEEL, width=2)
    img.paste(ns, (x, y))
    caption(d, kicker, title)


def textcard(d, kicker, title, body):
    d.text((64, 150), kicker.upper(), font=BOLD(19), fill=ORANGE)
    yy = 196
    for ln in wrap(d, title, BLACK(46), W - 160):
        d.text((64, yy), ln, font=BLACK(46), fill=WHITE); yy += 58
    yy += 18
    for ln in wrap(d, body, REG(26), W - 160):
        d.text((64, yy), ln, font=REG(26), fill=MUTE); yy += 38


frames = []  # (path, seconds)


def save(name, img, secs):
    p = os.path.join(FR, name); img.save(p); frames.append((p, secs))


# 1 — title
img, d = base()
d.text((64, 250), "PINTEREST API", font=BLACK(64), fill=WHITE)
d.text((64, 322), "INTEGRATION", font=BLACK(64), fill=ORANGE)
d.text((66, 410), "Standard-access review demo  ·  app 1584980  ·  account @bookedjob", font=REG(26), fill=MUTE)
save("01.png", img, 4)

# 2 — what we are (homepage)
img, d = base(); shot(img, d, f"{OUT}/home.png", "What Booked Job is",
                       "A content brand for home-service contractors — booked-job.com")
save("02.png", img, 6)

# 3 — the content (article)
img, d = base(); shot(img, d, f"{OUT}/article.png", "Our original content",
                       "We publish original articles + free tools for the trades")
save("03.png", img, 6)

# 4 — use case (text)
img, d = base()
textcard(d, "Our Pinterest use case",
         "We publish our OWN content as Pins.",
         "Each Pin is an original branded graphic from one of our articles, linking back to that article on booked-job.com. First-party content, to our own business account.")
save("04.png", img, 7)

# 5 — step 1: generate pin
img, d = base(); shot(img, d, f"{ROOT}/content/pins/is-angi-worth-it.png", "Step 1 — generate",
                       "Our pipeline renders a branded 2:3 Pin image from the article")
save("05.png", img, 6)

# 6 — step 2: API call (terminal)
img, d = base()
d.text((64, 120), "STEP 2 — CREATE THE PIN VIA PINTEREST API v5", font=BOLD(20), fill=ORANGE)
tx, ty, tw, th = 64, 168, W - 128, 360
d.rounded_rectangle([tx, ty, tx + tw, ty + th], 10, fill=(12, 14, 16), outline=STEEL, width=2)
d.ellipse([tx + 18, ty + 16, tx + 30, ty + 28], fill=(255, 95, 86))
d.ellipse([tx + 38, ty + 16, tx + 50, ty + 28], fill=(255, 189, 46))
d.ellipse([tx + 58, ty + 16, tx + 70, ty + 28], fill=(39, 201, 63))
lines = [
    ("$ python3 scripts/pinterest_runner.py", WHITE),
    ("", WHITE),
    ("POST https://api.pinterest.com/v5/pins", MUTE),
    ("  board_id: \"Booked Job\"   link: booked-job.com/blog/is-angi-worth-it/", MUTE),
    ("", WHITE),
    ("2026-06-26 17:38:24  PINNED 'is-angi-worth-it'", WHITE),
    ("✔ 201 Created  —  pin id 1138495980826538967", GREEN),
]
for i, (ln, col) in enumerate(lines):
    d.text((tx + 26, ty + 52 + i * 38), ln, font=MONO(20), fill=col)
caption(d, "Step 2 — publish", "A single POST to /v5/pins creates the Pin")
save("06.png", img, 8)

# 7 — step 3: links back
img, d = base(); shot(img, d, f"{ROOT}/content/pins/is-angi-worth-it.png", "Step 3 — drive traffic",
                       "The Pin links to our article: booked-job.com/blog/is-angi-worth-it/")
save("07.png", img, 6)

# 8 — compliance
img, d = base()
textcard(d, "Compliance",
         "Only our own content. Our own account.",
         "We publish first-party content to our own Pinterest business account on a schedule. No scraping, no posting on behalf of third parties, no automated engagement of other users. Privacy policy: booked-job.com/privacy")
save("08.png", img, 8)

# 9 — end
img, d = base()
d.text((64, 270), "Requesting Standard access", font=BLACK(50), fill=WHITE)
d.text((64, 332), "for pins:write + boards:write", font=BLACK(50), fill=ORANGE)
d.text((66, 420), "Booked Job  ·  booked-job.com  ·  @bookedjob", font=REG(26), fill=MUTE)
save("09.png", img, 4)

# assemble
listf = os.path.join(OUT, "list.txt")
with open(listf, "w") as f:
    for p, s in frames:
        f.write(f"file '{p}'\nduration {s}\n")
    f.write(f"file '{frames[-1][0]}'\n")
outmp4 = os.path.join(ROOT, "content", "pinterest_demo.mp4")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-pix_fmt", "yuv420p", outmp4],
               check=True, capture_output=True)
dur = sum(s for _, s in frames)
print(f"✅ wrote {outmp4}  (~{dur}s, {len(frames)} scenes)")
