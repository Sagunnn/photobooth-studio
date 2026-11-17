#!/usr/bin/env python3
"""Generate blank photobooth grid templates.

Each grid is saved to its own folder:
    Generated Templates/<name>/<name>.png     the frame (photo slots are see-through)
    Generated Templates/<name>/<name>_preview.png   grey slots + print guides drawn on, easy to eyeball
    Generated Templates/<name>/slots.json     pixel position of every photo slot

Usage:
    python3 tools/make_templates.py                      # build every grid in grids.json
    python3 tools/make_templates.py 4-cut 8-cut          # build only these
    python3 tools/make_templates.py --rows 3 --cols 1 --name 3-cut-strip   # one-off grid
    python3 tools/make_templates.py --rows 3 --cols 1 --name 3-cut-strip --save   # ...and add it to grids.json
    python3 tools/make_templates.py 4-cut --background-image Backgrounds/flowers.jpg   # use an image as the frame background
    python3 tools/make_templates.py --rows 4 --cols 1 --cut vertical --name my-strips  # two matching strips, cut down the middle

background_image (in grids.json or --background-image) is scaled to cover the whole frame;
paths are relative to this folder. Without it, the solid "background" colour is used.
bg_gradient (instead of a plain colour), e.g.
    {"type": "corners", "colors": ["#4B4FCF", "#C5527A", "#3EB8D3", "#B9AE6E"]}   one colour per corner (TL, TR, BL, BR)
    {"type": "linear", "colors": ["#FFD3A5", "#FD6585"], "angle": 160}             angle like CSS: 0 = up, 90 = right
    {"type": "radial", "colors": ["#FBC2EB", "#A6C1EE"]}                           from the centre outwards
bg_opacity (0-100) fades the image so the background colour shows through it.
text_shadow = caption shadow, e.g. {"color": "#000000", "angle": 45, "dist": 14, "blur": 18, "opacity": 55}
    angle: 0 = to the right, 90 = down; blur is a Gaussian blur like the app's
texture = paper texture over the background, e.g. {"type": "linen", "strength": 60}
    types: matte, linen, watercolor, kraft, canvas, recycled (identical to the app's)
bg_fit "cover" (fill and crop), "stretch" (exact page size) or "contain" (whole image);
bg_rotate (degrees), bg_zoom (%, 100 = as fitted), bg_x / bg_y (% of the page to move it).

machine (optional, e.g. "G14") puts that grid's output in Generated Templates/<machine>/<name>/.

Print settings (match the guides in the PSDs):
    bleed      trim line distance from every edge (45px)
    cut        "none", "vertical" (left | right strips) or "horizontal" (top / bottom strips)
    cut_gap    space across the cut line, half on each side (90px = guides at 915 / 960 / 1005)
    With a cut, rows x cols are per half, and the caption + background repeat in each half.

Style:
    radius     rounded corners on the photo slots, in px (0 = square)
    radius_corners [top left, top right, bottom right, bottom left] true/false: which corners are rounded (all if missing)
    line_frame {"color": "#c8a45c", "finish": "" | "gold" | "silver" | "rosegold", "width": 4, "page": true, "inset": 24,
               "photos": true, "gap": 10, "double": false, "round": 0}: fine lines like an invitation card. "page" = a line "inset"
               px inside the print guides (never in the bleed); "photos" = a line round every photo with "gap" px of
               background between; "double" adds a second line beside each; "round" = corner roundness (0 = sharp)
    post       {"name": "photobooth", "place": "Photo Booth", "likes": "1,234", "caption": "...", "when": "JUST NOW",
               "dark": false, "card": true, "verified": true}: social media post look. A card behind the photos, the
               account name above them when there's room, and like / comment / share icons, likes, the caption and
               the time in the biggest free space below (or beside) the photos
    rails      {"rail": "#c9ced6", "sleeper": "#7a5636", "gauge": 26, "pitch": 120, "overhang": 70, "couplers": true}:
               a railway track seen from above under every line of photos (top-view train look): sleepers every
               "pitch" px, rails "gauge" px outside the photos, couplings in the gaps between photos
    slot_stamp {"where": "photos" | "edge", "color": "#ffffff", "width": 30, "hole": 14, "shadow": true}: postage-stamp
               edges. "photos" = each photo on stamp paper ("width" px around it) with perforated edges; "edge" =
               holes along the trim line of every strip, the bleed in "color" ("transparent" = see-through)
    film       true = film-reel look: sprocket holes down both long edges of every strip
    film_band  width of the sprocket-hole edge (110px); photos move inward to make room
    film_holes hole colour ("#FFFFFF", or "transparent")
    slot_border {"color": "#ffffff", "width": 14, "pos": "inside" | "outside"}: a line around every photo
    slot_shape  "rect" (rounded by radius) | "circle" | "oval" | "arch" (round top, radius rounds the bottom corners)
                | "tv" (an old TV screen: a squircle filling the slot)
    slot_tv     {"bezel": "#2a2a2c", "bezel_w": 60, "scan": 35, "tint": 30, "tint_color": "#9fd4b0", "vignette": 55,
                 "static": 35, "glitch": true, "text1": "REC", "text2": "00:03:82 230", "seed": 1}: retro TV look, a dark
                casing round each photo and see-through screen effects over it (scanlines, tint, dark edges, static,
                a glitch block, on-screen text). bezel_w is the casing's thickness: what doesn't fit between the photos
                covers the photo's edge instead (a smaller screen)
    slot_shadow {"color", "angle", "dist", "blur", "opacity", "where": "inner" | "outer"}: "inner" = the frame edge's
                shadow falls onto the photo (depth, like behind glass); "outer" = a shadow around the photo, on the frame
    slot_glass  0-100: a soft diagonal glass/mirror shine across each photo
    slot_bubbles {"count": 6, "size": 22 (% of the photo), "seed": 1, "inside": true, "edge": null | 10-45}: soap bubbles
                over the photos; "edge" keeps them within that % of the photo from its edges (faces stay clear)
    slot_border can also have "bevel": true (light top-left, shade bottom-right: a raised 3D border) and
                "finish": "gold" | "silver" | "rosegold" (a metallic foil instead of the plain colour)
    circle_size 0-100: circles from "fits the slot" (0) up to the largest that stays inside the trim guides
                (and the cut line), up to where circles meet (100)
    bg_stripes  {"type": "stripes" | "checks" | "gingham", "color": "#ffffff", "color2": "#000000" or null (see-through),
                 "size": 80, "width": 50 (% stripe), "angle": 45, "opacity": 60}: drawn over the background colour/gradient
    film_split true (default) = on a layout that isn't cut with 2 photo columns across the film (2 rows on a
               landscape page), each half gets its own film edges like a cut print: holes down the middle too
    film_band up to the free space beside the photos never moves them. On 1-2 column layouts a wider
    film_band makes the photos narrower (same height and position); with 3+ columns, or exact "slots",
    the film edge stays in the free space so photos never move.

pattern (optional, made in the app) = PNGs from Stickers/ scattered behind the photos:
    {"items": ["m:star.png", ...], "size": 180, "gap": 80, "scatter": 60, "rotate": 25, "vary": 25,
     "opacity": 100, "seed": 1, "per_half": true}
    Same seed = same arrangement as in the app. (Built-in graphics/emoji items are app-only.)

slots (optional) = exact photo positions [[x, y, width, height], ...], e.g. from a template imported
in the app. When given, rows/cols/margin/gap/header/footer are not used for placing photos.
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent.parent   # the templates folder (this script lives in tools/)
CONFIG = HERE / "grids.json"
OUT_DIR = HERE / "Generated Templates"
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
BUILT_IN = {"background": "#000000", "background_image": "", "slot": "transparent", "text": "",
            "text_color": "#FFFFFF", "text_size": 110, "bleed": 45, "cut": "none", "cut_gap": 90,
            "bg_per_half": True, "machine": "", "radius": 0, "film": False, "film_band": 110,
            "film_holes": "#FFFFFF", "film_split": True, "slot_border": None, "slot_shape": "rect", "circle_size": 0, "bg_stripes": None, "slot_shadow": None, "slot_glass": None, "slot_bubbles": None, "radius_corners": None, "slot_stamp": None, "rails": None, "slot_tv": None, "post": None, "line_frame": None, "text_shadow": None, "texture": None, "bg_gradient": None, "bg_opacity": 100, "bg_fit": "cover", "bg_rotate": 0, "bg_zoom": 100,
            "bg_x": 0, "bg_y": 0}


def color(value):
    if value == "transparent":
        return (0, 0, 0, 0)
    return ImageColor.getcolor(value, "RGBA")


def load_font(size):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def rnd(v):
    """Round half up (same as Math.round in the app)."""
    return math.floor(v + 0.5)


def strip_sides(g, half):
    """The two long edges of a strip (where film holes go) -> distance from that edge to the trim line."""
    b = g["bleed"]   # outer edge is trimmed at the bleed guide; the cut side at the cut line
    if g["cut"] == "vertical":
        return {"l": b, "r": 0} if half == 0 else {"l": 0, "r": b}
    if g["cut"] == "horizontal":
        return {"t": b, "b": 0} if half == 0 else {"t": 0, "b": b}
    return {"l": b, "r": b} if g["height"] >= g["width"] else {"t": b, "b": b}


def regions(g):
    """The whole page, or two matching halves when it will be cut.
    Returns (x, y, w, h, inset_left, inset_right, inset_top, inset_bottom) for each."""
    W, H, m, c = g["width"], g["height"], g["margin"], g["cut_gap"] / 2
    start, end = m + g["header"], g["footer"] or m
    # photo slots exactly as in the original templates (outer margin m, cut-side margin c)
    if g["cut"] == "vertical":
        out = [(0, 0, W / 2, H, m, c, start, end), (W / 2, 0, W / 2, H, c, m, start, end)]
    elif g["cut"] == "horizontal":   # strip ends (header/footer) are left/right here
        out = [(0, 0, W, H / 2, start, end, m, c), (0, H / 2, W, H / 2, start, end, c, m)]
    else:
        out = [(0, 0, W, H, m, m, start, end)]
    if g["film"] and film_can_widen(g):   # a film edge wider than the free space makes photos narrower
        band = film_band(g)
        for half, (x, y, w, h, *ins) in enumerate(out):
            ins = dict(zip("lrtb", ins))
            for side, trim in strip_sides(g, half).items():
                ins[side] = max(ins[side], trim + band)
            out[half] = (x, y, w, h, *ins.values())
    return out


def strip_areas(g):
    """Cut prints: strip 1 = left guide -> cut line, strip 2 = cut line -> right guide. The left strip loses the
    bleed when trimmed, so strip 2's background starts that many pixels into the same image (moved by half the
    page minus the bleed). print = inside the guides, area = print plus bleed both sides, clip = its half."""
    b, W, H = g["bleed"], g["width"], g["height"]
    if g["cut"] == "vertical":
        S = W / 2 - b
        return [{"clip": (h * W / 2, 0, W / 2, H), "print": (W / 2 if h else b, 0, S, H),
                 "area": ((W / 2 if h else b) - b, 0, S + 2 * b, H)} for h in (0, 1)]
    if g["cut"] == "horizontal":
        S = H / 2 - b
        return [{"clip": (0, h * H / 2, W, H / 2), "print": (0, H / 2 if h else b, W, S),
                 "area": (0, (H / 2 if h else b) - b, W, S + 2 * b)} for h in (0, 1)]
    return [{"clip": (0, 0, W, H), "print": (b, b, W - 2 * b, H - 2 * b), "area": (0, 0, W, H)}]


def paste_area(img, piece, area, clip):
    """Paste an area-sized piece, keeping only the part inside clip."""
    ax, ay = round(area[0]), round(area[1])
    cx, cy, cw, ch = (round(v) for v in clip)
    img.alpha_composite(piece.crop((cx - ax, cy - ay, cx - ax + cw, cy - ay + ch)), (cx, cy))


def half_of(g, x0, y0, x1, y1):
    if g["cut"] == "vertical":
        return 0 if (x0 + x1) / 2 < g["width"] / 2 else 1
    if g["cut"] == "horizontal":
        return 0 if (y0 + y1) / 2 < g["height"] / 2 else 1
    return 0


def slot_boxes(g):
    """Split each region into rows x cols equal slots (or use the exact "slots" list).
    Returns [(x0, y0, x1, y1, half)]."""
    if g.get("slots"):
        boxes = [(x, y, x + w, y + h) for x, y, w, h in g["slots"]]
        return sorted(((*b, half_of(g, *b)) for b in boxes), key=lambda b: b[4])
    boxes = []
    split = film_split(g)
    parts = [(R, c, r) for R, c, r, _ in split_regions(g)] if split else [(R, g["cols"], g["rows"]) for R in regions(g)]
    def size(R, cols, rows):
        rx, ry, rw, rh, l, r, t, b = R
        return int((rw - l - r - g["gap"] * (cols - 1)) // cols), int((rh - t - b - g["gap"] * (rows - 1)) // rows)
    # two film strips: the same photo size in both (the smaller), centred in each strip's free space
    same = (min(size(*p)[0] for p in parts), min(size(*p)[1] for p in parts)) if split else None
    for half, ((rx, ry, rw, rh, l, r, t, b), cols, rows) in enumerate(parts):
        slot_w, slot_h = same or size((rx, ry, rw, rh, l, r, t, b), cols, rows)
        if slot_w <= 10 or slot_h <= 10:
            sys.exit(f"[{g['name']}] margins/gaps/header/footer leave no room for photos")
        ox = math.floor((rw - l - r - cols * slot_w - g["gap"] * (cols - 1)) / 2) if split else 0
        oy = math.floor((rh - t - b - rows * slot_h - g["gap"] * (rows - 1)) / 2) if split else 0
        # an even pitch, positions rounded (half up, like the app): a spare pixel goes into a gap, like templates
        # made in Photoshop, so the margins stay exactly as set
        px = slot_w + g["gap"] if split else (rw - l - r + g["gap"]) / cols
        py = slot_h + g["gap"] if split else (rh - t - b + g["gap"]) / rows
        for row in range(rows):
            for col in range(cols):
                x = math.floor(rx + l + ox + col * px + 0.5)
                y = math.floor(ry + t + oy + row * py + 0.5)
                boxes.append((x, y, x + slot_w, y + slot_h, 0 if split else half))
    if split:
        boxes.sort(key=lambda b: (b[1], b[0]))   # photo order stays row by row
    return boxes


def band_center(g, region, half_boxes, half=0):
    """Centre of the caption/logo strip in one half (across the strip: the middle of the printed strip)."""
    rx, ry, rw, rh = region[:4]
    px, py, pw, ph = strip_areas(g)[half]["print"] if g["cut"] != "none" else (rx, ry, rw, rh)
    first, last = half_boxes[0], half_boxes[-1]
    footer_side = g["footer"] >= g["header"]
    if g.get("slots"):   # exact slots: use whichever end has more free space
        footer_side = (rx + rw - last[2] >= first[0] - rx) if g["cut"] == "horizontal" \
            else (ry + rh - last[3] >= first[1] - ry)
    if g["cut"] == "horizontal":
        a, z = (last[2], rx + rw) if footer_side else (rx, first[0])
        return (a + z) / 2, py + ph / 2
    a, z = (last[3], ry + rh) if footer_side else (ry, first[1])
    return px + pw / 2, (a + z) / 2


def draw_text(img, g, boxes):
    if not g.get("text"):
        return
    font = load_font(g["text_size"])
    for half, region in enumerate(regions(g)):
        cx, cy = band_center(g, region, [b for b in boxes if b[4] == half], half)
        # draw on its own layer so it can be rotated for top/bottom-cut strips
        l, t, r, b = font.getbbox(g["text"])
        layer = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((10 - l, 10 - t), g["text"], font=font, fill=color(g["text_color"]))
        if g["cut"] == "horizontal":
            layer = layer.rotate(90, expand=True)   # reads upright when the strip is held vertically
        x0, y0 = round(cx - layer.width / 2), round(cy - layer.height / 2)
        sh = g.get("text_shadow")
        if sh:   # soft shadow: the text's shape, tinted, blurred and moved (blur like the app: sigma = blur / 2)
            pad = int(sh["blur"] * 1.5 + sh["dist"] + 4)
            shape = Image.new("L", (layer.width + 2 * pad, layer.height + 2 * pad), 0)
            shape.paste(layer.getchannel("A"), (pad, pad))
            if sh["blur"] > 0:
                shape = shape.filter(ImageFilter.GaussianBlur(sh["blur"] / 2))
            shape = shape.point(lambda v: v * sh.get("opacity", 55) // 100)
            shadow = Image.new("RGBA", shape.size, color(sh["color"])); shadow.putalpha(shape)
            a = math.radians(sh["angle"])
            sx, sy = x0 - pad + rnd(math.cos(a) * sh["dist"]), y0 - pad + rnd(math.sin(a) * sh["dist"])
            canvas = Image.new("RGBA", img.size, (0, 0, 0, 0)); canvas.paste(shadow, (sx, sy))
            img.alpha_composite(canvas)
        img.alpha_composite(layer, (x0, y0))


def slot_shadow(img, g, boxes):
    """A soft shadow around every photo window (around an outside border too). Drawn before the windows are cut out,
    so it only shows on the frame. Blur like the app: sigma = blur / 2."""
    sh = g["slot_shadow"]
    if sh.get("where", "inner") != "outer":
        return
    sb = g.get("slot_border") or {}
    out = sb.get("width", 0) if sb.get("pos") == "outside" else 0
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    for x0, y0, x1, y1, _ in boxes:
        draw_shape(d, (x0 - out, y0 - out, x1 - 1 + out, y1 - 1 + out), g["radius"] + out, g.get("slot_shape", "rect"), 255, g.get("radius_corners"))
    if sh.get("blur", 0) > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(sh["blur"] / 2))
    mask = mask.point(lambda v: v * sh.get("opacity", 55) // 100)
    shadow = Image.new("RGBA", img.size, color(sh.get("color", "#000000")))
    shadow.putalpha(mask)
    a = math.radians(sh.get("angle", 45))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer.paste(shadow, (rnd(math.cos(a) * sh.get("dist", 14)), rnd(math.sin(a) * sh.get("dist", 14))))
    img.alpha_composite(layer)


def window_of(box, g):
    """The photo's visible window: inside an inside border, else the slot itself. Returns (box, radius)."""
    (x0, y0, x1, y1), r = tv_screen(box, g)
    sb = g.get("slot_border")
    if sb and sb.get("pos", "inside") != "outside":
        w = sb.get("width", 14)
        return (x0 + w, y0 + w, x1 - w, y1 - w), max(0, r - w)
    return (x0, y0, x1, y1), r


def tv_split(g, boxes):
    """Retro TV casing: as much as fits between the photos goes round them (out), the rest covers the photo's
    edge (ins). Like the app."""
    tv = g.get("slot_tv")
    bw = tv.get("bezel_w", 0) if tv else 0
    if not bw:
        return 0, 0
    m = math.inf
    for i, a in enumerate(boxes):
        for j, b in enumerate(boxes):
            if i != j and a[4] == b[4]:
                dx, dy = max(b[0] - a[2], a[0] - b[2]), max(b[1] - a[3], a[1] - b[3])
                if dx >= 0 and dy < 0:
                    m = min(m, dx)
                if dy >= 0 and dx < 0:
                    m = min(m, dy)
    room = int(m // 2) - 2 if m != math.inf else math.inf
    areas = strip_areas(g)
    cut = g["cut"] in ("vertical", "horizontal")
    for x0, y0, x1, y1, half in boxes:   # and only half-way to the print's edge
        px, py, pw, ph = areas[half if cut else 0]["print"]
        room = min(room, math.floor(min(x0 - px, y0 - py, px + pw - x1, py + ph - y1) / 2))
    out = min(bw, max(0, room))
    return out, bw - out


def tv_screen(box, g):
    """The screen left inside a TV casing that covers the photo's edge. Returns (box, radius)."""
    i = g.get("_tv", (0, 0))[1]
    x0, y0, x1, y1 = box[:4]
    if not i:
        return (x0, y0, x1, y1), g["radius"]
    return (x0 + i, y0 + i, x1 - i, y1 - i), max(0, g["radius"] - i)


GLASS_STOPS = [(0, 0), (0.16, 0.6), (0.3, 0), (0.42, 0), (0.47, 0.28), (0.53, 0), (1, 0)]


def slot_depth(img, g, boxes):
    """Depth on the photo: the frame edge's shadow falling onto it ("inner" slot_shadow) and a glass shine.
    Both are see-through layers over the photo window."""
    import numpy as np
    sh = g.get("slot_shadow")
    sh = sh if sh and sh.get("where", "inner") == "inner" else None
    glass = g.get("slot_glass")
    if not sh and not glass:
        return
    shape = g.get("slot_shape", "rect")
    for b in boxes:
        (a0, b0, a1, b1), r = window_of(b[:4], g)
        w, h = a1 - a0, b1 - b0
        if w <= 0 or h <= 0:
            continue
        s = 4
        big = Image.new("L", (w * s, h * s), 0)
        draw_shape(ImageDraw.Draw(big), (0, 0, w * s - 1, h * s - 1), r * s, shape, 255, g.get("radius_corners"))
        M = big.resize((w, h), Image.LANCZOS)
        Mf = np.asarray(M, np.float32) / 255
        if sh:   # everything outside the window casts the shadow; keep the part that lands inside it
            pad = int(sh.get("blur", 18) * 1.5 + sh.get("dist", 14) + 4)
            F = Image.new("L", (w + 2 * pad, h + 2 * pad), 255)
            F.paste(Image.new("L", (w, h), 0), (pad, pad), M)
            a = math.radians(sh.get("angle", 45))
            S = Image.new("L", F.size, 255)
            S.paste(F, (rnd(math.cos(a) * sh.get("dist", 14)), rnd(math.sin(a) * sh.get("dist", 14))))
            if sh.get("blur", 0) > 0:
                S = S.filter(ImageFilter.GaussianBlur(sh["blur"] / 2))
            A = np.asarray(S.crop((pad, pad, pad + w, pad + h)), np.float32) / 255 * Mf * sh.get("opacity", 55) / 100
            layer = np.zeros((h, w, 4), np.uint8)
            layer[..., :3] = color(sh.get("color", "#000000"))[:3]
            layer[..., 3] = np.clip(A * 255 + 0.5, 0, 255).astype(np.uint8)
            img.alpha_composite(Image.fromarray(layer, "RGBA"), (a0, b0))
        if glass:   # soft white bands along the diagonal (same stops as the app)
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
            t = (xx * w + yy * h) / (w * w + h * h)
            A = np.interp(t, [o for o, _ in GLASS_STOPS], [v for _, v in GLASS_STOPS]) * glass / 100 * Mf
            layer = np.full((h, w, 4), 255, np.uint8)
            layer[..., 3] = np.clip(A * 255 + 0.5, 0, 255).astype(np.uint8)
            img.alpha_composite(Image.fromarray(layer, "RGBA"), (a0, b0))


def soap_bubble(img, cx, cy, r, clip=None):
    """A soap bubble like the app's: clear middle, bright rim with a rainbow sheen, highlight. clip = (mask, x, y)."""
    import numpy as np
    x0, y0 = max(0, math.floor(cx - r - 2)), max(0, math.floor(cy - r - 2))
    x1, y1 = min(img.width, math.ceil(cx + r + 2)), min(img.height, math.ceil(cy + r + 2))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64) + 0.5
    dx, dy = xx - cx, yy - cy
    d = np.hypot(dx, dy)
    disc = np.clip(r - d + 0.5, 0, 1)
    t = np.clip((d - 0.2 * r) / (0.8 * r), 0, 1)
    layers = [(np.full(d.shape + (3,), 255.0), np.interp(t, [0, 0.8, 0.96, 1], [0.04, 0.14, 0.55, 0]) * disc)]
    lw = max(2, r * 0.05)
    ring = np.clip(lw / 2 - np.abs(d - r * 0.97) + 0.5, 0, 1)
    sdiag = np.clip((dx + r + dy + r) / (4 * r), 0, 1)
    rim = np.stack([np.interp(sdiag, [0, 0.5, 1], c) for c in ([255, 120, 255], [120, 220, 230], [200, 255, 120])], -1)
    layers.append((rim, np.interp(sdiag, [0, 0.5, 1], [0.35, 0.3, 0.35]) * ring))
    th = -0.7
    ex, ey = dx + 0.42 * r, dy + 0.45 * r
    u, v = ex * math.cos(th) + ey * math.sin(th), -ex * math.sin(th) + ey * math.cos(th)
    rx, ry = 0.22 * r, 0.11 * r
    q = np.sqrt((u / rx) ** 2 + (v / ry) ** 2)
    layers.append((np.full(d.shape + (3,), 255.0), 0.75 * np.clip((1 - q) * ry + 0.5, 0, 1)))
    dd = np.hypot(dx - 0.45 * r, dy - 0.4 * r)
    layers.append((np.full(d.shape + (3,), 255.0), 0.75 * np.clip(0.05 * r - dd + 0.5, 0, 1)))
    cm = None
    if clip is not None:
        mask, mx, my = clip
        cm = np.zeros(d.shape)
        sub = np.asarray(mask, np.float64) / 255
        ax0, ay0 = max(x0, mx), max(y0, my)
        ax1, ay1 = min(x1, mx + mask.width), min(y1, my + mask.height)
        if ax1 > ax0 and ay1 > ay0:
            cm[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] = sub[ay0 - my:ay1 - my, ax0 - mx:ax1 - mx]
    for rgb, a in layers:
        if cm is not None:
            a = a * cm
        layer = np.zeros(d.shape + (4,), np.uint8)
        layer[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
        layer[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
        img.alpha_composite(Image.fromarray(layer, "RGBA"), (x0, y0))


def slot_bubbles(img, g, boxes):
    """Soap bubbles over the photos, placed like the app (the same in both strips of a cut print)."""
    bb = g.get("slot_bubbles")
    if not bb:
        return
    seen = {}
    for b in boxes:
        half = b[4]
        seen[half] = k = seen.get(half, -1) + 1
        (a0, b0, a1, b1), r = window_of(b[:4], g)
        w, h = a1 - a0, b1 - b0
        if w <= 0 or h <= 0:
            continue
        clip = None
        if bb.get("inside", True):
            s = 4
            big = Image.new("L", (w * s, h * s), 0)
            draw_shape(ImageDraw.Draw(big), (0, 0, w * s - 1, h * s - 1), r * s, g.get("slot_shape", "rect"), 255, g.get("radius_corners"))
            clip = (big.resize((w, h), Image.LANCZOS), a0, b0)
        elif g["cut"] in ("vertical", "horizontal"):   # a cut print: bubbles stop at the cut line
            cx_, cy_, cw_, ch_ = (round(v) for v in strip_areas(g)[half]["clip"])
            clip = (Image.new("L", (cw_, ch_), 255), cx_, cy_)
        rnd_ = mulberry32(bb.get("seed", 1) * 1000 + k + 1)
        max_r = bb.get("size", 22) / 100 * min(w, h)
        e = (bb.get("edge") or 0) / 100
        shape = g.get("slot_shape", "rect")

        def near_edge(cx, cy):   # "edges only": within the band from the photo's edge (curved for circles and ovals)
            if shape in ("circle", "oval"):
                n = math.hypot((cx - a0 - w / 2) / (w / 2), (cy - b0 - h / 2) / (h / 2))
                return 1 - 2 * e <= n <= 1
            return cx - a0 <= e * w or a0 + w - cx <= e * w or cy - b0 <= e * h or b0 + h - cy <= e * h

        for _ in range(bb.get("count", 6)):
            tries = 0
            while True:
                cx, cy = a0 + rnd_() * w, b0 + rnd_() * h
                tries += 1
                if not e or near_edge(cx, cy) or tries >= 200:
                    break
            rr = max_r * (0.25 + 0.75 * rnd_() ** 1.6)
            soap_bubble(img, cx, cy, rr, clip)


def circle_boxes(g, boxes):
    """Circle windows: each photo area becomes the circle's square. circle_size 0 = biggest circle inside the slot,
    100 = as big as possible inside the trim guides / cut line, up to where circles meet."""
    if g.get("slot_shape") != "circle":
        return boxes
    rnd_ = lambda v: math.floor(v + 0.5)
    strips = strip_areas(g)
    sb = g.get("slot_border") or {}
    border = sb.get("width", 0) if sb.get("pos") == "outside" else 0
    r0 = r_max = math.inf
    for b in boxes:
        x0, y0, x1, y1, half = b
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        px, py, pw, ph = (strips[half] if half < len(strips) else strips[0])["print"]
        r0 = min(r0, min(x1 - x0, y1 - y0) / 2)
        lim = min(cx - px, px + pw - cx, cy - py, py + ph - cy) - border
        for o in boxes:
            if o is not b and o[4] == half:
                lim = min(lim, math.hypot((o[0] + o[2]) / 2 - cx, (o[1] + o[3]) / 2 - cy) / 2 - border)
        r_max = min(r_max, lim)
    r_max = max(r0, r_max)
    r = rnd_(r0 + (r_max - r0) * max(0, min(100, g.get("circle_size", 0))) / 100)
    out = []
    for x0, y0, x1, y1, half in boxes:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = rnd_(cx - r), rnd_(cy - r)
        out.append((nx, ny, nx + 2 * r, ny + 2 * r, half))
    return out


def tv_points(x, y, w, h):
    """An old TV screen: a squircle (|x|^4.5 + |y|^4.5 = 1) filling the box, like the app."""
    n, cx, cy = 2 / 4.5, x + w / 2, y + h / 2
    f = lambda v: math.copysign(abs(v) ** n, v)
    return [(cx + w / 2 * f(math.cos(t)), cy + h / 2 * f(math.sin(t))) for t in (i / 256 * 2 * math.pi for i in range(256))]


def draw_shape(d, q, r, shape, fill, corners=None):
    """One photo window outline (x0, y0, x1, y1 inclusive) on an ImageDraw: rect (rounded), circle, oval or arch.
    corners = which corners are round (top left, top right, bottom right, bottom left); None = all."""
    corners = tuple(bool(c) for c in corners) if corners else None
    x0, y0, x1, y1 = q
    w, h = x1 - x0 + 1, y1 - y0 + 1
    if w <= 0 or h <= 0:
        return
    if shape == "oval" or (shape == "arch" and h < w / 2):
        d.ellipse(q, fill=fill)
    elif shape == "tv":
        d.polygon(tv_points(x0, y0, w, h), fill=fill)
    elif shape == "circle":
        c = min(w, h) / 2
        cx, cy = x0 + w / 2, y0 + h / 2
        d.ellipse((cx - c, cy - c, cx + c - 1, cy + c - 1), fill=fill)
    elif shape == "arch":
        R = w / 2
        rb = max(0, min(r, R, h - R))
        d.pieslice((x0, y0, x1, y0 + w - 1), 180, 360, fill=fill)   # the round top only
        d.rounded_rectangle((x0, y0 + R, x1, y1), radius=rb, fill=fill, corners=(True, True) + corners[2:] if corners else None)
        d.rectangle((x0, y0 + R, x1, y0 + R + rb), fill=fill)
    else:
        d.rounded_rectangle(q, radius=max(0, min(r, w / 2, h / 2)), fill=fill, corners=corners)


def stripes_image(sp, w, h):
    """Stripes / checks / gingham in one colour, as an RGBA piece the size of the area (smooth edges)."""
    import numpy as np
    size, a = max(4, round(sp.get("size", 80))), math.radians(sp.get("angle", 0))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    u, v = xx * math.cos(a) + yy * math.sin(a), -xx * math.sin(a) + yy * math.cos(a)
    def band(t, width, period):   # how much of each pixel is inside [0, width) of every period
        m = np.mod(t, period)
        dist = np.where(m < width, np.minimum(m, width - m), -np.minimum(m - width, period - m))
        return np.clip(dist + 0.5, 0, 1)
    kind = sp.get("type")
    if kind == "checks":
        cu, cv = band(u, size, 2 * size), band(v, size, 2 * size)
        alpha = cu * (1 - cv) + (1 - cu) * cv
    elif kind == "gingham":
        bw = round(size / 2)
        alpha = 1 - (1 - 0.5 * band(u, bw, size)) * (1 - 0.5 * band(v, bw, size))
    else:
        alpha = band(u, max(1, round(size * sp.get("width", 50) / 100)), size)
    op = sp.get("opacity", 60) / 100
    r, g_, b, _ = color(sp.get("color", "#ffffff"))
    out = np.zeros((h, w, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = r, g_, b
    out[..., 3] = np.clip(alpha * op * 255 + 0.5, 0, 255).astype(np.uint8)
    piece = Image.fromarray(out, "RGBA")
    if sp.get("color2"):   # the second colour fills the gaps (under the stripes)
        base = Image.new("RGBA", (w, h), color(sp["color2"])[:3] + (round(op * 255),))
        base.alpha_composite(piece)
        piece = base
    return piece


METALS = {
    "gold": ["#7a5a1e", "#f6e27a", "#c9a14a", "#fff4c2", "#b8862b", "#f2d16b", "#7a5a1e"],
    "silver": ["#6b7280", "#f3f4f6", "#a1a1aa", "#ffffff", "#8b8f99", "#e5e7eb", "#6b7280"],
    "rosegold": ["#8a4b3c", "#f6c9b5", "#c98f74", "#ffe6da", "#b06f5a", "#f1b9a3", "#8a4b3c"],
}


def slot_border(img, box, radius, sb, shape="rect", corners=None):
    """A coloured line around a photo slot: "inside" sits on the slot's edge, "outside" goes around it.
    Follows the rounded corners; drawn 4x bigger and shrunk for smooth edges."""
    x0, y0, x1, y1 = box
    w = max(1, sb.get("width", 14))
    out = sb.get("pos", "inside") == "outside"
    o = (x0 - w, y0 - w, x1 + w, y1 + w) if out else (x0, y0, x1, y1)
    i = (x0, y0, x1, y1) if out else (x0 + w, y0 + w, x1 - w, y1 - w)
    ro, ri = (radius + w, radius) if out else (radius, max(0, radius - w))
    s, (ox, oy) = 4, o[:2]
    big = Image.new("L", ((o[2] - o[0]) * s, (o[3] - o[1]) * s), 0)
    d = ImageDraw.Draw(big)
    def rr(q, r, fill):
        q = [(q[0] - ox) * s, (q[1] - oy) * s, (q[2] - ox) * s - 1, (q[3] - oy) * s - 1]
        if q[2] > q[0] and q[3] > q[1]:
            draw_shape(d, q, r * s, shape, fill, corners)
    rr(o, ro, 255)
    rr(i, ri, 0)
    mask = big.resize((o[2] - o[0], o[3] - o[1]), Image.LANCZOS)
    piece = Image.new("RGBA", mask.size, color(sb.get("color", "#ffffff")))
    if sb.get("finish") in METALS:   # metallic foil: light and dark bands along the diagonal (like the app)
        import numpy as np
        W_, H_ = mask.size
        yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32) + 0.5
        t = (xx * W_ + yy * H_) / (W_ * W_ + H_ * H_)
        stops = [color(c) for c in METALS[sb["finish"]]]
        pos = [i / (len(stops) - 1) for i in range(len(stops))]
        arr = np.zeros((H_, W_, 4), np.uint8)
        for ch in range(3):
            arr[..., ch] = np.clip(np.interp(t, pos, [c[ch] for c in stops]) + 0.5, 0, 255).astype(np.uint8)
        arr[..., 3] = 255
        piece = Image.fromarray(arr, "RGBA")
    if sb.get("bevel"):   # raised look: light from the top-left, shade towards the bottom-right (like the app)
        import numpy as np
        W_, H_ = mask.size
        yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32) + 0.5
        t = (xx * W_ + yy * H_) / (W_ * W_ + H_ * H_)
        light = np.clip(0.6 * (1 - 2 * t), 0, 1)[..., None]
        shade = np.clip(0.45 * (2 * t - 1), 0, 1)[..., None]
        c = np.asarray(piece, np.float32)[..., :3]
        c = c * (1 - light) + 255 * light
        c = c * (1 - shade)
        arr = np.asarray(piece).copy()
        arr[..., :3] = np.clip(c + 0.5, 0, 255).astype(np.uint8)
        piece = Image.fromarray(arr, "RGBA")
    img.paste(piece, (ox, oy), mask)


def guide_rects(g):
    """Each printed strip as it comes out of the cutter (x, y, w, h): inside the trim guides all round and up to the
    cut line. Like the app."""
    b, W, H = g["bleed"], g["width"], g["height"]
    if g["cut"] == "vertical":
        return [(b, b, W / 2 - b, H - 2 * b), (W / 2, b, W / 2 - b, H - 2 * b)]
    if g["cut"] == "horizontal":
        return [(b, b, W - 2 * b, H / 2 - b), (b, H / 2, W - 2 * b, H / 2 - b)]
    return [(b, b, W - 2 * b, H - 2 * b)]


def line_frame(img, g, boxes):
    """Fine lines like an invitation card: one inside the trim guides (never in the bleed or past the cut line) and one round every photo
    with a gap; optionally doubled. Like the app."""
    lf = g.get("line_frame")
    if not lf:
        return
    w = max(1, lf.get("width", 4))
    dd = rnd(2.5 * w)
    rr = max(0, lf.get("round") or 0)   # 0 = sharp corners
    sb = {"width": w, "pos": "outside", "color": lf.get("color", "#c8a45c"), "finish": lf.get("finish") or None}
    cut = g["cut"] in ("vertical", "horizontal")
    bsb = g.get("slot_border")
    out = bsb["width"] if bsb and bsb.get("pos") == "outside" else 0
    shape, corners = g.get("slot_shape", "rect"), g.get("radius_corners")
    for half, (px, py, pw, ph) in enumerate(guide_rects(g)):   # everything stays inside the strip's trim guides
        work = img.copy()
        if lf.get("page", True):
            i = max(2, lf.get("inset", 24)) + w
            q = (rnd(px + i), rnd(py + i), rnd(px + pw - i), rnd(py + ph - i))
            slot_border(work, q, rr, sb, "rect")
            if lf.get("double"):
                slot_border(work, (q[0] + dd, q[1] + dd, q[2] - dd, q[3] - dd), max(0, rr - dd), sb, "rect")
        if lf.get("photos", True):
            for x0, y0, x1, y1, h in boxes:
                if cut and h != half:
                    continue
                d = out + max(0, lf.get("gap", 10))
                slot_border(work, (x0 - d, y0 - d, x1 + d, y1 + d), rr, sb, shape)
                if lf.get("double"):
                    e = d + dd
                    slot_border(work, (x0 - e, y0 - e, x1 + e, y1 + e), rr + dd if rr else 0, sb, shape)
        keep = Image.new("L", img.size, 0)
        keep.paste(255, (rnd(px), rnd(py), rnd(px + pw), rnd(py + ph)))
        img.paste(work, (0, 0), keep)


def perf_holes(x, y, w, h, d):
    """Postage-stamp perforations: hole centres evenly spaced round a rectangle, one on every corner (like the app)."""
    pts, out = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], []
    for e in range(4):
        (ax, ay), (bx, by) = pts[e], pts[(e + 1) % 4]
        n = max(1, rnd(math.hypot(bx - ax, by - ay) / (d * 1.6)))
        out += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n)]
    return out


def holes_cover(mask, holes, d, ox=0, oy=0):
    """Add round holes (smooth edges) to a float coverage array whose top-left pixel is at (ox, oy)."""
    import numpy as np
    r, H, W = d / 2, *mask.shape
    for cx, cy in holes:
        cx, cy = cx - ox, cy - oy
        a0, a1 = max(0, int(cx - r - 1)), min(W, int(cx + r + 2))
        b0, b1 = max(0, int(cy - r - 1)), min(H, int(cy + r + 2))
        if a0 >= a1 or b0 >= b1:
            continue
        yy, xx = np.mgrid[b0:b1, a0:a1].astype(np.float32) + 0.5
        c = np.clip(r - np.hypot(xx - cx, yy - cy) + 0.5, 0, 1)
        mask[b0:b1, a0:a1] = np.maximum(mask[b0:b1, a0:a1], c)


def _shade(hexc, t):
    c = color(hexc)[:3]
    return tuple(round(v + (255 - v) * t) if t > 0 else round(v * (1 + t)) for v in c)


def tv_bezels(img, g, boxes):
    """Retro TV: a dark casing round each photo (light at the top, darker at the bottom) with a soft shadow, and a
    dark lip round the screen. Like the app."""
    import numpy as np
    tv = g.get("slot_tv")
    if not tv or not tv.get("bezel_w"):
        return
    bw = tv["bezel_w"]
    lip = max(4, rnd(bw * 0.22))
    out, ins = g.get("_tv", (bw, 0))
    cut = g["cut"] in ("vertical", "horizontal")
    for x0, y0, x1, y1, half in boxes:
        if not out:
            continue
        ow, oh = x1 - x0 + 2 * out, y1 - y0 + 2 * out
        pad = int(out * 0.9 + 8)
        W_, H_ = ow + 2 * pad, oh + 2 * pad
        s = 4
        big = Image.new("L", (W_ * s, H_ * s), 0)
        ImageDraw.Draw(big).rounded_rectangle((pad * s, pad * s, (pad + ow) * s - 1, (pad + oh) * s - 1), radius=min(ow, oh) * 0.06 * s, fill=255)
        case = big.resize((W_, H_), Image.LANCZOS)
        layer = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
        sh = Image.new("L", (W_, H_), 0)
        sh.paste(case, (0, rnd(out * 0.15)))
        sh = sh.filter(ImageFilter.GaussianBlur(out * 0.3)).point(lambda v: v * 45 // 100)
        layer.paste(Image.new("RGBA", (W_, H_), (0, 0, 0, 255)), (0, 0), sh)
        top, bot = np.array(_shade(tv.get("bezel", "#2a2a2c"), 0.18), np.float32), np.array(_shade(tv.get("bezel", "#2a2a2c"), -0.3), np.float32)
        t = np.clip((np.arange(H_, dtype=np.float32) + 0.5 - pad) / oh, 0, 1)[:, None, None]
        grad = np.broadcast_to(top + (bot - top) * t, (H_, W_, 3))
        arr = np.zeros((H_, W_, 4), np.uint8)
        arr[..., :3] = np.clip(grad + 0.5, 0, 255).astype(np.uint8)
        arr[..., 3] = 255
        layer.paste(Image.fromarray(arr, "RGBA"), (0, 0), case)
        if not ins:   # the dark lip round the screen (a thicker casing draws it over the photo, in tv_inner)
            lw, lh = x1 - x0 + 2 * lip, y1 - y0 + 2 * lip
            lb = Image.new("L", (lw * s, lh * s), 0)
            draw_shape(ImageDraw.Draw(lb), (0, 0, lw * s - 1, lh * s - 1), (g["radius"] + lip) * s, g.get("slot_shape", "rect"), 255, g.get("radius_corners"))
            layer.paste(Image.new("RGBA", (lw, lh), (13, 13, 14, 255)), (pad + out - lip, pad + out - lip), lb.resize((lw, lh), Image.LANCZOS))
        X, Y = x0 - out - pad, y0 - out - pad
        if cut:   # a casing stays inside its own strip
            cx, cy, cw, ch = (round(v) for v in strip_areas(g)[half]["clip"])
            keep = Image.new("L", layer.size, 0)
            keep.paste(255, (cx - X, cy - Y, cx - X + cw, cy - Y + ch))
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), keep))
        full = Image.new("RGBA", img.size, (0, 0, 0, 0))
        full.paste(layer, (X, Y))
        img.alpha_composite(full)


def tv_inner(img, g, boxes):
    """The part of a thick TV casing that covers the photo's edge, and the dark lip round the smaller screen.
    Drawn after the windows are cut out. Like the app."""
    import numpy as np
    tv = g.get("slot_tv")
    out, ins = g.get("_tv", (0, 0))
    if not tv or not ins:
        return
    lip, e, s = max(4, rnd(tv["bezel_w"] * 0.22)), min(1, out), 4
    shape, corners = g.get("slot_shape", "rect"), g.get("radius_corners")
    top, bot = np.array(_shade(tv.get("bezel", "#2a2a2c"), 0.18), np.float32), np.array(_shade(tv.get("bezel", "#2a2a2c"), -0.3), np.float32)
    cut = g["cut"] in ("vertical", "horizontal")
    for x0, y0, x1, y1, half in boxes:
        (a0, b0, a1, b1), rs = tv_screen((x0, y0, x1, y1), g)
        if a1 <= a0 or b1 <= b0:
            continue
        X, Y, W_, H_ = x0 - e, y0 - e, x1 - x0 + 2 * e, y1 - y0 + 2 * e

        def mask(q, r):
            big = Image.new("L", (W_ * s, H_ * s), 0)
            draw_shape(ImageDraw.Draw(big), ((q[0] - X) * s, (q[1] - Y) * s, (q[2] - X) * s - 1, (q[3] - Y) * s - 1), r * s, shape, 255, corners)
            return np.asarray(big.resize((W_, H_), Image.LANCZOS), np.int16)
        screen = mask((a0, b0, a1, b1), rs)
        case_a = np.clip(mask((X, Y, x1 + e, y1 + e), g["radius"] + e) - screen, 0, 255)
        lip_a = np.clip(mask((a0 - lip, b0 - lip, a1 + lip, b1 + lip), rs + lip) - screen, 0, 255)
        t = np.clip((Y + np.arange(H_, dtype=np.float32) + 0.5 - (y0 - out)) / (y1 - y0 + 2 * out), 0, 1)[:, None, None]
        rgb = np.broadcast_to(top + (bot - top) * t, (H_, W_, 3)).astype(np.float32)
        la = lip_a[..., None] / 255.0
        rgb = rgb * (1 - la) + np.array((13, 13, 14), np.float32) * la
        alpha = np.maximum(case_a, lip_a)
        arr = np.zeros((H_, W_, 4), np.uint8)
        arr[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
        arr[..., 3] = alpha.astype(np.uint8)
        layer = Image.fromarray(arr, "RGBA")
        if cut:   # stays inside its own strip
            cx, cy, cw, ch = (round(v) for v in strip_areas(g)[half]["clip"])
            keep = Image.new("L", layer.size, 0)
            keep.paste(255, (cx - X, cy - Y, cx - X + cw, cy - Y + ch))
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), keep))
        full = Image.new("RGBA", img.size, (0, 0, 0, 0))
        full.paste(layer, (X, Y))
        img.alpha_composite(full)


POST_RED, POST_BLUE = "#ff3040", "#3897f0"
POST_FONTS = ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def post_ink(dark):
    return ({"card": "#121212", "ink": "#f5f5f5", "grey": "#a8a8a8", "dot": "#555555", "avatar": "#2a2a2a"} if dark else
            {"card": "#ffffff", "ink": "#262626", "grey": "#8e8e8e", "dot": "#c7c7c7", "avatar": "#efefef"})


def post_icon_pts(kind):
    """Icon outlines on a 24 x 24 grid (the same points as the app)."""
    if kind == "heart":
        p = []
        for i in range(72):
            t = i / 72 * 2 * math.pi
            p.append((16 * math.sin(t) ** 3, -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))))
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        k = 20 / max(max(xs) - min(xs), max(ys) - min(ys))
        return [(12 + (x - mx) * k, 12 + (y - my) * k) for x, y in p]
    if kind == "comment":
        p = [(12 + 9.5 * math.cos(math.radians(150 + i / 40 * 330)), 11.5 + 9.5 * math.sin(math.radians(150 + i / 40 * 330))) for i in range(41)]
        return p + [(2.6, 21.4)]
    if kind == "plane":
        return [(22, 2.5), (2, 9.6), (10.2, 13.6), (13.8, 21.8)]
    if kind == "bookmark":
        return [(5, 2.5), (19, 2.5), (19, 21.5), (12, 15.5), (5, 21.5)]
    return []


def _pfont(size, bold=False):
    try:
        return ImageFont.truetype(POST_FONTS[1 if bold else 0], max(1.0, size))
    except OSError:
        return ImageFont.load_default()


def post_plan(g, boxes, half):
    """Where the post look's parts go for one strip. Like the app's postPlan."""
    pt = g.get("post")
    bs = [b for b in boxes if b[4] == half]
    if not pt or not bs:
        return None
    cut = g["cut"] in ("vertical", "horizontal")
    areas = strip_areas(g)[half if cut else 0]
    px, py, pw, ph = areas["print"]
    sb = g.get("slot_border")
    out = sb["width"] if sb and sb.get("pos") == "outside" else 0
    gx, gy = min(b[0] for b in bs) - out, min(b[1] for b in bs) - out
    gx1, gy1 = max(b[2] for b in bs) + out, max(b[3] for b in bs) + out
    gw, gh = gx1 - gx, gy1 - gy
    sp = max(0, min(gy - py, py + ph - gy1, gx - px, px + pw - gx1))
    cm = max(4, min(30, rnd(sp * 0.3))) if pt.get("card") else 0
    card = (px + cm, py + cm, pw - 2 * cm, ph - 2 * cm, rnd(min(pw, ph) * 0.025))
    u0 = max(12, min(72, rnd(min(pw, ph) * 0.036)))
    R = {"top": (gx, card[1], gw, gy - card[1]), "bottom": (gx, gy1, gw, card[1] + card[3] - gy1),
         "right": (gx1, gy, card[0] + card[2] - gx1, gh), "left": (card[0], gy, gx - card[0], gh)}
    uh = min(u0, math.floor(R["top"][3] / 4.2))
    header = {"u": uh, "x": gx, "x1": gx1, "cy": gy - 2.05 * uh} if uh >= u0 * 0.6 else None
    block = None
    for k in (["bottom", "right", "left"] if header else ["bottom", "top", "right", "left"]):
        r = R[k]
        u = min(u0, r[2] / 12, r[3] / 6.5)
        if u >= u0 * 0.75:
            block = {"k": k, "u": u}
            break
        if u >= max(12, u0 * 0.35) and (not block or u > block["u"]):
            block = {"k": k, "u": u}
    if block:
        block.update(zip(("x", "y", "w", "h"), R[block["k"]]))
    return {"card": card, "header": header, "block": block, "n": len(bs), "clip": areas["clip"]}


def post_wrap(words, size, max_w, max_lines, bold_first=True):
    """Caption words in lines no wider than max_w; the account name (first word) is bold."""
    lines, w = [[]], 0
    space = _pfont(size).getlength(" ")
    for i, t in enumerate(words):
        b = bold_first and i == 0
        tw = _pfont(size, b).getlength(t)
        if lines[-1] and w + space + tw > max_w:
            lines.append([])
            w = 0
        lines[-1].append({"t": t, "b": b, "x": w + space if w else 0})
        w = (w + space if w else 0) + tw
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1][-1]["t"] += "…"
    return lines


class _Pen:
    """Draws on a layer S times bigger than the page area it covers (smooth edges once shrunk)."""
    def __init__(self, x, y, w, h, S=3):
        self.x, self.y, self.S = x, y, S
        self.img = Image.new("RGBA", (max(1, math.ceil(w * S)), max(1, math.ceil(h * S))), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def P(self, x, y):
        return ((x - self.x) * self.S, (y - self.y) * self.S)

    def circle(self, cx, cy, r, fill):
        X, Y = self.P(cx, cy)
        self.d.ellipse((X - r * self.S, Y - r * self.S, X + r * self.S, Y + r * self.S), fill=fill)

    def text(self, x, y, t, size, fill, bold=False):
        self.d.text(self.P(x, y), t, font=_pfont(size * self.S, bold), fill=fill, anchor="ls")

    def icon(self, kind, cx, cy, size, color, fill=None):
        k = size / 24
        pts = [self.P(cx + (a - 12) * k, cy + (b - 12) * k) for a, b in post_icon_pts(kind)]
        if fill:
            self.d.polygon(pts, fill=fill)
            return
        w = max(1, rnd(2 * k * self.S))
        self.d.line(pts + [pts[0], pts[1]], fill=color, width=w, joint="curve")
        if kind == "plane":
            self.d.line([self.P(cx - 1.8 * k, cy + 1.6 * k), self.P(cx + 10 * k, cy - 9.5 * k)], fill=color, width=w)
            for q in (self.P(cx - 1.8 * k, cy + 1.6 * k),):
                self.d.ellipse((q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2), fill=color)

    def done(self, layer):
        small = self.img.resize((max(1, round(self.img.width / self.S)), max(1, round(self.img.height / self.S))), Image.LANCZOS)
        layer.alpha_composite(small, (round(self.x), round(self.y)))


def post(img, g, boxes):
    """Social post look: a card behind the photos, the account name above them (when there's room), and the like /
    comment / share icons, likes, caption and time in the biggest free space. Like the app."""
    import numpy as np
    pt = g.get("post")
    if not pt:
        return
    c = post_ink(pt.get("dark"))
    cut = g["cut"] in ("vertical", "horizontal")
    for half in sorted({b[4] for b in boxes}):
        pl = post_plan(g, boxes, half)
        if not pl:
            continue
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        if pt.get("card"):
            kx, ky, kw, kh, kr = pl["card"]
            kx, ky, kw, kh = rnd(kx), rnd(ky), rnd(kw), rnd(kh)
            s = 4
            big = Image.new("L", (kw * s, kh * s), 0)
            ImageDraw.Draw(big).rounded_rectangle((0, 0, kw * s - 1, kh * s - 1), radius=kr * s, fill=255)
            m = big.resize((kw, kh), Image.LANCZOS)
            sh = Image.new("L", img.size, 0)
            sh.paste(m, (kx, ky + rnd(kr * 0.25)))
            sh = sh.filter(ImageFilter.GaussianBlur(kr / 2)).point(lambda v: v * 18 // 100)
            layer.paste(Image.new("RGBA", img.size, (0, 0, 0, 255)), (0, 0), sh)
            layer.paste(Image.new("RGBA", (kw, kh), color(c["card"])), (kx, ky), m)
        hd = pl["header"]
        if hd:
            u = hd["u"]
            r, cy = 1.25 * u, hd["cy"]
            pen = _Pen(hd["x"] - 2, cy - 1.7 * u, hd["x1"] - hd["x"] + 4, 3.4 * u)
            ax = hd["x"] + r
            X0, Y0 = pen.P(ax - r, cy - r)
            n = max(1, rnd(2 * r * pen.S))
            t = (np.add.outer(n - 1 - np.arange(n), np.arange(n)) / max(1, 2 * (n - 1)))[..., None].astype(np.float32)   # bottom-left -> top-right
            stops = [np.array(color(h)[:3], np.float32) for h in ("#ffb347", "#ff4f8b", "#a64dff")]
            grad = np.where(t < 0.5, stops[0] + (stops[1] - stops[0]) * (t / 0.5), stops[1] + (stops[2] - stops[1]) * ((t - 0.5) / 0.5))
            ring = Image.fromarray(np.dstack([np.clip(grad + 0.5, 0, 255).astype(np.uint8), np.full((n, n, 1), 255, np.uint8)]), "RGBA")
            mask = Image.new("L", (n, n), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, n - 1, n - 1), fill=255)
            pen.img.paste(ring, (rnd(X0), rnd(Y0)), mask)
            pen.circle(ax, cy, r - 0.2 * u, c["card"])
            pen.circle(ax, cy, r - 0.32 * u, c["avatar"])
            q = r - 0.32 * u   # a little camera as the profile picture
            a0, b0 = pen.P(ax - 0.5 * q, cy - 0.26 * q)
            a1, b1 = pen.P(ax + 0.5 * q, cy + 0.4 * q)
            pen.d.rounded_rectangle((a0, b0, a1, b1), radius=0.12 * q * pen.S, fill=c["grey"])
            a0, b0 = pen.P(ax - 0.2 * q, cy - 0.4 * q)
            a1, b1 = pen.P(ax + 0.2 * q, cy - 0.24 * q)
            pen.d.rectangle((a0, b0, a1, b1), fill=c["grey"])
            pen.circle(ax, cy + 0.07 * q, 0.2 * q, c["avatar"])
            nx = hd["x"] + 3.1 * u
            nb = cy - 0.12 * u if pt.get("place") else cy + 0.38 * u
            name = pt.get("name") or ""
            pen.text(nx, nb, name, 1.05 * u, c["ink"], True)
            if pt.get("verified") and name:
                vx, vy, vr = nx + _pfont(1.05 * u, True).getlength(name) + 0.75 * u, nb - 0.38 * u, 0.52 * u
                pen.d.polygon([pen.P(vx + vr * (0.9 + 0.1 * math.cos(8 * a)) * math.cos(a), vy + vr * (0.9 + 0.1 * math.cos(8 * a)) * math.sin(a))
                               for a in (i / 48 * 2 * math.pi for i in range(48))], fill=POST_BLUE)
                pen.d.line([pen.P(vx - 0.24 * u, vy + 0.02 * u), pen.P(vx - 0.06 * u, vy + 0.2 * u), pen.P(vx + 0.26 * u, vy - 0.18 * u)],
                           fill="#ffffff", width=max(1, rnd(0.15 * u * pen.S)), joint="curve")
            if pt.get("place"):
                pen.text(nx, cy + 0.95 * u, pt["place"], 0.85 * u, c["ink"])
            for i in range(3):
                pen.circle(hd["x1"] - 0.3 * u - i * 0.42 * u, cy, 0.13 * u, c["ink"])
            pen.done(layer)
        bk = pl["block"]
        if bk:
            u = bk["u"]
            bottom = bk["y"] + bk["h"] - 0.3 * u
            y = bk["y"] + 0.45 * u
            pen = _Pen(bk["x"] - 2, bk["y"], bk["w"] + 4, bk["h"])
            iy, s = y + 1.3 * u, 1.9 * u
            pen.icon("heart", bk["x"] + 0.95 * u, iy, s, c["ink"], POST_RED)
            pen.icon("comment", bk["x"] + 3.35 * u, iy, s, c["ink"])
            pen.icon("plane", bk["x"] + 5.75 * u, iy, s, c["ink"])
            pen.icon("bookmark", bk["x"] + bk["w"] - 0.95 * u, iy, s, c["ink"])
            dw, room = (pl["n"] - 1) * 0.75 * u, bk["w"] - 2 * 6.9 * u
            if pl["n"] > 1 and dw <= room:
                for i in range(pl["n"]):
                    pen.circle(bk["x"] + bk["w"] / 2 - dw / 2 + i * 0.75 * u, iy, 0.24 * u, c["dot"] if i else POST_BLUE)
            y += 2.6 * u
            likes = pt.get("likes") or ""
            if likes and y + 1.6 * u <= bottom:
                pen.text(bk["x"], y + 1.15 * u, likes if "like" in likes.lower() else likes + " likes", 1.05 * u, c["ink"], True)
                y += 1.6 * u
            cap = (pt.get("caption") or "").split()
            name = pt.get("name") or ""
            words = [name] + cap if name else cap
            when_h = 1.3 * u if pt.get("when") else 0
            n = math.floor((bottom - y - when_h) / (1.45 * u))
            if cap and n < 1:   # short of room: the caption before the time
                n = math.floor((bottom - y) / (1.45 * u))
            if cap and n >= 1:
                for line in post_wrap(words, u, bk["w"], n, bool(name)):
                    for w_ in line:
                        pen.text(bk["x"] + w_["x"], y + 1.05 * u, w_["t"], u, c["ink"], w_["b"])
                    y += 1.45 * u
            if pt.get("when") and y + 1.3 * u <= bottom:
                pen.text(bk["x"], y + 1.0 * u, pt["when"].upper(), 0.72 * u, c["grey"])
            pen.done(layer)
        if cut:   # stays inside its own strip
            cx, cy_, cw, ch = (round(v) for v in pl["clip"])
            keep = Image.new("L", layer.size, 0)
            keep.paste(255, (cx, cy_, cx + cw, cy_ + ch))
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), keep))
        img.alpha_composite(layer)


def slot_tv(img, g, boxes):
    """Retro TV screen effects over each photo window: tint, scanlines, dark curved edges, static scratches, a glitch
    block and on-screen text. Same random static as the app (same seed)."""
    import numpy as np
    tv = g.get("slot_tv")
    if not tv:
        return
    tv_inner(img, g, boxes)
    seen = {}
    try:
        font_path = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
        ImageFont.truetype(font_path, 10)
    except OSError:
        font_path = None
    for b in boxes:
        half = b[4]
        seen[half] = k = seen.get(half, -1) + 1
        (a0, b0, a1, b1), r = window_of(b[:4], g)
        w, h = a1 - a0, b1 - b0
        if w <= 0 or h <= 0:
            continue
        rnd_ = mulberry32((tv.get("seed", 1)) * 1000 + k + 7)
        m = min(w, h)
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        def over(piece, xy=(0, 0)):
            layer.alpha_composite(piece, xy)

        def lines(segs):   # [(x0, y0, x1, y1, rgba, width)] drawn on their own layer, then laid over
            for x_0, y_0, x_1, y_1, rgba, lw in segs:
                L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                ImageDraw.Draw(L).line((x_0, y_0, x_1, y_1), fill=rgba, width=max(1, round(lw)))
                over(L)
        if tv.get("tint"):
            over(Image.new("RGBA", (w, h), color(tv.get("tint_color", "#9fd4b0"))[:3] + (round(tv["tint"] / 100 * 0.5 * 255),)))
        if tv.get("scan"):
            st_ = max(2, rnd(m / 220))
            sl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            dd = ImageDraw.Draw(sl)
            a_ = round(tv["scan"] / 100 * 0.35 * 255)
            for y in range(0, h, st_ * 2):
                dd.rectangle((0, y, w - 1, min(h, y + st_) - 1), fill=(0, 0, 0, a_))
            over(sl)
        if tv.get("vignette"):
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
            dist = np.hypot(xx - w / 2, yy - h / 2)
            r0, r1 = m * 0.3, math.hypot(w, h) / 2
            A = np.clip((dist - r0) / (r1 - r0), 0, 1) * tv["vignette"] / 100 * 0.75
            arr = np.zeros((h, w, 4), np.uint8)
            arr[..., 3] = np.clip(A * 255 + 0.5, 0, 255).astype(np.uint8)
            over(Image.fromarray(arr, "RGBA"))
        if tv.get("static"):
            n = rnd(tv["static"] / 100 * 26)
            segs = []
            for _ in range(n):   # scratches down the screen
                x_0, y_0 = rnd_() * w, rnd_() * h * 0.5
                y_1 = y_0 + h * (0.3 + rnd_() * 0.7)
                dx = (rnd_() - 0.5) * m * 0.05
                al = 0.15 + rnd_() * 0.35
                segs.append((x_0, y_0, x_0 + dx, y_1, (255, 255, 255, round(al * 255)), 1.5 + rnd_() * 1.5))
            for _ in range(math.ceil(n / 4)):   # lines of static across
                y = rnd_() * h
                a = rnd_() * w * 0.5
                z = a + w * (0.2 + rnd_() * 0.6)
                al = 0.3 + rnd_() * 0.4
                segs.append((a, y, z, y, (255, 255, 255, round(al * 255)), 2 + rnd_() * 2))
            lines(segs)
        if tv.get("glitch"):   # a block of digital noise on the right
            gw, gh = rnd(w * (0.14 + rnd_() * 0.12)), rnd(h * (0.07 + rnd_() * 0.07))
            X0, Y0 = rnd(w * 0.97 - gw), rnd(h * (0.25 + rnd_() * 0.3))
            cw, ch = max(3, rnd(m / 90)), max(2, rnd(m / 160))
            gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            dd = ImageDraw.Draw(gl)
            for yy_ in range(0, gh, ch):
                for xx_ in range(0, gw, cw):
                    v = rnd_()
                    c = (0, 0, 0) if v < 0.45 else (255, 255, 255) if v < 0.9 else (128, 128, 128)
                    dd.rectangle((X0 + xx_, Y0 + yy_, X0 + xx_ + min(cw, gw - xx_) - 1, Y0 + yy_ + min(ch, gh - yy_) - 1), fill=c + (230,))
            over(gl)
        fs, pad = rnd(m * 0.06), m * 0.1
        if (tv.get("text1") or tv.get("text2")) and font_path:
            font = ImageFont.truetype(font_path, fs)
            tl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            dd = ImageDraw.Draw(tl)
            tx = pad
            t1, t2 = tv.get("text1", ""), tv.get("text2", "")
            if t1 and "REC" in t1.upper():
                cx_, cy_, rr = tx + fs * 0.35, pad + fs * 0.62, fs * 0.32
                dd.ellipse((cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr), fill=(255, 59, 48, 255))
                tx += fs * 0.95
            if t1:
                dd.text((tx, pad + fs), t1, font=font, fill=(255, 255, 255, 235), anchor="ls")
            if t2:
                dd.text((pad, h - pad), t2, font=font, fill=(255, 255, 255, 235), anchor="ls")
            over(tl)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5   # a soft reflection on the glass
        dx_, dy_ = w * 0.6, h * 0.6
        t = (xx * dx_ + yy * dy_) / (dx_ * dx_ + dy_ * dy_)
        A = np.clip(1 - t / 0.5, 0, 1) * 0.10
        arr = np.full((h, w, 4), 255, np.uint8)
        arr[..., 3] = np.clip(A * 255 + 0.5, 0, 255).astype(np.uint8)
        over(Image.fromarray(arr, "RGBA"))
        s = 4   # keep it all inside the screen shape
        big = Image.new("L", (w * s, h * s), 0)
        draw_shape(ImageDraw.Draw(big), (0, 0, w * s - 1, h * s - 1), r * s, g.get("slot_shape", "rect"), 255, g.get("radius_corners"))
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), big.resize((w, h), Image.LANCZOS)))
        img.alpha_composite(layer, (a0, b0))


def track_lines(g, boxes):
    """Photos grouped into lines along the strip (each rides on its own track), with how far sleepers may reach:
    halfway to the next line, or the edge of the strip. Same as the app."""
    vert = "l" in strip_sides(g, 0)
    strips = strip_areas(g)
    groups = {}
    for b in boxes:
        x0, y0, x1, y1, half = b
        key = (half, x0, x1 - x0) if vert else (half, y0, y1 - y0)
        groups.setdefault(key, []).append(b)
    lines = []
    for bs in groups.values():
        bs.sort(key=lambda b: b[1] if vert else b[0])
        f = bs[0]
        lines.append({"half": f[4], "vert": vert, "lo": f[0] if vert else f[1], "hi": f[2] if vert else f[3], "boxes": bs})
    for L in lines:
        cx, cy, cw, ch = strips[L["half"]]["clip"] if L["half"] < len(strips) else strips[0]["clip"]
        L["min"] = cx if vert else cy
        L["max"] = L["min"] + (cw if vert else ch)
        for o in lines:
            if o is not L and o["half"] == L["half"]:
                if o["lo"] >= L["hi"]:
                    L["max"] = min(L["max"], (L["hi"] + o["lo"]) / 2)
                elif o["hi"] <= L["lo"]:
                    L["min"] = max(L["min"], (o["hi"] + L["lo"]) / 2)
    return lines


def rails(img, g, boxes):
    """A railway track seen from above under every line of photos: wooden sleepers across, two steel rails just
    outside the photos, and couplings in the gaps, so the photos look like carriages. Drawn like the app."""
    rl = g.get("rails")
    if not rl or not boxes:
        return
    strips, rw = strip_areas(g), 18
    sb = g.get("slot_border") or {}
    out = sb.get("width", 0) if sb.get("pos") == "outside" else 0
    W_, H_ = img.size
    for L in track_lines(g, boxes):
        C = strips[L["half"]]["clip"] if L["half"] < len(strips) else strips[0]["clip"]
        vert = L["vert"]
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        def R(a, b, la, lb):   # (across, along) -> x, y, w, h
            return (a, b, la, lb) if vert else (b, a, lb, la)

        def fill(r, rgba, radius=0):
            x, y, w, h = (int(v) for v in r)
            x0, y0, x1, y1 = max(0, x), max(0, y), min(W_, x + w), min(H_, y + h)
            if x1 <= x0 or y1 <= y0:
                return
            if rgba[3] == 255:
                if radius:
                    d.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=radius, fill=rgba)
                else:
                    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgba)
            else:
                layer.alpha_composite(Image.new("RGBA", (x1 - x0, y1 - y0), rgba), (x0, y0))

        a0 = C[1] if vert else C[0]
        a1 = a0 + (C[3] if vert else C[2])
        left, right = rnd(L["lo"] - rl.get("gauge", 26)), rnd(L["hi"] + rl.get("gauge", 26))
        s0 = rnd(max(L["min"], left - rw / 2 - rl.get("overhang", 70)))
        s1 = rnd(min(L["max"], right + rw / 2 + rl.get("overhang", 70)))
        pitch = max(30, rl.get("pitch", 120))
        th = rnd(pitch * 0.42)
        f, l = L["boxes"][0], L["boxes"][-1]
        mid = (f[1] + l[3]) / 2 if vert else (f[0] + l[2]) / 2
        sleeper, rail = color(rl.get("sleeper", "#7a5636")), color(rl.get("rail", "#c9ced6"))
        k = math.floor((a0 - mid) / pitch) - 1
        while mid + k * pitch - pitch < a1:   # sleepers
            c = rnd(mid + k * pitch - th / 2)
            fill(R(s0, c, s1 - s0, th), sleeper, 4)
            for q in (0.3, 0.68):   # wood grain
                fill(R(s0 + 6, c + rnd(th * q), s1 - s0 - 12, 2), (0, 0, 0, 56))
            fill(R(s0, c + th - 4, s1 - s0, 4), (0, 0, 0, 77))   # shade on one edge
            for r in (left, right):   # steel plates
                fill(R(r - rw, c + 4, 2 * rw, th - 8), color("#3d3a38"))
            k += 1
        for r in (left, right):   # rails: shadow, steel, shiny top
            fill(R(r - rw / 2 + 3, a0, rw, a1 - a0), (0, 0, 0, 89))
            fill(R(r - rw / 2, a0, rw, a1 - a0), color("#5f656d"))
            fill(R(r - rw / 2 + 4, a0, rw - 8, a1 - a0), rail)
            fill(R(r - 1, a0, 3, a1 - a0), (255, 255, 255, 179))
        if rl.get("couplers", True):   # concertina couplings in the gaps
            bs = L["boxes"]
            for p_, n_ in zip(bs, bs[1:]):
                a, b = (p_[3], n_[1]) if vert else (p_[2], n_[0])
                if b - a < 4:
                    continue
                cw = rnd(min(160, (L["hi"] - L["lo"]) * 0.22))
                cx = rnd((L["lo"] + L["hi"]) / 2 - cw / 2)
                fill(R(cx, a - 12, cw, b - a + 24), color("#2c2f34"))
                y = a + out + 4
                while y + 4 <= b - out - 4:
                    fill(R(cx + 4, y, cw - 8, 4), color("#4a4f57"))
                    y += 10
        cx_, cy_, cw_, ch_ = (round(v) for v in C)   # the track stays inside its own strip
        keep = Image.new("L", img.size, 0)
        keep.paste(255, (cx_, cy_, cx_ + cw_, cy_ + ch_))
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), keep))
        img.alpha_composite(layer)


def slot_stamps(img, g, boxes):
    """Each photo on a piece of stamp paper with perforated edges (the background shows in the holes), with an
    optional soft shadow under it. Same sizes as the app."""
    import numpy as np
    sp = g.get("slot_stamp")
    if not sp or sp.get("where", "photos") == "edge":
        return
    m, d = sp.get("width", 30), sp.get("hole", 14)
    cut = g["cut"] in ("vertical", "horizontal")
    for x0, y0, x1, y1, half in boxes:
        w, h = x1 - x0 + 2 * m, y1 - y0 + 2 * m
        holes = np.zeros((h, w), np.float32)
        holes_cover(holes, perf_holes(0, 0, w, h, d), d)
        paper = Image.fromarray(np.clip((1 - holes) * 255 + 0.5, 0, 255).astype(np.uint8), "L")
        pad, X, Y = 0, x0 - m, y0 - m
        if sp.get("shadow", True):
            dist, blur = max(2, rnd(m * 0.15)), max(4, rnd(m * 0.5))
            pad = int(blur * 1.5 + dist + 4)
        layer = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        if pad:
            a = math.radians(60)
            S = Image.new("L", layer.size, 0)
            S.paste(paper, (pad + rnd(math.cos(a) * dist), pad + rnd(math.sin(a) * dist)))
            S = S.filter(ImageFilter.GaussianBlur(blur / 2)).point(lambda v: v * 35 // 100)
            shadow = Image.new("RGBA", layer.size, (0, 0, 0, 255))
            shadow.putalpha(S)
            layer.alpha_composite(shadow)
        sheet = Image.new("RGBA", (w, h), color(sp.get("color", "#ffffff")))
        sheet.putalpha(paper)
        layer.alpha_composite(sheet, (pad, pad))
        if cut:   # a stamp stays inside its own strip
            cx, cy, cw, ch = (round(v) for v in strip_areas(g)[half]["clip"])
            keep = Image.new("L", layer.size, 0)
            keep.paste(255, (cx - (X - pad), cy - (Y - pad), cx - (X - pad) + cw, cy - (Y - pad) + ch))
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), keep))
        full = Image.new("RGBA", img.size, (0, 0, 0, 0))
        full.paste(layer, (X - pad, Y - pad))
        img.alpha_composite(full)


def stamp_edge(img, g):
    """The whole print as one big stamp: holes along the trim line of every strip, the bleed in the hole colour."""
    import numpy as np
    sp = g.get("slot_stamp")
    if not sp or sp.get("where") != "edge":
        return
    d, W, H = sp.get("hole", 14), *img.size
    cover = np.zeros((H, W), np.float32)
    for st in strip_areas(g):
        cx, cy, cw, ch = st["clip"]
        px, py, pw, ph = st["print"]
        part = np.zeros((H, W), np.float32)
        xs, ys = np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32)
        inx = np.clip(np.minimum(xs + 1, px + pw) - np.maximum(xs, px), 0, 1)
        iny = np.clip(np.minimum(ys + 1, py + ph) - np.maximum(ys, py), 0, 1)
        part[:] = 1 - iny[:, None] * inx[None, :]
        holes_cover(part, perf_holes(px, py, pw, ph, d), d)
        a0, b0, a1, b1 = round(cx), round(cy), round(cx + cw), round(cy + ch)
        cover[b0:b1, a0:a1] = np.maximum(cover[b0:b1, a0:a1], part[b0:b1, a0:a1])
    M = Image.fromarray(np.clip(cover * 255 + 0.5, 0, 255).astype(np.uint8), "L")
    if sp.get("color") == "transparent":
        img.putalpha(ImageChops.multiply(img.getchannel("A"), ImageOps.invert(M)))
    else:
        img.paste(Image.new("RGBA", img.size, color(sp.get("color", "#ffffff"))), (0, 0), M)


def punch(img, box, radius, fill, shape="rect", corners=None):
    """Fill a photo window (rounded rectangle, circle, oval or arch) with a colour, or make it see-through.
    Edges are smoothed."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    r = max(0, min(radius, w / 2, h / 2))
    rgba = color(fill)
    if r < 1 and shape in ("rect", None):
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgba)
        return
    s = 4   # draw 4x bigger, then shrink = smooth edges
    big = Image.new("L", (w * s, h * s), 0)
    draw_shape(ImageDraw.Draw(big), (0, 0, w * s - 1, h * s - 1), r * s, shape, 255, corners)
    mask = big.resize((w, h), Image.LANCZOS)
    if rgba[3] == 0:
        area = img.crop(box)
        area.putalpha(ImageChops.multiply(area.getchannel("A"), ImageOps.invert(mask)))
        img.paste(area, (x0, y0))
    else:
        img.paste(Image.new("RGBA", (w, h), rgba), (x0, y0), mask)


def film_room(g):
    """Free space beside the photos on the film edges (trim line to photo edge), measured with film off."""
    g0 = {**g, "film": False}
    boxes, room = slot_boxes(g0), math.inf
    for half, (x, y, w, h, *_) in enumerate(regions(g0)):
        hb = [b for b in boxes if b[4] == half]
        if not hb:
            continue
        for side, trim in strip_sides(g, half).items():
            d = {"l": min(b[0] for b in hb) - x, "r": x + w - max(b[2] for b in hb),
                 "t": min(b[1] for b in hb) - y, "b": y + h - max(b[3] for b in hb)}[side]
            room = min(room, d - trim)
    return 0 if room == math.inf else max(0, math.floor(room))


def film_can_widen(g):
    """1-2 photo columns across the film (rows for a landscape strip): the film edge may be wider than the free space."""
    across = g["cols"] if "l" in strip_sides(g, 0) else g["rows"]
    return not g.get("slots") and across <= 2


def film_band(g):
    """The film edge actually used: on 3+ columns (or exact slots) it stays in the free space."""
    return g["film_band"] if film_can_widen(g) else min(g["film_band"], film_room(g))


def film_split_ok(g):
    across = g["cols"] if "l" in strip_sides(g, 0) else g["rows"]
    return g["cut"] not in ("vertical", "horizontal") and not g.get("slots") and across == 2


def film_split(g):
    """Two film strips on a layout that isn't cut: film edges on each half, holes down the middle too."""
    return bool(g["film"]) and g.get("film_split", True) is not False and film_split_ok(g)


def split_regions(g):
    """The two film strips: [(region, cols, rows, sides)]; each half has its own film edge in the middle."""
    x, y, w, h, l, r, t, b = regions(g)[0]
    band, bl = film_band(g), g["bleed"]
    inner = max(band, g["gap"] / 2)
    if "l" in strip_sides(g, 0):
        hw = w / 2
        return [((x, y, hw, h, l, inner, t, b), g["cols"] // 2, g["rows"], {"l": bl, "r": 0}),
                ((x + hw, y, hw, h, inner, r, t, b), g["cols"] // 2, g["rows"], {"l": 0, "r": bl})]
    hh = h / 2
    return [((x, y, w, hh, l, r, t, inner), g["cols"], g["rows"] // 2, {"t": bl, "b": 0}),
            ((x, y + hh, w, hh, l, r, inner, b), g["cols"], g["rows"] // 2, {"t": 0, "b": bl})]


def film_holes(g):
    """Sprocket holes down both long edges of every strip: [(x0, y0, x1, y1)].
    Shaped like 35mm film: wider across the strip than along it."""
    if not g["film"]:
        return []
    band = film_band(g)
    if band < 8:
        return []
    across, along = band * 0.5, band * 0.35
    pitch = band * 0.85
    holes = []
    split = film_split(g)
    parts = [(R[:4], sides) for R, _, _, sides in split_regions(g)] if split \
        else [(R[:4], strip_sides(g, half)) for half, R in enumerate(regions(g))]
    for (x, y, w, h), sides in parts:
        for side, trim in sides.items():
            length = h if side in "lr" else w
            n = int(length // pitch)
            first = (length - (n - 1) * pitch) / 2
            mid = trim + band / 2   # from the strip edge
            for k in range(n):
                pos = first + k * pitch
                if side in "lr":
                    cx = x + mid if side == "l" else x + w - mid
                    x0, y0 = rnd(cx - across / 2), rnd(y + pos - along / 2)
                    holes.append((x0, y0, x0 + rnd(across), y0 + rnd(along)))
                else:
                    cy = y + mid if side == "t" else y + h - mid
                    x0, y0 = rnd(x + pos - along / 2), rnd(cy - across / 2)
                    holes.append((x0, y0, x0 + rnd(along), y0 + rnd(across)))
    return holes


def mulberry32(seed):
    """Small random-number generator, identical to the one in the app."""
    a = seed & 0xFFFFFFFF
    imul = lambda x, y: (x * y) & 0xFFFFFFFF

    def rnd():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return (t ^ (t >> 14)) / 4294967296
    return rnd


def pattern_placements(p, area, n):
    """Staggered rows, each item nudged, turned and resized at random: [(x, y, item, scale, rotation)]."""
    rnd = mulberry32(p["seed"])
    ax, ay, aw, ah = area
    cell = max(10, p["size"] + p["gap"])
    row_h, j = cell * 0.866, p["scatter"] / 100 * cell * 0.5
    cols, rows = math.ceil(aw / cell) + 2, math.ceil(ah / row_h) + 2
    out = []
    for r in range(-1, rows):
        prev = -1
        for c in range(-1, cols):
            jx, jy, pick, sc, rt = rnd() * 2 - 1, rnd() * 2 - 1, rnd(), rnd(), rnd()
            item = math.floor(pick * n)
            if n > 1 and item == prev:
                item = (item + 1) % n
            prev = item
            out.append((ax + c * cell + (cell / 2 if r & 1 else 0) + jx * j, ay + r * row_h + jy * j,
                        item, 1 - sc * p["vary"] / 100, (rt * 2 - 1) * p["rotate"]))
    return out


def draw_pattern(img, g):
    p = g.get("pattern")
    if not p or not p.get("items"):
        return
    pics = []
    for key in p["items"]:
        path = HERE / "Stickers" / key[2:]
        if key.startswith("m:") and path.exists():
            pic = Image.open(path).convert("RGBA")
            pics.append(pic.crop(pic.getchannel("A").getbbox() or (0, 0, *pic.size)))
        else:
            print(f"  [{g['name']}] pattern item skipped (only Stickers/ files work here): {key}")
            pics.append(None)
    W, H = g["width"], g["height"]
    strips = strip_areas(g) if g["cut"] != "none" and p.get("per_half", True) else [{"clip": (0, 0, W, H), "area": (0, 0, W, H)}]
    A0 = strips[0]["area"]
    base = pattern_placements(p, A0, len(pics))
    pad = int(p["size"] * 2)
    for st in strips:
        (ax, ay, _, _), (kx, ky, kw, kh) = st["area"], st["clip"]
        layer = Image.new("RGBA", (round(kw) + 2 * pad, round(kh) + 2 * pad), (0, 0, 0, 0))
        for x, y, item, scale, rot in base:
            pic = pics[item]
            if pic is None:
                continue
            k = p["size"] * scale / max(pic.size)
            one = pic.resize((max(1, rnd(pic.width * k)), max(1, rnd(pic.height * k))), Image.LANCZOS)
            one = one.rotate(-rot, expand=True, resample=Image.BICUBIC)
            if p["opacity"] < 100:
                one.putalpha(one.getchannel("A").point(lambda v: v * p["opacity"] // 100))
            cx, cy = x - A0[0] + ax - kx + pad, y - A0[1] + ay - ky + pad
            dx, dy = rnd(cx - one.width / 2), rnd(cy - one.height / 2)
            if 0 <= dx and 0 <= dy and dx + one.width <= layer.width and dy + one.height <= layer.height:
                layer.alpha_composite(one, (dx, dy))
        img.alpha_composite(layer.crop((pad, pad, pad + round(kw), pad + round(kh))), (round(kx), round(ky)))


TEX_SIZE = 512
TEX_AMP = {"matte": 0.35, "linen": 0.3, "watercolor": 0.45, "kraft": 0.35, "canvas": 0.4, "recycled": 0.35}


def texture_tile(kind):
    """512 px grey tile (128 = no change), built exactly like the app's."""
    import numpy as np
    S, M = TEX_SIZE, np.uint64(0xFFFFFFFF)

    def hash_u(idx, seed):   # the (i+1)-th value of mulberry32(seed)
        idx = np.asarray(idx, dtype=np.uint64)
        a = (np.uint64(seed) + (idx + np.uint64(1)) * np.uint64(0x6D2B79F5)) & M
        t = ((a ^ (a >> np.uint64(15))) * (a | np.uint64(1))) & M
        t = ((t + (((t ^ (t >> np.uint64(7))) * (t | np.uint64(61))) & M)) & M) ^ t
        return ((t ^ (t >> np.uint64(14))) & M).astype(np.float64) / 4294967296

    def white(seed):
        return hash_u(np.arange(S * S), seed).reshape(S, S)

    def vnoise(cx, cy, seed):
        g = hash_u(np.arange(cx * cy), seed).reshape(cy, cx)
        f = np.arange(S, dtype=np.float64)
        fx, fy = f * cx / S, f * cy / S
        i0, j0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - i0, fy - j0
        sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        i1, j1 = (i0 + 1) % cx, (j0 + 1) % cy
        sx, sy = sx[None, :], sy[:, None]
        top = g[j0][:, i0] * (1 - sx) + g[j0][:, i1] * sx
        bot = g[j1][:, i0] * (1 - sx) + g[j1][:, i1] * sx
        return top * (1 - sy) + bot * sy

    W1, W2 = white(101), white(202)
    ys, xs = np.mgrid[0:S, 0:S].astype(np.float64)
    if kind == "matte":
        d = 0.55 * (2 * W1 - 1) + 0.45 * (2 * vnoise(64, 64, 303) - 1)
    elif kind == "linen":
        rows = hash_u(np.arange(S), 404)[:, None]
        cols = hash_u(np.arange(S), 505)[None, :]
        d = 0.45 * (2 * rows - 1) + 0.45 * (2 * cols - 1) + 0.25 * (2 * W1 - 1)
    elif kind == "watercolor":
        v = 0.5 * vnoise(3, 3, 606) + 0.3 * vnoise(7, 7, 707) + 0.2 * vnoise(16, 16, 808)
        d = 2.2 * (v - 0.5) + 0.25 * (2 * W1 - 1)
    elif kind == "kraft":
        d = 0.6 * (2 * vnoise(64, 6, 909) - 1) + 0.35 * (2 * W1 - 1) + np.where(W2 > 0.992, -1.6, 0)
    elif kind == "canvas":
        d = (0.55 * np.sin(2 * np.pi * (xs + 0.5) / 8) * np.sin(2 * np.pi * (ys + 0.5) / 8)
             + 0.25 * (2 * W1 - 1) + 0.2 * (2 * vnoise(32, 32, 1010) - 1))
    elif kind == "recycled":
        d = (0.3 * (2 * W1 - 1) + 0.3 * (2 * vnoise(48, 48, 1111) - 1)
             + np.where(W2 > 0.996, -2.5, np.where(W2 < 0.002, 1.8, 0)))
    else:
        return None
    return np.clip(np.floor(128 + 127 * TEX_AMP[kind] * d + 0.5), 0, 255)


def apply_texture(img, tex, box=None, anchor=(0, 0)):
    """Hard-light blend of the repeated tile over box (default: the whole image), tiles starting at anchor."""
    import numpy as np
    tile = texture_tile(tex["type"])
    if tile is None:
        return img
    bx, by, w, h = (round(v) for v in (box or (0, 0, *img.size)))
    ox, oy = (bx - round(anchor[0])) % TEX_SIZE, (by - round(anchor[1])) % TEX_SIZE
    B = np.tile(tile, ((h + oy) // TEX_SIZE + 2, (w + ox) // TEX_SIZE + 2))[oy:oy + h, ox:ox + w, None] / 255
    full = np.asarray(img, dtype=np.float64).copy()
    arr = full[by:by + h, bx:bx + w]
    base = arr[..., :3] / 255
    blended = np.where(B <= 0.5, base * 2 * B, base + (2 * B - 1) - base * (2 * B - 1))
    a = tex.get("strength", 60) / 100
    arr[..., :3] = np.clip((base * (1 - a) + blended * a) * 255 + 0.5, 0, 255)
    full[by:by + h, bx:bx + w] = arr
    return Image.fromarray(full.astype(np.uint8), "RGBA")


def gradient_image(gr, w, h):
    """A w x h gradient (same maths as the app)."""
    import numpy as np
    cols = [np.array(ImageColor.getrgb(c)[:3], dtype=float) for c in gr["colors"]]
    if gr["type"] == "corners":   # bilinear blend of the four corner colours
        tl, tr, bl, br = (cols + [cols[-1]] * 4)[:4]
        u = np.linspace(0, 1, w)[None, :, None]
        v = np.linspace(0, 1, h)[:, None, None]
        arr = (tl * (1 - u) + tr * u) * (1 - v) + (bl * (1 - u) + br * u) * v
    else:
        ys, xs = np.mgrid[0:h, 0:w] + 0.5
        cx, cy = w / 2, h / 2
        if gr["type"] == "radial":
            t = np.hypot(xs - cx, ys - cy) / (math.hypot(w, h) / 2)
        else:
            a = math.radians(gr.get("angle", 180))
            dx, dy = math.sin(a), -math.cos(a)
            half = (abs(w * dx) + abs(h * dy)) / 2
            t = ((xs - cx) * dx + (ys - cy) * dy) / (2 * half) + 0.5
        t = np.clip(t, 0, 1)
        stops = np.linspace(0, 1, len(cols)) if len(cols) > 1 else np.array([0.0])
        arr = np.stack([np.interp(t, stops, [c[ch] for c in cols]) for ch in range(3)], axis=-1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def place_background(art, w, h, g):
    """The image fitted into a w x h area: fill / stretch / fit, then rotated, zoomed and moved (same as the app)."""
    plain = g["bg_fit"] == "cover" and not g["bg_rotate"] and g["bg_zoom"] == 100 and not g["bg_x"] and not g["bg_y"]
    if plain:
        return ImageOps.fit(art, (w, h), Image.LANCZOS)
    iw, ih = art.size
    rot = math.radians(g["bg_rotate"])
    c, sn = abs(math.cos(rot)), abs(math.sin(rot))
    bw, bh = iw * c + ih * sn, iw * sn + ih * c
    if g["bg_fit"] == "stretch":
        sx, sy = w / bw, h / bh
    elif g["bg_fit"] == "contain":
        sx = sy = min(w / bw, h / bh)
    else:   # cover: no empty corners even when turned
        sx = sy = max((w * c + h * sn) / iw, (w * sn + h * c) / ih)
    z = g["bg_zoom"] / 100
    turned = art.rotate(-g["bg_rotate"], expand=True, resample=Image.BICUBIC) if g["bg_rotate"] else art
    sized = turned.resize((max(1, rnd(turned.width * sx * z)), max(1, rnd(turned.height * sy * z))), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cx, cy = w / 2 + g["bg_x"] / 100 * w, h / 2 + g["bg_y"] / 100 * h
    pad = max(sized.width, sized.height)
    big = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(sized, (rnd(cx - sized.width / 2) + pad, rnd(cy - sized.height / 2) + pad))
    out.alpha_composite(big.crop((pad, pad, pad + w, pad + h)))
    return out


def draw_guides(img, g):
    """Trim line (cyan) and cut line (magenta) with its safe zone — only on the preview."""
    d, W, H = ImageDraw.Draw(img), g["width"], g["height"]
    trim, cut, b, c = (0, 200, 255, 255), (255, 43, 214, 255), g["bleed"], g["cut_gap"] / 2
    if b:
        d.rectangle((b, b, W - b, H - b), outline=trim, width=3)
    if g["cut"] == "vertical":
        d.line((W / 2, 0, W / 2, H), fill=cut, width=4)
        for x in (W / 2 - c, W / 2 + c):
            d.line((x, 0, x, H), fill=trim, width=3)
    elif g["cut"] == "horizontal":
        d.line((0, H / 2, W, H / 2), fill=cut, width=4)
        for y in (H / 2 - c, H / 2 + c):
            d.line((0, y, W, y), fill=trim, width=3)


def build(g):
    boxes = circle_boxes(g, slot_boxes(g))
    size = (g["width"], g["height"])
    frame = Image.new("RGBA", size, color(g["background"]))
    whole = [{"clip": (0, 0, *size), "area": (0, 0, *size)}]
    strips = strip_areas(g) if g["cut"] != "none" and g["bg_per_half"] else whole
    if g.get("bg_gradient"):
        for st in strips:
            ax, ay, aw, ah = st["area"]
            paste_area(frame, gradient_image(g["bg_gradient"], round(aw), round(ah)), st["area"], st["clip"])
    if g.get("bg_stripes") and g["bg_stripes"].get("type"):
        for st in strips:
            ax, ay, aw, ah = st["area"]
            paste_area(frame, stripes_image(g["bg_stripes"], round(aw), round(ah)), st["area"], st["clip"])
    if g.get("background_image"):
        path = Path(g["background_image"]).expanduser()
        if not path.is_absolute():
            path = HERE / path
        if not path.exists():
            sys.exit(f"[{g['name']}] background image not found: {path}")
        art = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
        # placed in each printed strip (plus bleed) when cutting, so both strips match
        for st in strips:
            ax, ay, aw, ah = st["area"]
            piece = place_background(art, round(aw), round(ah), g)
            if g["bg_opacity"] < 100:   # let the background colour show through
                piece.putalpha(piece.getchannel("A").point(lambda v: v * g["bg_opacity"] // 100))
            paste_area(frame, piece, st["area"], st["clip"])
    draw_pattern(frame, g)
    if g.get("texture") and g["texture"].get("type"):
        for st in (strip_areas(g) if g["cut"] != "none" else whole):
            frame = apply_texture(frame, g["texture"], st["clip"], st["area"][:2])
    g["_tv"] = tv_split(g, boxes)
    post(frame, g, boxes)
    rails(frame, g, boxes)
    slot_stamps(frame, g, boxes)
    tv_bezels(frame, g, boxes)
    if g.get("slot_shadow"):
        slot_shadow(frame, g, boxes)
    for x0, y0, x1, y1, _ in boxes:
        punch(frame, (x0, y0, x1, y1), g["radius"], g["slot"], g.get("slot_shape", "rect"), g.get("radius_corners"))
    slot_depth(frame, g, boxes)
    slot_tv(frame, g, boxes)
    if g.get("slot_border"):
        for b in boxes:
            q, r = tv_screen(b, g)
            slot_border(frame, q, r, g["slot_border"], g.get("slot_shape", "rect"), g.get("radius_corners"))
    line_frame(frame, g, boxes)
    slot_bubbles(frame, g, boxes)
    for hole in film_holes(g):
        punch(frame, hole, film_band(g) * 0.08, g["film_holes"])
    stamp_edge(frame, g)
    draw_text(frame, g, boxes)

    preview = Image.new("RGBA", frame.size, (210, 210, 210, 255))
    preview.alpha_composite(frame)
    draw_guides(preview, g)

    folder = OUT_DIR / g["machine"] / g["name"] if g["machine"] else OUT_DIR / g["name"]
    folder.mkdir(parents=True, exist_ok=True)
    frame.save(folder / f"{g['name']}.png")
    preview.convert("RGB").save(folder / f"{g['name']}_preview.png")
    slots = [{"index": i + 1, "half": b[4] + 1, "x": b[0], "y": b[1], "width": b[2] - b[0], "height": b[3] - b[1]}
             for i, b in enumerate(boxes)]
    (folder / "slots.json").write_text(json.dumps(
        {"name": g["name"], "size": [g["width"], g["height"]], "bleed": g["bleed"],
         "cut": g["cut"], "cut_gap": g["cut_gap"], "radius": g["radius"], "slots": slots}, indent=2))
    w, h = slots[0]["width"], slots[0]["height"]
    halves = " x2 halves" if g["cut"] != "none" else ""
    print(f"✓ {g['name']:<24} {g['rows']}x{g['cols']}{halves}  slot {w}x{h}px  → {folder.relative_to(HERE)}/")


def main():
    p = argparse.ArgumentParser(description="Generate blank photobooth grid templates.")
    p.add_argument("names", nargs="*", help="grid names from grids.json (default: all)")
    p.add_argument("--name", help="name for a one-off grid")
    p.add_argument("--rows", type=int)
    p.add_argument("--cols", type=int)
    int_keys = ["width", "height", "margin", "gap", "header", "footer", "text_size", "bleed", "cut_gap",
                "radius", "film_band", "bg_opacity", "bg_rotate", "bg_zoom", "bg_x", "bg_y"]
    str_keys = ["background", "background_image", "slot", "text", "text_color", "machine", "film_holes", "bg_fit"]
    for key in int_keys:
        p.add_argument(f"--{key.replace('_', '-')}", type=int, dest=key)
    for key in str_keys:
        p.add_argument(f"--{key.replace('_', '-')}", dest=key)
    p.add_argument("--cut", choices=["none", "vertical", "horizontal"])
    p.add_argument("--film", action="store_true", default=None, help="film-reel look with sprocket holes")
    p.add_argument("--save", action="store_true", help="also add the one-off grid to grids.json")
    a = p.parse_args()

    cfg = json.loads(CONFIG.read_text())
    defaults = {**BUILT_IN, **cfg["defaults"]}

    if a.rows or a.cols:
        if not (a.rows and a.cols):
            sys.exit("Give both --rows and --cols")
        custom = {"name": a.name or f"{a.rows}x{a.cols}", "rows": a.rows, "cols": a.cols}
        for key in int_keys + str_keys + ["cut", "film"]:
            if getattr(a, key) is not None:
                custom[key] = getattr(a, key)
        build({**defaults, **custom})
        if a.save:
            cfg["grids"] = [g for g in cfg["grids"] if g["name"] != custom["name"]] + [custom]
            CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
            print(f"  saved '{custom['name']}' to grids.json")
        return

    grids = cfg["grids"]
    if a.names:
        unknown = set(a.names) - {g["name"] for g in grids}
        if unknown:
            sys.exit(f"Not in grids.json: {', '.join(sorted(unknown))}")
        grids = [g for g in grids if g["name"] in a.names]
    for g in grids:
        build({**defaults, **g})


if __name__ == "__main__":
    main()
