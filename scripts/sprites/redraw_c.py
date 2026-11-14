"""Hebrew redraw of the images in translation/audit_sprites_c.json (see translation/SPRITE_BRIEF.md).

    python scripts/sprites/redraw_c.py                 # redraw everything
    python scripts/sprites/redraw_c.py --only a,b      # only some images (by name)
    python scripts/sprites/redraw_c.py --preview DIR   # also write original-vs-new check images to DIR

Writes fonts/sprites/<name>__<frame>.png and fonts/backgrounds/<name>.png.
Notes: translation/notes/sprites_c.md.
"""
import os, sys, argparse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from sprite_text import FS, visual, load_sprite, load_bg, save_sprite, save_bg, preview, clear  # noqa: E402
from PIL import Image  # noqa: E402

# ----------------------------------------------------------------------------------------------
# glyph helpers (the FontStruct font: rows 0..19, x-height top = row 5, baseline row = 11)
# A glyph here is (rows: list[str] of '#'/'.', top: font row of rows[0]).
# ----------------------------------------------------------------------------------------------
XTOP, BASE = 5, 11


def fglyph(ch):
    """Font glyph cropped to its ink: (rows, top)."""
    rows = FS[ch]["rows"]
    ys = [y for y, r in enumerate(rows) if "#" in r]
    xs = [x for r in rows for x, c in enumerate(r) if c == "#"]
    x0, x1 = min(xs), max(xs)
    return [rows[y][x0:x1 + 1] for y in range(ys[0], ys[-1] + 1)], ys[0]


def g_w(g):
    return len(g[0][0])


def narrow(g, n=1):
    """Remove n columns that duplicate their neighbour (closest to the centre first)."""
    rows, top = g
    for _ in range(n):
        w = len(rows[0])
        cols = ["".join(r[x] for r in rows) for x in range(w)]
        cand = [x for x in range(w - 1) if cols[x] == cols[x + 1]]
        if not cand:
            break
        x = min(cand, key=lambda c: abs(c + 0.5 - w / 2))
        rows = [r[:x] + r[x + 1:] for r in rows]
    return rows, top


def widen(g, n=1):
    """Duplicate n vertical-stem columns (the columns with the most ink, nearest the centre)."""
    rows, top = g
    for _ in range(n):
        w = len(rows[0])
        cols = ["".join(r[x] for r in rows) for x in range(w)]
        x = max(range(w), key=lambda c: (cols[c].count("#"), -abs(c - w / 2)))
        rows = [r[:x + 1] + r[x] + r[x + 1:] for r in rows]
    return rows, top


def thin(g):
    """Zhang-Suen thinning: the bold 2px strokes become 1px strokes."""
    rows, top = g
    h, w = len(rows) + 2, len(rows[0]) + 2
    a = [[0] * w for _ in range(h)]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            a[y + 1][x + 1] = 1 if c == "#" else 0
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            kill = []
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if not a[y][x]:
                        continue
                    p = [a[y - 1][x], a[y - 1][x + 1], a[y][x + 1], a[y + 1][x + 1], a[y + 1][x], a[y + 1][x - 1],
                         a[y][x - 1], a[y - 1][x - 1]]
                    b = sum(p)
                    t = sum(1 for i in range(8) if p[i] == 0 and p[(i + 1) % 8] == 1)
                    if not (2 <= b <= 6 and t == 1):
                        continue
                    if step == 0 and p[0] * p[2] * p[4] == 0 and p[2] * p[4] * p[6] == 0:
                        kill.append((y, x))
                    if step == 1 and p[0] * p[2] * p[6] == 0 and p[0] * p[4] * p[6] == 0:
                        kill.append((y, x))
            for y, x in kill:
                a[y][x] = 0
            changed = changed or bool(kill)
    out = ["".join("#" if a[y][x] else "." for x in range(1, w - 1)) for y in range(1, h - 1)]
    # crop empty columns
    xs = [x for r in out for x, c in enumerate(r) if c == "#"]
    x0, x1 = min(xs), max(xs)
    return [r[x0:x1 + 1] for r in out], top


def vstretch(g, extra, rows_from=XTOP + 2, rows_to=BASE - 2):
    """Make the x-height `extra` rows taller by repeating the font rows rows_from..rows_to
    (the same rows for every glyph, so all letters keep the same proportions)."""
    rows, top = g
    if extra <= 0:
        return g
    cand = list(range(rows_from, rows_to + 1))
    reps = Counter(cand[(i * len(cand)) // extra] if extra >= len(cand) else cand[int((i + 0.5) * len(cand) / extra)]
                   for i in range(extra))
    out = []
    for i, r in enumerate(rows):
        out.append(r)
        out.extend([r] * reps[top + i])
    return out, top  # note: rows below the stretched part move down by `extra`


def cut_desc(g, keep=1):
    """Shorten a descender to `keep` rows below the baseline."""
    rows, top = g
    last = BASE + keep - top
    return rows[:last + 1], top


# ----------------------------------------------------------------------------------------------
# tiny 5-row Hebrew font for the 5-7px tall labels (row 0 = x-height top; ל has one row above)
# ----------------------------------------------------------------------------------------------
MINI = {
    "א": ["#.#", ".##", ".#.", "##.", "#.#"],
    "ב": ["##.", "..#", "..#", "..#", "###"],
    "ג": ["##.", ".#.", ".#.", ".##", "#.#"],
    "ד": ["####", "..#.", "..#.", "..#.", "..#."],
    "ה": ["###", "..#", "#.#", "#.#", "#.#"],
    "ו": ["#", "#", "#", "#", "#"],
    "ז": ["###", ".#.", ".#.", ".#.", ".#."],
    "ח": ["###", "#.#", "#.#", "#.#", "#.#"],
    "ט": ["#.##", "#..#", "#..#", "#..#", "####"],
    "י": ["#", "#", ".", ".", "."],
    "כ": ["##.", "..#", "..#", "..#", "##."],
    "ל": ["#..", "###", "..#", "..#", ".#.", "#.."],  # 6 rows, starts one row above
    "מ": ["#.#.", ".###", "#..#", "#..#", "#.##"],
    "ם": ["####", "#..#", "#..#", "#..#", "####"],
    "נ": ["##", ".#", ".#", ".#", "##"],
    "ן": ["##", ".#", ".#", ".#", ".#"],
    "ס": ["###", "#.#", "#.#", "#.#", "##."],
    "ע": ["#.#", "#.#", "#.#", ".##", "##."],
    "פ": ["###", "#.#", "..#", "..#", "###"],
    "ק": ["###", "..#", "#.#", "#..", "#.."],
    "ר": ["##.", "..#", "..#", "..#", "..#"],
    "ש": ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    "ת": ["####", ".#.#", ".#.#", ".#.#", "##.#"],
    "!": ["#", "#", "#", ".", "#"],
    ".": [".", ".", ".", ".", "#"],
    ":": [".", "#", ".", "#", "."],
}
MINI_TOP = {"ל": -1}


def mini_image(text, color, gap=1, space=3, cell=(1, 1), dot_gap=1):
    """Render with the tiny font. Returns (img, y of x-height top row inside img)."""
    sx, sy = cell
    vis = visual(text)
    items = []
    for i, ch in enumerate(vis):
        if ch == " ":
            items.append(None)
            continue
        items.append((MINI[ch], MINI_TOP.get(ch, 0)))
    up = 1 if any(it and it[1] < 0 for it in items) else 0
    width = 0
    for i, it in enumerate(items):
        width += space if it is None else len(it[0][0])
        if i < len(items) - 1 and it is not None and items[i + 1] is not None:
            width += dot_gap if (vis[i] in "." and vis[i + 1] in ".") else gap
    img = Image.new("RGBA", (width * sx, (5 + up) * sy), (0, 0, 0, 0))
    x = 0
    for i, it in enumerate(items):
        if it is None:
            x += space
            continue
        rows, t = it
        for yy, r in enumerate(rows):
            for xx, c in enumerate(r):
                if c == "#":
                    for dx in range(sx):
                        for dy in range(sy):
                            img.putpixel(((x + xx) * sx + dx, (yy + t + up) * sy + dy), color)
        x += len(rows[0])
        if i < len(items) - 1 and items[i + 1] is not None:
            x += dot_gap if (vis[i] in "." and vis[i + 1] in ".") else gap
    return img, up * sy


# ----------------------------------------------------------------------------------------------
# main-font renderer with per-glyph transforms
# ----------------------------------------------------------------------------------------------
def word_image(text, color, scale=(1, 1), gap=1, space=4, outline=None, fx=None, extra_rows=0):
    """Render text (logical order) with the FontStruct glyphs.
    fx(ch, glyph) -> glyph lets the caller narrow/thin/... each glyph. extra_rows = vstretch amount.
    Returns (img, y_xtop, y_base): y of the x-height top row and of the row just below the baseline."""
    sx, sy = scale
    vis = visual(text)
    gl = []
    for ch in vis:
        if ch == " ":
            gl.append(None)
            continue
        g = fglyph(ch)
        if fx:
            g = fx(ch, g)
        if extra_rows:
            g = vstretch(g, extra_rows)
        gl.append(g)
    # vertical extent in font rows (stretched coordinates)
    def span(g):
        rows, top = g
        return top, top + len(rows) - 1
    tops = [span(g)[0] for g in gl if g]
    bots = [span(g)[1] for g in gl if g]
    t0, b0 = min(tops + [XTOP]), max(bots + [BASE + extra_rows])
    width = sum(space if g is None else g_w(g) for g in gl) + gap * max(0, len(gl) - 1)
    pad = 1 if outline else 0
    H = b0 - t0 + 1
    img = Image.new("RGBA", ((width + 2 * pad) * sx, (H + 2 * pad) * sy), (0, 0, 0, 0))
    pts = []
    x = 0
    for g in gl:
        if g is None:
            x += space + gap
            continue
        rows, top = g
        for yy, r in enumerate(rows):
            for xx, c in enumerate(r):
                if c == "#":
                    pts.append((x + xx + pad, top + yy - t0 + pad))
        x += g_w(g) + gap

    def put(px, py, c, over):
        for dx in range(sx):
            for dy in range(sy):
                X, Y = px * sx + dx, py * sy + dy
                if 0 <= X < img.width and 0 <= Y < img.height:
                    if over or img.getpixel((X, Y))[3] == 0:
                        img.putpixel((X, Y), c)
    if outline:
        for px, py in pts:
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    put(px + ox, py + oy, outline, False)
    for px, py in pts:
        put(px, py, color, True)
    return img, (XTOP - t0 + pad) * sy, (BASE + extra_rows - t0 + 1 + pad) * sy


# ----------------------------------------------------------------------------------------------
# pixel helpers
# ----------------------------------------------------------------------------------------------
def bbox_of(im, pred, box=None):
    x0, y0, x1, y1 = box or (0, 0, im.width - 1, im.height - 1)
    xs, ys = [], []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if pred(im.getpixel((x, y))):
                xs.append(x); ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def recolor(im, pred, color, box=None):
    """Replace every pixel matching pred inside box with color (tight clearing of text pixels)."""
    x0, y0, x1, y1 = box or (0, 0, im.width - 1, im.height - 1)
    for y in range(max(0, y0), min(im.height - 1, y1) + 1):
        for x in range(max(0, x0), min(im.width - 1, x1) + 1):
            if pred(im.getpixel((x, y))):
                im.putpixel((x, y), color)


def is_(c):
    c = tuple(c)
    return lambda p: tuple(p) == c


def put_img(im, t, x, y, mask=None):
    """Composite t at (x, y); mask(x, y) -> bool limits where it may draw."""
    for yy in range(t.height):
        for xx in range(t.width):
            p = t.getpixel((xx, yy))
            X, Y = x + xx, y + yy
            if p[3] and 0 <= X < im.width and 0 <= Y < im.height and (mask is None or mask(X, Y)):
                im.putpixel((X, Y), p)


def center_x(box, w):
    return box[0] + ((box[2] - box[0] + 1) - w) // 2


def recolor_img(t, color):
    o = t.copy()
    for y in range(o.height):
        for x in range(o.width):
            if o.getpixel((x, y))[3]:
                o.putpixel((x, y), color)
    return o


def shear_v(t, slope):
    """Vertical shear: column x moves down by round(slope * x) (slope<0: text rises to the right)."""
    off = [round(slope * x) for x in range(t.width)]
    mn = min(off)
    h = t.height + max(off) - mn
    o = Image.new("RGBA", (t.width, h), (0, 0, 0, 0))
    for x in range(t.width):
        for y in range(t.height):
            p = t.getpixel((x, y))
            if p[3]:
                o.putpixel((x, y + off[x] - mn), p)
    return o, -mn  # second value: how far row 0 of the left column moved down


RESULTS = []  # (kind, name, frame, original, new)


def out_spr(name, frame, orig, new):
    assert new.size == orig.size, (name, new.size, orig.size)
    save_sprite(new, name, frame)
    RESULTS.append(("spr", name, frame, orig, new))


def out_bg(name, orig, new):
    assert new.size == orig.size, (name, new.size, orig.size)
    save_bg(new, name)
    RESULTS.append(("bg", name, 0, orig, new))


# ==============================================================================================
# the images
# ==============================================================================================
def do_snowsans():
    o = load_sprite("spr_snowsans", 0); im = o.copy()
    red, snow = (255, 71, 17, 255), (133, 163, 216, 255)
    box = bbox_of(im, is_(red))                      # letters, rows 4-8
    recolor(im, is_(red), snow, box)
    t, _ = mini_image("סאנס", red)
    x = center_x(box, t.width)
    put_img(im, t, x, box[1], mask=lambda X, Y: im.getpixel((X, Y)) == snow)
    out_spr("spr_snowsans", 0, o, im)


def do_soapbul():
    # the word is stored sideways: work on the sprite turned so the word reads normally
    o = load_sprite("spr_soapbul", 0)
    r = o.rotate(90, expand=True)
    white, black = (255, 255, 255, 255), (0, 0, 0, 255)
    clear(r, (6, 8, 31, 17), white)                  # old HOPE (black on white), keep the frame lines
    # 2px cells like HOPE, 1px gaps. "תקווה" is 2px too wide for the box, so the short spelling "תקוה"
    letters = [mini_image(ch, black, cell=(2, 2))[0] for ch in visual("תקוה")]
    w = sum(l.width for l in letters) + (len(letters) - 1)
    x = 6 + ((31 - 6 + 1) - w) // 2
    for l in letters:
        put_img(r, l, x, 8)
        x += l.width + 1
    out_spr("spr_soapbul", 0, o, r.rotate(-90, expand=True))


def do_spellbt():
    sys.path.insert(0, os.path.dirname(HERE))
    import build_buttons as bb
    for f in (0, 1):
        o = load_sprite("spr_spellbt", f)
        src = os.path.join(os.path.dirname(os.path.dirname(HERE)), "extract", "sprites", f"spr_spellbt_{f}.png")
        im = bb.process(src, "כישוף")
        out_spr("spr_spellbt", f, o, im)


def tiny_label(name, text, color, bg=(0, 0, 0, 255), top=None):
    o = load_sprite(name, 0)
    im = Image.new("RGBA", o.size, bg)
    t, up = mini_image(text, color)
    y = (o.height - 5) // 2 - up + (1 if up else 0) if top is None else top - up
    put_img(im, t, (o.width - t.width) // 2, y)
    out_spr(name, 0, o, im)


def do_tiny_texts():
    cyan, red = (64, 255, 255, 255), (237, 28, 36, 255)
    tiny_label("spr_text_congratulations", "כל הכבוד!", cyan, top=1)
    tiny_label("spr_text_missionfailed", "המשימה נכשלה!", red, top=1)
    tiny_label("spr_text_restart", "שוב...", red, top=1)
    tiny_label("spr_text_restaurant", "שווארמה...", red, top=1)


def do_text_shot():
    o = load_sprite("spr_text_shot", 0)
    # colour per row (vertical red -> magenta gradient of the old letters)
    rowc = []
    for y in range(o.height):
        c = Counter(p for p in (o.getpixel((x, y)) for x in range(o.width)) if p[3] and p[:3] != (0, 0, 0))
        rowc.append(c.most_common(1)[0][0] if c else None)
    im = Image.new("RGBA", o.size, (0, 0, 0, 255))
    t, _ = mini_image("יריות:", (255, 255, 255, 255), cell=(1, 4))
    x0 = (o.width - t.width) // 2
    for y in range(t.height):
        for x in range(t.width):
            if t.getpixel((x, y))[3]:
                im.putpixel((x0 + x, y), rowc[y] or rowc[0])
    out_spr("spr_text_shot", 0, o, im)


def do_timehud():
    red, black = (237, 28, 36, 255), (0, 0, 0, 255)
    for name, words in (("spr_timehud", ["זמן"]), ("spr_timehud_vert", ["טעם", "זמן"])):
        o = load_sprite(name, 0); im = o.copy()
        # each label = a cluster of red pixels; handle them left to right
        bb = bbox_of(im, is_(red))
        cols = sorted({x for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1) if im.getpixel((x, y)) == red})
        groups, cur = [], [cols[0]]
        for c in cols[1:]:
            if c - cur[-1] > 6:
                groups.append(cur); cur = [c]
            else:
                cur.append(c)
        groups.append(cur)
        assert len(groups) == len(words), (name, len(groups))
        for g, word in zip(groups, words):
            box = bbox_of(im, is_(red), (g[0], 0, g[-1], im.height - 1))
            recolor(im, is_(red), black, box)
            t, up = mini_image(word, red)
            put_img(im, t, center_x(box, t.width), box[3] - 4 - up)
        out_spr(name, 0, o, im)


def do_tv_warning():
    o = load_sprite("spr_tv_warning", 0); im = o.copy()
    yel, red = (255, 242, 0, 255), (237, 28, 36, 255)
    box = bbox_of(im, is_(yel))
    recolor(im, is_(yel), red, box)
    t, xt, base = word_image("אזהרה", yel, scale=(2, 3), gap=2)
    cy = (box[1] + box[3]) // 2
    put_img(im, t, center_x(box, t.width), cy - (xt + base) // 2)
    out_spr("spr_tv_warning", 0, o, im)


def do_wordfall():
    # positions are fixed left to right in obj_wordfall: * [EVEN] [MY] [WORDS] [ARE] ... !
    # Hebrew reads right to left, so the slots get (left to right): הן / שלי / המילים / גם
    white, black = (255, 255, 255, 255), (0, 0, 0, 255)
    for name, word in (("spr_wordfall2", "הן"), ("spr_wordfall3", "שלי"), ("spr_wordfall4", "המילים"),
                       ("spr_wordfall5", "גם")):
        o = load_sprite(name, 0)
        box = bbox_of(o, is_(white))                  # old letters (9 rows tall)
        im = Image.new("RGBA", o.size, (0, 0, 0, 0))
        gap = 1
        fx = None
        t, xt, base = word_image(word, white, gap=gap, outline=black, extra_rows=2, fx=fx)
        if t.width > o.width:
            t, xt, base = word_image(word, white, gap=gap, outline=black, extra_rows=2,
                                     fx=lambda ch, g: narrow(g, 2) if ch == "ש" else narrow(g, 1))
        assert t.width <= o.width, (name, t.width, o.width)
        x = (o.width - t.width) // 2
        y = box[3] + 1 - base                          # same baseline as the old word
        put_img(im, t, x, y)
        out_spr(name, 0, o, im)


# ---------------------------------------------------------------- title logo
def do_title():
    """Hebrew logo 'אנדרטייל' built from the font glyphs on the English logo's 3px block grid:
    one font column = 2 blocks, font rows 5..11 -> 9 blocks (top/bottom strokes 3 blocks thick),
    grey chips on outer corners, and the red heart sits in the cup of the ט (as in the R)."""
    o = load_sprite("spr_undertaletitle", 0)
    white, grey, red, black = (255, 255, 255, 255), (132, 132, 132, 255), (237, 28, 36, 255), (0, 0, 0, 255)
    heart = [(x - 160, y - 115) for x in range(160, 169) for y in range(115, 124) if o.getpixel((x, y)) == red]
    im = o.copy()
    clear(im, (20, 100, 294, 140), black)               # old logo; the TM mark at the right stays
    B, ytop = 3, 109
    rowmap = [0, 0, 1, 2, 3, 4, 5, 6, 6]
    glyphs = []
    for ch in visual("אנדרטייל"):
        rows, top = fglyph(ch)
        fr = lambda r: rows[r - top] if 0 <= r - top < len(rows) else "." * len(rows[0])
        asc = [fr(top)] + [fr(r) for r in range(top, XTOP)] if top < XTOP else []
        blk = asc + [fr(XTOP + m) for m in rowmap]
        glyphs.append((ch, ["".join(c * 2 for c in r) for r in blk], len(asc)))
    total = sum(len(b[0]) for _, b, _ in glyphs) + len(glyphs) - 1
    bx0 = 160 // B - total // 2
    cells, heart_xy, bx = {}, None, bx0
    for ch, blk, asc in glyphs:
        for by, r in enumerate(blk):
            for i, c in enumerate(r):
                if c == "#":
                    cells[(bx + i, by - asc)] = white
        if ch == "ט":
            heart_xy = ((bx + 4) * B + 2, ytop + 2 * B + 3)
        bx += len(blk[0]) + 1
    for (x, y) in sorted(cells, key=lambda c: -c[1]):     # bolder: every stroke grows one block down
        if y + 1 <= 8 and (x, y + 1) not in cells:
            cells[(x, y + 1)] = white
    for (x, y) in list(cells):                           # grey chips: top-left outer corners
        if (x - 1, y) not in cells and (x, y - 1) not in cells and (x + 1, y) in cells and (x, y + 1) in cells:
            cells[(x, y)] = grey
    for (x, y), c in cells.items():
        clear(im, (x * B, ytop + y * B, x * B + B - 1, ytop + y * B + B - 1), c)
    for dx, dy in heart:
        im.putpixel((heart_xy[0] + dx, heart_xy[1] + dy), red)
    out_spr("spr_undertaletitle", 0, o, im)


# ---------------------------------------------------------------- backgrounds
def do_exitsign():
    o = load_bg("bg_exitsign"); im = o.copy()
    red, black = im.getpixel((1, 1)), (0, 0, 0, 255)
    box = (0, 0, o.width - 1, 16)                        # letters rows 0..16, arrow below stays
    recolor(im, lambda p: p[3] and p[:3] != (0, 0, 0), black, box)
    t, xt, base = word_image("יציאה", red, gap=2, extra_rows=10)
    put_img(im, t, center_x(box, t.width), 0 - xt)
    out_bg("bg_exitsign", o, im)


def lab_plate(name, slope, text_col, fill_col, region, line_v=None):
    """Slanted LAB plate: text pixels in region -> fill; draw sheared 'לאב'.
    slope -1: plate rises to the right (v = y + x); slope +1: falls to the right (v = y - x)."""
    o = load_bg(name); im = o.copy()
    x0, y0, x1, y1 = region
    vk = (lambda x, y: y + x) if slope < 0 else (lambda x, y: y - x)
    pts = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
           if im.getpixel((x, y)) == text_col and (line_v is None or vk(x, y) < line_v)]
    vs = [vk(x, y) for x, y in pts]; xs = [x for x, _ in pts]
    for x, y in pts:
        im.putpixel((x, y), fill_col)
    vmin, vmax, xmin, xmax = min(vs), max(vs), min(xs), max(xs)
    # A sheared font breaks up at this size, so each letter stays upright and steps along the slant
    # (centred on the plate's slanted middle line at the letter's own centre column).
    vmid = (vmin + vmax) / 2
    gl = [narrow(fglyph(ch), 1) for ch in visual("לאב")]
    w = sum(g_w(g) for g in gl) + len(gl) - 1
    x = xmin + ((xmax - xmin + 1) - w) // 2
    for rows, top in gl:
        gw = len(rows[0])
        xc = x + (gw - 1) / 2
        ymid = vmid - xc if slope < 0 else vmid + xc      # plate middle at this column
        y_xtop = round(ymid - 3)                          # font rows 5..11 centred on it
        for yy, r in enumerate(rows):
            for xx, c in enumerate(r):
                P = (x + xx, y_xtop + (top + yy - XTOP))
                if c == "#" and im.getpixel(P) == fill_col:   # never paint over the plate's border
                    im.putpixel(P, text_col)
        x += gw + 1
    out_bg(name, o, im)


def do_labs():
    lab_plate("bg_alab_outside_r", -1, (144, 31, 15, 255), (213, 202, 200, 255), (50, 160, 72, 198), line_v=248)
    lab_plate("bg_alphyslabl_new", +1, (144, 31, 15, 255), (213, 202, 200, 255), (70, 40, 98, 80))
    lab_plate("bg_alphyslaboutside", +1, (52, 50, 61, 255), (179, 182, 198, 255), (90, 84, 112, 115))


def plate_word(name, box, text, color, fill, scale=(1, 1), fx=None, gap=1, extra_rows=0, text_pred=None,
               yoff=0, space=4):
    o = load_bg(name); im = o.copy()
    pred = text_pred or is_(color)
    tb = bbox_of(im, pred, box)
    if fill is None:                                      # most common non-text colour in the box
        fill = Counter(p for p in (im.getpixel((x, y)) for x in range(box[0], box[2] + 1)
                                   for y in range(box[1], box[3] + 1)) if not pred(p)).most_common(1)[0][0]
    recolor(im, pred, fill, box)
    t, xt, base = word_image(text, color, scale=scale, gap=gap, fx=fx, extra_rows=extra_rows, space=space)
    cy2 = tb[1] + tb[3] + 1                               # 2 * centre of old letters
    y = (cy2 - (xt + base)) // 2 + yoff
    put_img(im, t, center_x(tb, t.width), y)
    return o, im


def do_simple_bgs():
    # Snowdin library: deliberately misspelled like LIBRARBY (one letter too many)
    lb = (207, 219, 255, 255)
    o, im = plate_word("bg_library_outside", (52, 67, 91, 75), "ספררייה", lb, (133, 163, 216, 255),
                       fx=lambda ch, g: thin(g), extra_rows=2)
    out_bg("bg_library_outside", o, im)
    # Temmie statue plaque
    o, im = plate_word("bg_temstatue", (11, 69, 42, 75), "טם", (120, 77, 116, 255), (181, 150, 172, 255),
                       scale=(2, 1), gap=1)
    out_bg("bg_temstatue", o, im)
    # ending tileset: SCHOOL plate
    # ending tileset: SCHOOL plate -> the usual sign abbreviation בי"ס (בית ספר does not fit)
    o, im = plate_word("bg_endtileset", (87, 224, 110, 234), 'בי"ס', (0, 0, 0, 255), (242, 242, 216, 255),
                       text_pred=lambda p: p[:3] == (0, 0, 0) and p[3], extra_rows=4, gap=2, yoff=1)
    out_bg("bg_endtileset", o, im)


def do_inn_shop():
    o = load_bg("bg_inn_shop"); im = o.copy()
    org, wood = (219, 148, 68, 255), (145, 74, 59, 255)
    for box, word, fx in (((49, 71, 82, 77), "חנות", None),
                          ((229, 71, 262, 77), "פונדק", lambda ch, g: cut_desc(g, 1) if ch == "ק" else g)):
        tb = bbox_of(im, is_(org), box)
        recolor(im, is_(org), wood, box)
        t, xt, base = word_image(word, org, fx=fx)
        put_img(im, t, center_x(tb, t.width), tb[3] + 1 - base)
    out_bg("bg_inn_shop", o, im)


def do_snowdinlogo():
    o = load_sprite("spr_snowdinlogo", 0); im = o.copy()
    plate, red, blue = (214, 220, 228, 255), (220, 63, 67, 255), (112, 208, 245, 255)
    recolor(im, is_(red), plate, (40, 13, 150, 21))
    recolor(im, is_(blue), plate, (46, 22, 141, 36))      # letters only; the snow dots around them stay
    # "ברוכים הבאים" (red, right-aligned like Hebrew signs) over "לסנודין" (big, blue)
    t, xt, base = word_image("ברוכים הבאים", red, gap=2)
    put_img(im, t, 143 - t.width, 20 - base)
    t, xt, base = word_image("לסנודין", blue, scale=(2, 2), gap=1,
                             fx=lambda ch, g: cut_desc(g, 1) if ch == "ן" else g)
    put_img(im, t, (46 + 141 + 1 - t.width) // 2 - 6, 35 - base)
    out_spr("spr_snowdinlogo", 0, o, im)


def do_blookposter():
    o = load_bg("bg_blookposter_1"); im = o.copy()
    yel, purple = (255, 242, 0, 255), (163, 73, 164, 255)
    box = (18, 11, 43, 24)                                 # MOVIE; the two stars at the left stay
    tb = bbox_of(im, is_(yel), box)
    recolor(im, is_(yel), purple, box)
    t, xt, base = word_image("סרט", yel, gap=2, extra_rows=4)
    put_img(im, t, center_x(tb, t.width), tb[3] + 1 - base)
    out_bg("bg_blookposter_1", o, im)


def do_bratty():
    o = load_bg("bg_brattybg"); im = o.copy()
    board, ink = (55, 42, 109, 255), (43, 32, 82, 255)
    notb = lambda p: p != board
    for box in ((121, 12, 126, 22), (127, 12, 178, 25), (179, 16, 187, 25)):   # text + underlines, not the hearts
        recolor(im, notb, board, box)
    t, xt, base = word_image("ברטי וקטי", ink, gap=2, extra_rows=4,
                             fx=lambda ch, g: cut_desc(g, 1) if ch == "ק" else g)
    put_img(im, t, (121 + 187 + 1 - t.width) // 2 - 3, 25 - base)
    out_bg("bg_brattybg", o, im)


def do_grillbyout():
    o = load_bg("bg_grillbyout"); im = o.copy()
    sal, board = (255, 136, 88, 255), (47, 32, 26, 255)
    box = (0, 59, o.width - 1, 74)
    tb = bbox_of(im, is_(sal), box)
    recolor(im, is_(sal), board, box)
    t, xt, base = word_image("אצל גרילבי", sal, scale=(2, 2), gap=2)
    put_img(im, t, center_x(tb, t.width), 75 - base)      # x-height rows 61..74, ל rises to row 57
    # OPEN sign in the window
    org, plate = (255, 154, 38, 255), (109, 47, 41, 255)
    box = (64, 106, 92, 113)
    tb = bbox_of(im, lambda p: p in (org, (201, 97, 41, 255)), box)
    recolor(im, lambda p: p in (org, (201, 97, 41, 255)), plate, box)
    t, xt, base = word_image("פתוח", org)
    put_img(im, t, center_x(tb, t.width), 114 - base)
    out_bg("bg_grillbyout", o, im)


def do_grillby_neon():
    o = load_bg("bg_grillbyplaceholder"); im = o.copy()
    wall, pink, dark = (61, 18, 14, 255), (255, 74, 218, 255), (142, 23, 103, 255)
    recolor(im, lambda p: p in (pink, dark), wall, (244, 10, 302, 34))   # neon writing; the glass stays
    # neon letters and an underline swoosh
    t, xt, base = word_image("גרילבי", pink, scale=(1, 2), gap=2)
    x0 = 281 - t.width
    put_img(im, t, x0, 29 - base)
    for x in range(x0 - 2, 283):
        im.putpixel((x, 31), pink)
    for x, y in ((x0 - 3, 30), (x0 - 4, 29), (283, 30), (284, 29)):
        im.putpixel((x, y), pink)
    for x in range(x0 - 1, 282, 5):                        # a few darker tube pixels, as on the old sign
        im.putpixel((x, 32), dark)
    out_bg("bg_grillbyplaceholder", o, im)


# ---------------------------------------------------------------- Monster Kidz word search
# Grid rows are in reading order (right to left). Like the English page most list words are NOT in the
# grid: only שלדים (backwards), מפלצת, בתים (backwards), סיגרים and סיג are, and the first row is the
# "word" גיאספצלפהברהחבהר from the list, except that the list has ה where the grid has ו (the English
# page has the same slip: GIASFCLFUBREHBER vs giasfclfebrehber).
WS_GRID = [
    "גיאספצלפוברהחבהר",
    "נפבאווקגקסשאמשאו",
    "ירםידלשטכהגקשתפב",
    "רלחאתמפלצתרמנגוח",
    "פמדםיתבנאוקקחהיט",
    "שסיגריםסוחרשוגדצ",
]
WS_LIST = [  # columns right to left (Hebrew reading order), each top to bottom
    ["סתיו", "חורף", "אביב", "קיץ"],
    ["מפלצת", "שלדים", "בת ים", "רובוט"],
    ["סיגרים", "סיג", "גיאספצלפהברהחבהר", "חם"],
]
WS_BUBBLE = ["היי ילד'ים!", "תעזרו לי", "לפתור את", "הפאזל?"]   # "Kid's" keeps its wrong apostrophe


def do_wordsearch():
    white, black = (255, 255, 255, 255), (0, 0, 0, 255)
    pink, red, orange, yellow = (255, 174, 201, 255), (237, 28, 36, 255), (255, 127, 39, 255), (255, 242, 0, 255)
    # the thin (Zhang-Suen) letters lose ת's foot and ל's ascender at this size, so the list, labels and
    # bubble use the bold letters made one column narrower
    thinfx = lambda ch, g: narrow(g, 1)
    for f in (0, 1):
        o = load_sprite("spr_wordsearch", f); im = o.copy()
        dx = 0 if f == 0 else -22                                   # frame 1 has the grid and list 22px left
        # --- title (both frames): "תפזורת ילדי מפלצות" in the four title colours
        clear(im, (30, 10, 250, 28), white)
        parts = [("מפלצות", pink), (" ", None), ("ילדי", red), (" ", None), ("ורת", yellow), ("", None), ("תפז", orange)]
        imgs = []
        for txt, col in parts:
            if col is None:
                imgs.append((None, 8 if txt == " " else 2, 0))
            else:
                t, xt, base = word_image(txt, col, scale=(2, 2))
                imgs.append((t, t.width, base))
        tw = sum(w for _, w, _ in imgs)
        x = 140 - tw // 2
        for t, w, base in imgs:
            if t is not None:
                put_img(im, t, x, 27 - base)
            x += w
        # --- letter grid: 16 x 6, 8px cells, 9px tall bold letters
        clear(im, (98 + dx, 40, 228 + dx, 127), white)
        for r, row in enumerate(WS_GRID):
            for i, ch in enumerate(visual(row)):
                t, xt, base = word_image(ch, black, extra_rows=2,
                                         fx=lambda c, g: narrow(g, max(0, g_w(g) - 6)))
                put_img(im, t, 100 + dx + 8 * i + (7 - t.width) // 2, 42 + 15 * r + 9 - base)
        # --- word list: columns right-aligned (frame 1 keeps rows 1-2 clear of the snowman)
        if f == 0:
            clear(im, (82, 134, 270, 193), white)
        else:
            clear(im, (58, 134, 218, 193), white); clear(im, (218, 165, 266, 193), white)
        right = 240 + dx
        for col in WS_LIST:
            ws = []
            for j, w in enumerate(col):
                t, xt, base = word_image(w, black, fx=thinfx, space=3)
                put_img(im, t, right - t.width + 1, 145 + 15 * j + 1 - base)
                ws.append(t.width)
            right -= max(w for w in ws if w < 60) + 6
        # --- labels
        boxes = [(22, 38, 62, 52)] if f == 0 else [(8, 44, 48, 57), (222, 33, 275, 47)]
        for box, word in zip(boxes, ["קרחי", "סיוט"]):
            tb = bbox_of(im, lambda p: p[3] and p[:3] != (255, 255, 255), box)
            clear(im, tb, white)
            t, xt, base = word_image(word, black, fx=thinfx)
            put_img(im, t, center_x(tb, t.width), tb[3] + 1 - base)
        # --- speech bubble (frame 0)
        if f == 0:
            clear(im, (16, 139, 72, 186), white)
            for k, line in enumerate(WS_BUBBLE):
                t, xt, base = word_image(line, black, fx=thinfx, space=3)
                put_img(im, t, 44 - t.width // 2, 148 + 11 * k + 1 - base)
        out_spr("spr_wordsearch", f, o, im)


# ----------------------------------------------------------------------------------------------
JOBS = {
    "spr_snowsans": do_snowsans,
    "spr_soapbul": do_soapbul,
    "spr_spellbt": do_spellbt,
    "spr_text_*": do_tiny_texts,
    "spr_text_shot": do_text_shot,
    "spr_timehud*": do_timehud,
    "spr_tv_warning": do_tv_warning,
    "spr_wordfall*": do_wordfall,
    "spr_undertaletitle": do_title,
    "bg_exitsign": do_exitsign,
    "bg_lab*": do_labs,
    "bg_simple": do_simple_bgs,
    "bg_inn_shop": do_inn_shop,
    "spr_snowdinlogo": do_snowdinlogo,
    "bg_blookposter_1": do_blookposter,
    "bg_brattybg": do_bratty,
    "bg_grillbyout": do_grillbyout,
    "bg_grillbyplaceholder": do_grillby_neon,
    "spr_wordsearch": do_wordsearch,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--preview", default="")
    a = ap.parse_args()
    only = [s for s in a.only.split(",") if s]
    for key, fn in JOBS.items():
        if only and not any(o == key or (key.endswith("*") and o.startswith(key[:-1])) for o in only):
            continue
        fn()
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
        for kind, name, frame, orig, new in RESULTS:
            s = 4 if max(orig.size) <= 64 else (3 if max(orig.size) <= 160 else 2)
            preview([orig, new], os.path.join(a.preview, f"pv_{name}_{frame}.png"), scale=s)
    print("written:", len(RESULTS))


if __name__ == "__main__":
    main()
