"""Redraw the English-text sprites of translation/audit_sprites_b.json with Hebrew (see translation/SPRITE_BRIEF.md).

Run:  python scripts/sprites/redraw_b.py           (writes fonts/sprites/<name>__<frame>.png)
      python scripts/sprites/redraw_b.py preview   (also writes before/after check images to %TEMP%/redraw_b_preview)
Notes: translation/notes/sprites_b.md
"""
import os, sys, tempfile
from collections import Counter
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from sprite_text import FS, visual, load_sprite, save_sprite, clear, paste, preview, W  # noqa: E402

DONE = []  # (name, frame) written, for the preview

# ---------------------------------------------------------------- rendering helpers
BASE_ROW = 11  # last row of the x-height in the FontStruct raster (letters sit on row 11)


def glyph(ch, thin=False, trim_asc=None, trim_desc=None):
    """Font pixels of one glyph as (x, y) in font rows (x from 0). thin: 2px strokes -> 1px."""
    g = FS[ch]
    pts = {(x, y) for y, r in enumerate(g["rows"]) for x, c in enumerate(r) if c == "#"}
    if trim_asc is not None:  # keep only the lowest `trim_asc` ascender rows (rows < 5)
        pts = {(x, y) for x, y in pts if y >= 5 - trim_asc}
    if trim_desc is not None:
        pts = {(x, y) for x, y in pts if y <= BASE_ROW + trim_desc}
    if thin and pts:
        out = set()
        for y in {p[1] for p in pts}:  # horizontal runs of 2 -> 1
            xs = sorted(x for x, yy in pts if yy == y)
            i = 0
            while i < len(xs):
                j = i
                while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
                    j += 1
                run = xs[i:j + 1]
                out.update((x, y) for x in (run[-1:] if len(run) == 2 else run))
                i = j + 1
        pts = out
    if not pts:
        return set(), g["adv"]
    mn = min(p[0] for p in pts)
    return {(x - mn, y) for x, y in pts}, None


def render(text, sx=1, sy=1, color=(255, 255, 255, 255), gap=1, space=4, outline=None, ow=1,
           thin=False, trim_asc=None, trim_desc=None, jitter=None, custom=None):
    """One line of Hebrew. Returns (RGBA image, baseline) where baseline = image row just below the x-height.
    outline: colour of a square outline `ow` px wide (in image pixels, after scaling).
    jitter: list of per-letter y offsets (font rows) for a hand-written look.
    custom: dict ch -> list of strings (own pixel glyphs, bottom row = baseline)."""
    vis = visual(text)
    cols = []
    for i, ch in enumerate(vis):
        if ch == " ":
            cols.append((set(), space)); continue
        if custom and ch in custom:
            rows = custom[ch]
            pts = {(x, BASE_ROW - (len(rows) - 1 - y)) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"}
            cols.append((pts, len(rows[0]))); continue
        pts, adv = glyph(ch, thin, trim_asc, trim_desc)
        if not pts:
            cols.append((set(), space)); continue
        cols.append((pts, max(p[0] for p in pts) + 1))
    allp = []
    x = 0
    for i, (pts, w) in enumerate(cols):
        dy = jitter[i % len(jitter)] if jitter else 0
        allp += [(x + px, py + dy) for px, py in pts]
        x += w + gap
    top = min(p[1] for p in allp); bot = max(p[1] for p in allp)
    width = max(p[0] for p in allp) + 1
    pad = ow if outline else 0
    img = Image.new("RGBA", (width * sx + 2 * pad, (bot - top + 1) * sy + 2 * pad), (0, 0, 0, 0))
    mask = set()
    for px, py in allp:
        for dx in range(sx):
            for dy in range(sy):
                mask.add((pad + px * sx + dx, pad + (py - top) * sy + dy))
    if outline:
        for (px, py) in mask:
            for dx in range(-ow, ow + 1):
                for dy in range(-ow, ow + 1):
                    img.putpixel((px + dx, py + dy), outline)
    for p in mask:
        img.putpixel(p, color)
    return img, pad + (BASE_ROW + 1 - top) * sy


def recolor(img, color):
    out = img.copy()
    px = out.load()
    for x in range(out.width):
        for y in range(out.height):
            if px[x, y][3]:
                px[x, y] = color
    return out


def hand(text, fx, fy, color, gap=1, space=4, jitter=None, trim_asc=None, trim_desc=None, bold=False):
    """Thin, hand-drawn looking line: the 1px skeleton of each glyph, scaled by joining neighbouring
    font pixels with 1px lines (so strokes stay thin at any size). Returns (image, baseline)."""
    from PIL import ImageDraw
    vis = visual(text)
    P = set(); x = 0
    for i, ch in enumerate(vis):
        if ch == " ":
            x += space + gap; continue
        pts, _ = glyph(ch, True, trim_asc, trim_desc)
        dy = jitter[i % len(jitter)] if jitter else 0
        P |= {(x + px, py + dy) for px, py in pts}
        x += (max(p[0] for p in pts) + 1 if pts else space) + gap
    top = min(p[1] for p in P); bot = max(p[1] for p in P); right = max(p[0] for p in P)
    img = Image.new("RGBA", (int(right * fx) + 2 + bold, int((bot - top) * fy) + 1), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = lambda p: (round(p[0] * fx), round((p[1] - top) * fy))
    for p in P:
        lone = True
        for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1), (-1, 0), (0, -1), (-1, -1), (-1, 1)):
            q = (p[0] + dx, p[1] + dy)
            if q not in P:
                continue
            lone = False
            if dx and dy and ((p[0] + dx, p[1]) in P or (p[0], p[1] + dy) in P):
                continue  # corner already joined orthogonally
            d.line([m(p), m(q)], fill=color)
        if lone:
            d.point(m(p), fill=color)
    if bold:
        b = img.copy(); img.alpha_composite(b, (1, 0))
    return img, round((BASE_ROW - top) * fy) + 1


def place(im, t, cx, baseline, base):
    """Paste t (with its baseline offset `base`) centred on column cx with its baseline at row `baseline`."""
    paste(im, t, cx - t.width // 2, baseline - base)


def bbox_of(im, pred, box=None):
    x0, y0, x1, y1 = box or (0, 0, im.width - 1, im.height - 1)
    pts = [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) if pred(im.getpixel((x, y)))]
    if not pts:
        return None
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def erase(im, box, pred, fill):
    """Replace pixels matching pred inside box with fill (colour or function (x, y) -> colour)."""
    x0, y0, x1, y1 = box
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if pred(im.getpixel((x, y))):
                im.putpixel((x, y), fill(x, y) if callable(fill) else fill)


def save(im, name, frame):
    save_sprite(im, name, frame)
    DONE.append((name, frame))


T = (0, 0, 0, 0)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

# ---------------------------------------------------------------- custom pixel glyphs
# GAME OVER: chunky 5-row block letters with 2-block-wide verticals and 1-block bars, like the original
# (1 block = 13 x 16 px).
BIG = {
    "ה": ["######", "....##", "##..##", "##..##", "##..##"],
    "מ": ["#.####.", "###..##", ".##..##", ".##..##", ".##.###"],
    "ש": ["##.##.##", "##.##.##", "####..##", "##....##", "########"],
    "ח": ["######", "##..##", "##..##", "##..##", "##..##"],
    "ק": ["######", "....##", "##..##", "##.##.", "##....", "##....", "##...."],  # 2 descender rows
    "נ": ["###.", "..##", "..##", "..##", "####"],
    "ג": [".###.", "...##", ".####", "##.##", "##.##"],
    "ר": ["#####.", "....##", "....##", "....##", "....##"],
}
BIG_DESC = {"ק": 2}

# Papyrus's shirt: 4 px tall hand-drawn letters.
TINY4 = {
    "ג": ["##.", ".#.", ".#.", "#.#"],
    "ב": ["##.", "..#", "..#", "###"],
    "ר": ["###", "..#", "..#", "..#"],
    "מ": ["#.##", ".#.#", "#..#", "#.##"],
    "נ": ["##", ".#", ".#", "##"],
    "י": ["##", ".#", "..", ".."],
}
# "out to lunch" sign: 5 px tall hand-written letters (ל has a 2 px ascender).
TINY5 = {
    "י": ["##", ".#", "..", "..", ".."],
    "צ": ["#..#", ".#.#", "..#.", "...#", "####"],
    "א": ["#..#", ".#.#", ".##.", "#.#.", "#..#"],
    "ת": ["####", ".#.#", ".#.#", ".#.#", "##.#"],
    "ל": ["#..", "#..", "###", "..#", "..#", ".#.", "#.."],
    "כ": ["###", "..#", "..#", "..#", "###"],
    "ו": ["##", ".#", ".#", ".#", ".#"],
}
# Dog bark: 3 px tall.
TINY3 = {
    "ה": ["###", "..#", "#.#"],
    "ב": ["##.", ".#.", "###"],
}


def render_blocks(text, glyphs, ux, uy, gap=1, desc=None):
    """Block-font line. Returns (white mask image, baseline)."""
    vis = visual(text)
    desc = desc or {}
    h = max(len(glyphs[c]) - desc.get(c, 0) for c in vis)
    dmax = max(desc.get(c, 0) for c in vis)
    width = sum(len(glyphs[c][0]) for c in vis) + gap * (len(vis) - 1)
    img = Image.new("RGBA", (width * ux, (h + dmax) * uy), T)
    x = 0
    for c in vis:
        for gy, row in enumerate(glyphs[c]):
            for gx, ch in enumerate(row):
                if ch == "#":
                    img.paste(WHITE, ((x + gx) * ux, gy * uy, (x + gx + 1) * ux, (gy + 1) * uy))
        x += len(glyphs[c][0]) + gap
    return img, h * uy


def outlined(img, ow, color=BLACK):
    """Add a square outline of width ow around the opaque pixels (image grows by ow on each side)."""
    out = Image.new("RGBA", (img.width + 2 * ow, img.height + 2 * ow), T)
    a = img.split()[3]
    sil = Image.new("RGBA", img.size, color)
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            out.paste(sil, (ow + dx, ow + dy), a)
    out.alpha_composite(img, (ow, ow))
    return out


def tiny_text(text, glyphs, color, outline=None):
    vis = visual(text)
    h = max(len(glyphs[c]) for c in vis)
    width = sum(len(glyphs[c][0]) for c in vis) + len(vis) - 1
    img = Image.new("RGBA", (width + (2 if outline else 0), h + (2 if outline else 0)), T)
    o = 1 if outline else 0
    pts = []
    x = 0
    for c in vis:
        off = h - len(glyphs[c])  # glyphs sit on a common baseline
        for gy0, row in enumerate(glyphs[c]):
            gy = gy0 + off
            for gx, ch in enumerate(row):
                if ch == "#":
                    pts.append((x + gx + o, gy + o))
        x += len(glyphs[c][0]) + 1
    if outline:
        for px, py in pts:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    img.putpixel((px + dx, py + dy), outline)
    for p in pts:
        img.putpixel(p, color)
    return img


# ---------------------------------------------------------------- sprites
def gameoverbg():
    im = load_sprite("spr_gameoverbg", 0)
    im = Image.new("RGBA", im.size, T)  # the sprite is only the two words on transparent
    l1, b1 = render_blocks("המשחק", BIG, 13, 16, desc=BIG_DESC)
    l2, b2 = render_blocks("נגמר", BIG, 13, 16)
    l1, l2 = outlined(l1, 3), outlined(l2, 3)
    # original: GAME at rows 36-115, OVER at rows 132-211 (white), centred on x=320 / 315.5
    im.alpha_composite(l1, (320 - l1.width // 2, 36 - 3))
    im.alpha_composite(l2, (316 - l2.width // 2, 132 - 3))
    save(im, "spr_gameoverbg", 0)


def gameshowlogo():
    im = load_sprite("spr_gameshowlogo", 0)
    red, pink = (237, 28, 36, 255), (255, 174, 201, 255)
    erase(im, (3, 3, 116, 36), lambda p: p in (red, pink), BLACK)
    word = "שעשועון"
    # each letter alternately red / pink, starting with red at the first (rightmost) letter
    letters = [render(c, 2, 3, red if i % 2 == 0 else pink, trim_desc=2) for i, c in enumerate(word)]
    gap = 4
    total = sum(t.width for t, _ in letters) + gap * (len(letters) - 1)
    x = 62 - total // 2 + total  # right edge (ן keeps clear of the rounded corner)
    for t, base in letters:
        x -= t.width
        paste(im, t, x, 28 - base)
        x -= gap
    save(im, "spr_gameshowlogo", 0)


def goalhud():
    im = load_sprite("spr_goalhud", 0)
    red = (237, 28, 36, 255)
    erase(im, (40, 4, 60, 11), lambda p: p == red, BLACK)
    t, base = render("יעד", 1, 1, red)
    paste(im, t, 41, 11 - base)
    save(im, "spr_goalhud", 0)


def embolden(img):
    out = Image.new("RGBA", (img.width + 1, img.height), T)
    out.alpha_composite(img, (0, 0)); out.alpha_composite(img, (1, 0))
    return out


def bubbly(img):
    """Thicken with a plus-shaped kernel (rounded, blobby letters)."""
    out = Image.new("RGBA", (img.width + 2, img.height + 2), T)
    a = img.split()[3]
    for dx, dy in ((1, 0), (0, 1), (2, 1), (1, 2), (1, 1)):
        out.paste(img, (dx, dy), a)
    return out


def hollow(img):
    """Keep only the edge pixels of each stroke (thin outlined letters)."""
    out = img.copy(); src = img.load(); dst = out.load()
    for x in range(img.width):
        for y in range(img.height):
            if src[x, y][3]:
                inner = all(0 <= x + dx < img.width and 0 <= y + dy < img.height and src[x + dx, y + dy][3]
                            for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                if inner:
                    dst[x, y] = T
    return out


def happybreaktime():
    im = load_sprite("spr_happybreaktime", 0)
    clear(im, (1, 1, 118, 38), BLACK)
    top, _ = render("הפסקה", 2, 2, WHITE, gap=2)
    top = bubbly(top)
    paste(im, top, 60 - top.width // 2, 2)
    bot, b = hand("שמחה", 3, 2, WHITE, gap=1)
    paste(im, bot, 60 - bot.width // 2, 38 - b)
    save(im, "spr_happybreaktime", 0)


def killervisage():
    im = load_sprite("spr_killervisage", 0)
    pink = (255, 174, 201, 255)
    # the little sparkle after "Robot" (right end of line 2) stays
    spark = bbox_of(im, lambda p: p == pink, (229, 0, 242, 63))
    sp = im.crop((spark[0], spark[1], spark[2] + 1, spark[3] + 1))
    clear(im, spark, BLACK)
    erase(im, (0, 0, 242, 63), lambda p: p == pink, BLACK)
    l1, b1 = hand("מבשלים עם", 3, 3, pink, gap=1, space=4, bold=True)
    l2, b2 = hand("רובוט רוצח", 3, 3, pink, gap=1, space=4, bold=True)
    x1 = 121 - l1.width // 2
    x2 = 121 - l2.width // 2
    paste(im, l1, x1, 27 - b1)
    paste(im, l2, x2, 58 - b2)
    # the sparkle goes after the last word, which in Hebrew is on the left
    paste(im, ImageOps.mirror(sp), x2 - sp.width - 2, 58 - sp.height)
    save(im, "spr_killervisage", 0)


def librarysign():
    im = load_sprite("spr_librarysign", 0)
    txt, bg = (207, 219, 255, 255), (133, 163, 216, 255)
    clear(im, (2, 3, 38, 11), bg)
    t, base = render("ספרריה", 1, 1, txt)
    paste(im, t, 20 - (t.width - 1) // 2, 11 - base)
    save(im, "spr_librarysign", 0)


def button(name, frame, word):
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_buttons", os.path.join(W, "scripts", "build_buttons.py"))
    bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
    load_sprite(name, frame)
    im = bb.process(os.path.join(W, "extract", "allspr", f"{name}__{frame}.png"), word)
    save(im, name, frame)


def mettatonb():
    for name in ("spr_mettatonb_behind", "spr_mettatonb_behind_on"):
        im = load_sprite(name, 0)
        erase(im, (30, 9, 72, 17), lambda p: p == WHITE, BLACK)
        t, base = render("מתג", 1, 1, WHITE)
        paste(im, t, 52 - t.width // 2, 17 - base)
        save(im, name, 0)


def mettnewslogo():
    im = load_sprite("spr_mettnewslogo", 0)
    yel = (255, 242, 0, 255)
    clear(im, (97, 3, 204, 37), T)
    t, base = render("חדשות", 2, 4, yel, gap=2)
    t = embolden(t).resize((t.width + 1, 31), Image.NEAREST)  # same height as MTT (rows 5-35)
    t = outlined(t, 1)
    paste(im, t, 142 - t.width // 2, 4)
    save(im, "spr_mettnewslogo", 0)


def out_to_lunch():
    im = load_sprite("spr_out_to_lunch_sign", 0)
    ink, board = (58, 57, 72, 255), (200, 194, 226, 255)
    # text = ink pixels strictly inside the board (the board edge is also ink)
    erase(im, (2, 6, 26, 17), lambda p: p == ink, board)
    l1 = tiny_text("יצאתי", TINY5, ink)
    l2 = tiny_text("לאכול", TINY5, ink)
    paste(im, l1, 15 - l1.width // 2, 11 - l1.height)
    paste(im, l2, 15 - l2.width // 2, 18 - l2.height)
    save(im, "spr_out_to_lunch_sign", 0)


def papdate_cool():
    im = load_sprite("spr_papdate_cool", 0)
    # COOL / DUDE on the shirt: black pixels in crop box (12..31, 11..25) of origin (5, 30)
    for x in range(17, 37):
        for y in range(41, 56):
            if im.getpixel((x, y)) == BLACK and not (y == 55 and x < 25):
                im.putpixel((x, y), WHITE)
    l1 = tiny_text("גבר", TINY4, BLACK)
    l2 = tiny_text("מגניב", TINY4, BLACK)
    paste(im, l1, 26 - l1.width // 2, 43)
    paste(im, l2, 27 - l2.width // 2, 50)
    save(im, "spr_papdate_cool", 0)


def punchcard():
    im = load_sprite("spr_punchcard", 0)
    grey = (127, 127, 127, 255)
    ref = {y: im.getpixel((255, y)) for y in range(im.height)}  # clean paper column (lines run full width)
    erase(im, (55, 66, 196, 140), lambda p: p == grey, lambda x, y: ref[y])
    jit = [0, 1, 0, 0, -1, 1, 0]
    for text, baseline in (("בבקשה...", 92), ("בבקשה,", 122), ("תחזור...", 138)):
        t, base = hand(text, 1.6, 1.5, grey, gap=1, jitter=jit, trim_desc=2)
        paste(im, t, 245 - t.width, baseline - base)
    save(im, "spr_punchcard", 0)


def pxquit():
    for f in (0, 1):
        im = load_sprite("spr_pxquit", f)
        bgc = [(25, 31, 88, 255), (25, 19, 70, 255)]
        ink = Counter(p for p in im.getdata() if p not in bgc).most_common(1)[0][0]
        # the background is a wave pattern repeating every 20 px: rebuild it under the text
        pat = {}
        for y in range(im.height):
            for x in range(im.width):
                p = im.getpixel((x, y))
                if p != ink:
                    pat.setdefault((x % 20, y), Counter())[p] += 1
        for y in range(im.height):
            for x in range(im.width):
                if im.getpixel((x, y)) == ink:
                    c = pat.get((x % 20, y))
                    im.putpixel((x, y), c.most_common(1)[0][0] if c else bgc[0])
        orig = load_sprite("spr_pxquit", f)
        # "X->" (x 0..12) mirrored to the right end, so it reads "יציאה <- X" right to left
        xa = orig.crop((0, 2, 21, 17))
        xa = Image.eval(xa, lambda v: v)  # copy
        keep = Image.new("RGBA", xa.size, T)
        for x in range(xa.width):
            for y in range(xa.height):
                if xa.getpixel((x, y)) == ink:
                    keep.putpixel((x, y), ink)
        keep = ImageOps.mirror(keep)
        paste(im, keep, im.width - 1 - keep.width, 2)
        t, base = render("יציאה", 1, 1, ink, gap=1, thin=True, jitter=[0, 1, -1, 0, 1])
        paste(im, t, 35 - t.width, 14 - base)
        save(im, "spr_pxquit", f)


def pressz_press():
    im = load_sprite("spr_pressz_press", 0)
    clear(im, (3, 4, 41, 16), T)
    t, base = render("לחץ", 1, 1, (64, 255, 64, 255), outline=BLACK, ow=1)
    paste(im, t, 22 - t.width // 2, 15 - base)
    save(im, "spr_pressz_press", 0)


def quittingmessage():
    ims = [load_sprite("spr_quittingmessage", f) for f in range(3)]
    full, base = render("יוצא..", 2, 2, WHITE, outline=BLACK, ow=2)
    right = 1 + full.width  # right edge of the word, same in every frame
    for f, im in enumerate(ims):
        clear(im, (0, 0, im.width - 1, im.height - 1), T)
        t, b = render("יוצא" + "." * f, 2, 2, WHITE, outline=BLACK, ow=2)
        paste(im, t, right - t.width, 18 - b)
        save(im, "spr_quittingmessage", f)


def quiztouch():
    im = load_sprite("spr_quiztouch", 0)
    clear(im, (0, 0, im.width - 1, im.height - 1), T)
    t, base = render("גע", 1, 1, (0, 128, 0, 255), jitter=[0, 1])
    paste(im, t, 18 - t.width // 2, 8 - base + 0)
    save(im, "spr_quiztouch", 0)


def recrew():
    im = load_sprite("spr_recbox", 0)
    clear(im, (16, 2, 49, 18), (255, 255, 255, 0))
    t, base = render("הקלטה", 1, 2, (255, 201, 14, 255), trim_asc=1, trim_desc=1)
    paste(im, t, 49 - t.width, 17 - base + 1)
    save(im, "spr_recbox", 0)
    im = load_sprite("spr_rewbox", 0)
    clear(im, (15, 1, 49, 17), (255, 255, 255, 0))
    t, base = render("אחורה", 1, 2, (64, 255, 64, 255))
    paste(im, t, 33 - t.width // 2, 17 - base + 1)
    save(im, "spr_rewbox", 0)


def movedoge():
    for f, (x0, x1) in ((0, (9, 25)), (1, (45, 62))):
        im = load_sprite("spr_movedogeheadb", f)
        clear(im, (x0, 22, x1, 26), T)
        t = tiny_text("הב", TINY3, WHITE, outline=BLACK)
        if f == 1:
            t = ImageOps.mirror(t)  # the original frame 1 is the mirrored drawing ("naw")
        paste(im, t, (x0 + x1 + 1) // 2 - t.width // 2, 22)
        save(im, "spr_movedogeheadb", f)


def main():
    gameoverbg(); gameshowlogo(); goalhud(); happybreaktime(); killervisage(); librarysign()
    button("spr_mercybutton_normal", 0, "רחמים")
    button("spr_savebt", 0, "שמירה"); button("spr_savebt", 1, "שמירה")
    mettatonb(); mettnewslogo(); out_to_lunch(); papdate_cool(); punchcard(); pxquit(); pressz_press()
    quittingmessage(); quiztouch(); recrew(); movedoge()
    print("redraw_b:", len(DONE), "frames")
    if "preview" in sys.argv:
        out = os.path.join(tempfile.gettempdir(), "redraw_b_preview"); os.makedirs(out, exist_ok=True)
        for name, f in DONE:
            preview([os.path.join(W, "extract", "allspr", f"{name}__{f}.png"),
                     os.path.join(W, "fonts", "sprites", f"{name}__{f}.png")],
                    os.path.join(out, f"{name}__{f}.png"), scale=1 if name in ("spr_gameoverbg", "spr_punchcard") else 4)
        print("previews in", out)


if __name__ == "__main__":
    main()
