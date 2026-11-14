// Writer context: horizontal advance for one character when drawing right-to-left.
// Hebrew letters use their glyph width (proportional), everything else the writer's fixed spacing.
var o = ord(argument0);
if (o >= 1488 && o <= 1514)
{
    return round(string_width(argument0) * htextscale) + (spacing - rtl_refw);
}
return spacing;
