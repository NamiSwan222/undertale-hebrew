// Logical -> visual for a whole draw_text string ('#' separated lines). Cached.
var s = argument0;
if (is_real(s))
{
    return s;
}
if (!variable_global_exists("rtl_cache"))
{
    global.rtl_cache = ds_map_create();
}
var v = ds_map_find_value(global.rtl_cache, s);
if (!is_undefined(v))
{
    return v;
}
var r = "";
var rest = s;
var p = string_pos("#", rest);
while (p > 0)
{
    r += scr_rtl_visual(string_copy(rest, 1, p - 1)) + "#";
    rest = string_delete(rest, 1, p);
    p = string_pos("#", rest);
}
r += scr_rtl_visual(rest);
if (ds_map_size(global.rtl_cache) > 3000)
{
    ds_map_clear(global.rtl_cache);
}
ds_map_add(global.rtl_cache, s, r);
return r;
