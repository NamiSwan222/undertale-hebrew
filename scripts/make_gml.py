"""Generate the modified GML for the build:
 - build/gml/gml_Script_textdata_en.gml : Hebrew where translated, English fallback
 - build/gml/gml_Object_obj_base_writer_Draw_0.gml : RTL writer (patched from the original decompile)
"""
import json, os, glob, re
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CE = os.path.join(W, "extract", "CodeEntries")
OUT = os.path.join(W, "build", "gml"); os.makedirs(OUT, exist_ok=True)
for _f in glob.glob(os.path.join(OUT, "*.gml")):
    os.remove(_f)  # generated files only; rebuilt below

def load(code):
    """Current text of a code entry: already-patched copy in OUT if any, else the original decompile."""
    p = os.path.join(OUT, code + ".gml")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    return open(os.path.join(CE, code + ".gml"), encoding="utf-8").read()

def gml_str(s):
    if '"' not in s:
        return '"' + s + '"'
    if "'" not in s:
        return "'" + s + "'"
    parts = s.split('"')
    return ' + \'"\' + '.join('"' + p + '"' for p in parts)

def load_he():
    he = {}
    for f in sorted(glob.glob(os.path.join(W, "translation", "he", "*.json"))):
        if "_part" in os.path.basename(f):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except ValueError as e:
            print("SKIP (bad json):", f, e)
            continue
        for k, v in d.items():
            he[k] = v
    return he

def textdata():
    items = json.load(open(os.path.join(W, "translation", "strings_en.json"), encoding="utf-8"))
    he = load_he()
    lines = ["global.text_data_en = ds_map_create();"]
    n = 0
    for it in items:
        v = he.get(it["id"])
        if v is None:
            v = it["en"]
        else:
            n += 1
        lines.append(f'ds_map_add(global.text_data_en, "{it["id"]}", {gml_str(v)});')
    open(os.path.join(OUT, "gml_Script_textdata_en.gml"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"textdata: {n}/{len(items)} translated")

def must_replace(src, old, new, count=1):
    c = src.count(old)
    if c != count:
        raise SystemExit(f"patch anchor found {c}x (want {count}): {old[:60]!r}")
    return src.replace(old, new)

def writer_draw():
    src = open(os.path.join(CE, "gml_Object_obj_base_writer_Draw_0.gml"), encoding="utf-8").read()
    src = must_replace(src, """if (vtext)
{
    myx = writingxend - vspacing;
}
else
{
    myx = writingx;
}
""", """if (originalstring != rtl_src)
{
    rtl_src = originalstring;
    scr_rtl_prep();
}
if (myfont == fnt_plain || myfont == fnt_curs || myfont == fnt_plainbig || string_copy(room_get_name(room), 1, 9) == "room_shop")
{
    rtl_anchor = writingx + rtl_w;
}
else
{
    rtl_anchor = writingxend;
}
rtl_line = 0;
if (vtext)
{
    myx = writingxend - vspacing;
}
else if (rtl_ltr[0])
{
    myx = writingx;
}
else
{
    myx = rtl_anchor;
}
""")
    n_before = src.count("string_char_at(originalstring")
    src = src.replace("string_char_at(originalstring", "string_char_at(rtl_str")
    # icons
    src = must_replace(src, """                else
                {
                    draw_sprite_ext(sprite, 0, spritex, spritey, icon_scale, icon_scale, 0, c_white, 1);
                    myx += ((sprite_get_width(sprite) + 1) * icon_scale);
                }""", """                else if (!rtl_ltr[min(rtl_line, 39)])
                {
                    draw_sprite_ext(sprite, 0, spritex - (sprite_get_width(sprite) * icon_scale), spritey, icon_scale, icon_scale, 0, c_white, 1);
                    myx -= ((sprite_get_width(sprite) + 1) * icon_scale);
                }
                else
                {
                    draw_sprite_ext(sprite, 0, spritex, spritey, icon_scale, icon_scale, 0, c_white, 1);
                    myx += ((sprite_get_width(sprite) + 1) * icon_scale);
                }""")
    src = must_replace(src, """        if (!vtext && myx > writingxend)
        {
            script_execute(SCR_NEWLINE);
        }
        var letterx = myx;
""", """        if (!vtext)
        {
            if (rtl_ltr[min(rtl_line, 39)])
            {
                if (myx > writingxend)
                {
                    script_execute(SCR_NEWLINE);
                }
            }
            else if ((myx - spacing) < (writingx - 4))
            {
                script_execute(SCR_NEWLINE);
            }
        }
        var rtl_now = 0;
        if (!vtext && !rtl_ltr[min(rtl_line, 39)])
        {
            rtl_now = 1;
        }
        scr_setfont(myfont);
        var rtl_step = scr_rtl_step(myletter);
        if (halfsize)
        {
            rtl_step = round(rtl_step / 2);
        }
        var letterx = myx;
        if (rtl_now)
        {
            letterx = myx - rtl_step;
        }
        var rtl_next = letterx;
""")
    src = must_replace(src, """        if (!vtext)
        {
            if (halfsize)
            {
                myx = round(myx + ((letterx - myx) / 2));""", """        if (rtl_now)
        {
            myx = rtl_next;
        }
        else if (!vtext)
        {
            if (halfsize)
            {
                myx = round(myx + ((letterx - myx) / 2));""")
    src = must_replace(src, "        letterx += spacing;\n", "        letterx += scr_rtl_step(myletter);\n")
    open(os.path.join(OUT, "gml_Object_obj_base_writer_Draw_0.gml"), "w", encoding="utf-8").write(src)
    print("writer draw patched; char reads redirected:", n_before)

def newline():
    open(os.path.join(OUT, "gml_Script_SCR_NEWLINE.gml"), "w", encoding="utf-8").write("""if (vtext)
{
    myx -= vspacing;
    myy = writingy;
}
else
{
    rtl_line += 1;
    if (rtl_ltr[min(rtl_line, 39)])
    {
        myx = writingx;
    }
    else
    {
        myx = rtl_anchor;
    }
    myy += vspacing;
}
""")

INIT = """
rtl_src = "";
rtl_str = "";
rtl_w = 0;
rtl_line = 0;
rtl_anchor = 0;
rtl_refw = 0;
for (var rtl_k = 0; rtl_k < 40; rtl_k += 1)
{
    rtl_ltr[rtl_k] = 0;
}
"""
def creates():
    for name in ["gml_Object_obj_base_writer_Create_0", "gml_Object_OBJ_NOMSCWRITER_Create_0"]:
        src = open(os.path.join(CE, name + ".gml"), encoding="utf-8").read()
        open(os.path.join(OUT, name + ".gml"), "w", encoding="utf-8").write(INIT.lstrip() + src)

LIT = re.compile(r'"[^"\n]*"(?: \+ \'"\' \+ "[^"\n]*")*|\'[^\'\n]*\'')

def code_literals():
    # Hardcoded on-screen strings outside the text table. The repo stores only a SHA-1 of the original GML
    # literal (no English text); the literal is found in the player's own decompiled code by its hash.
    import hashlib
    lits = json.load(open(os.path.join(W, "translation", "he_code_literals_hashed.json"), encoding="utf-8"))
    by = {}
    for l in lits:
        by.setdefault(l["code"], []).append(l)
    for code, ls in by.items():
        src = load(code)
        found = {hashlib.sha1(m.encode("utf-8")).hexdigest(): m for m in LIT.findall(src)}
        for l in ls:
            old = found.get(l["en_sha1"])
            if old is None:
                raise SystemExit(f"code literal not found in {code} (sha1 {l['en_sha1']})")
            src = must_replace(src, old, gml_str(l["he"]), src.count(old))
        open(os.path.join(OUT, code + ".gml"), "w", encoding="utf-8").write(src)
    print("code literals:", len(lits))

HEB_GRID = "אבגדהוזחטיכךלמםנןסעפףצץקרשת"

def naming():
    # lower half of the Latin grid -> Hebrew letters, filled right to left
    src = load("gml_Script_scr_namingscreen_setup")
    src = must_replace(src, 'hiragana_chstr[0] = ', """var heb_letters = "%s";
for (var hi = 0; hi < 4; hi++)
{
    for (var hj = 0; hj < 7; hj++)
    {
        var hk = (hi * 7) + hj;
        if (hk < 27)
        {
            ascii_charmap[hi + 4, 6 - hj] = string_char_at(heb_letters, hk + 1);
        }
        else
        {
            ascii_charmap[hi + 4, 6 - hj] = "";
        }
    }
}
hiragana_chstr[0] = """ % HEB_GRID)
    open(os.path.join(OUT, "gml_Script_scr_namingscreen_setup.gml"), "w", encoding="utf-8").write(src)
    src = load("gml_Script_scr_namingscreen_check")
    src = must_replace(src, "var l_char = string_to_hiragana(string_lower(argument0));",
                       "var l_char = string_to_hiragana(string_lower(scr_heb_namealias(argument0)));")
    open(os.path.join(OUT, "gml_Script_scr_namingscreen_check.gml"), "w", encoding="utf-8").write(src)
    src = load("gml_Script_scr_hardmodename")
    src = must_replace(src, 'string_lower(argument0) == "frisk"', 'string_lower(scr_heb_namealias(argument0)) == "frisk"')
    open(os.path.join(OUT, "gml_Script_scr_hardmodename.gml"), "w", encoding="utf-8").write(src)
    print("naming screen: Hebrew grid + name aliases")

def wordfall():
    # Mettaton news "* EVEN MY WORDS ARE...!": Hebrew reads right to left, so "*" goes to the right end
    # and "..." / "!" to the left end (the word sprites themselves were redrawn in Hebrew order).
    src = load("gml_Object_obj_wordfall_Create_0")
    pos = {"1": (178, 10), "2": (43, 9), "3": (76, 9), "4": (111, 9), "5": (151, 9), "6": (14, 9), "7": (7, 9)}
    old = {"1": (7, 10), "2": (33, 9), "3": (66, 9), "4": (101, 9), "5": (141, 9), "6": (164, 9), "7": (182, 9)}
    for k in pos:
        a = "    w = instance_create(x + %d, y + %d, obj_wordfall_word);\n    w.sprite_index = spr_wordfall%s;" % (old[k][0], old[k][1], k)
        b = "    w = instance_create(x + %d, y + %d, obj_wordfall_word);\n    w.sprite_index = spr_wordfall%s;" % (pos[k][0], pos[k][1], k)
        src = must_replace(src, a, b)
    open(os.path.join(OUT, "gml_Object_obj_wordfall_Create_0.gml"), "w", encoding="utf-8").write(src)
    print("wordfall: mirrored")

if __name__ == "__main__":
    textdata(); writer_draw(); newline(); creates(); code_literals(); naming(); wordfall()
