"""Redraw the English-text sprites from translation/audit_sprites_a.json with Hebrew.

Run:  python scripts/sprites/redraw_a.py            (writes fonts/sprites/<name>__<frame>.png)
      python scripts/sprites/redraw_a.py --preview  (also writes original|new previews to a scratch dir)

Notes on every image (redrawn or kept) are in translation/notes/sprites_a.md.
"""
import os, sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from sprite_text import (Image, text_image, clear, paste, save_sprite, preview, load_sprite)

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)
DONE = []  # (name, frame) for previews


# ---------------------------------------------------------------- helpers
def is_col(c):
    return lambda p: p[3] > 0 and p[:3] == c[:3]


def bbox_of(im, pred, box=None):
    """Inclusive bbox of pixels matching pred inside box (inclusive)."""
    x0, y0, x1, y1 = box or (0, 0, im.width - 1, im.height - 1)
    pts = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if pred(im.getpixel((x, y)))]
    if not pts:
        return None
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def recolor(im, box, pred, color):
    x0, y0, x1, y1 = box
    for y in range(max(0, y0), min(im.height, y1 + 1)):
        for x in range(max(0, x0), min(im.width, x1 + 1)):
            if pred(im.getpixel((x, y))):
                im.putpixel((x, y), color)


def bold(t, dx=1):
    """Thicken strokes horizontally by dx pixels."""
    o = Image.new("RGBA", (t.width + dx, t.height), CLEAR)
    for i in range(dx, -1, -1):
        o.alpha_composite(t, (i, 0))
    return o


def italic(t, step):
    """Shear: every `step` rows from the bottom shift one pixel further right."""
    h = t.height
    o = Image.new("RGBA", (t.width + (h - 1) // step + 1, h), CLEAR)
    for y in range(h):
        row = t.crop((0, y, t.width, y + 1))
        o.alpha_composite(row, ((h - 1 - y) // step, y))
    return o


def recolor_img(t, color):
    o = t.copy()
    px = o.load()
    for y in range(o.height):
        for x in range(o.width):
            if px[x, y][3] > 0:
                px[x, y] = color
    return o


def outlined(t, color, outline, shadow=False):
    """Text image t (single colour) -> color with a 1px outline (all round) or a right/bottom shadow."""
    w, h = t.width + 2, t.height + 2
    o = Image.new("RGBA", (w, h), CLEAR)
    sil = recolor_img(t, outline)
    offs = [(1, 1), (2, 1), (1, 2), (2, 2)] if shadow else [(dx, dy) for dx in (0, 1, 2) for dy in (0, 1, 2)]
    for dx, dy in offs:
        o.alpha_composite(sil, (dx, dy))
    o.alpha_composite(recolor_img(t, color), (1, 1) if not shadow else (0, 0))
    return o


def place(im, t, box, h="center", v="center"):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    x = {"center": x0 + (bw - t.width) // 2, "right": x1 + 1 - t.width, "left": x0}[h]
    y = {"center": y0 + (bh - t.height) // 2, "top": y0, "bottom": y1 + 1 - t.height}[v]
    paste(im, t, x, y)
    return (x, y)


def interior(im, x, y):
    """True when the pixel and its 4 neighbours are all opaque (i.e. not on a sprite's silhouette edge)."""
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        xx, yy = x + dx, y + dy
        if not (0 <= xx < im.width and 0 <= yy < im.height) or im.getpixel((xx, yy))[3] == 0:
            return False
    return True


def ascent(text, sy):
    """Pixels of ink above the Hebrew body top (font row 5) for this line, e.g. the lamed's ascender."""
    from sprite_text import FS
    rows = [y for ch in text if ch in FS for y, r in enumerate(FS[ch]["rows"]) if "#" in r]
    return max(0, 5 - min(rows)) * sy if rows else 0


def paste_line(im, t, text, sy, x, body_top):
    """Paste rendered line t so that the top of its letter bodies sits at body_top."""
    paste(im, t, x, body_top - ascent(text, sy))


def out(im, name, frame=0):
    save_sprite(im, name, frame)
    DONE.append((name, frame))


# ---------------------------------------------------------------- Flowey notes (spr_19_2 / spr_19_4)
def title(im):
    # "~A NOTE FROM YOUR FRIEND~" spans x 69..551, y 34..60 on both notes.
    clear(im, (60, 30, 600, 64), BLACK)
    t = text_image("~פתק מחבר שלך~", scale=3, letter_gap=1)
    place(im, t, (69, 30, 551, 64))


def flowey_notes():
    im = load_sprite("spr_19_2", 0)
    title(im)
    # body text column x 358..561 (Flowey drawing ends at x 312); lines at y 166/228/262/326
    clear(im, (340, 150, 639, 360), BLACK)
    for y, s in [(166, "חה חה חה..."), (228, "אפילו לא ניסית"), (262, "לחוס עליה."), (326, "רוצח.")]:
        t = text_image(s, scale=2)
        paste_line(im, t, s, 2, 561 + 1 - t.width, y + 4)
    out(im, "spr_19_2")

    im = load_sprite("spr_19_4", 0)
    title(im)
    # "Don't get too cocky." x 181..418, y 176..199 (centred)
    clear(im, (170, 170, 430, 205), BLACK)
    t = text_image("אל תהיה כל כך שחצן.", scale=2)
    place(im, t, (181, 172, 418, 203))
    out(im, "spr_19_4")


# ---------------------------------------------------------------- Temmie shop box
def tembox():
    im = load_sprite("spr_5_tembox", 0)
    BEIGE = (192, 177, 163, 255)
    YEL = (255, 242, 0, 255)
    BLUE = (153, 217, 234, 255)
    paint = lambda p: p[3] > 0 and p[:3] in (YEL[:3], BLUE[:3])
    # the hand-painted "*TEM SHOP" (with drips) covers x 27..107, y 24..51; keep the decorations
    keep = [(53, 22, 57, 26),   # yellow sparkle left of the handle hole
            (96, 18, 100, 22),  # yellow sparkle top right
            (64, 46, 71, 51),   # blue heart bottom
            (92, 43, 97, 49),   # yellow sparkle bottom right
            (108, 38, 115, 45)]  # blue heart right
    for y in range(24, 52):
        for x in range(27, 108):
            if any(a <= x <= c and b <= y <= d for a, b, c, d in keep):
                continue
            if paint(im.getpixel((x, y))):
                im.putpixel((x, y), BEIGE)
    # Hebrew: "*חנות טם" (the shop dialogue says "חנות טם"); yellow, with the vav light blue like the blue "O"
    sc = (1, 3)
    shop = text_image("*חנות", scale=sc, color=YEL)
    tem = text_image("טם", scale=sc, color=YEL)
    vx0 = text_image("ת", scale=sc).width + 1          # visual order "תונח*": the vav follows the tav
    vx1 = vx0 + text_image("ו", scale=sc).width
    recolor(shop, (vx0, 0, vx1 - 1, shop.height - 1), lambda p: p[3] > 0, BLUE)
    gap = 7
    total = tem.width + gap + shop.width
    x0 = 27 + (81 - total) // 2
    y0 = 26
    paste(im, tem, x0, y0)
    sx = x0 + tem.width + gap
    paste(im, shop, sx, y0)
    # paint drips like the original
    for (x, length, c) in [(x0 + 1, 3, YEL), (x0 + tem.width - 2, 5, YEL), (sx + vx0 + 1, 4, BLUE),
                           (sx + shop.width - 4, 3, YEL)]:
        for k in range(length):
            if y0 + tem.height + k < im.height and im.getpixel((x, y0 + tem.height + k))[:3] == BEIGE[:3]:
                im.putpixel((x, y0 + tem.height + k), c)
    out(im, "spr_5_tembox")


# ---------------------------------------------------------------- word bullets / battle text
def hope():
    im = load_sprite("spr_6hope", 0)
    clear(im, (0, 0, im.width - 1, im.height - 1), CLEAR)
    t = text_image("תקווה", scale=1, color=WHITE, letter_gap=0)
    sh = Image.new("RGBA", (t.width + 1, t.height + 1), CLEAR)
    sh.alpha_composite(recolor_img(t, BLACK), (1, 1))
    sh.alpha_composite(t, (0, 0))
    place(im, sh, (0, 0, 28, 10))
    out(im, "spr_6hope")


def barkbullet():
    im = load_sprite("spr_barkbullet", 0)
    b = bbox_of(im, is_col(WHITE))
    clear(im, b, CLEAR)
    t = text_image("הב", scale=2)
    place(im, t, b)
    out(im, "spr_barkbullet")


def barktry():
    im = load_sprite("spr_barktry", 0)
    clear(im, (0, 0, 99, 99), CLEAR)
    # original lines: y 17..27, 38..55, 62..76, left edge x~7 -> right-aligned at x 90 in Hebrew
    l1 = outlined(italic(text_image("אי אפשר לכעוס", scale=1), 3), WHITE, BLACK, shadow=True)
    place(im, l1, (4, 15, 92, 29), h="right")
    hav = outlined(italic(text_image("הב", scale=2), 3), WHITE, BLACK)
    al = outlined(italic(text_image("על", scale=1), 3), WHITE, BLACK, shadow=True)
    w = hav.width + 5 + al.width
    paste(im, al, 92 + 1 - al.width, 47 - al.height // 2 + 2)
    paste(im, hav, 92 + 1 - w, 47 - hav.height // 2)
    l3 = outlined(italic(text_image("שמנסה...", scale=1), 3), WHITE, BLACK, shadow=True)
    place(im, l3, (4, 62, 92, 77), h="right")
    out(im, "spr_barktry")


def dontmove():
    im = load_sprite("spr_bluedontmove", 0)
    BL = (66, 226, 255, 255)
    b = bbox_of(im, is_col(BL))
    clear(im, (0, 0, im.width - 1, im.height - 1), CLEAR)
    t = text_image("אל תזוז", scale=(4, 4), color=BL, letter_gap=1)
    place(im, t, b)
    out(im, "spr_bluedontmove")


def bombs():
    # red starburst with yellow+black lettering
    im = load_sprite("spr_bombburst", 0)
    RED = (252, 17, 0, 255)
    YEL = (255, 255, 64, 255)
    box = (1, 8, 41, 32)
    for y in range(box[1], box[3] + 1):
        for x in range(box[0], box[2] + 1):
            p = im.getpixel((x, y))
            if p[3] > 0 and (p[:3] == YEL[:3] or (p[:3] == (0, 0, 0) and interior(im, x, y))):
                im.putpixel((x, y), RED)
    t = outlined(text_image("בום", scale=(2, 2), color=YEL, letter_gap=1), YEL, BLACK)
    place(im, t, (0, 9, 41, 31))
    out(im, "spr_bombburst")

    # white starburst with black hand lettering
    im = load_sprite("spr_bombexplosion", 0)
    box = (6, 12, 34, 36)
    for y in range(box[1], box[3] + 1):
        for x in range(box[0], box[2] + 1):
            p = im.getpixel((x, y))
            if p[3] > 0 and p[:3] == (0, 0, 0) and interior(im, x, y):
                im.putpixel((x, y), WHITE)
    t = bold(text_image("בום", scale=(1, 3), color=BLACK, letter_gap=2))
    place(im, t, (7, 15, 33, 33))
    out(im, "spr_bombexplosion")


def napsta():
    im = load_sprite("spr_bulletNapstaSad", 0)
    G = (211, 209, 209, 255)
    b = bbox_of(im, is_col(G))
    clear(im, (0, 0, im.width - 1, im.height - 1), CLEAR)
    lines = ["ממש אין לי", "כוח לזה", "עכשיו.", "סליחה."]
    for i, line in enumerate(lines):
        t = italic(text_image(line, scale=2, color=G, letter_gap=2, space=6), 2)
        paste_line(im, t, line, 2, b[2] + 1 - t.width, b[1] + 3 + i * 18)
    out(im, "spr_bulletNapstaSad")


def coresign():
    for f in range(4):
        im = load_sprite("spr_coresign", f)
        cnt = Counter(im.getdata())
        letter = [c for c, _ in cnt.most_common() if c[:3] != (0, 0, 0)][0]  # most common = letter colour
        b = bbox_of(im, is_col(letter))
        clear(im, b, BLACK)
        t = text_image("הליבה", scale=(2, 3), color=letter, letter_gap=2)
        place(im, t, b)
        out(im, "spr_coresign", f)


def defuse():
    im = load_sprite("spr_defusebox", 0)
    b = bbox_of(im, is_col(WHITE), (0, 0, 39, 16))  # letters only; the arrow is below
    clear(im, b, CLEAR)
    t = text_image("נטרול", scale=(1, 2), letter_gap=2)
    place(im, t, (b[0], 0, b[2], b[3] + 2), v="top")
    out(im, "spr_defusebox")


def miss():
    im = load_sprite("spr_dmgmiss_o", 0)
    ow = im.width
    clear(im, (0, 0, im.width - 1, im.height - 1), CLEAR)
    # each letter: black glyph strokes inside a white block, 1px black outline, 2px black drop shadow
    word = "פספוס"
    from sprite_text import visual
    blocks = []
    for ch in visual(word):
        g = text_image(ch, scale=3, color=BLACK)
        pad = 3
        bw, bh = g.width + 2 * pad, 21 + 2 * pad
        blk = Image.new("RGBA", (bw + 3, bh + 3), CLEAR)
        # shadow + outline
        for (dx, dy) in [(0, 0), (1, 1), (2, 2), (3, 3), (1, 3), (3, 1), (2, 3), (3, 2)]:
            blk.alpha_composite(Image.new("RGBA", (bw, bh), BLACK), (dx, dy))
        blk.alpha_composite(Image.new("RGBA", (bw - 2, bh - 2), WHITE), (1, 1))
        # rounded corners
        for (x, y) in [(1, 1), (bw - 2, 1), (1, bh - 2), (bw - 2, bh - 2)]:
            blk.putpixel((x, y), BLACK)
        blk.alpha_composite(g, (pad, pad + (21 - g.height) // 2))
        blocks.append(blk)
    gap = -1
    total = sum(b.width for b in blocks) + gap * (len(blocks) - 1)
    x = (ow - total) // 2
    for blk in blocks:
        paste(im, blk, x, (im.height - blk.height) // 2)
        x += blk.width + gap
    out(im, "spr_dmgmiss_o")


# tiny 3x5 hand-drawn Hebrew for the 20x20 egg graph label ("ביצה", visual order left->right: ה צ י ב)
TINY = {
    "ה": ["###", "..#", "#.#", "#.#", "#.#"],
    "צ": ["#.#", "#.#", ".##", "..#", "###"],
    "י": ["##", ".#", "..", "..", ".."],
    "ב": ["##.", "..#", "..#", "..#", "###"],
}


def tiny(word, color):
    from sprite_text import visual
    v = visual(word)
    w = sum(len(TINY[c][0]) for c in v) + (len(v) - 1)
    o = Image.new("RGBA", (w, 5), CLEAR)
    x = 0
    for c in v:
        for y, row in enumerate(TINY[c]):
            for i, ch in enumerate(row):
                if ch == "#":
                    o.putpixel((x + i, y), color)
        x += len(TINY[c][0]) + 1
    return o


def eggs():
    im = load_sprite("spr_egggraph", 0)
    b = bbox_of(im, is_col(WHITE), (0, 0, 19, 10))
    clear(im, b, CLEAR)
    t = tiny("ביצה", WHITE)
    place(im, t, (0, b[1], 19, b[3]))
    out(im, "spr_egggraph")

    # egg carton: black block letters engraved in the white bottom band, frames 0-2 (1 cracked, 2 shattered)
    f0 = load_sprite("spr_eggcarton_pl", 0)
    b = bbox_of(f0, is_col(BLACK), (6, 18, 37, 27))
    new0 = f0.copy()
    clear(new0, b, WHITE)
    t = text_image("ביצים", scale=1, color=BLACK, letter_gap=1)
    place(new0, t, (b[0] - 3, b[1], b[2] + 3, b[3]))
    out(new0, "spr_eggcarton_pl", 0)
    for f in (1, 2):
        fr = load_sprite("spr_eggcarton_pl", f)
        n = new0.copy()
        for y in range(fr.height):
            for x in range(fr.width):
                if fr.getpixel((x, y)) != f0.getpixel((x, y)):
                    n.putpixel((x, y), fr.getpixel((x, y)))
        out(n, "spr_eggcarton_pl", f)


def file_erased():
    full = load_sprite("spr_fileerased", 0)
    b = bbox_of(full, is_col(WHITE), (8, 8, 203, 78))  # "File erased." x 16..90, y 14..23
    clear(full, b, BLACK)
    t = text_image("הקובץ נמחק.", scale=1)
    place(full, t, b)
    out(full, "spr_fileerased")
    # crack animation: each piece is at the same coordinates as the full box -> copy the new box into
    # every opaque, non-red pixel of the piece (the red crack line stays)
    RED = (237, 28, 36)
    for f in range(4):
        p = load_sprite("spr_fileerased_parts", f)
        for y in range(p.height):
            for x in range(p.width):
                q = p.getpixel((x, y))
                if q[3] > 0 and q[:3] != RED:
                    p.putpixel((x, y), full.getpixel((x, y)))
        out(p, "spr_fileerased_parts", f)


def main():
    flowey_notes()
    tembox()
    hope()
    barkbullet()
    barktry()
    dontmove()
    bombs()
    napsta()
    coresign()
    defuse()
    miss()
    eggs()
    file_erased()
    if "--preview" in sys.argv:
        d = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(d, exist_ok=True)
        W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for name, f in DONE:
            o = os.path.join(W, "extract", "allspr", f"{name}__{f}.png")
            n = os.path.join(W, "fonts", "sprites", f"{name}__{f}.png")
            sc = 1 if Image.open(o).width >= 300 else (2 if Image.open(o).width >= 100 else 6)
            preview([o, n], os.path.join(d, f"a_prev_{name}__{f}.png"), scale=sc)
    print("wrote", len(DONE), "images")


if __name__ == "__main__":
    main()
