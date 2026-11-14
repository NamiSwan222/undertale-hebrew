#!/bin/bash
# Full build: fonts -> gml -> patched data.win in build/data.win
set -e
W="$(cd "$(dirname "$0")/.." && pwd)"
python "$W/scripts/build_fonts.py"
python "$W/scripts/build_buttons.py"
python "$W/scripts/pack_sprites.py"
python "$W/scripts/make_gml.py"
cd "$W/tools/utmt"
UTHE_ROOT="$(cygpath -w "$W")" ./UndertaleModCli.exe load "$(cygpath -w "$W/backup/data.win.orig")" \
  -s "$(cygpath -w "$W/scripts/build_hebrew.csx")" -o "$(cygpath -w "$W/build/data.win")" -f < /dev/null 2>&1 | tee "$W/build/build.log" | grep -vE "^\[MESSAGE\]" | tail -30
grep -q "HEBREW BUILD OK" "$W/build/build.log"
ls -la "$W/build/data.win"
