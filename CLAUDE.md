# Angband (Asciiverse packaging)

Angband, the Tolkien-themed roguelike (1990 on, now the Angband Dev Team),
packaged for the Asciiverse catalog and as system packages, curses build
only. Not our code: keep changes small and list every one in PATCHES.md.

- Remotes: `upstream` is github.com/angband/angband, `origin` is
  github.com/theasciiverse/angband.
- Branch `asciiverse` = upstream tag `4.2.6` plus our commits. Never push
  `master`: upstream's own workflows run on it.
- Release: tag `v4.2.6-av.<n>` and push it (`.github/workflows/release.yml`).
- Local static build: `docker run --rm -v "$PWD":/src -w /src alpine:3.22
  sh asciiverse/build.sh`, then `sh asciiverse/stage.sh` (files come out
  root-owned from Docker; chown them).
- Data: read-only `lib/` beside the binary or `/usr/share/angband`;
  player files in `$XDG_DATA_HOME/angband` (`src/main.c`, `src/init.c`).
- The Shockbolt tiles are non-free and removed; never ship tiles.
- Preview: `python3 asciiverse/record-preview.py` after build and stage
  (needs pyte).
