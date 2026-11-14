"""Split strings_en.json into translation batches (~TARGET strings, split at object-prefix boundaries)."""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_batch import limits, is_face
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = 420
d = json.load(open(os.path.join(W, "translation", "strings_en.json"), encoding="utf-8"))
def prefix(i):
    p = i.rsplit("_", 1)
    return p[0] if len(p) == 2 and p[1].isdigit() else re.sub(r"_?\d+[a-z]?$", "", i)
out = os.path.join(W, "translation", "batches"); os.makedirs(out, exist_ok=True)
batches, cur = [], []
for k, x in enumerate(d):
    if len(cur) >= TARGET and prefix(x["id"]) != prefix(cur[-1]["id"]):
        batches.append(cur); cur = []
    if len(cur) >= TARGET * 1.6:  # very long single group
        batches.append(cur); cur = []
    wlim, _ = limits(x["en"])
    cur.append({"id": x["id"], "en": x["en"], "max": round(wlim, 2), "face": is_face(x["en"]),
                "where": [r.replace("gml_Object_", "").replace("gml_Script_", "") for r in x["refs"][:3]]})
batches.append(cur)
for n, b in enumerate(batches, 1):
    json.dump(b, open(os.path.join(out, f"b{n:02d}_in.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"b{n:02d}: {len(b):4d} strings, {sum(len(x['en']) for x in b):6d} chars, {b[0]['id']} .. {b[-1]['id']}")
