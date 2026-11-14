// Logical-order single line -> visual order for left-to-right drawing APIs.
var s = argument0;
var n = string_length(s);
var cls, i, j, k, hasr, outs;
hasr = 0;
for (i = 1; i <= n; i += 1)
{
    cls[i] = scr_rtl_cls(ord(string_char_at(s, i)));
    if (cls[i] == 1)
    {
        hasr = 1;
    }
}
if (hasr == 0)
{
    return s;
}
i = 1;
while (i <= n)
{
    if (cls[i] == 0)
    {
        j = i;
        while (j <= n && cls[j] == 0)
        {
            j += 1;
        }
        if (i > 1 && j <= n)
        {
            if (cls[i - 1] == 2 && cls[j] == 2)
            {
                for (k = i; k < j; k += 1)
                {
                    cls[k] = 2;
                }
            }
        }
        i = j;
    }
    else
    {
        i += 1;
    }
}
outs = "";
i = n;
while (i >= 1)
{
    if (cls[i] == 2)
    {
        j = i;
        while (j > 1 && cls[j - 1] == 2)
        {
            j -= 1;
        }
        outs += string_copy(s, j, (i - j) + 1);
        i = j - 1;
    }
    else
    {
        outs += scr_rtl_mirror(string_char_at(s, i));
        i -= 1;
    }
}
return outs;
