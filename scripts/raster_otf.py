"""Rasterize the FontStruct OTF to exact pixel bitmaps (1 brick = 1 pixel)."""
import sys, json
from PIL import Image, ImageDraw, ImageFont
OTF = sys.argv[1]
BRICK_UNITS = 2000/9          # FontStruct brick size in font units (em=2000)
S = 100                       # px per brick when sampling
em_px = int(2000/BRICK_UNITS*S)
font = ImageFont.truetype(OTF, em_px)
asc_units = 2000  # ascender
out = {}
chars = [chr(c) for c in range(0x5d0, 0x5eb)] + [chr(c) for c in range(32,127)]
for ch in chars:
    W = 30*S; H = 20*S
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    # baseline at y = 12 bricks
    d.text((5*S, 12*S), ch, font=font, fill=255, anchor="ls")
    adv = font.getlength(ch)/S
    rows = []
    for by in range(20):
        row = ""
        for bx in range(30):
            row += "#" if im.getpixel((bx*S+S//2, by*S+S//2)) > 127 else "."
        rows.append(row)
    out[ch] = {"adv": round(adv,2), "rows": rows}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
