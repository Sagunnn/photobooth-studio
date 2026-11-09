# Photobooth Studio

Design photobooth grid frames, drop in photos, add stickers and logos, and export print-ready PNGs.

## What's here

| Path | What it is |
|---|---|
| `studio/web/index.html` | The app (one page: layout, background, caption, photos, stickers, export) |
| `studio/src-tauri/` | Desktop app wrapper (Tauri / Rust): file access, fonts, save dialogs |
| `studio/server.py` | Small local server for running the app in a browser instead |
| `Open Photobooth Studio.command` | Double-click launcher for the browser version (macOS) |
| `grids.json` | Layout presets, grouped by machine (e.g. `G14`) |
| `tools/make_templates.py` | Command-line generator for blank templates from `grids.json` |
| `Original Templates/` | The original PSD and PNG templates the layouts were measured from (kept locally, not in git) |

The app works inside a templates folder containing `grids.json`, `Backgrounds/`, `Stickers/` and
`Generated Templates/` (created as needed). Saved designs go to `Generated Templates/<machine>/<layout>/`.

## Features

- Grid layouts: rows × columns, size, margins, gaps, logo space; presets per machine
- Cut-in-half prints: two matching strips, logos/stickers repeated and centred in both halves
- Print guides (bleed, cut line, safe zone)
- Import a template from a Photoshop `.psd` or a `.png`: copies its size, exact photo slots, rounded corners,
  background colour and (PSD) guides, ready to save as a new layout
- Rounded photo corners (slider from square to fully round)
- 🎞 Film switch: film-reel edges with sprocket holes on any layout, holes in any colour
- Pattern maker: scatter your PNGs behind the photos, with gap, size, randomness, rotation and shuffle
- Layers panel: every sticker and change in one list; hide stickers, or delete any change
- Background: solid colour or gradient (4 corners, linear, radial); image with fill/stretch/fit, rotate, zoom, move and opacity
- Paper textures: matte, linen, watercolour, kraft, canvas, recycled, with strength
- Shadows for stickers, text and the caption: colour, angle, distance, Gaussian blur, opacity
- Stickers: tint (colour or solid), and remove a plain logo background with clean, un-mixed edges
- Print preview: one strip exactly as printed, cropped to the guides
- Backgrounds, built-in graphics and emoji, your own PNG stickers (auto-trims empty edges), text in any installed font
- Export PNG (template with see-through slots, or with photos) or save into the machine/layout folder

## Run it

**Desktop app (macOS):**

```bash
cd studio
npm install
npm run build          # → src-tauri/target/release/bundle/macos/Photobooth Studio.app
```

Needs Rust (`rustup`) and Xcode Command Line Tools. On first launch it uses
`~/Documents/Templates Washing Machine` if it has a `grids.json`, otherwise asks for a folder.

**Browser version:** double-click `Open Photobooth Studio.command` (needs Python 3), or `python3 studio/server.py`.

**Blank templates from the command line** (needs Pillow):

```bash
python3 tools/make_templates.py                 # every layout in grids.json
python3 tools/make_templates.py g14-6cut-split  # one layout
python3 tools/make_templates.py --rows 4 --cols 1 --cut vertical --name my-strips
python3 tools/make_templates.py --rows 4 --cols 1 --cut vertical --film --radius 12 --name my-film
```
