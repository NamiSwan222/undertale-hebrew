"""Hebrew battle buttons: replace the English word on each button sprite frame with a Hebrew word
drawn from the FontStruct glyphs (scaled 2x wide, 3x tall), in the frame's own text colour.
Input : extract/sprites/<sprite>_<frame>.png ; Output: fonts/sprites/<sprite>_<frame>.png
"""
import json, os, glob
from PIL import Image

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(W, "extract", "sprites")
OUT = os.path.join(W, "fonts", "sprites"); os.makedirs(OUT, exist_ok=True)
FS = json.load(open(os.path.join(W, "fonts", "otf_bitmaps.json"), encoding="utf-8"))

WORDS = {"fightbt": "הילחם", "talkbt": "פעולה", "actbt": "פעולה", "itembt": "חפצים", "sparebt": "רחמים"}
SX, SY = 2, 3


def word_image(word, color):
    glyphs = []
    for ch in reversed(word):  # visual order (left to right)
        rows = FS[ch]["rows"]
        pts = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"]
        minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
        glyphs.append((pts, minx, maxx))
    gap = 1
    width = sum((mx - mn + 1) * SX for _, mn, mx in glyphs) + gap * SX * (len(glyphs) - 1)
    top = min(p[1] for g, _, _ in glyphs for p in g if p[1] <= 12)
    bottom = max(p[1] for g, _, _ in glyphs for p in g)
    img = Image.new("RGBA", (width, (bottom - top + 1) * SY), (0, 0, 0, 0))
    x0 = 0
    for pts, mn, mx in glyphs:
        for x, y in pts:
            for dx in range(SX):
                for dy in range(SY):
                    img.putpixel(((x - mn) * SX + dx + x0, (y - top) * SY + dy), color)
        x0 += (mx - mn + 1) * SX + gap * SX
    return img, (12 - top) * SY  # baseline offset from image top


def process(path, word):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    # text = opaque pixels right of the icon area, inside the border
    def bright(px):
        return px[3] > 0 and (px[0] + px[1] + px[2]) > 120
    pts = [(x, y) for x in range(28, w - 5) for y in range(5, h - 5) if bright(im.getpixel((x, y)))]
    if not pts:
        return None
    x0 = min(p[0] for p in pts); x1 = max(p[0] for p in pts)
    y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
    from collections import Counter
    color = Counter(im.getpixel(p) for p in pts).most_common(1)[0][0]
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            px = im.getpixel((x, y))
            im.putpixel((x, y), (0, 0, 0, px[3]))
    wi, base = word_image(word, color)
    # fit horizontally into the old text box, baseline at the old text bottom
    if wi.width > (x1 - x0 + 1) + 6:
        wi = wi.resize((x1 - x0 + 7, wi.height), Image.NEAREST)
    cx = (x0 + x1 + 1) // 2 - wi.width // 2
    cy = y1 + 1 - base
    im.alpha_composite(wi, (max(0, cx), max(0, cy)))
    return im


def main():
    n = 0
    for path in sorted(glob.glob(os.path.join(SRC, "spr_*bt*_[0-9].png"))):
        name = os.path.basename(path)
        if "_ja_" in name or name.startswith("spr_savebt") or name.startswith("spr_spellbt"):
            continue
        key = next((k for k in WORDS if name.startswith("spr_" + k)), None)
        if not key:
            continue
        im = process(path, WORDS[key])
        if im:
            im.save(os.path.join(OUT, name)); n += 1
    print("buttons:", n)


if __name__ == "__main__":
    main()
