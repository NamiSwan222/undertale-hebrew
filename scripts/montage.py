import sys, glob
from PIL import Image
files = sorted(glob.glob(sys.argv[1]))
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
ims = [Image.open(f).convert("RGB") for f in files]
w = int(640 * scale); h = int(480 * scale)
rows = (len(ims) + cols - 1) // cols
m = Image.new("RGB", (w * cols, h * rows), (40, 40, 40))
for i, im in enumerate(ims):
    m.paste(im.resize((w, h), Image.NEAREST), ((i % cols) * w, (i // cols) * h))
m.save(sys.argv[2])
print(len(ims), "->", sys.argv[2])
