var f = file_text_open_append("lab_log.txt");
file_text_write_string(f, argument0);
file_text_writeln(f);
file_text_close(f);
