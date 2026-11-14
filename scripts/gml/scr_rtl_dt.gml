// Replacement for draw_text: bidi reorder; multi-line Hebrew left-aligned text is right-aligned per line.
var xx = argument0;
var yy = argument1;
var s = argument2;
if (is_real(s))
{
    draw_text(xx, yy, s);
    exit;
}
var v = scr_rtl_str(s);
if (string_pos("#", v) == 0)
{
    draw_text(xx, yy, v);
    exit;
}
var ha = 0;
if (variable_global_exists("rtl_halign"))
{
    ha = global.rtl_halign;
}
if (ha != fa_left || scr_rtl_hasheb(s) == 0)
{
    draw_text(xx, yy, v);
    exit;
}
var maxw = string_width(v);
var lh = string_height("M");
var rest = v;
var p = string_pos("#", rest);
var line;
while (true)
{
    if (p > 0)
    {
        line = string_copy(rest, 1, p - 1);
    }
    else
    {
        line = rest;
    }
    draw_text((xx + maxw) - string_width(line), yy, line);
    if (p <= 0)
    {
        break;
    }
    rest = string_delete(rest, 1, p);
    p = string_pos("#", rest);
    yy += lh;
}
