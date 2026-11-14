if (variable_global_exists("lab_shot"))
{
    if (global.lab_shot != "")
    {
        surface_save(application_surface, global.lab_shot + ".png");
        scr_lab_log("shot " + global.lab_shot);
        global.lab_shot = "";
    }
}
