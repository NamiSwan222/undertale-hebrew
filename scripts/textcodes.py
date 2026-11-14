"""Tokenizer for Undertale text strings, mirroring obj_base_writer's Draw parsing.

Token kinds:
  ("code", text)   control code: \\X, \\X<arg> (M E F S T z * >), ^<c>, \\[C] style substitution
  ("nl", "&")      writer newline        ("#" is the draw_text newline, also "nl")
  ("end", text)    "/" , "%", "/%%" etc. (message terminators)
  ("ch", c)        printable character
"""
import re

ARG_CODES = set("MEFSTz*>")
SUBST = re.compile(r"\\\[(.)\]")
SUBST_WIDTH = {"C": 6, "G": 4, "I": 12, "1": 4, "2": 4, "3": 4, "4": 4, "5": 4, "6": 4, "7": 4}


def tokens(s):
    i, n = 0, len(s)
    out = []
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            if s[i + 1] == "[" and i + 3 < n and s[i + 3] == "]":
                out.append(("subst", s[i:i + 4]))
                i += 4
                continue
            c2 = s[i + 1]
            if c2 in ARG_CODES and i + 2 < n:
                out.append(("code", s[i:i + 3]))
                i += 3
            else:
                out.append(("code", s[i:i + 2]))
                i += 2
        elif c == "^" and i + 1 < n:
            out.append(("code", s[i:i + 2]))
            i += 2
        elif c in "&#":
            out.append(("nl", c))
            i += 1
        elif c in "/%":
            j = i
            while j < n and s[j] in "/%":
                j += 1
            out.append(("end", s[i:j]))
            i = j
        else:
            out.append(("ch", c))
            i += 1
    return out


def codes(s):
    """Ordered list of non-printing tokens that must be preserved (codes, substitutions, terminators)."""
    return [t for k, t in tokens(s) if k in ("code", "subst", "end")]


def newline_count(s):
    return sum(1 for k, t in tokens(s) if k == "nl")


def messages_lines(s):
    """Split into lines of printable text (per message chunk). Substitutions become placeholders."""
    lines = [[]]
    for k, t in tokens(s):
        if k == "ch":
            lines[-1].append(t)
        elif k == "subst":
            lines[-1].append(("SUBST", t[2]))
        elif k in ("nl", "end"):
            lines.append([])
    return [l for l in lines]


def is_heb(c):
    return isinstance(c, str) and "֐" <= c <= "׿"


# Hebrew glyph advance (fnt_maintext pixels, 1x) as built from the FontStruct font:
# writer step = glyph shift + (spacing - shift of bet)
HEB_SHIFT = {"א": 8, "ב": 7, "ג": 6, "ד": 8, "ה": 7, "ו": 4, "ז": 6, "ח": 7, "ט": 7, "י": 4, "ך": 6, "כ": 6, "ל": 7,
             "ם": 7, "מ": 8, "ן": 4, "נ": 5, "ס": 7, "ע": 8, "ף": 7, "פ": 7, "ץ": 7, "צ": 7, "ק": 7, "ר": 6, "ש": 9, "ת": 8}


def line_units(line):
    """Width of a line in 'cells' (1.0 = one fixed-width writer cell). Hebrew letters are proportional."""
    w = 0.0
    for c in line:
        if isinstance(c, tuple):
            w += SUBST_WIDTH.get(c[1], 4)
        elif is_heb(c):
            w += (HEB_SHIFT.get(c, 7) + 1) / 8.0
        else:
            w += 1.0
    return w
