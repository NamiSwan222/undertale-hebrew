// Lab driver (lab build only). Reads lab_script.txt from the game folder; one command per line:
//   wait N | press KEY | hold KEY N | shot NAME | msg ID [ID...] | room NAME | typer N | quit
if (!variable_global_exists("lab_init"))
{
    global.lab_init = 1;
    global.lab_n = 0;
    global.lab_pc = 0;
    global.lab_wait = 0;
    global.lab_release = -1;
    global.lab_holdkey = -1;
    global.lab_holdn = 0;
    global.lab_shot = "";
    var f = file_text_open_read(program_directory + "\lab_script.txt");
    if (f == -1)
    {
        f = file_text_open_read("lab_script.txt");
    }
    if (f != -1)
    {
        while (!file_text_eof(f))
        {
            var ln = file_text_read_string(f);
            file_text_readln(f);
            if (string_length(ln) > 0)
            {
                global.lab_cmd[global.lab_n] = ln;
                global.lab_n += 1;
            }
        }
        file_text_close(f);
    }
    scr_lab_log("lab start, commands=" + string(global.lab_n));
}
if (global.lab_release >= 0)
{
    keyboard_key_release(global.lab_release);
    global.lab_release = -1;
}
if (global.lab_holdn > 0)
{
    keyboard_key_press(global.lab_holdkey);
    global.lab_holdn -= 1;
    if (global.lab_holdn == 0)
    {
        global.lab_release = global.lab_holdkey;
    }
    exit;
}
if (variable_global_exists("lab_until"))
{
    if (global.lab_until != "")
    {
        if (room_get_name(room) == global.lab_until || global.lab_untiln > 240)
        {
            global.lab_until = "";
        }
        else
        {
            global.lab_untilt += 1;
            if (global.lab_untilt >= 15)
            {
                global.lab_untilt = 0;
                global.lab_untiln += 1;
                keyboard_key_press(global.lab_untilk);
                global.lab_release = global.lab_untilk;
            }
            exit;
        }
    }
}
if (global.lab_wait > 0)
{
    global.lab_wait -= 1;
    exit;
}
if (global.lab_pc >= global.lab_n)
{
    exit;
}
var c = global.lab_cmd[global.lab_pc];
global.lab_pc += 1;
scr_lab_log(string(current_time) + " room=" + room_get_name(room) + " cmd=" + c);
var sp = string_pos(" ", c);
var op = c;
var arg = "";
if (sp > 0)
{
    op = string_copy(c, 1, sp - 1);
    arg = string_delete(c, 1, sp);
}
if (op == "wait")
{
    global.lab_wait = real(arg);
}
else if (op == "press" || op == "hold")
{
    var nm = arg;
    var cnt = 1;
    var sp2 = string_pos(" ", arg);
    if (sp2 > 0)
    {
        nm = string_copy(arg, 1, sp2 - 1);
        cnt = real(string_delete(arg, 1, sp2));
    }
    var k = ord(string_upper(nm));
    if (nm == "up") k = vk_up;
    if (nm == "down") k = vk_down;
    if (nm == "left") k = vk_left;
    if (nm == "right") k = vk_right;
    if (nm == "enter") k = vk_enter;
    if (nm == "shift") k = vk_shift;
    if (nm == "esc") k = vk_escape;
    keyboard_key_press(k);
    if (op == "hold")
    {
        global.lab_holdkey = k;
        global.lab_holdn = cnt;
    }
    else
    {
        global.lab_release = k;
    }
}
else if (op == "until")
{
    var sp3 = string_pos(" ", arg);
    global.lab_until = string_copy(arg, 1, sp3 - 1);
    global.lab_untilk = ord(string_upper(string_delete(arg, 1, sp3)));
    global.lab_untilt = 0;
    global.lab_untiln = 0;
}
else if (op == "shot")
{
    global.lab_shot = arg;
}
else if (op == "room")
{
    room_goto(asset_get_index(arg));
}
else if (op == "typer")
{
    global.typer = real(arg);
}
else if (op == "msg")
{
    var i = 0;
    var rest = arg + " ";
    var p = string_pos(" ", rest);
    while (p > 0)
    {
        var id_ = string_copy(rest, 1, p - 1);
        if (id_ != "")
        {
            global.msg[i] = scr_gettext(id_);
            i += 1;
        }
        rest = string_delete(rest, 1, p);
        p = string_pos(" ", rest);
    }
    if (i > 0)
    {
        var last = global.msg[i - 1];
        if (string_copy(last, string_length(last) - 1, 2) != "%%")
        {
            if (string_char_at(last, string_length(last)) == "/")
            {
                global.msg[i - 1] = last + "%%";
            }
            else
            {
                global.msg[i - 1] = last + "/%%";
            }
        }
    }
    global.msg[i] = "%%%";
    global.msc = 0;
    instance_create(0, 0, obj_dialoguer);
}
else if (op == "msc")
{
    global.msc = real(arg);
    global.facechoice = 0;
    global.faceemotion = 0;
    instance_create(0, 0, obj_dialoguer);
}
else if (op == "savemenu")
{
    global.interact = 5;
    global.menuno = 4;
    global.menucoord[4] = 0;
}
else if (op == "battle")
{
    global.battlegroup = real(arg);
    instance_create(0, 0, obj_battleblcon);
}
else if (op == "create")
{
    var oi = asset_get_index(arg);
    if (oi >= 0)
    {
        instance_create(0, 0, oi);
    }
}
else if (op == "gold")
{
    global.gold = real(arg);
}
else if (op == "item")
{
    scr_itemget(real(arg));
}
else if (op == "quit")
{
    game_end();
}
