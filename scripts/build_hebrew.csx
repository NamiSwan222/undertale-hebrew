// Undertale Hebrew build: run with UndertaleModCli load <original data.win> -s build_hebrew.csx -o <out data.win>
// Env: UTHE_ROOT = workspace root (Windows path)
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UndertaleModLib.Util;
using UndertaleModLib.Models;
using ImageMagick;

EnsureDataLoaded();
string root = Environment.GetEnvironmentVariable("UTHE_ROOT");
string fontDir = Path.Combine(root, "fonts", "build");
string rtlDir = Path.Combine(root, "scripts", "gml");
string genDir = Path.Combine(root, "build", "gml");

// ---------- 1. fonts ----------
foreach (string csv in Directory.GetFiles(fontDir, "glyphs_*.csv"))
{
    string name = Path.GetFileNameWithoutExtension(csv).Substring("glyphs_".Length);
    UndertaleFont font = Data.Fonts.ByName(name);
    if (font == null) throw new Exception("font missing: " + name);
    byte[] png = File.ReadAllBytes(Path.Combine(fontDir, name + ".png"));
    var tex = new UndertaleEmbeddedTexture();
    tex.Name = new UndertaleString("Texture " + Data.EmbeddedTextures.Count);
    tex.TextureData.Image = GMImage.FromPng(png);
    Data.EmbeddedTextures.Add(tex);
    int w = tex.TextureData.Image.Width, h = tex.TextureData.Image.Height;
    var tpi = new UndertaleTexturePageItem();
    tpi.Name = new UndertaleString("PageItem " + Data.TexturePageItems.Count);
    tpi.SourceX = 0; tpi.SourceY = 0; tpi.SourceWidth = (ushort)w; tpi.SourceHeight = (ushort)h;
    tpi.TargetX = 0; tpi.TargetY = 0; tpi.TargetWidth = (ushort)w; tpi.TargetHeight = (ushort)h;
    tpi.BoundingWidth = (ushort)w; tpi.BoundingHeight = (ushort)h;
    tpi.TexturePage = tex;
    Data.TexturePageItems.Add(tpi);
    font.Texture = tpi;
    var lines = File.ReadAllLines(csv).Skip(1).Where(l => l.Trim().Length > 0).ToList();
    font.Glyphs.Clear();
    uint maxc = 0;
    foreach (var l in lines)
    {
        var s = l.Split(';');
        var g = new UndertaleFont.Glyph()
        {
            Character = ushort.Parse(s[0]),
            SourceX = ushort.Parse(s[1]), SourceY = ushort.Parse(s[2]),
            SourceWidth = ushort.Parse(s[3]), SourceHeight = ushort.Parse(s[4]),
            Shift = short.Parse(s[5]), Offset = short.Parse(s[6]),
        };
        font.Glyphs.Add(g);
        maxc = Math.Max(maxc, g.Character);
    }
    if (font.RangeEnd < maxc) font.RangeEnd = maxc;
    Console.WriteLine($"font {name}: {font.Glyphs.Count} glyphs, page {w}x{h}, range {font.RangeStart}-{font.RangeEnd}");
}

// ---------- 1b. redrawn sprites (Hebrew text) on new texture pages ----------
string pageDir = Path.Combine(root, "build", "sprite_pages");
var pageTex = new Dictionary<int, UndertaleEmbeddedTexture>();
foreach (string pg in Directory.GetFiles(pageDir, "page_*.png"))
{
    int idx = int.Parse(Path.GetFileNameWithoutExtension(pg).Substring(5));
    var t = new UndertaleEmbeddedTexture();
    t.Name = new UndertaleString("Texture " + Data.EmbeddedTextures.Count);
    t.TextureData.Image = GMImage.FromPng(File.ReadAllBytes(pg));
    Data.EmbeddedTextures.Add(t);
    pageTex[idx] = t;
}
var atlas = Newtonsoft.Json.Linq.JArray.Parse(File.ReadAllText(Path.Combine(pageDir, "atlas.json")));
int nspr = 0;
foreach (var e in atlas)
{
    string spName = (string)e["sprite"]; int frame = (int)e["frame"];
    if (spName.StartsWith("BG:"))
    {
        var bg = Data.Backgrounds.ByName(spName.Substring(3));
        if (bg == null) throw new Exception("background missing: " + spName);
        int bw = (int)e["w"], bh = (int)e["h"];
        var ot = bg.Texture;
        var btp = new UndertaleTexturePageItem();
        btp.Name = new UndertaleString("PageItem " + Data.TexturePageItems.Count);
        btp.SourceX = (ushort)(int)e["x"]; btp.SourceY = (ushort)(int)e["y"];
        btp.SourceWidth = (ushort)bw; btp.SourceHeight = (ushort)bh;
        if (bw == ot.BoundingWidth && bh == ot.BoundingHeight)
        {
            btp.TargetX = 0; btp.TargetY = 0; btp.TargetWidth = (ushort)bw; btp.TargetHeight = (ushort)bh;
        }
        else if (bw == ot.SourceWidth && bh == ot.SourceHeight)
        {   // exported trimmed: keep the original placement inside the bounding box
            btp.TargetX = ot.TargetX; btp.TargetY = ot.TargetY; btp.TargetWidth = ot.TargetWidth; btp.TargetHeight = ot.TargetHeight;
        }
        else throw new Exception($"size mismatch {spName}: {bw}x{bh} vs {ot.BoundingWidth}x{ot.BoundingHeight} / src {ot.SourceWidth}x{ot.SourceHeight}");
        btp.BoundingWidth = ot.BoundingWidth; btp.BoundingHeight = ot.BoundingHeight;
        btp.TexturePage = pageTex[(int)e["page"]];
        Data.TexturePageItems.Add(btp);
        bg.Texture = btp;
        nspr++;
        continue;
    }
    var sp = Data.Sprites.ByName(spName);
    if (sp == null) throw new Exception("sprite missing: " + spName);
    if (frame >= sp.Textures.Count) throw new Exception($"frame {frame} out of range for {spName}");
    int w = (int)e["w"], h = (int)e["h"];
    if (w != sp.Width || h != sp.Height) throw new Exception($"size mismatch {spName}: {w}x{h} vs {sp.Width}x{sp.Height}");
    var tpi = new UndertaleTexturePageItem();
    tpi.Name = new UndertaleString("PageItem " + Data.TexturePageItems.Count);
    tpi.SourceX = (ushort)(int)e["x"]; tpi.SourceY = (ushort)(int)e["y"];
    tpi.SourceWidth = (ushort)w; tpi.SourceHeight = (ushort)h;
    tpi.TargetX = 0; tpi.TargetY = 0; tpi.TargetWidth = (ushort)w; tpi.TargetHeight = (ushort)h;
    tpi.BoundingWidth = (ushort)w; tpi.BoundingHeight = (ushort)h;
    tpi.TexturePage = pageTex[(int)e["page"]];
    Data.TexturePageItems.Add(tpi);
    sp.Textures[frame].Texture = tpi;
    nspr++;
}
Console.WriteLine("sprite frames replaced: " + nspr);

// ---------- 2. route text drawing through RTL wrappers ----------
var renames = new Dictionary<string, string> {
    {"draw_text", "scr_rtl_dt"},
    {"draw_text_transformed", "scr_rtl_dtt"},
    {"draw_text_ext", "scr_rtl_dte"},
    {"draw_text_transformed_color", "scr_rtl_dttc"},
    {"draw_set_halign", "scr_rtl_halign"},
};
foreach (var kv in renames)
{
    var f = Data.Functions.ByName(kv.Key);
    if (f == null) throw new Exception("function missing: " + kv.Key);
    f.Name = Data.Strings.MakeString(kv.Value);
}

// ---------- 3. code ----------
UndertaleModLib.Compiler.CodeImportGroup importGroup = new(Data);
foreach (string f in Directory.GetFiles(rtlDir, "*.gml"))
    importGroup.QueueReplace("gml_Script_" + Path.GetFileNameWithoutExtension(f), File.ReadAllText(f));
foreach (string f in Directory.GetFiles(genDir, "*.gml"))
    importGroup.QueueReplace(Path.GetFileNameWithoutExtension(f), File.ReadAllText(f));
importGroup.Import();

// ---------- 4. sanity: wrappers must call the real builtins, not themselves ----------
foreach (var kv in renames)
{
    var real = Data.Functions.ByName(kv.Key);
    var wrap = Data.Functions.ByName(kv.Value);
    Console.WriteLine($"func {kv.Key}: real={(real != null)} wrapper={(wrap != null)} same={(real == wrap)}");
    if (real == null || wrap == null || real == wrap) throw new Exception("function routing broken for " + kv.Key);
}
foreach (var kv in renames)
{
    var code = Data.Code.ByName("gml_Script_" + kv.Value);
    var called = code.Instructions.Where(i => i.Kind == UndertaleInstruction.Opcode.Call).Select(i => i.ValueFunction.Name.Content).ToArray();
    Console.WriteLine($"{code.Name.Content} calls: {string.Join(",", called)}");
    if (called.Contains(kv.Value)) throw new Exception("wrapper recursion: " + kv.Value);
}
Console.WriteLine("HEBREW BUILD OK");
