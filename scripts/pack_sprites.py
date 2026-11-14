"""Pack every redrawn sprite frame (fonts/sprites/<sprite>__<frame>.png, full sprite size) into atlas pages
build/sprite_pages/page_N.png + atlas.json  ->  consumed by build_hebrew.csx."""
import glob, os, json
from PIL import Image
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(W, "fonts", "sprites")
OUT = os.path.join(W, "build", "sprite_pages"); os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*")):
    os.remove(f)
PAGE = 2048
frames = []
for p in sorted(glob.glob(os.path.join(SRC, "*.png"))):
    b = os.path.basename(p)[:-4]
    if "__" in b:
        name, fr = b.rsplit("__", 1)
    else:
        name, fr = b.rsplit("_", 1)
    frames.append((name, int(fr), Image.open(p).convert("RGBA")))
for p in sorted(glob.glob(os.path.join(W, "fonts", "backgrounds", "*.png"))):
    frames.append(("BG:" + os.path.basename(p)[:-4], 0, Image.open(p).convert("RGBA")))
frames.sort(key=lambda t: -t[2].height)
pages, atlas = [], []
cur = Image.new("RGBA", (PAGE, PAGE), (0, 0, 0, 0)); x = y = rowh = 0
for name, fr, im in frames:
    if x + im.width + 2 > PAGE:
        x = 0; y += rowh + 2; rowh = 0
    if y + im.height + 2 > PAGE:
        pages.append(cur); cur = Image.new("RGBA", (PAGE, PAGE), (0, 0, 0, 0)); x = y = rowh = 0
    cur.paste(im, (x, y))
    atlas.append({"sprite": name, "frame": fr, "page": len(pages), "x": x, "y": y, "w": im.width, "h": im.height})
    x += im.width + 2; rowh = max(rowh, im.height)
pages.append(cur)
for i, pg in enumerate(pages):
    pg.save(os.path.join(OUT, f"page_{i}.png"))
json.dump(atlas, open(os.path.join(OUT, "atlas.json"), "w"), indent=0)
print(f"sprite frames: {len(atlas)} on {len(pages)} page(s)")
