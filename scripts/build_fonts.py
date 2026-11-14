"""Build Hebrew-extended font sheets for Undertale.

Input : extract/fonts/<font>.png + glyphs_<font>.csv  (exported from the user's data.win)
        fonts/otf_bitmaps.json                        (FontStruct "Undertale Hebrew" rasterised, 1 brick = 1 px)
Output: fonts/build/<font>.png + glyphs_<font>.csv    (original sheet + Hebrew glyphs appended below)

Per font we pick an integer pixel scale and align the FontStruct baseline with the game font baseline
(bottom of the game's 'A' glyph rect, since all glyph rects start at the line top).
"""
import json, os, csv
from PIL import Image

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(W, "extract", "fonts")
OUT = os.path.join(W, "fonts", "build")
os.makedirs(OUT, exist_ok=True)

FS = json.load(open(os.path.join(W, "fonts", "otf_bitmaps.json"), encoding="utf-8"))
FS_BASE = 12   # baseline row in otf_bitmaps rows
FS_ORIGIN = 5  # pen origin column in otf_bitmaps rows

# font -> (scale_x, scale_y, extra_shift)
FONTS = {
    "fnt_maintext": (1, 1, 0),
    "fnt_main": (2, 2, 0),
    "fnt_plain": (1, 1, 0),
    "fnt_comicsans": (1, 1, 0),
    "fnt_papyrus": (1, 1, 1),
    "fnt_curs": (2, 2, 0),
    "fnt_plainbig": (4, 4, 0),
}
HEB = [chr(c) for c in range(0x5D0, 0x5EB)]
# extra non-ASCII punctuation we may use (rendered from FontStruct ASCII lookalikes)
EXTRA = {"־": "-", "׳": "'", "״": '"'}


def fs_glyph(ch):
    g = FS[ch]
    rows = g["rows"]
    pts = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"]
    return pts, g["adv"]


def load_font(name):
    rows = open(os.path.join(SRC, f"glyphs_{name}.csv"), encoding="utf-8").read().splitlines()
    head = rows[0]
    glyphs = [list(map(int, r.split(";"))) for r in rows[1:] if r.strip()]
    return head, glyphs


def build(name, sx, sy, extra):
    head, glyphs = load_font(name)
    sheet = Image.open(os.path.join(SRC, f"{name}.png")).convert("RGBA")
    gA = next(g for g in glyphs if g[0] == 65)
    base = gA[4]  # A rect height == baseline (rect top is line top)
    fs_adv_A = FS["A"]["adv"]
    game_adv_A = gA[5]
    new = []
    for ch in HEB + list(EXTRA):
        src = EXTRA.get(ch, ch)
        pts, adv = fs_glyph(src)
        if not pts:
            continue
        minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
        maxy = max(p[1] for p in pts)
        w = (maxx - minx + 1) * sx
        h = base + (maxy - FS_BASE + 1) * sy  # rect from line top to lowest ink row
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for x, y in pts:
            px = (x - minx) * sx
            py = base + (y - FS_BASE) * sy
            for dx in range(sx):
                for dy in range(sy):
                    if 0 <= py + dy < h:
                        img.putpixel((px + dx, py + dy), (255, 255, 255, 255))
        shift = w + sx + extra  # ink width + 1px gap (scaled)
        offset = (minx - FS_ORIGIN) * sx
        new.append((ord(ch), img, shift, offset))
    # pack below the existing sheet
    pad = 2
    width = sheet.width
    x = pad; y = sheet.height + pad; rowh = 0
    placed = []
    for code, img, shift, offset in new:
        if x + img.width + pad > width:
            x = pad; y += rowh + pad; rowh = 0
        placed.append((code, x, y, img, shift, offset))
        x += img.width + pad; rowh = max(rowh, img.height)
    total_h = y + rowh + pad
    hh = 1
    while hh < total_h:
        hh *= 2
    out = Image.new("RGBA", (width, hh), (0, 0, 0, 0))
    out.paste(sheet, (0, 0))
    for code, gx, gy, img, shift, offset in placed:
        out.paste(img, (gx, gy))
    out.save(os.path.join(OUT, f"{name}.png"))
    allg = [g for g in glyphs if g[0] not in {p[0] for p in placed}]
    allg += [[code, gx, gy, img.width, img.height, shift, offset] for code, gx, gy, img, shift, offset in placed]
    allg.sort(key=lambda g: g[0])
    with open(os.path.join(OUT, f"glyphs_{name}.csv"), "w", encoding="utf-8", newline="\n") as f:
        f.write(head + "\n")
        for g in allg:
            f.write(";".join(map(str, g)) + "\n")
    print(f"{name}: +{len(placed)} glyphs, sheet {width}x{hh}, baseline {base}")


if __name__ == "__main__":
    for n, (sx, sy, ex) in FONTS.items():
        build(n, sx, sy, ex)
