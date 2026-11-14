#!/bin/bash
# lab variant of build/data.win -> build/lab/data.win
W="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$W/build/lab"; cd "$W/tools/utmt"
UTHE_ROOT="$(cygpath -w "$W")" ./UndertaleModCli.exe load "$(cygpath -w "$W/build/data.win")" -s "$(cygpath -w "$W/scripts/build_lab.csx")" -o "$(cygpath -w "$W/build/lab/data.win")" -f < /dev/null 2>&1 | grep -vE "^\[MESSAGE\]" | tail -5
