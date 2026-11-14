// Writer context. Builds rtl_str (same length/positions as originalstring) for right-to-left drawing:
//  - RTL lines: Latin/digit runs reversed in place, brackets mirrored (writer then draws chars right-to-left).
//  - Choice lines (containing \C): drawn left-to-right; each Hebrew word reversed in place.
// Also sets rtl_w (widest line in px) and rtl_ltr[line].
var s = originalstring;
scr_setfont(myfont);
rtl_refw = round(string_width("ב") * htextscale);
var n = string_length(s);
var cls, res, i, j, k, a, b, ch, c2, line, cnt, maxc, isltr, tmp;
i = 1;
while (i <= n)
{
    ch = string_char_at(s, i);
    res[i] = ch;
    if (ch == "^" && i < n)
    {
        cls[i] = -1;
        cls[i + 1] = -1;
        res[i + 1] = string_char_at(s, i + 1);
        i += 2;
    }
    else if (ch == "\" && i < n)
    {
        c2 = string_char_at(s, i + 1);
        cls[i] = -1;
        cls[i + 1] = -1;
        res[i + 1] = c2;
        i += 2;
        if ((c2 == "M" || c2 == "E" || c2 == "F" || c2 == "S" || c2 == "T" || c2 == "z" || c2 == "*" || c2 == ">") && i <= n)
        {
            cls[i] = -1;
            res[i] = string_char_at(s, i);
            i += 1;
        }
    }
    else if (ch == "&" || ch == "/" || ch == "%")
    {
        cls[i] = -2;
        i += 1;
    }
    else
    {
        cls[i] = scr_rtl_cls(ord(ch));
        i += 1;
    }
}
for (k = 0; k < 40; k += 1)
{
    rtl_ltr[k] = 0;
}
// a message with no Hebrew but with Latin text stays fully left-to-right (untranslated / English-only)
var anyr = 0;
var anyl = 0;
for (k = 1; k <= n; k += 1)
{
    if (cls[k] == 1)
    {
        anyr = 1;
    }
    if (cls[k] == 2)
    {
        anyl = 1;
    }
}
var allltr = 0;
if (anyr == 0 && anyl == 1)
{
    allltr = 1;
}
if (string_pos("\>", s) > 0)
{
    allltr = 1;
}
var sp0 = 1;
while (sp0 <= n && cls[sp0] == -1)
{
    sp0 += 1;
}
var sps = 0;
while (sp0 <= n && string_char_at(s, sp0) == " ")
{
    sp0 += 1;
    sps += 1;
}
if (sps >= 2 && sp0 <= n && string_char_at(s, sp0) == "*")
{
    allltr = 1;
}
// per line
line = 0;
maxc = 0;
a = 1;
while (a <= n)
{
    b = a;
    cnt = 0;
    isltr = 0;
    while (b <= n && !(cls[b] == -2))
    {
        if (cls[b] >= 0)
        {
            cnt += scr_rtl_step(res[b]);
        }
        if (res[b] == "\" && b < n)
        {
            if (string_char_at(s, b + 1) == "C")
            {
                isltr = 1;
            }
        }
        b += 1;
    }
    if (allltr)
    {
        isltr = 1;
    }
    // line is [a, b-1]
    if (line < 40)
    {
        rtl_ltr[line] = isltr;
    }
    maxc = max(maxc, cnt);
    i = a;
    while (i < b)
    {
        if (cls[i] < 0)
        {
            i += 1;
            continue;
        }
        j = i;
        while (j < b && cls[j] >= 0)
        {
            j += 1;
        }
        // text segment [i, j-1]
        if (isltr)
        {
            k = i;
            while (k < j)
            {
                if (cls[k] >= 1)
                {
                    var e = k + 1;
                    var last = k;
                    var hasr = 0;
                    if (cls[k] == 1)
                    {
                        hasr = 1;
                    }
                    while (e < j)
                    {
                        if (cls[e] >= 1)
                        {
                            last = e;
                            if (cls[e] == 1)
                            {
                                hasr = 1;
                            }
                            e += 1;
                        }
                        else if (res[e] == " " && (e + 1) < j && res[e + 1] == " ")
                        {
                            break;
                        }
                        else
                        {
                            e += 1;
                        }
                    }
                    if (hasr)
                    {
                        var sub = "";
                        var q;
                        for (q = k; q <= last; q += 1)
                        {
                            sub += res[q];
                        }
                        sub = scr_rtl_visual(sub);
                        for (q = k; q <= last; q += 1)
                        {
                            res[q] = string_char_at(sub, (q - k) + 1);
                        }
                    }
                    k = last + 1;
                }
                else
                {
                    k += 1;
                }
            }
        }
        else
        {
            // neutrals between two LTR chars join the LTR run
            k = i;
            while (k < j)
            {
                if (cls[k] == 0)
                {
                    var e2 = k;
                    while (e2 < j && cls[e2] == 0)
                    {
                        e2 += 1;
                    }
                    if (k > i && e2 < j)
                    {
                        if (cls[k - 1] == 2 && cls[e2] == 2)
                        {
                            for (var q = k; q < e2; q += 1)
                            {
                                cls[q] = 2;
                            }
                        }
                    }
                    k = e2;
                }
                else
                {
                    k += 1;
                }
            }
            k = i;
            while (k < j)
            {
                if (cls[k] == 2)
                {
                    var e3 = k;
                    while (e3 < j && cls[e3] == 2)
                    {
                        e3 += 1;
                    }
                    var lo2 = k;
                    var hi2 = e3 - 1;
                    while (lo2 < hi2)
                    {
                        tmp = res[lo2];
                        res[lo2] = res[hi2];
                        res[hi2] = tmp;
                        lo2 += 1;
                        hi2 -= 1;
                    }
                    k = e3;
                }
                else
                {
                    res[k] = scr_rtl_mirror(res[k]);
                    k += 1;
                }
            }
        }
        i = j;
    }
    line += 1;
    if (b <= n && (res[b] == "/" || res[b] == "%"))
    {
        break;
    }
    a = b + 1;
}
rtl_w = maxc;
var outs = "";
for (i = 1; i <= n; i += 1)
{
    outs += res[i];
}
rtl_str = outs;
