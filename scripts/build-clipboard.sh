#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p assets
x86_64-w64-mingw32-gcc -std=c11 -O2 -Wall -Wextra -Werror -municode -mwindows -static -s src/clipboard.c -o assets/ibs-clipboard.exe -luser32 -lws2_32
