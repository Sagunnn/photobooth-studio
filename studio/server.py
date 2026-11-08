#!/usr/bin/env python3
"""Photobooth Studio: a small local server so the browser app can read grids.json
and save designs straight into "Generated Templates/<grid>/".

Start it by double-clicking "Open Photobooth Studio.command" (or: python3 studio/server.py).
Only reachable from this computer (127.0.0.1). Close the Terminal window to quit.
"""
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
CONFIG = ROOT / "grids.json"
OUT_DIR = ROOT / "Generated Templates"
FOLDERS = {"Backgrounds": ROOT / "Backgrounds", "Stickers": ROOT / "Stickers"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
PORT = 8765
MAX_UPLOAD = 300 * 1024 * 1024


def clean(name):
    """Make a safe single file/folder name (no slashes, no '..')."""
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", str(name)).strip().strip(".")
    return name[:120]


def unique(path):
    """Don't overwrite: add -2, -3, ... if the file already exists."""
    n, candidate = 2, path
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        n += 1
    return candidate


_fonts = None


def system_fonts():
    """Font family names installed on this computer (macOS: asks CoreText directly)."""
    global _fonts
    if _fonts is not None:
        return _fonts
    names = set()
    try:
        import ctypes
        import ctypes.util
        ct = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreText"))
        cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation"))
        ct.CTFontManagerCopyAvailableFontFamilyNames.restype = ctypes.c_void_p
        cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]
        cf.CFArrayGetCount.restype = ctypes.c_long
        cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]
        cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
        cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
        cf.CFStringGetCString.restype = ctypes.c_bool
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        arr = ct.CTFontManagerCopyAvailableFontFamilyNames()
        buf = ctypes.create_string_buffer(1024)
        for i in range(cf.CFArrayGetCount(arr)):
            if cf.CFStringGetCString(cf.CFArrayGetValueAtIndex(arr, i), buf, 1024, 0x08000100):  # UTF-8
                names.add(buf.value.decode("utf-8"))
        cf.CFRelease(arr)
    except Exception:  # not macOS: fall back to font file names
        for d in [Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path("/usr/share/fonts"),
                  Path.home() / ".fonts", Path("C:/Windows/Fonts")]:
            if d.is_dir():
                names.update(f.stem for f in d.rglob("*") if f.suffix.lower() in {".ttf", ".otf", ".ttc"})
    _fonts = sorted((n for n in names if not n.startswith(".")), key=str.casefold)
    return _fonts


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_UPLOAD:
            raise ValueError("empty or too large upload")
        return self.rfile.read(length)

    # ---------- GET ----------
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        path = urllib.parse.unquote(url.path)

        if path in ("/", "/index.html"):
            self.path = f"/{APP.name}/web/index.html"
            return super().do_GET()
        if path == "/api/grids":
            return self.send_json(json.loads(CONFIG.read_text(encoding="utf-8")))
        if path == "/api/fonts":
            return self.send_json({"fonts": system_fonts()})
        if path == "/api/list":
            folder = FOLDERS.get(q.get("folder", [""])[0])
            if not folder:
                return self.send_json({"error": "unknown folder"}, 400)
            folder.mkdir(exist_ok=True)
            files = sorted(f.name for f in folder.iterdir()
                           if f.is_file() and f.suffix.lower() in IMAGE_EXT)
            return self.send_json({"files": files})
        if path.split("/")[1] in FOLDERS:
            return super().do_GET()
        self.send_error(404)

    # ---------- POST ----------
    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        try:
            if url.path == "/api/save":
                return self.save_design(q)
            if url.path == "/api/upload":
                return self.upload(q)
            if url.path == "/api/grids":
                return self.save_preset()
            if url.path == "/api/delete":
                return self.delete_file(q)
            self.send_error(404)
        except Exception as e:  # report problems back to the app instead of hanging
            self.send_json({"error": str(e)}, 400)

    def save_design(self, q):
        grid, file = clean(q.get("grid", "")), clean(q.get("file", ""))
        if not grid or not file:
            raise ValueError("missing grid or file name")
        data = self.read_body()
        if not data.startswith(b"\x89PNG"):
            raise ValueError("not a PNG")
        machine = clean(q.get("machine", ""))
        folder = OUT_DIR / machine / grid if machine else OUT_DIR / grid
        folder.mkdir(parents=True, exist_ok=True)
        target = unique(folder / f"{file}.png")
        target.write_bytes(data)
        self.send_json({"path": str(target.relative_to(ROOT))})

    def upload(self, q):
        folder = FOLDERS.get(q.get("folder", ""))
        name = clean(q.get("name", ""))
        if not folder or not name or Path(name).suffix.lower() not in IMAGE_EXT:
            raise ValueError("bad folder or file type")
        folder.mkdir(exist_ok=True)
        target = unique(folder / name)
        target.write_bytes(self.read_body())
        self.send_json({"name": target.name})

    def delete_file(self, q):
        """Move a background/sticker to the macOS Trash (recoverable), not a permanent delete."""
        folder = FOLDERS.get(q.get("folder", ""))
        name = clean(q.get("name", ""))
        if not folder or not name:
            raise ValueError("bad folder or file name")
        source = folder / name
        if not source.is_file():
            raise ValueError(f"{name} not found")
        try:
            target = unique(Path.home() / ".Trash" / name)
            shutil.move(str(source), str(target))
            where = "Trash"
        except OSError:   # Trash not writable: keep it in a local folder instead
            target = unique(ROOT / "Deleted Files" / folder.name / name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            where = str(target.parent.relative_to(ROOT))
        self.send_json({"ok": True, "movedTo": where})

    def save_preset(self):
        grid = json.loads(self.read_body())
        grid["name"] = clean(grid.get("name", ""))
        if not grid["name"]:
            raise ValueError("layout needs a name")
        for key in ("rows", "cols"):
            if not (isinstance(grid.get(key), int) and 1 <= grid[key] <= 20):
                raise ValueError(f"bad {key}")
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        grids = cfg["grids"]
        idx = next((i for i, g in enumerate(grids) if g["name"] == grid["name"]), None)
        if idx is None:
            grids.append(grid)
        else:
            grids[idx] = grid
        CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.send_json({"ok": True, "updated": idx is not None})


def main():
    url = f"http://127.0.0.1:{PORT}/"
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        try:  # already running? just open it again
            urllib.request.urlopen(url + "api/grids", timeout=2)
            webbrowser.open(url)
            print("Photobooth Studio is already running — opened it in your browser.")
            return
        except Exception:
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Photobooth Studio running at {url}")
    print("Keep this window open while you work. Close it (or press Ctrl+C) to quit.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
