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
| `make_templates.py` | Command-line generator for blank templates from `grids.json` |

The app works inside a templates folder containing `grids.json`, `Backgrounds/`, `Stickers/` and
`Generated Templates/` (created as needed). Saved designs go to `Generated Templates/<machine>/<layout>/`.

## Features

- Grid layouts: rows × columns, size, margins, gaps, logo space; presets per machine
- Cut-in-half prints: two matching strips, logos/stickers repeated and centred in both halves
- Print guides (bleed, cut line, safe zone); reads guides straight from Photoshop `.psd` files
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
python3 make_templates.py                 # every layout in grids.json
python3 make_templates.py g14-6cut-split  # one layout
python3 make_templates.py --rows 4 --cols 1 --cut vertical --name my-strips
```
