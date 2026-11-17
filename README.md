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
| `tools/build_site.js` | Builds the website version (app, layouts, built-in backgrounds and thumbnails) into `site/` |
| `tools/make_backgrounds.js` | Draws the background designs in `Backgrounds/` (laundry and train themes + general set) |
| `Original Templates/` | The original PSD and PNG templates the layouts were measured from (kept locally, not in git) |

The app works inside a templates folder containing `grids.json`, `Backgrounds/`, `Stickers/` and
`Generated Templates/` (created as needed). Saved designs go to `Generated Templates/<machine>/<layout>/`.

## Features

- Grid layouts: rows × columns, size, margins, gaps, logo space; presets per machine
- Cut-in-half prints: two matching strips, logos/stickers repeated and centred in both halves. Switching a layout to
  Left | Right or Top / Bottom (or back) keeps every photo where it is: only the cut line is added
- Other layouts: repeat a sticker at the same spot in the other half (left ↔ right, top ↕ bottom, or all 4 quarters)
- Print guides (bleed, cut line, safe zone)
- Import a template from a Photoshop `.psd` or a `.png`: copies its size, exact photo slots, rounded corners,
  background colour and (PSD) guides, ready to save as a new layout
- Correct a template and save it back, save it as a new one, or delete it (a copy is kept in `Deleted Files/Layouts/`)
- Rounded photo corners (slider from square to fully round), on all four corners or only the ones you pick
- Line frame (invitation-card look): a fine line inside the print guides (never in the bleed or past the cut line)
  and a line round every photo with a gap of background between, in a colour or gold / silver / rose gold foil, single
  or double, with sharp or rounded corners
- Photo border: a coloured line inside or around every photo slot, any thickness, in a colour or gold / silver / rose gold foil, with an optional 3D bevel
- 🚂 Train track (for a top-view booth): a railway seen from above runs under every line of photos (sleepers, rails,
  couplings in the gaps), so the photos look like carriages. "Make it a train from above" sets it all up in one click:
  gravel background, carriage frames, the track and an engine (or a steam train in the logo space when it's short).
  Train graphics (top-view engine, track, steam train, wagon, ticket, platform sign, crossing, signal…), four Train
  backgrounds (gravel, metro tiles, tickets, rail map), train phrases in Cute words, and a train edition of the
  newspaper graphics ("The Photo Express" masthead, headlines, NOW DEPARTING bar, ON TIME stamp, a Nepali headline)
- Stamp edges: each photo on postage-stamp paper with perforated edges (paper colour, edge, hole size, soft shadow),
  or the whole print's edge perforated like one big stamp
- Depth: an inner shadow falling onto the photo (or a shadow around it), a glass/mirror shine, and soap bubbles over the photos (all over, or only near the edges)
- Photo shape: rectangle, circle, oval, arch or old-TV-screen windows on any layout; circles can grow up to the guidelines
- CCTV graphics: CAUGHT ON CAMERA (sign, tape, buttons, REC badge, headline, and single-line text in three styles), CCTV / SMILE YOU'RE ON CAMERA warning signs, caution tape, hazard stripes, a warning triangle, a REC badge,
  a CCTV camera, and booth buttons (TAKE PHOTO, START, PRINT, RETAKE…) with a yellow-and-black caution border
- 📺 Retro TV: a dark TV casing round each photo (as thick as you like: when there isn't room between the photos it covers the photo's edge and the screen gets smaller), and see-through screen effects over the photo (scanlines, green
  tint, dark curved edges, static scratches, a glitch block, on-screen text like ● REC and a timestamp)
- One-photo layouts: make the photo window smaller (any rectangle or a square) and move it around, always inside the original photo window
- Stripes, checks and gingham in two colours (or one colour over the background), with size, thickness, angle and opacity
- 50+ background designs in `Backgrounds/`, with a theme filter (Laundry, Train, Newspaper, Classic, Y2K, Wedding, Party, Graduation, Seasonal, Minimal)
- 🎞 Film switch: film-reel edges with sprocket holes on any layout, holes in any colour; on 2-column layouts,
  "Two film strips" gives each half its own film edges like a cut print (holes down the middle too)
- Pattern maker: scatter your PNGs behind the photos, with gap, size, randomness, rotation and shuffle
- Layers panel: every sticker and change in one list; drag stickers to put them in front of / behind each other
  (or ⌘] / ⌘[, ⇧ for front / back); hide stickers, or delete any change
- Undo (⌘Z) for stickers and template changes alike (a whole slider drag is one step)
- New window (⌘N): work on several designs side by side; each window's title shows its template
- Picks up where you left off: each window's design (template, changes, stickers) is saved as you work, and the
  windows that were open come back when the app is reopened (test photos aren't kept)
- Background: solid colour or gradient (4 corners, linear, radial); image with fill/stretch/fit, rotate, zoom (up to 800%),
  move and opacity; drag it on the page and scroll to zoom
- Paper textures: matte, linen, watercolour, kraft, canvas, recycled, with strength
- Shadows for stickers, text and the caption: colour, angle, distance, Gaussian blur, opacity
- Stickers: tint (colour, solid, black & white or gold foil), and remove a plain logo background with clean, un-mixed edges
- Soft eraser: brush away a sticker's edges with adjustable size, softness and strength (and a restore brush)
  so pictures blend into the background
- Print preview: one strip exactly as printed, cropped to the guides; copy it (⌘C) or save it as a PNG at full size
- 166 built-in graphics in groups (Party, Love, Captions, Social, Words, Props, Decor, Buttons, Care labels, Newspaper, CCTV, Train, Seasonal),
  500+ emoji in groups, emoticons and kaomoji (added as editable text), backgrounds, your own PNG stickers (auto-trims empty edges), text in any installed font
  (double-click text on the page to type it there)
- Wedding typography: names, initials, a date and a line in 11 styles (scripts, serifs, monogram ring, crest, laurel
  wreath, interlocked initials…) in a colour or gold / silver / rose gold; select it later to change the names
- 📱 Social post: the print looks like a social media post: a card behind the photos, the account name (avatar ring,
  blue tick, place) above them when there's room, and like / comment / share / save icons, carousel dots, likes, the
  caption and the time in the biggest free space below or beside the photos. Light or dark; every word can be changed
- Social buttons (generic, no app logos): like / comment / share icons, like and activity bubbles, Follow, Following,
  double-tap heart, a comment, Liked by…, blue tick, LIVE, your story, #photobooth, TAG US, views, NEW POST, 10K followers,
  a post header and footer
- Caption lines: 49 ready-made lines (short & sweet, funny & sassy, friends, couples, beauty, Nepali) added as editable
  text in a matching look; long lines split over two or three lines
- Captions: photobooth and beauty captions (Strike a pose, Picture perfect, Say cheese, 3·2·1 SMILE!, Glow up, Flawless,
  Beauty mode ON, Slay, Main character, Gorgeous…) and Nepali ones (मुस्कुराउनुहोस्!, फोटो खिचौं!, कति राम्री!, सुन्दर पल)
- Cute words: photobooth word stickers in English or Nepali (bubble letters, heart + words, star burst, words down a
  pill, star tag, die-cut) with ready-made phrases and colour sets; select one later to change its words
- Black text graphics show on a light tile in the library, and turn white by themselves when dropped on a dark part of
  the page (Tint changes them back)
- Paste (⌘V) or drag graphics from Canva or a web page: embedded images, image links and inline SVG all work
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

**Website:** <https://photobooth.sagunpradhan.com.np> runs the same app with no install. Every push to `main` rebuilds it
(`.github/workflows/pages.yml` runs `node tools/build_site.js site`). On the website the built-in backgrounds are drawn
by `make_backgrounds.js`, your own backgrounds, stickers and saved layouts stay in that browser, and Export downloads the PNG.
Your local `Backgrounds/` and `Stickers/` folders are never published.

**Blank templates from the command line** (needs Pillow):

```bash
python3 tools/make_templates.py                 # every layout in grids.json
python3 tools/make_templates.py g14-6cut-split  # one layout
python3 tools/make_templates.py --rows 4 --cols 1 --cut vertical --name my-strips
python3 tools/make_templates.py --rows 4 --cols 1 --cut vertical --film --radius 12 --name my-film
```
