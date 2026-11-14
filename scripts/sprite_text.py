"""Helpers for redrawing Undertale images with Hebrew text in the game's pixel-font style.

    import sys; sys.path.insert(0, r"<workspace>\\scripts")
    from sprite_text import *
    im = load_sprite("spr_gameoverbg", 0)          # full-size RGBA frame (from extract/allspr or exported on demand)
    clear(im, (x0, y0, x1, y1))                    # erase old text: fills with the surrounding colour (or color=...)
    t = text_image("המשחק נגמר", scale=4, color=(255,255,255,255), outline=None)
    paste_center(im, t, (x0, y0, x1, y1))          # or paste(im, t, x, y)
    save_sprite(im, "spr_gameoverbg", 0)           # -> fonts/sprites/<name>__<frame>.png (picked up by the build)

Backgrounds: load_bg(name) / save_bg(im, name).
Text is given in LOGICAL order (as typed); text_image() lays it out right to left, keeps Latin/digit runs LTR,
mirrors brackets. Glyphs come from the FontStruct Hebrew font (1 brick = 1 px), Latin from the same font.
scale may be an int or (sx, sy). letter_gap is in font pixels (before scaling).
"""
import json, os, glob, subprocess
from PIL import Image

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FS = json.load(open(os.path.join(W, "fonts", "otf_bitmaps.json"), encoding="utf-8"))
BASE, ORIGIN = 12, 5
SPR_OUT = os.path.join(W, "fonts", "sprites")
BG_OUT = os.path.join(W, "fonts", "backgrounds")
os.makedirs(SPR_OUT, exist_ok=True); os.makedirs(BG_OUT, exist_ok=True)
MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "<": ">", ">": "<", "{": "}", "}": "{"}


def _cls(c):
    o = ord(c)
    if 0x590 <= o <= 0x5FF:
        return 1
    if c.isalnum():
        return 2
    return 0


def visual(s):
    """Logical -> visual order (left to right) for one line, same rules as the in-game wrapper."""
    cls = [_cls(c) for c in s]
    if 1 not in cls:
        return s
    n = len(s); i = 0
    while i < n:
        if cls[i] == 0:
            j = i
            while j < n and cls[j] == 0:
                j += 1
            if i > 0 and j < n and cls[i - 1] == 2 and cls[j] == 2:
                for k in range(i, j):
                    cls[k] = 2
            i = j
        else:
            i += 1
    out = []; i = n - 1
    while i >= 0:
        if cls[i] == 2:
            j = i
            while j > 0 and cls[j - 1] == 2:
                j -= 1
            out.append(s[j:i + 1]); i = j - 1
        else:
            out.append(MIRROR.get(s[i], s[i])); i -= 1
    return "".join(out)


def _glyph(ch):
    g = FS.get(ch)
    if g is None:
        raise KeyError(f"no glyph for {ch!r}")
    pts = [(x, y) for y, r in enumerate(g["rows"]) for x, c in enumerate(r) if c == "#"]
    return pts, g["adv"]


def text_image(text, scale=1, color=(255, 255, 255, 255), outline=None, letter_gap=1, space=4, line_gap=3,
               align="right"):
    """Render (multi-line with '\\n') text. Returns RGBA image tightly cropped vertically to the font's line box."""
    sx, sy = (scale, scale) if isinstance(scale, (int, float)) else scale
    lines = [visual(l) for l in text.split("\n")]
    rendered = []
    for line in lines:
        cols = []  # list of (pts, minx, width)
        for ch in line:
            if ch == " ":
                cols.append(([], 0, space)); continue
            pts, adv = _glyph(ch)
            if not pts:
                cols.append(([], 0, space)); continue
            mn = min(p[0] for p in pts); mx = max(p[0] for p in pts)
            cols.append((pts, mn, mx - mn + 1))
        width = sum(w for _, _, w in cols) + letter_gap * max(0, len(cols) - 1)
        rendered.append((cols, width))
    top, bottom = 0, 19  # all rows of the FontStruct raster (result is cropped to the ink)
    lh = bottom - top + 1
    W_ = max(w for _, w in rendered) if rendered else 1
    H_ = lh * len(rendered) + line_gap * (len(rendered) - 1)
    pad = 1 if outline else 0
    img = Image.new("RGBA", (int((W_ + 2 * pad) * sx), int((H_ + 2 * pad) * sy)), (0, 0, 0, 0))
    def put(x, y, c):
        for dx in range(int(sx)):
            for dy in range(int(sy)):
                px, py = int(x * sx) + dx, int(y * sy) + dy
                if 0 <= px < img.width and 0 <= py < img.height:
                    if c is color or img.getpixel((px, py))[3] == 0:
                        img.putpixel((px, py), c)
    for li, (cols, width) in enumerate(rendered):
        x0 = {"right": W_ - width, "left": 0, "center": (W_ - width) // 2}[align] + pad
        y0 = li * (lh + line_gap) + pad
        x = x0
        for pts, mn, w in cols:
            for (gx, gy) in pts:
                if top <= gy <= bottom:
                    if outline:
                        for ox in (-1, 0, 1):
                            for oy in (-1, 0, 1):
                                put(x + gx - mn + ox, y0 + gy - top + oy, outline)
            for (gx, gy) in pts:
                if top <= gy <= bottom:
                    put(x + gx - mn, y0 + gy - top, color)
            x += w + letter_gap
    return img.crop(img.getbbox()) if img.getbbox() else img


def fit_scale(text, box_w, box_h, max_scale=8, **kw):
    """Largest integer scale whose rendering fits the box."""
    for s in range(max_scale, 0, -1):
        t = text_image(text, scale=s, **kw)
        if t.width <= box_w and t.height <= box_h:
            return s
    return 1


def _ensure_frame(name, frame):
    p = os.path.join(W, "extract", "allspr", f"{name}__{frame}.png")
    if os.path.exists(p):
        return p
    # export every frame of this sprite on demand
    out = os.path.join(W, "extract", "allspr")
    script = os.path.join(W, "scripts", "export_sprites_frames.csx")
    cli = os.path.join(W, "tools", "utmt", "UndertaleModCli.exe")
    env = dict(os.environ, UTHE_OUT=out, UTHE_SPRITES=name)
    subprocess.run([cli, "load", os.path.join(W, "backup", "data.win.orig"), "-s", script], env=env,
                   stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    return p


def load_sprite(name, frame=0):
    return Image.open(_ensure_frame(name, frame)).convert("RGBA")


def load_bg(name):
    return Image.open(os.path.join(W, "extract", "allbg", f"{name}.png")).convert("RGBA")


def surrounding_color(im, box):
    from collections import Counter
    x0, y0, x1, y1 = box
    ring = []
    for x in range(max(0, x0 - 1), min(im.width, x1 + 2)):
        for y in (y0 - 1, y1 + 1):
            if 0 <= y < im.height:
                ring.append(im.getpixel((x, y)))
    for y in range(max(0, y0), min(im.height, y1 + 1)):
        for x in (x0 - 1, x1 + 1):
            if 0 <= x < im.width:
                ring.append(im.getpixel((x, y)))
    return Counter(ring).most_common(1)[0][0] if ring else (0, 0, 0, 0)


def clear(im, box, color=None):
    """Fill box (inclusive x0,y0,x1,y1) with color, default = most common colour just outside the box."""
    c = color if color is not None else surrounding_color(im, box)
    x0, y0, x1, y1 = box
    for x in range(max(0, x0), min(im.width, x1 + 1)):
        for y in range(max(0, y0), min(im.height, y1 + 1)):
            im.putpixel((x, y), c)
    return im


def paste(im, t, x, y):
    im.alpha_composite(t, (int(x), int(y)))
    return im


def paste_center(im, t, box):
    x0, y0, x1, y1 = box
    return paste(im, t, x0 + ((x1 - x0 + 1) - t.width) // 2, y0 + ((y1 - y0 + 1) - t.height) // 2)


def save_sprite(im, name, frame):
    im.save(os.path.join(SPR_OUT, f"{name}__{frame}.png"))


def save_bg(im, name):
    im.save(os.path.join(BG_OUT, f"{name}.png"))


def preview(paths_or_images, out, scale=2):
    """Side-by-side preview image (for checking your work with the Read tool)."""
    ims = [Image.open(p).convert("RGBA") if isinstance(p, str) else p for p in paths_or_images]
    w = sum(i.width for i in ims) + 4 * len(ims); h = max(i.height for i in ims)
    m = Image.new("RGBA", (w, h), (40, 40, 60, 255)); x = 0
    for i in ims:
        bg = Image.new("RGBA", i.size, (0, 0, 0, 255)); bg.alpha_composite(i); m.paste(bg, (x, 0)); x += i.width + 4
    m.resize((m.width * scale, m.height * scale), Image.NEAREST).save(out)
    return out
