"""Checker for Hebrew translations.

  python scripts/check_batch.py translation/he/b07.json          # check one output file
  python scripts/check_batch.py --all                            # check everything + coverage

Rules (see translation/glossary.md, "Technical rules"):
  E-missing   id in the batch input but not in the output (or, with --all, not translated anywhere)
  E-unknown   output id that doesn't exist in the game
  E-codes     control codes / substitutions / terminators differ (order and count)
  E-msgs      number of messages differs
  E-lines     a message has more lines than allowed
  E-width     a line is wider than allowed
  E-glyph     a character the game fonts can't draw (e.g. niqqud)
  W-latin     Latin word left in the Hebrew (possible untranslated text)
  W-nohebrew  translation has no Hebrew letters but English has letters
"""
import json, os, sys, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textcodes import tokens, codes, line_units

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = {x["id"]: x for x in json.load(open(os.path.join(W, "translation", "strings_en.json"), encoding="utf-8"))}
LATIN_OK = {"HP", "LV", "EXP", "AT", "DF", "G", "MTT", "RG", "EX", "NEO", "Z", "X", "C", "A", "B", "ENTER",
            "SHIFT", "CTRL", "ESC", "F4", "OK", "LOVE", "UNDERTALE", "TV", "DT", "EXECUTION", "POINTS", "LEVEL",
            "OF", "VIOLENCE", "ID", "SOS", "VS", "PS", "KO", "UFO", "DVD", "CD", "DJ", "MC", "PM", "AM", "XOXO",
            "LOL", "OMG", "NYEH", "Toby", "Fox", "N", "S", "W", "E", "Esc", "or", "Hold", "PAGE", "PRESS", "AND"}


def messages(s):
    """List of messages; each message is a list of lines; each line a list of chars/subst tuples."""
    msgs = [[[]]]
    for k, t in tokens(s):
        if k == "ch":
            msgs[-1][-1].append(t)
        elif k == "subst":
            msgs[-1][-1].append(("SUBST", t[2]))
        elif k == "nl":
            msgs[-1].append([])
        elif k == "end":
            msgs.append([[]])
    if msgs and msgs[-1] == [[]]:
        msgs.pop()
    return msgs


def is_face(s):
    return bool(re.search(r"\\[EF]\d", s))


def limits(en):
    em = messages(en)
    widest = max([line_units(l) for m in em for l in m] or [0])
    star = any(l and l[0] == "*" for m in em for l in m)
    if ("&" in en or "/" in en or "\\" in en) and not star:
        # speech bubbles / free text without "* ": bubbles are narrow, stay near the English width
        wlim = max(widest + 2, 8)
    elif "&" in en or "/" in en or "\\" in en or en.startswith("*"):
        cap = 26 if is_face(en) else 28
        wlim = max(widest, cap) + 0.25
    else:
        wlim = widest + 3 if widest <= 10 else widest + 1
    llims = [max(3, len(m)) for m in em]
    return wlim, llims


def check_one(i, en, he):
    errs = []
    if codes(en) != codes(he):
        errs.append(("E-codes", f"en {codes(en)} != he {codes(he)}"))
    em, hm = messages(en), messages(he)
    if len(em) != len(hm):
        errs.append(("E-msgs", f"{len(em)} != {len(hm)}"))
    wlim, llims = limits(en)
    for mi, m in enumerate(hm):
        lim = llims[mi] if mi < len(llims) else 3
        if len(m) > lim:
            errs.append(("E-lines", f"message {mi + 1}: {len(m)} lines > {lim}"))
        for l in m:
            u = line_units(l)
            if u > wlim:
                txt = "".join(c if isinstance(c, str) else "\\[" + c[1] + "]" for c in l)
                errs.append(("E-width", f"{u:.1f} > {wlim:.1f}: '{txt}'"))
    bad_chars = sorted(set(c for c in he if ord(c) > 126 and not ("א" <= c <= "ת") and c not in en))
    if bad_chars:
        errs.append(("E-glyph", f"no glyph in the game fonts for {bad_chars}"))
    plain = re.sub(r"\\\[.\]|\\[MEFSTz*>].|\\.|\^.", "", he)
    if re.search(r"[A-Za-z]", re.sub(r"\\\[.\]|\\[MEFSTz*>].|\\.|\^.", "", en)) and not re.search("[\u05d0-\u05ea]", plain):
        errs.append(("W-nohebrew", he))
    for w in re.findall(r"[A-Za-z]{2,}", plain):
        if w not in LATIN_OK and w.upper() not in LATIN_OK:
            errs.append(("W-latin", w))
            break
    return errs


def report(results, show=60):
    from collections import Counter
    c = Counter(k for _, errs in results for k, _ in errs)
    shown = 0
    for i, errs in results:
        for k, msg in errs:
            if shown < show:
                print(f"{k:11} {i}: {msg}")
                shown += 1
    print("SUMMARY", dict(c))
    return sum(v for k, v in c.items() if k.startswith("E-"))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 2
    results = []
    if args[0] == "--all":
        he = {}
        for f in sorted(glob.glob(os.path.join(W, "translation", "he", "*.json"))):
            if "_part" not in os.path.basename(f):
                he.update(json.load(open(f, encoding="utf-8")))
        for i in he:
            if i not in EN:
                results.append((i, [("E-unknown", "")]))
        missing = [i for i in EN if i not in he]
        for i in EN:
            if i in he:
                e = check_one(i, EN[i]["en"], he[i])
                if e:
                    results.append((i, e))
        n_err = report(results, show=int(args[1]) if len(args) > 1 else 60)
        print(f"COVERAGE {len(EN) - len(missing)}/{len(EN)} translated, {len(missing)} missing")
        if missing:
            print("first missing:", missing[:10])
        ok = n_err == 0 and not missing
        print("CHECK PASS" if ok else "CHECK FAIL")
        return 0 if ok else 1
    path = args[0]
    he = json.load(open(path, encoding="utf-8"))
    inp = path.replace(os.sep + "he" + os.sep, os.sep + "batches" + os.sep).replace(".json", "_in.json")
    want = None
    if os.path.exists(inp):
        want = [x["id"] for x in json.load(open(inp, encoding="utf-8"))]
    for i, v in he.items():
        if i not in EN:
            results.append((i, [("E-unknown", "")]))
        else:
            e = check_one(i, EN[i]["en"], v)
            if e:
                results.append((i, e))
    if want:
        for i in want:
            if i not in he:
                results.append((i, [("E-missing", "")]))
    n_err = report(results, show=200)
    print("BATCH PASS" if n_err == 0 else "BATCH FAIL")
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
