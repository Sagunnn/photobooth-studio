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
    film       true = film-reel look: sprocket holes down both long edges of every strip
    film_band  width of the sprocket-hole edge (110px); photos move inward to make room
    film_holes hole colour ("#FFFFFF", or "transparent")
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
            "film_holes": "#FFFFFF", "text_shadow": None, "texture": None, "bg_gradient": None, "bg_opacity": 100, "bg_fit": "cover", "bg_rotate": 0, "bg_zoom": 100,
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
    for half, (rx, ry, rw, rh, l, r, t, b) in enumerate(regions(g)):
        slot_w = int((rw - l - r - g["gap"] * (g["cols"] - 1)) // g["cols"])
        slot_h = int((rh - t - b - g["gap"] * (g["rows"] - 1)) // g["rows"])
        if slot_w <= 10 or slot_h <= 10:
            sys.exit(f"[{g['name']}] margins/gaps/header/footer leave no room for photos")
        for row in range(g["rows"]):
            for col in range(g["cols"]):
                x = round(rx + l + col * (slot_w + g["gap"]))
                y = round(ry + t + row * (slot_h + g["gap"]))
                boxes.append((x, y, x + slot_w, y + slot_h, half))
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


def punch(img, box, radius, fill):
    """Fill a (rounded) rectangle with a colour, or make it see-through. Corners are smoothed."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    r = max(0, min(radius, w / 2, h / 2))
    rgba = color(fill)
    if r < 1:
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgba)
        return
    s = 4   # draw 4x bigger, then shrink = smooth edges
    big = Image.new("L", (w * s, h * s), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=r * s, fill=255)
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
    for half, (x, y, w, h, *_) in enumerate(regions(g)):
        for side, trim in strip_sides(g, half).items():
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
    boxes = slot_boxes(g)
    size = (g["width"], g["height"])
    frame = Image.new("RGBA", size, color(g["background"]))
    whole = [{"clip": (0, 0, *size), "area": (0, 0, *size)}]
    strips = strip_areas(g) if g["cut"] != "none" and g["bg_per_half"] else whole
    if g.get("bg_gradient"):
        for st in strips:
            ax, ay, aw, ah = st["area"]
            paste_area(frame, gradient_image(g["bg_gradient"], round(aw), round(ah)), st["area"], st["clip"])
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
    for x0, y0, x1, y1, _ in boxes:
        punch(frame, (x0, y0, x1, y1), g["radius"], g["slot"])
    for hole in film_holes(g):
        punch(frame, hole, film_band(g) * 0.08, g["film_holes"])
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
