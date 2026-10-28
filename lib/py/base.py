# Shared by the suite's MicroPython apps (Home, Projector): helpers, files in parts, the app
# registry, and class UI: the key loop, hint bar, menu bar hook and question screens of
# docs/UI.md. AREA512 MicroPython is built at MINIMUM (no import), so build.sh puts this file
# in front of each app's main.py. Change it with both apps' tests (tests/sim.py --both).

REG = "/data/area512/apps.txt"


def toint(s, d):
    try:
        return int(s)
    except ValueError:
        return d


def cut(s, a, b):
    out = ""
    if b > len(s):
        b = len(s)
    i = a
    while i < b:
        out = out + s[i]
        i = i + 1
    return out


def clean(s):
    return s.replace("|", "/").replace("\n", " ").strip()


def wrap(text, cols):
    lines = []
    cur = ""
    for word in text.split(" "):
        while len(word) > cols:
            if cur != "":
                lines.append(cur)
                cur = ""
            lines.append(cut(word, 0, cols))
            word = cut(word, cols, len(word))
        if cur == "":
            cur = word
        elif len(cur) + 1 + len(word) <= cols:
            cur = cur + " " + word
        else:
            lines.append(cur)
            cur = word
    if cur != "" or len(lines) == 0:
        lines.append(cur)
    return lines


def arrow(k):
    # the bare ; . , / keys have the arrows printed on them: one key, not Fn+key (docs/UI.md)
    if k == ";":
        return "UP"
    if k == ".":
        return "DOWN"
    if k == ",":
        return "LEFT"
    if k == "/":
        return "RIGHT"
    return k


def reg_read():
    # the app registry Home writes: [[digit, name, path], ...]; none without Home
    out = []
    if File.exist(REG):
        for line in read_lines(REG):
            p = line.split("|")
            if len(p) == 3 and len(p[0]) == 1 and p[2] != "":
                out.append(p)
    return out


class Switch(Exception):
    # raised once Area512.run_next is set: every loop unwinds and the app returns
    pass


def heap_total():
    if GC is None:
        return 0
    return GC.mem_free() + GC.mem_alloc()


def free_kb():
    # diagnostic: how many 1 KB blocks can still be allocated (hidden key %)
    keep = []
    try:
        base = "x"
        while len(base) < 1000:
            base = base + base
        while True:
            keep.append(base + str(len(keep)))
    except MemoryError:
        pass
    n = len(keep)
    keep = None
    return n


try:
    GC = __import__("gc")     # the import statement is off at MINIMUM; __import__ works
except Exception:
    GC = None


def collect():
    if GC is not None:
        GC.collect()


# Files are written in parts of at most PART_MAX bytes (<path>, <path>.1, <path>.2, ...):
# the SD API has no append, so a part is one string and needs one contiguous run of heap,
# which a fragmented heap may not have for a 3 KB idea. A 1 KB block, taken while the
# heap is clean, is dropped just before each part is read or written.
PART_MAX = 900
SPARE = [None]


def spare_take():
    if SPARE[0] is not None:
        return
    try:
        b = "x"
        while len(b) < 1024:
            b = b + b
        SPARE[0] = b
    except MemoryError:
        SPARE[0] = None


def spare_free():
    SPARE[0] = None


def part_path(path, k):
    if k == 0:
        return path
    return path + "." + str(k)


def write_part(path, buf):
    buf.append("")
    spare_free()
    try:
        SD.write(path, "\n".join(buf))
    finally:
        spare_take()


def write_lines(path, out):
    buf = []
    size = 0
    k = 0
    for line in out:
        if size + len(line) + 1 > PART_MAX and len(buf) > 0:
            write_part(part_path(path, k), buf)
            k = k + 1
            buf = []
            size = 0
        buf.append(line)
        size = size + len(line) + 1
    write_part(part_path(path, k), buf)
    out.clear()
    k = k + 1
    while File.exist(part_path(path, k)):      # a shorter file than last time
        File.unlink(part_path(path, k))
        k = k + 1


def read_lines(path):
    lines = []
    k = 0
    while File.exist(part_path(path, k)):
        spare_free()
        try:
            lines.extend(SD.read(part_path(path, k)).split("\n"))
        finally:
            spare_take()
        k = k + 1
    return lines


def ensure_dir(path):
    if not Dir.exist(path):
        Dir.mkdir(path)



class UI:
    # Screen setup and the plumbing every screen uses. An app subclasses it and sets
    # self.home (its folder) and, for the menu bar, menu() and switch().
    def __init__(self):
        self.console = IO()
        self.sp = None
        self.home = ""
        self.msg = ""
        self.hl_spec = None
        self.hl = []
        # TERM512: leave the 240x135 window (firmware after v2.7; older has no screen_width)
        try:
            if Display.screen_width() > Display.width():
                Display.full_screen()
        except Exception:
            pass
        self.W = Display.width()
        self.H = Display.height()
        self.top = Widget.body_top()
        self.bot = Widget.body_bottom()
        self.cw = Widget.char_width()
        self.lh = 13
        self.cols = (self.W - 12) // self.cw
        self.c_text = Widget.theme_text()
        self.c_em = Widget.theme_emphasis()
        self.c_sel = Widget.theme_selected()
        self.c_box = Widget.theme_box()
        self.c_bg = Widget.theme_background()
        self.c_dim = Widget.dim()

    def key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def nav(self, k):
        if k == "%":
            collect()
            g = 0
            if GC is not None:
                g = GC.mem_free() // 1024
            self.msg = "{} KB free ({} in 1 KB blocks) of {}".format(g, free_kb(), heap_total() // 1024)
        if k == "j":
            return "DOWN"
        if k == "k":
            return "UP"
        if k == "h":
            return "LEFT"
        if k == "l":
            return "RIGHT"
        return arrow(k)

    def cmd(self, spec, fn, args):
        # one key on a screen with a key table: Tab opens the menu bar, which hands back the
        # key of the item picked, so the screen has one code path for both
        while True:
            self.paint(fn, args)
            self.msg = ""
            k = self.nav(self.key())
            if k != "\t":
                return k
            k = self.menu(spec, fn, args)
            if k is not None and k[0] == "@":
                # Apps menu: save, leave a place.txt, hand off to that app
                if self.switch(cut(k, 1, len(k))):
                    raise Switch()
                k = None
            if k is not None:
                return k

    def paint(self, fn, args):
        # BandedSprite: fn redraws the WHOLE screen once per band
        while self.sp.draw():
            fn(*args)

    def t(self, x, y, s, c):
        self.sp.text(x, y, s, c)

    def lines(self, x, y, text, cols, maxn, c):
        n = 0
        for ln in wrap(text, cols):
            if n >= maxn:
                break
            self.t(x, y, ln, c)
            y = y + self.lh
            n = n + 1
        return y

    def frame(self, title, right):
        self.sp.fill(self.c_bg)
        Widget.header(self.sp, title, right)

    def foot(self, hints):
        if self.msg != "":
            Widget.footer(self.sp, self.msg)
            return
        if isinstance(hints, str):
            if not (self.hl_spec is hints):
                self.hl = self.hint_list(hints)
                self.hl_spec = hints
            hints = self.hl
        Widget.hints(self.sp, hints)

    def hint_list(self, spec):
        # the table's numbered items, in order, while they fit beside "[Tab] menu"
        # (Widget.hints draws "[key] label " with no clipping)
        found = []
        for it in spec.replace(";", "|").split("|"):
            if it[0] >= "1" and it[0] <= "9":
                found.append(it)
        found.sort()
        room = (self.W - 3) // self.cw - 10     # the bar starts 3 px in; [Tab] menu is 10
        out = []
        for it in found:
            sp = it.find(" ")
            room = room - len(it) - 2
            if room < 0:
                break
            out.append((cut(it, 1, sp), cut(it, sp + 1, len(it))))
        out.append(("Tab", "menu"))
        return out

    def row(self, y, text, selected, w=0):
        if w == 0:
            w = self.W
        if selected:
            self.sp.fill_rect(2, y - 1, w - 4, self.lh, self.c_box)
            self.t(6, y, Widget.clip(self.sp, text, w - 12), self.c_sel)
        else:
            self.t(6, y, Widget.clip(self.sp, text, w - 12), self.c_text)

    def visible_rows(self):
        return (self.bot - self.top - 4) // self.lh

    def list_top(self, sel, count, rows):
        top = sel - rows + 1
        if top < 0:
            top = 0
        return top

    def ask_yn(self, title, q, body):
        while True:
            self.paint(self.r_yn, (title, q, body))
            k = self.key()
            if k == "y" or k == "Y":
                return True
            if k == "n" or k == "N":
                return False
            if k == "ESC":
                return None

    def r_yn(self, title, q, body):
        self.frame(title, "")
        y = self.top + 3
        for b in body:
            y = self.lines(6, y, b, self.cols, 3, self.c_text) + 2
        self.lines(6, y + 2, q, self.cols, 2, self.c_em)
        Widget.hints(self.sp, [("y", "yes"), ("n", "no"), ("ESC", "back")])

    def show(self, title, right, body, hints):
        # body: list of (text, colour); waits for a key and returns it
        self.paint(self.r_show, (title, right, body, hints))
        return self.key()

    def r_show(self, title, right, body, hints):
        self.frame(title, right)
        y = self.top + 3
        for b in body:
            if y > self.bot - self.lh:
                break
            y = self.lines(6, y, b[0], self.cols, (self.bot - y) // self.lh, b[1])
        Widget.hints(self.sp, hints)
