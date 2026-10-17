#!/bin/sh
# Gathers what ships into stage/, after asciiverse/build.sh: the program,
# the read-only game data it needs (lib/gamedata, customize, help and
# screens, without their build files) and the licence. No tiles, fonts,
# sounds or icons: this build is curses only. The av archive is stage/
# as it is; nfpm.yaml installs the same files in /usr.
set -eu
rm -rf stage
mkdir -p stage/lib
cp angband stage/
for d in gamedata customize help screens; do
  cp -R "lib/$d" stage/lib/
done
# drop the build files (Makefile, and .deps from configure)
find stage/lib -type f \( -name Makefile -o -name '.*' \) -exec rm {} +
cp docs/copying.rst asciiverse/GPL-2 stage/
