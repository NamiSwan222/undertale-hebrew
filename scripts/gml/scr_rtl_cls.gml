// 1 = RTL (Hebrew), 2 = LTR strong (Latin letters / digits), 0 = neutral
var o = argument0;
if (o >= 1424 && o <= 1535)
{
    return 1;
}
if ((o >= 48 && o <= 57) || (o >= 65 && o <= 90) || (o >= 97 && o <= 122) || (o >= 192 && o < 1424) || (o >= 12288))
{
    return 2;
}
return 0;
