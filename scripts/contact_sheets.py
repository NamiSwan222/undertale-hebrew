"""Numbered contact sheets of first sprite frames + backgrounds, for finding images with text."""
import glob, os, json
from PIL import Image, ImageDraw
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = []
for p in sorted(glob.glob(os.path.join(W, "extract", "allspr", "*__0.png"))):
    items.append(("spr", os.path.basename(p)[:-7], p))
for p in sorted(glob.glob(os.path.join(W, "extract", "allbg", "*.png"))):
    items.append(("bg", os.path.basename(p)[:-4], p))
items = [it for it in items if not (Image.open(it[2]).size[0] < 10 or Image.open(it[2]).size[1] < 6)]
CW, CH, COLS, ROWS = 240, 180, 5, 4
index = {}
sheet_n = 0
for start in range(0, len(items), COLS * ROWS):
    sheet = Image.new("RGB", (CW * COLS, (CH + 14) * ROWS), (60, 60, 90))
    d = ImageDraw.Draw(sheet)
    for k, (kind, name, p) in enumerate(items[start:start + COLS * ROWS]):
        num = start + k
        im = Image.open(p).convert("RGBA")
        s = min(CW / im.width, CH / im.height, 3)
        s = int(s) if s >= 1 else s
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)
        bgc = Image.new("RGBA", im.size, (0, 0, 0, 255)); bgc.alpha_composite(im)
        x = (k % COLS) * CW; y = (k // COLS) * (CH + 14)
        sheet.paste(bgc, (x + (CW - im.width) // 2, y + (CH - im.height) // 2))
        d.text((x + 3, y + CH + 1), f"{num}", fill=(255, 255, 0))
        index[num] = [kind, name]
    sheet.save(os.path.join(W, "extract", "sheets", f"sheet_{sheet_n:03d}.png"))
    sheet_n += 1
json.dump(index, open(os.path.join(W, "extract", "sheets", "index.json"), "w"), indent=0)
print(len(items), "images,", sheet_n, "sheets")
