#!/usr/bin/env python3
"""Records asciiverse/angband.cast, Angband's catalog preview, at 100x30
(hub/RECORDING.md). A Warrior called Ada is made at the birth screens,
looks into the General Store, takes the stairs down from the town and
explores the first levels: it walks to the nearest unexplored edge,
fights what is next to it, picks things up and takes stairs down it
comes across. Several takes are made and the liveliest one is kept.

Usage, from the repo root after asciiverse/build.sh and
asciiverse/stage.sh, with pyte installed:
    python3 asciiverse/record-preview.py

The game runs by name from a copy of stage/ on PATH, with a throwaway
home folder, so the cast holds no local path or login name."""
import fcntl, json, os, pty, random, select, shutil, struct, sys, tempfile, termios, time
from collections import deque

import pyte

# ncurses repeats a character with REP (CSI n b), which pyte does not
# know; without this a run of wall would read as a single cell
_draw = pyte.Screen.draw


def _draw_remembering(self, data):
    if data:
        self.last_char = data[-1]
    _draw(self, data)


def _repeat_last(self, n=1, *rest, **kw):
    if getattr(self, "last_char", None):
        _draw(self, self.last_char * max(1, n))


pyte.Screen.draw = _draw_remembering
pyte.Screen.repeat_last = _repeat_last
pyte.Stream.csi = dict(pyte.Stream.csi, b="repeat_last")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAST = os.path.join(ROOT, "asciiverse", "angband.cast")
COLS, ROWS = 100, 30
# the map starts after the 13-column sidebar, under the message line, and
# ends above the status line
X0, Y0, Y1 = 13, 1, ROWS - 1

# the original keyset's number keys, which need no keypad
DIRS = {(-1, 1): "1", (0, 1): "2", (1, 1): "3", (-1, 0): "4",
        (1, 0): "6", (-1, -1): "7", (0, -1): "8", (1, -1): "9"}
FLOOR = set("·.'<>:")
ITEMS = set("!?_-=\"$~|/\\()[]{},&")
DOORS = set("+")
WALLS = set("#%*")


class Game:
    def __init__(self, stage, home):
        env = {"PATH": f"{stage}:/usr/bin:/bin", "HOME": home, "USER": "player",
               "LOGNAME": "player", "TERM": "xterm-256color", "COLORTERM": "truecolor",
               "LANG": "C.UTF-8"}
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(home)
            os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q",
                "--idle-time-limit", "2", "--window-size", f"{COLS}x{ROWS}",
                "--capture-env", "TERM,COLORTERM,LANG", "--title", "Angband",
                "--command", "angband -uAda", CAST], env)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        self.start = time.time()

    def pump(self, t):
        end = time.time() + t
        while True:
            left = end - time.time()
            r, _, _ = select.select([self.fd], [], [], max(0.0, min(0.02, left)))
            if r:
                try:
                    data = os.read(self.fd, 65536)
                except OSError:
                    return False
                if not data:
                    return False
                self.stream.feed(data)
            if left <= 0:
                return True

    def key(self, k, wait=0.2):
        os.write(self.fd, k.encode() if isinstance(k, str) else k)
        return self.pump(wait)

    def text(self):
        return "\n".join(self.screen.display)

    def wait_for(self, s, timeout=6.0):
        end = time.time() + timeout
        while time.time() < end:
            if s in self.text():
                return True
            self.pump(0.05)
        return False

    def elapsed(self):
        return time.time() - self.start

    def grid(self):
        return [row[X0:] for row in self.screen.display[Y0:Y1]]

    def finish(self):
        end = time.time() + 6
        while time.time() < end:
            if not self.pump(0.1):
                break
            if os.waitpid(self.pid, os.WNOHANG)[0]:
                break
        else:
            print("game did not exit; stopping the recording", file=sys.stderr)
            os.kill(self.pid, 15)
        try:
            os.waitpid(self.pid, 0)
        except ChildProcessError:
            pass


def find(grid, chars):
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch in chars:
                return (x, y)
    return None


def is_monster(ch):
    return ch.isalpha() and ch.isascii()


def bfs(grid, me, want, passable):
    """First step from me toward the nearest cell want() likes."""
    h, w = len(grid), len(grid[0])
    seen = {me: None}
    q = deque([me])
    while q:
        cur = q.popleft()
        if cur != me and want(cur):
            while seen[cur] != me:
                cur = seen[cur]
            return (cur[0] - me[0], cur[1] - me[1])
        for (dx, dy) in DIRS:
            x, y = cur[0] + dx, cur[1] + dy
            if 0 <= y < h and 0 <= x < w and (x, y) not in seen and \
                    (passable(grid[y][x]) or want((x, y))):
                seen[(x, y)] = cur
                q.append((x, y))
    return None


def take(stage):
    home = tempfile.mkdtemp(prefix="angband-rec-")
    g = Game(stage, home)
    g.wait_for("Press any key", 8)
    g.pump(1.2)
    g.key("\r", 1.0)
    # birth: Human, Warrior, point-based stats, the name from -u, accept
    for k, wait in (("a", 0.6), ("a", 0.6), ("a", 0.8), ("\r", 0.8), ("\r", 0.6),
                    ("y", 0.6), (" ", 1.0)):
        g.key(k, wait)
    g.wait_for("Town", 3)
    g.pump(1.0)

    phase = "store"          # then "stairs", then "dungeon"
    visited = set()
    depth = 0
    stuck = 0
    last = None
    while g.elapsed() < 55:
        t = g.text()
        top = g.screen.display[0]
        if "-more-" in top:
            g.key("\x1b", 0.15)
            continue
        if "[y/n]" in t or "(y/n)" in t:
            g.key("n", 0.2)
            continue
        if phase == "store" and ("Purchase" in t or "General Store" in t or "(Store" in t):
            g.pump(2.0)
            g.key("\x1b", 0.6)
            phase = "stairs"
            continue
        grid = g.grid()
        me = find(grid, "@")
        if me is None:
            g.key("\x1b", 0.3)
            continue
        visited.add((depth, me))
        here = g.screen.display[ROWS - 1]

        # adjacent monster: fight it
        target = None
        for (dx, dy) in DIRS:
            x, y = me[0] + dx, me[1] + dy
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]) and is_monster(grid[y][x]):
                target = (dx, dy)
                break
        if target:
            g.key(DIRS[target], 0.25)
            continue

        if "staircase" in here and "Down" in here and phase != "store" and \
                (phase == "stairs" or g.elapsed() > 22 + 12 * depth):
            g.key(">", 1.2)
            depth += 1
            phase = "dungeon"
            visited.clear()
            continue
        if "You see" in top and phase == "dungeon":
            g.key("g", 0.35)
            continue

        def passable(ch):
            return ch in FLOOR or ch in DOORS or ch in ITEMS or is_monster(ch) or \
                ch.isdigit()

        def want(c):
            ch = grid[c[1]][c[0]]
            if phase == "store":
                return ch == "1"
            if phase == "stairs":
                return ch == ">"
            if ch in ITEMS:
                return True
            if ch == ">" and g.elapsed() > 22 + 12 * depth:
                return True
            if (depth, c) in visited or ch not in FLOOR and ch not in DOORS:
                return False
            for (dx, dy) in DIRS:
                x, y = c[0] + dx, c[1] + dy
                if 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] == " ":
                    return True
            return False

        step = bfs(grid, me, want, passable)
        if step is None or stuck >= 3:
            step = random.choice(list(DIRS))
            stuck = 0
        nx, ny = me[0] + step[0], me[1] + step[1]
        if grid[ny][nx] in DOORS:
            g.key("o", 0.1)        # open it; with one door near, no direction is asked
            if "Direction" in g.screen.display[0]:
                g.key(DIRS[step], 0.3)
            else:
                g.pump(0.2)
            continue
        g.key(DIRS[step], 0.15 if phase != "dungeon" else 0.12)
        now = g.grid()
        stuck = stuck + 1 if now == last else 0
        last = now

    # save and quit: Ctrl-X saves, then the score list, then out
    g.key("\x18", 1.5)
    g.key("\r", 2.5)
    g.key("\x1b", 0.5)
    g.finish()
    shutil.rmtree(home, ignore_errors=True)


def score(cast):
    """How good a take is to watch: it must last 30 seconds; fights,
    kills and levels gone down count."""
    lines = open(cast).read().splitlines()
    idle = json.loads(lines[0]).get("idle_time_limit") or 2
    events = [json.loads(l) for l in lines[1:]]
    length = sum(min(e[0], idle) for e in events)
    if length < 30 or length > 60:
        return -1
    text = "".join(e[2] for e in events if e[1] == "o")
    if "You die" in text or "Killed by" in text and "nobody" not in text:
        return -1
    return (text.count("You hit") + 4 * text.count("You have slain")
            + 4 * text.count("You have killed") + 6 * text.count("You enter a maze")
            + 3 * text.count("You have no more") + text.count("You have "))


def main():
    src = os.path.join(ROOT, "stage")
    if not os.path.exists(os.path.join(src, "angband")):
        sys.exit("run asciiverse/build.sh and asciiverse/stage.sh first")
    stage = tempfile.mkdtemp(prefix="angband-stage-")
    shutil.copytree(src, stage, dirs_exist_ok=True)
    best = None
    for attempt in range(int(os.environ.get("TAKES", "5"))):
        take(stage)
        sc = score(CAST)
        print(f"take {attempt + 1}: score {sc}", file=sys.stderr)
        if best is None or sc > best[0]:
            best = (sc, open(CAST).read())
    with open(CAST, "w") as f:
        f.write(best[1])
    shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    main()
