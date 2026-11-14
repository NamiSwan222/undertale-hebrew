using System.IO;
using System.Linq;
using UndertaleModLib.Util;
EnsureDataLoaded();
string outDir = Environment.GetEnvironmentVariable("UTHE_OUT");
string[] want = Environment.GetEnvironmentVariable("UTHE_SPRITES").Split(',');
using (TextureWorker worker = new())
{
    foreach (var sp in Data.Sprites.Where(s => want.Any(w => s.Name.Content.Contains(w))))
    {
        for (int i = 0; i < sp.Textures.Count; i++)
            worker.ExportAsPNG(sp.Textures[i].Texture, Path.Combine(outDir, $"{sp.Name.Content}_{i}.png"), null, true);
        Console.WriteLine($"{sp.Name.Content} {sp.Width}x{sp.Height} frames={sp.Textures.Count} origin={sp.OriginX},{sp.OriginY}");
    }
}
