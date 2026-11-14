"""Extract every textdata_en entry with ID, order, context (referencing code, typer/font, room hints)."""
import re, json, os, glob, collections, sys
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CE = os.path.join(W, "extract", "CodeEntries")
LINE = re.compile(r'^ds_map_add\(global\.text_data_en, "([^"]*)", (".*"|\'.*\')\);$')

def gml_eval(expr):
    """Evaluate a GML string expression made of literals joined with +, e.g. 'won' + "'" + 't'."""
    parts = re.findall(r"\"[^\"]*\"|'[^']*'", expr)
    rebuilt = " + ".join(parts)
    if rebuilt != expr:
        raise SystemExit("unexpected string expression: " + expr)
    return "".join(p[1:-1] for p in parts)

def parse_table(path):
    out = []
    for ln in open(path, encoding="utf-8").read().splitlines()[1:]:
        m = LINE.match(ln)
        if not m:
            raise SystemExit("unparsed: " + ln)
        out.append((m.group(1), gml_eval(m.group(2))))
    return out

en = parse_table(os.path.join(CE, "gml_Script_textdata_en.gml"))
ja = dict(parse_table(os.path.join(CE, "gml_Script_textdata_ja.gml").replace("x","x")) if False else [])
# references
refs = collections.defaultdict(list)
typer_ctx = {}
GT = re.compile(r'scr_gettext\("([^"]+)"')
for f in glob.glob(os.path.join(CE, "*.gml")):
    name = os.path.basename(f)[:-4]
    if name.startswith("gml_Script_textdata_"):
        continue
    typer = None
    for ln in open(f, encoding="utf-8", errors="replace"):
        t = re.search(r'global\.typer = (\d+)', ln)
        if t: typer = int(t.group(1))
        for k in GT.findall(ln):
            refs[k].append(name)
            if typer is not None and k not in typer_ctx:
                typer_ctx[k] = typer
            # draw/menu usage hint
items = []
for i, (k, v) in enumerate(en):
    use = "writer"
    items.append({"id": k, "idx": i, "en": v, "refs": sorted(set(refs.get(k, [])))[:6], "typer": typer_ctx.get(k)})
os.makedirs(os.path.join(W, "translation"), exist_ok=True)
json.dump(items, open(os.path.join(W, "translation", "strings_en.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(items), "entries;", sum(1 for x in items if not x["refs"]), "unreferenced")
