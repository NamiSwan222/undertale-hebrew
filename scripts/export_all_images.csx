using System.IO;
using System.Linq;
using UndertaleModLib.Util;
EnsureDataLoaded();
string sprDir = Environment.GetEnvironmentVariable("UTHE_SPR");
string bgDir = Environment.GetEnvironmentVariable("UTHE_BG");
using (TextureWorker worker = new())
{
    foreach (var sp in Data.Sprites)
    {
        if (sp.Textures.Count == 0 || sp.Textures[0].Texture == null) continue;
        int n = Math.Min(sp.Textures.Count, 4);
        for (int i = 0; i < n; i++)
            if (sp.Textures[i].Texture != null)
                worker.ExportAsPNG(sp.Textures[i].Texture, Path.Combine(sprDir, $"{sp.Name.Content}__{i}.png"), null, true);
    }
    foreach (var bg in Data.Backgrounds)
        if (bg.Texture != null) worker.ExportAsPNG(bg.Texture, Path.Combine(bgDir, $"{bg.Name.Content}.png"));
}
Console.WriteLine("EXPORT DONE");
