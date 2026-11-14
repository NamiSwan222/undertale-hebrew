// Lab variant: separate save folder name + lab driver. Run on build/data.win -> build/lab/data.win
using System;
using System.IO;
EnsureDataLoaded();
string root = Environment.GetEnvironmentVariable("UTHE_ROOT");
Data.GeneralInfo.Name = Data.Strings.MakeString("UNDERTALE_HEBLAB");
Data.GeneralInfo.FileName = Data.Strings.MakeString("UNDERTALE_HEBLAB");
UndertaleModLib.Compiler.CodeImportGroup g = new(Data);
g.QueueReplace("gml_Script_scr_lab_tick", File.ReadAllText(Path.Combine(root, "scripts", "lab", "scr_lab_tick.gml")));
g.QueueReplace("gml_Script_scr_lab_log", File.ReadAllText(Path.Combine(root, "scripts", "lab", "scr_lab_log.gml")));
g.QueueReplace("gml_Script_scr_lab_draw", File.ReadAllText(Path.Combine(root, "scripts", "lab", "scr_lab_draw.gml")));
g.QueueAppend("gml_Object_obj_time_Step_1", "\nscr_lab_tick();\n");
g.QueueAppend("gml_Object_obj_time_Draw_77", "\nscr_lab_draw();\n");
g.Import();
Console.WriteLine("LAB BUILD OK");
