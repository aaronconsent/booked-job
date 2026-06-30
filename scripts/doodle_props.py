#!/usr/bin/env python3
"""Generate richer DOODLE props via Recraft (hand_drawn_outline marker style),
key out the solid background (corner-sampled) -> transparent PNG, tight-crop, save
to doodle/assets/<id>.png for the engine. Run after adding Recraft credits."""
import os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recraft_image as RC

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "doodle", "assets")
# style locked FROM the character (matches its thin clean marker line + flat palette)
STYLE_ID = open(os.path.join(ROOT, "content", "course", ".doodle_prop_style.txt")).read().strip()
# --- the shared style suffix (EDIT THIS to tune the look) ---
DOODLE = (", very simple minimal doodle, thin clean black outline, flat white fill, no shading, "
          "no gradient, single small object, lots of white space, matching a plain stick-figure "
          "marker doodle. No text, no words.")
PROPS = {
    "megaphone": "a megaphone bullhorn with three sound wave lines",
    "fancylogo": "an ornate fancy abstract business logo emblem badge with a swirl, a star and a laurel ribbon",
    "foundperson": "a big magnifying glass held over one happy little standing person, discovering them",
    "trustbadge": "a shield badge with a large checkmark in the center and three small stars above it",
    "funnelpeople": "a big funnel with three little person figures dropping into the top opening and one gold coin dropping out the bottom",
    "talkers": "two people facing each other talking, with a speech bubble between their heads",
    "phonemap": "a smartphone showing a map with a location pin and a short list of result bars",
    "housetruck": "a small house with a service work van parked in front of it",
    "person": "one single simple standing person figure seen from the front, arms at sides, small",
    "emptyfunnel": "one single empty funnel, wide circular opening at the top narrowing to a small spout at the bottom, clean simple outline, nothing inside it",
    "calendar": "a simple monthly wall calendar, a grid of empty square day cells with a header bar at top",
    "truck": "a simple cartoon work pickup truck with a ladder, side view facing right, on wheels",
    "reviewstars": "a horizontal row of five identical stars in a line, a rating",
    "dollarstack": "a small neat stack of cash money bills with a dollar sign on top",
    "waterheater": "a home water heater tank with a broken pipe at the top spraying water out in an arc, water droplets",
    "citybg": "a simple row of three or four city buildings, a small skyline, plain",
    "suburbbg": "two simple suburban houses side by side with a single tree",
    "door": "one single simple closed door with a round doorknob, front view, in a door frame",
    "thumbsup": "a single hand giving a thumbs up, a like symbol",
    "laptop": "an open laptop computer showing a simple web browser window with a search bar",
    "robot": "a friendly simple chatbot robot head with two round eyes and a small antenna",
    "clipboard": "a clipboard holding a checklist with a few lines and small checkmarks, a scorecard",
    "vestguy": "a smug salesman character wearing a sweater vest and dark sunglasses, arms crossed, standing front view, full body, simple doodle",
    "bsdetector": "a handheld meter device with a round dial gauge, the needle pegged hard all the way into the red zone on the far right",
    "viral": "a smartphone with a rocket ship launching up and out of the screen, motion lines, going viral",
    "heart": "one single simple heart shape, a social media like",
    "acunit": "a wall mounted air conditioner unit with a few cold air lines blowing out of it",
    "roofdamage": "a simple house with a broken damaged roof and a fallen tree branch on top",
    "calculator": "a simple handheld calculator with number buttons and a small screen",
    "leadhand": "a single hand raised straight up high in the air, palm open, volunteering",
    "moneybag": "a sack of money tied at the top with a large dollar sign on the front",
    "scale": "an old fashioned balance scale with two hanging pans, one pan lower than the other",
    "sharedlead": "a single smartphone with four different hands all grabbing and reaching for it at once",
    "handshake": "two hands shaking on a deal, a handshake",
    "ghost": "a simple cute cartoon ghost floating with a wavy bottom",
    "leadapp": "a smartphone showing a service marketplace app, a list of contractor profiles each with a star rating",
    "piechart": "a simple pie chart divided into four colored slices of different sizes",
    "eggsbasket": "a wicker basket full of eggs, all the eggs in one single basket",
    "magnet": "a classic horseshoe magnet with small attraction lines pulling things toward it",
    "camera": "a simple camera for taking photos, with a lens and a shutter button",
    "mappin": "one large single map location pin marker, teardrop shape with a round dot in the center",
    "profilecard": "a business listing card with a small photo box at the top, a name line, and a row of five stars below",
    "blankprofile": "an empty blank business listing card, just a plain gray outline with a big question mark and no information",
    "stopwatch": "a classic stopwatch with a big round dial and a button on top",
    "callbutton": "a large round green button with a white phone handset icon in the center, a call now button",
    "mobilesite": "a smartphone showing a simple contractor website page with a big call now button on it",
    "reviewbubble": "a speech bubble containing a row of five stars and two short text lines, a customer review",
    "trophy": "a simple winners trophy cup",
    "phonestars": "a smartphone showing a list of customer reviews, each with five stars",
    "lsabadge": "a green shield badge with a white checkmark in the center, a guaranteed verified badge",
    "mousetrap": "a wooden mousetrap with a piece of cheese on it, set and ready",
    "moneyfire": "a dollar bill on fire with flames coming off it, burning money",
    "target": "a bullseye target with rings and a dart stuck in the center",
    "googleads": "a smartphone search results screen with a sponsored ad box highlighted at the very top",
    "searchbar": "a long web search bar input box with a magnifying glass icon at the right end",
    "seedling": "a small green plant seedling with two leaves sprouting up from a little mound of soil",
    "aiscreen": "a smartphone showing a chatbot conversation, a robot icon and a speech answer bubble",
    "scorecard": "a report card dashboard sheet with several rows, each row a label line and a colored status dot",
    "trafficlight": "a traffic light signal with a red, a yellow, and a green light stacked",
}


def key_bg(png_in, out):
    im = Image.open(png_in).convert("RGB")
    a = np.array(im).astype(int)
    h, w = a.shape[:2]
    # bg = median of the four corner patches
    c = 26
    corners = np.concatenate([a[:c, :c].reshape(-1, 3), a[:c, -c:].reshape(-1, 3),
                              a[-c:, :c].reshape(-1, 3), a[-c:, -c:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))
    mask = dist < 72                       # bg pixels -> transparent
    rgba = np.dstack([np.array(im), np.where(mask, 0, 255).astype(np.uint8)])
    img = Image.fromarray(rgba, "RGBA")
    # tight crop to content
    al = np.array(img)[..., 3]; ys, xs = np.where(al > 16)
    if len(xs):
        img = img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    img.save(out)


def main():
    only = sys.argv[1:] or list(PROPS)         # optional: regenerate just named props
    for pid in only:
        prompt = PROPS[pid]
        webp, how = RC.generate(prompt + DOODLE, style_id=STYLE_ID, size="1024x1024")
        raw = os.path.join(ASSETS, pid + "_raw.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", webp, raw], check=True)
        key_bg(raw, os.path.join(ASSETS, pid + ".png"))
        os.remove(raw)
        print(f"  {pid}: {how} -> keyed PNG")
    print("doodle props ready")


if __name__ == "__main__":
    main()
