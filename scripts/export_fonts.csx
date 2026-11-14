using System.IO;
using System.Linq;
using UndertaleModLib.Util;
EnsureDataLoaded();
string outDir = Environment.GetEnvironmentVariable("UTHE_OUT");
using (TextureWorker worker = new())
{
    foreach (var font in Data.Fonts)
    {
        worker.ExportAsPNG(font.Texture, Path.Combine(outDir, $"{font.Name.Content}.png"));
        using StreamWriter w = new(Path.Combine(outDir, $"glyphs_{font.Name.Content}.csv"));
        w.WriteLine($"{font.DisplayName.Content};{font.EmSize};{font.Bold};{font.Italic};{font.Charset};{font.AntiAliasing};{font.ScaleX};{font.ScaleY};{font.RangeStart};{font.RangeEnd}");
        foreach (var g in font.Glyphs)
            w.WriteLine($"{g.Character};{g.SourceX};{g.SourceY};{g.SourceWidth};{g.SourceHeight};{g.Shift};{g.Offset}");
    }
}
