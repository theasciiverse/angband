# Changes from upstream

This is the Asciiverse packaging of Angband 4.2.6 by the Angband Dev Team
(maintainer Nick McConnell), from [angband/angband](https://github.com/angband/angband)
(the `upstream` remote). Branch `asciiverse` starts at upstream's tag
`4.2.6` (commit `f3082213b`, 2025-12-15) and carries the commits below.

Licence: Angband is under either the GNU GPL version 2 or the "Angband
licence" (non-commercial), at the user's choice (`docs/copying.rst`). The
text says "version 2" with no "or later", so this edition is taken under
GPL-2.0-only. `asciiverse/GPL-2` is the licence text (upstream ships
none), copied from Debian's `/usr/share/common-licenses/GPL-2`.

## Removed

- The Shockbolt tileset (`lib/tiles/shockbolt/`, its entries in
  `lib/tiles/list.txt`, `lib/tiles/Makefile` and `src/Makefile.std`):
  Raymond Gaustadnes' terms forbid modifying it or using it with other
  projects, so it is not free. Debian's `+dfsg` repack drops its
  `64x64.png` for the same reason. It is still in upstream's history,
  which this repository carries. Debian also drops the MP3 sounds and the
  Windows `.fon` fonts; we keep them in the tree but build and ship
  neither.

## Code

- Paths (`src/main.c`, `src/init.c`): on Unix the game reads its data
  (`gamedata`, `customize`, `help`, `screens`) from a `lib` folder beside
  the running program when there is one, found through `/proc/self/exe`
  on Linux and `_NSGetExecutablePath()` on macOS, so av's symbolic link
  in `~/.local/bin` still finds it; otherwise from the configured
  `/usr/share/angband`. The data is only read. The player's folder,
  `~/.angband/Angband` upstream, is `$XDG_DATA_HOME/angband` (else
  `~/.local/share/angband`), holding options, keymaps, character dumps
  and the `save`, `scores`, `panic` and `archive` folders. Upstream's
  `-d<dir>=<path>` options still override any of these.

## Packaging (new files)

- `asciiverse/build.sh`: autotools build of the curses (GCU) frontend
  only (`--enable-curses --disable-x11 --disable-sdl --disable-sdl2`, no
  sound), `--with-private-dirs` (no setgid, no shared score file) and
  `--sysconfdir=/usr/share` so the whole read-only lib is
  `/usr/share/angband`. Fully static in Alpine (musl, static ncursesw);
  on macOS it links the system ncurses through upstream's own
  `NCURSES_CONFIG` workaround from its `mac.yaml`. Git is hidden from
  the build so the version shown is `4.2.6`, not a `git describe` of our
  commits.
- `asciiverse/stage.sh`: puts the program, `lib/{gamedata,customize,help,screens}`
  without the build files (`Makefile`, `.deps`), `docs/copying.rst` and `GPL-2` in `stage/`, the av
  archive's contents. No tiles, fonts, sounds or icons are shipped.
- `asciiverse/nfpm.yaml`: .deb, .rpm, .apk and Arch packages: `/usr/bin/angband`,
  `/usr/share/angband`, the licence in `/usr/share/doc/angband`. No
  `.desktop` file or icon.
- `asciiverse/record-preview.py` and `asciiverse/angband.cast`: the
  catalog preview, a scripted Warrior who visits the General Store and
  explores the first dungeon level (best of several takes).
- `.github/workflows/release.yml`: builds all of it on a tag. Upstream's
  own workflows (`release.yaml` and the rest) run only on pushes to
  `master`, which this repository does not push.

## Not built

- Windows: upstream's Windows edition is its own GUI frontend
  (`main-win.c`). Its CMake build can also make a console GCU binary
  (`WIN32_CONSOLE_MODE`, against MSYS2's mingw-w64 ncurses, as its
  `msys2.yaml` does). A Windows console build for av would take that
  CMake route plus a Windows branch of our path change (lib beside the
  `.exe` through `GetModuleFileName()`, the player's folder under
  `%APPDATA%`), and has not been tried.
- X11, SDL, SDL2, sound, tiles, the stats and test frontends.

## Ours

- **How to play it, at the top of README.md.** A short note on installing and
  starting it with av, or from a release archive; the original text follows
  unchanged.
