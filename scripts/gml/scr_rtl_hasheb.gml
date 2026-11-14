var s = argument0;
if (is_real(s))
{
    return 0;
}
var n = string_length(s);
for (var i = 1; i <= n; i += 1)
{
    var o = ord(string_char_at(s, i));
    if (o >= 1424 && o <= 1535)
    {
        return 1;
    }
}
return 0;
