// draw_text_ext replacement: wrap in logical order, then draw each line visually (right-aligned).
var xx = argument0;
var yy = argument1;
var s = argument2;
var sep = argument3;
var w = argument4;
if (scr_rtl_hasheb(s) == 0)
{
    draw_text_ext(xx, yy, s, sep, w);
    exit;
}
if (sep < 0)
{
    sep = string_height("M");
}
var lines, nl, cur, word, rest, p, c, i, n;
nl = 0;
cur = "";
word = "";
n = string_length(s);
for (i = 1; i <= (n + 1); i += 1)
{
    if (i <= n)
    {
        c = string_char_at(s, i);
    }
    else
    {
        c = "#";
    }
    if (c == " " || c == "#")
    {
        if (cur != "" && string_width(cur + " " + word) > w)
        {
            lines[nl] = cur;
            nl += 1;
            cur = word;
        }
        else if (cur == "")
        {
            cur = word;
        }
        else
        {
            cur += (" " + word);
        }
        word = "";
        if (c == "#")
        {
            lines[nl] = cur;
            nl += 1;
            cur = "";
        }
    }
    else
    {
        word += c;
    }
}
var maxw = 0;
for (i = 0; i < nl; i += 1)
{
    lines[i] = scr_rtl_visual(lines[i]);
    maxw = max(maxw, string_width(lines[i]));
}
for (i = 0; i < nl; i += 1)
{
    draw_text((xx + maxw) - string_width(lines[i]), yy + (i * sep), lines[i]);
}
