#!/usr/bin/env python3
"""Generate blank photobooth grid templates.

Each grid is saved to its own folder:
    Generated Templates/<name>/<name>.png     the frame (photo slots are see-through)
    Generated Templates/<name>/<name>_preview.png   grey slots + print guides drawn on, easy to eyeball
    Generated Templates/<name>/slots.json     pixel position of every photo slot

Usage:
    python3 make_templates.py                      # build every grid in grids.json
    python3 make_templates.py 4-cut 8-cut          # build only these
    python3 make_templates.py --rows 3 --cols 1 --name 3-cut-strip   # one-off grid
    python3 make_templates.py --rows 3 --cols 1 --name 3-cut-strip --save   # ...and add it to grids.json
    python3 make_templates.py 4-cut --background-image Backgrounds/flowers.jpg   # use an image as the frame background
    python3 make_templates.py --rows 4 --cols 1 --cut vertical --name my-strips  # two matching strips, cut down the middle

background_image (in grids.json or --background-image) is scaled to cover the whole frame;
paths are relative to this folder. Without it, the solid "background" colour is used.

machine (optional, e.g. "G14") puts that grid's output in Generated Templates/<machine>/<name>/.

Print settings (match the guides in the PSDs):
    bleed      trim line distance from every edge (45px)
    cut        "none", "vertical" (left | right strips) or "horizontal" (top / bottom strips)
    cut_gap    space across the cut line, half on each side (90px = guides at 915 / 960 / 1005)
    With a cut, rows x cols are per half, and the caption + background repeat in each half.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "grids.json"
OUT_DIR = HERE / "Generated Templates"
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
BUILT_IN = {"background": "#000000", "background_image": "", "slot": "transparent", "text": "",
            "text_color": "#FFFFFF", "text_size": 110, "bleed": 45, "cut": "none", "cut_gap": 90,
            "bg_per_half": True, "machine": ""}


def color(value):
    if value == "transparent":
        return (0, 0, 0, 0)
    return ImageColor.getcolor(value, "RGBA")


def load_font(size):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def regions(g):
    """The whole page, or two matching halves when it will be cut.
    Returns (x, y, w, h, inset_left, inset_right, inset_top, inset_bottom) for each."""
    W, H, m, c = g["width"], g["height"], g["margin"], g["cut_gap"] / 2
    start, end = m + g["header"], g["footer"] or m
    if g["cut"] == "vertical":
        return [(0, 0, W / 2, H, m, c, start, end), (W / 2, 0, W / 2, H, c, m, start, end)]
    if g["cut"] == "horizontal":   # strip ends (header/footer) are left/right here
        return [(0, 0, W, H / 2, start, end, m, c), (0, H / 2, W, H / 2, start, end, c, m)]
    return [(0, 0, W, H, m, m, start, end)]


def slot_boxes(g):
    """Split each region into rows x cols equal slots. Returns [(x0, y0, x1, y1, half)]."""
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


def band_center(g, region, half_boxes):
    """Centre of the caption/logo strip in one half."""
    rx, ry, rw, rh = region[:4]
    first, last = half_boxes[0], half_boxes[-1]
    footer_side = g["footer"] >= g["header"]
    if g["cut"] == "horizontal":
        a, z = (last[2], rx + rw) if footer_side else (rx, first[0])
        return (a + z) / 2, ry + rh / 2
    a, z = (last[3], ry + rh) if footer_side else (ry, first[1])
    return rx + rw / 2, (a + z) / 2


def draw_text(img, g, boxes):
    if not g.get("text"):
        return
    font = load_font(g["text_size"])
    for half, region in enumerate(regions(g)):
        cx, cy = band_center(g, region, [b for b in boxes if b[4] == half])
        # draw on its own layer so it can be rotated for top/bottom-cut strips
        l, t, r, b = font.getbbox(g["text"])
        layer = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((10 - l, 10 - t), g["text"], font=font, fill=color(g["text_color"]))
        if g["cut"] == "horizontal":
            layer = layer.rotate(90, expand=True)   # reads upright when the strip is held vertically
        img.alpha_composite(layer, (round(cx - layer.width / 2), round(cy - layer.height / 2)))


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
    if g.get("background_image"):
        path = Path(g["background_image"]).expanduser()
        if not path.is_absolute():
            path = HERE / path
        if not path.exists():
            sys.exit(f"[{g['name']}] background image not found: {path}")
        art = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
        # scale to cover (each half when cutting), cropping the overflow from the centre
        areas = regions(g) if g["cut"] != "none" and g["bg_per_half"] else [(0, 0, *size)]
        for rx, ry, rw, rh, *_ in areas:
            frame.alpha_composite(ImageOps.fit(art, (round(rw), round(rh)), Image.LANCZOS), (round(rx), round(ry)))
    d = ImageDraw.Draw(frame)
    for x0, y0, x1, y1, _ in boxes:
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=color(g["slot"]))
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
         "cut": g["cut"], "cut_gap": g["cut_gap"], "slots": slots}, indent=2))
    w, h = slots[0]["width"], slots[0]["height"]
    halves = " x2 halves" if g["cut"] != "none" else ""
    print(f"✓ {g['name']:<24} {g['rows']}x{g['cols']}{halves}  slot {w}x{h}px  → {folder.relative_to(HERE)}/")


def main():
    p = argparse.ArgumentParser(description="Generate blank photobooth grid templates.")
    p.add_argument("names", nargs="*", help="grid names from grids.json (default: all)")
    p.add_argument("--name", help="name for a one-off grid")
    p.add_argument("--rows", type=int)
    p.add_argument("--cols", type=int)
    int_keys = ["width", "height", "margin", "gap", "header", "footer", "text_size", "bleed", "cut_gap"]
    str_keys = ["background", "background_image", "slot", "text", "text_color", "machine"]
    for key in int_keys:
        p.add_argument(f"--{key.replace('_', '-')}", type=int, dest=key)
    for key in str_keys:
        p.add_argument(f"--{key.replace('_', '-')}", dest=key)
    p.add_argument("--cut", choices=["none", "vertical", "horizontal"])
    p.add_argument("--save", action="store_true", help="also add the one-off grid to grids.json")
    a = p.parse_args()

    cfg = json.loads(CONFIG.read_text())
    defaults = {**BUILT_IN, **cfg["defaults"]}

    if a.rows or a.cols:
        if not (a.rows and a.cols):
            sys.exit("Give both --rows and --cols")
        custom = {"name": a.name or f"{a.rows}x{a.cols}", "rows": a.rows, "cols": a.cols}
        for key in int_keys + str_keys + ["cut"]:
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
