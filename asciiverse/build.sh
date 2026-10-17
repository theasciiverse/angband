#!/bin/sh
# Builds Angband with its curses (GCU) frontend only: no X11, SDL, SDL2,
# sound or tiles. Linux: run inside alpine:3.22 for a fully static binary
# (musl, static ncursesw); macOS: run on the runner, with CC_ARCH set to
# x86_64 or arm64, linking the system ncurses.
#   docker run --rm -v "$PWD":/src -w /src alpine:3.22 sh asciiverse/build.sh
# Leaves the program as ./angband in the repository root. It reads its game
# data from the lib folder beside it when there is one (the av archive),
# else from /usr/share/angband (system packages), and keeps the player's
# files in $XDG_DATA_HOME/angband (PATCHES.md).
set -eu
if [ -f /etc/alpine-release ]; then
  apk add --no-cache build-base autoconf automake ncurses-dev ncurses-static >/dev/null
  ldflags="-static"
  ncurses_config=""
else
  ldflags=""
  # macOS has no ncursesw6-config; this is upstream's own workaround from
  # .github/workflows/mac.yaml: the SDK's ncurses has the wide functions
  ncurses_config="$(mktemp -d)/ncursesw6-config"
  printf '%s\n' '#!/bin/sh' \
    'case "$1" in --cflags) echo "-D_DARWIN_C_SOURCE" ;; --libs) echo "-lncurses" ;; esac' \
    >"$ncurses_config"
  chmod +x "$ncurses_config"
fi
cc="cc${CC_ARCH:+ -arch $CC_ARCH}"
./autogen.sh >/dev/null
# --with-private-dirs: no setgid, nothing shared between users;
# --sysconfdir=/usr/share puts gamedata and customize in /usr/share/angband
# beside help and screens, so the whole read-only lib is one folder
./configure --prefix=/usr --bindir=/usr/bin --sysconfdir=/usr/share \
  --with-private-dirs --enable-release \
  --enable-curses --disable-x11 --disable-sdl --disable-sdl2 \
  --disable-sdl-mixer --disable-sdl2-mixer \
  CC="$cc" LDFLAGS="$ldflags" ${ncurses_config:+NCURSES_CONFIG="$ncurses_config"} >/dev/null
grep -q '#define USE_GCU 1' src/autoconf.h || { echo "curses frontend not found" >&2; exit 1; }
make clean >/dev/null 2>&1 || true
# without git, src/version.h falls back to the release number (4.2.6)
# instead of a git describe string of our own commits
GIT_DIR=/nonexistent make -C src -j"$(getconf _NPROCESSORS_ONLN)" >/dev/null
cp src/angband angband
strip angband
