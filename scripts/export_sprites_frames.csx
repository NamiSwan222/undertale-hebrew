// Export ALL frames (full size) of the sprites named in UTHE_SPRITES (comma list, exact names) to UTHE_OUT as <name>__<frame>.png
using System.IO;
using System.Linq;
using UndertaleModLib.Util;
EnsureDataLoaded();
string outDir = Environment.GetEnvironmentVariable("UTHE_OUT");
var want = Environment.GetEnvironmentVariable("UTHE_SPRITES").Split(',').Select(s => s.Trim()).ToHashSet();
using (TextureWorker worker = new())
{
    foreach (var sp in Data.Sprites.Where(s => want.Contains(s.Name.Content)))
        for (int i = 0; i < sp.Textures.Count; i++)
            if (sp.Textures[i].Texture != null)
                worker.ExportAsPNG(sp.Textures[i].Texture, Path.Combine(outDir, $"{sp.Name.Content}__{i}.png"), null, true);
}
