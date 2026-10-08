# PROJECTOR - play your ideas forward.  AREA512 MicroPython (MINIMUM level:
# no imports, no slicing, no f-strings).  Sister app to Harness: a projection
# that holds is promoted to /data/harness/inbox (docs/PROMOTION_FORMAT.md).
# The app never suggests words or numbers; it asks, and it does arithmetic.

APPDIR = "/data/projector"
IDEAS = "/data/projector/ideas"
INDEX = "/data/projector/library.txt"
META = "/data/projector/meta.txt"
OUTBOX = "/data/harness/inbox"

CONF = ["", "sure", "rough", "guess"]
SPREAD = [0, 10, 30, 60]          # % a stage's numbers can be off, by confidence
DIFF = ["", "easy", "medium", "hard"]
DTAG = ["", "easy", "med", "HARD"]
HARD_OVERRUN = 25                 # hard stages run this much % longer in the worst case
WINDOWS = [6, 12, 24, 36, 60]
WINDOW_NAMES = ["6 months", "1 year", "2 years", "3 years", "5 years"]
SCEN = ["best", "likely", "worst"]
TAG = {"incubating": "new", "simulating": "sim", "ready": "HOLDS",
       "promoted": "sent", "archived": "arch"}
FIELDS = ["title", "status", "touched", "wish", "picture", "why", "window",
          "cash", "obstacle", "ifthen", "note", "fruit", "feel", "effort", "worth",
          "task", "done", "minutes"]
MAX_STAGES = 7
TEXT_MAX = 80
MAX_ASSUME = 6


# ---------------------------------------------------------------- helpers

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


def akey(text):
    # crack key for an assumption: short, so the text isn't stored twice
    return "a:" + cut(text, 0, 16)


def has_digit(s):
    for ch in s:
        if ch >= "0" and ch <= "9":
            return True
    return False


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


def money(n):
    a = abs(n)
    if a >= 10000:
        s = "{}k".format((a + 500) // 1000)
    elif a >= 1000:
        s = "{}.{}k".format(a // 1000, (a % 1000) // 100)
    else:
        s = "{}".format(a)
    if n < 0:
        return "-$" + s
    return "$" + s


def smoney(n):
    if n > 0:
        return "+" + money(n)
    return money(n)


def pct(n, p):
    # n * p / 100, rounded half away from zero
    r = (abs(n) * p + 50) // 100
    if n < 0:
        return 0 - r
    return r


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


# A 3 KB block taken while the heap is clean and dropped just before each whole-file read
# or write: the device's SD API has no append, so a file is one string that needs one
# contiguous run of heap, and a long session leaves the heap fragmented.
SPARE = [None]


def spare_take():
    try:
        b = "x"
        while len(b) < 3072:
            b = b + b
        SPARE[0] = b
    except MemoryError:
        SPARE[0] = None


def spare_free():
    SPARE[0] = None


def write_lines(path, out):
    out.append("")
    spare_free()
    try:
        SD.write(path, "\n".join(out))
    finally:
        out.clear()
        spare_take()


def read_lines(path):
    spare_free()
    try:
        return SD.read(path).split("\n")
    finally:
        spare_take()


def ensure_dir(path):
    if not Dir.exist(path):
        Dir.mkdir(path)


# ---------------------------------------------------------------- model

class Idea:
    def __init__(self, iid):
        self.id = iid
        self.f = {}
        self.stages = []    # [name, months, net per month, conf 1-3, diff 1-3]
        self.assume = []    # [checked 0/1, text]
        self.faced = {}     # crack key -> "If it happens, I will ..."

    def get(self, k):
        return self.f.get(k, "")

    def num(self, k, d):
        return toint(self.f.get(k, ""), d)

    def path(self):
        return IDEAS + "/" + str(self.id) + ".txt"


def load_idea(iid):
    idea = Idea(iid)
    if not File.exist(idea.path()):
        return idea
    for line in read_lines(idea.path()):
        if len(line) > 1 and line[1] == "|":
            p = line.split("|")
            if line[0] == "S" and len(p) >= 6:
                idea.stages.append([p[1], toint(p[2], 1), toint(p[3], 0),
                                    toint(p[4], 2), toint(p[5], 2)])
            elif line[0] == "A" and len(p) >= 3:
                idea.assume.append([toint(p[1], 0), p[2]])
            elif line[0] == "F" and len(p) >= 3:
                idea.faced[p[1]] = p[2]
        else:
            kv = line.split(": ", 1)
            if len(kv) == 2:
                idea.f[kv[0]] = kv[1]
    return idea


def save_idea(idea):
    ensure_dir(IDEAS)
    out = ["PROJECTOR-IDEA 1"]
    for k in FIELDS:
        v = idea.f.get(k, "")
        if v != "":
            out.append(k + ": " + v)
    for s in idea.stages:
        out.append("S|{}|{}|{}|{}|{}".format(s[0], s[1], s[2], s[3], s[4]))
    for a in idea.assume:
        out.append("A|{}|{}".format(a[0], a[1]))
    for k in idea.faced:
        out.append("F|{}|{}".format(k, idea.faced[k]))
    write_lines(idea.path(), out)


# ---------------------------------------------------------------- engine

def stage_case(st, sc):
    # (months, net per month) for one stage in scenario sc: 0 best, 1 likely, 2 worst
    m = st[1]
    n = st[2]
    s = SPREAD[st[3]]
    if sc == 1:
        return m, n
    if sc == 2:
        extra = 0
        if st[4] == 3:
            extra = HARD_OVERRUN
        m2 = (m * (100 + s + extra) + 99) // 100
        if n < 0:
            return m2, pct(n, 100 + s)
        return m2, pct(n, 100 - s)
    m2 = (m * (100 - s)) // 100
    if m2 < 1:
        m2 = 1
    if n < 0:
        return m2, pct(n, 100 - s)
    return m2, pct(n, 100 + s)


class Proj:
    # Within a stage the balance moves in a straight line, so per-stage segments are enough:
    # no per-month list (RAM), and lowest point / first month below zero are exact.
    def __init__(self, idea, sc):
        b = idea.num("cash", 0)
        self.start = b
        self.starts = []
        self.ends = []
        self.nets = []
        self.sbal = []
        self.low = b
        self.high = b
        self.low_m = 0
        self.out_m = 0
        m = 0
        for st in idea.stages:
            r = stage_case(st, sc)
            self.starts.append(m)
            self.sbal.append(b)
            self.nets.append(r[1])
            if self.out_m == 0 and r[1] < 0 and b + r[0] * r[1] < 0:
                if b < 0:
                    self.out_m = m + 1
                else:
                    self.out_m = m + b // (0 - r[1]) + 1
            b = b + r[0] * r[1]
            m = m + r[0]
            self.ends.append(m)
            if b < self.low:
                self.low = b
                self.low_m = m
            if b > self.high:
                self.high = b
        self.months = m
        self.end = b

    def bal(self, month):
        if month <= 0 or len(self.ends) == 0:
            return self.start
        i = self.stage_at(month)
        if month > self.ends[i]:
            month = self.ends[i]
        return self.sbal[i] + (month - self.starts[i]) * self.nets[i]

    def stage_at(self, month):
        i = 0
        while i < len(self.ends):
            if month <= self.ends[i]:
                return i
            i = i + 1
        return len(self.ends) - 1


def find_cracks(idea, pl, pw):
    # [key, text, must_fix, where]; where = stage index or a screen name
    out = []
    st = idea.stages
    if len(st) == 0:
        out.append(["nostage", "No stages yet", True, "stage"])
    else:
        if pl.out_m > 0:
            out.append(["out_base", "Cash out in month {} (likely)".format(pl.out_m),
                        False, pl.stage_at(pl.out_m)])
        elif pw.out_m > 0:
            out.append(["out_worst", "Cash out in month {} (worst case)".format(pw.out_m),
                        False, pw.stage_at(pw.out_m)])
        win = idea.num("window", 36)
        if pl.months > win:
            out.append(["horizon", "Takes {} months; window is {}".format(pl.months, win),
                        False, pl.stage_at(win + 1)])
        i = 0
        while i < len(st):
            if st[i][4] == 3 and st[i][3] == 3:
                out.append(["wildhard:" + st[i][0], "{}: hard, and a guess".format(st[i][0]),
                            False, i])
            if i > 0 and st[i][4] == 3 and st[i - 1][4] == 3:
                out.append(["hardrun:" + st[i][0],
                            "{} + {}: hard back to back".format(st[i - 1][0], st[i][0]),
                            False, i])
            i = i + 1
        if pl.end < pl.start:
            out.append(["endbelow", "Ends below the money you start with", False, "money"])
    for a in idea.assume:
        if not a[0]:
            out.append([akey(a[1]), "Unchecked: " + a[1], False, "assume"])
    if idea.get("picture") != "" and not has_digit(idea.get("picture")):
        out.append(["vague", "Proof has no number to check", False, "vision"])
    if idea.get("obstacle") == "":
        out.append(["premortem", "No obstacle named yet (o)", True, "premortem"])
    elif idea.get("ifthen") == "":
        out.append(["ifthen", "No If-Then for the obstacle (o)", True, "premortem"])
    return out


def is_open(idea, c):
    return c[2] or not (c[0] in idea.faced)


# ---------------------------------------------------------------- app

class App:
    def __init__(self):
        self.console = IO()
        self.sp = None
        self.lib = []          # [id, status, touched, title]
        self.session = 1
        self.next_id = 1
        self.idea = None
        self.dirty = False
        self.msg = ""
        self.sel = 0
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

    # ---- plumbing

    def key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def nav(self, k):
        if k == "%":
            n = free_kb()
            self.msg = "free ~{} KB".format(n)
        if k == "j":
            return "DOWN"
        if k == "k":
            return "UP"
        if k == "h":
            return "LEFT"
        if k == "l":
            return "RIGHT"
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
        else:
            Widget.hints(self.sp, hints)

    def row(self, y, text, selected):
        if selected:
            self.sp.fill_rect(2, y - 1, self.W - 4, self.lh, self.c_box)
            self.t(6, y, Widget.clip(self.sp, text, self.W - 12), self.c_sel)
        else:
            self.t(6, y, Widget.clip(self.sp, text, self.W - 12), self.c_text)

    def visible_rows(self):
        return (self.bot - self.top - 4) // self.lh

    def list_top(self, sel, count, rows):
        top = sel - rows + 1
        if top < 0:
            top = 0
        return top

    # ---- question screens (own: Widget.input blanks the screen to one line)

    def ask_text(self, title, q, hint, initial, maxlen):
        s = initial
        while True:
            self.paint(self.r_ask, (title, q, hint, s + "_",
                                          "{}/{}".format(len(s), maxlen)))
            k = self.key()
            if k == "ENTER":
                return clean(s)
            if k == "ESC":
                return None
            if k == "BS":
                s = cut(s, 0, len(s) - 1)
            elif len(k) == 1 and k >= " " and k <= "~" and len(s) < maxlen:
                s = s + k

    def ask_number(self, title, q, hint, initial, lo, hi):
        s = ""
        while True:
            shown = s + "_"
            if s == "":
                shown = "_   (ENTER keeps {})".format(initial)
            self.paint(self.r_ask, (title, q, hint, shown, "5k=5000"))
            k = self.key()
            if k == "ESC":
                return None
            if k == "ENTER":
                if s == "" or s == "-":
                    return initial
                v = toint(s.replace("k", "000"), initial)
                if v < lo:
                    v = lo
                if v > hi:
                    v = hi
                return v
            if k == "BS":
                s = cut(s, 0, len(s) - 1)
            elif k >= "0" and k <= "9" and len(k) == 1 and len(s) < 9:
                if s.find("k") < 0:
                    s = s + k
            elif k == "-" and s == "" and lo < 0:
                s = "-"
            elif k == "k" and s != "" and s != "-" and s.find("k") < 0:
                s = s + "k"

    def r_ask(self, title, q, hint, shown, right):
        self.frame(title, right)
        y = self.top + 3
        y = self.lines(6, y, q, self.cols, 3, self.c_em)
        if hint != "":
            y = self.lines(6, y, hint, self.cols, 2, self.c_dim)
        y = y + 2
        h = self.bot - y - 2
        self.sp.fill_rect(2, y, self.W - 4, h, self.c_box)
        self.sp.rect(2, y, self.W - 4, h, Widget.theme_border())
        ans = wrap(shown, self.cols - 1)
        fit = (h - 4) // self.lh
        first = len(ans) - fit
        if first < 0:
            first = 0
        yy = y + 3
        i = first
        while i < len(ans):
            self.t(8, yy, ans[i], self.c_sel)
            yy = yy + self.lh
            i = i + 1
        Widget.hints(self.sp, [("ENT", "ok"), ("ESC", "back")])

    def ask_choice(self, title, q, options, cur):
        sel = cur
        if sel < 0:
            sel = 0
        while True:
            self.paint(self.r_choice, (title, q, options, sel))
            k = self.nav(self.key())
            if k == "ESC":
                return None
            if k == "ENTER" or k == " ":
                return sel
            if k == "DOWN" and sel < len(options) - 1:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif len(k) == 1 and k >= "1" and k <= "9":
                n = ord(k) - ord("1")
                if n < len(options):
                    return n

    def r_choice(self, title, q, options, sel):
        self.frame(title, "")
        y = self.lines(6, self.top + 3, q, self.cols, 2, self.c_em) + 2
        i = 0
        while i < len(options):
            self.row(y, "{} {}".format(i + 1, options[i]), i == sel)
            y = y + self.lh
            i = i + 1
        Widget.hints(self.sp, [("1-{}".format(len(options)), "pick"), ("ESC", "back")])

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

    # ---- storage

    def load_lib(self):
        ensure_dir("/data")
        ensure_dir(APPDIR)
        ensure_dir(IDEAS)
        if File.exist(META):
            for line in read_lines(META):
                kv = line.split(": ", 1)
                if len(kv) == 2 and kv[0] == "session":
                    self.session = toint(kv[1], 0) + 1
                elif len(kv) == 2 and kv[0] == "next_id":
                    self.next_id = toint(kv[1], 1)
        self.save_meta()
        if File.exist(INDEX):
            for line in read_lines(INDEX):
                p = line.split("|", 3)
                if len(p) == 4:
                    self.lib.append([toint(p[0], 0), p[1], toint(p[2], 0), p[3]])

    def save_meta(self):
        SD.write(META, "session: {}\nnext_id: {}\n".format(self.session, self.next_id))

    def save_lib(self):
        out = []
        for e in self.lib:
            out.append("{}|{}|{}|{}".format(e[0], e[1], e[2], e[3]))
        write_lines(INDEX, out)

    def save(self):
        idea = self.idea
        st = idea.get("status")
        if st != "promoted" and st != "archived":
            if self.holds():
                st = "ready"
            elif len(idea.stages) > 0:
                st = "simulating"
            else:
                st = "incubating"
        idea.f["status"] = st
        idea.f["touched"] = str(self.session)
        try:
            save_idea(idea)
        except MemoryError:
            self.msg = "Out of memory, NOT saved: s again"
            return False
        found = False
        for e in self.lib:
            if e[0] == idea.id:
                e[1] = st
                e[2] = self.session
                e[3] = idea.get("title")
                found = True
        if not found:
            self.lib.insert(0, [idea.id, st, self.session, idea.get("title")])
        try:
            self.save_lib()
        except MemoryError:
            self.msg = "Out of memory, NOT saved: s again"
            return False
        self.dirty = False
        self.msg = "saved"
        return True

    # ---- library

    def run(self):
        Display.fill_screen(self.c_bg)
        self.sp = BandedSprite(12)
        try:
            self.paint(Widget.splash, (self.sp, "PROJECTOR", "play your ideas forward"))
            sleep_ms(700)
            self.load_lib()
            spare_take()
            self.library()
        finally:
            self.sp.delete()
            self.sp = None
            Display.fill_screen(self.c_bg)

    def library(self):
        sel = 0
        while True:
            self.paint(self.r_library, (sel,))
            self.msg = ""
            k = self.nav(self.key())
            if k == "q" or k == "ESC":
                return
            if k == "DOWN" and sel < len(self.lib) - 1:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif k == "a":
                if self.new_idea():
                    sel = 0
                    self.work()
                self.idea = None
            elif k == "ENTER" and len(self.lib) > 0:
                self.idea = None
                try:
                    self.idea = load_idea(self.lib[sel][0])
                except MemoryError:
                    self.msg = "Out of memory opening it"
                if self.idea is not None:
                    self.dirty = False
                    self.work()
                    self.idea = None
            elif k == "d" and len(self.lib) > 0:
                self.archive(sel)

    def r_library(self, sel):
        self.frame("PROJECTOR", "LIBRARY")
        if len(self.lib) == 0:
            Widget.center_lines(self.sp, [("No ideas yet.", self.c_em),
                                          ("Press a to start one.", self.c_text)])
        rows = self.visible_rows()
        top = self.list_top(sel, len(self.lib), rows)
        y = self.top + 3
        i = top
        while i < len(self.lib) and i < top + rows:
            e = self.lib[i]
            self.row(y, e[3], i == sel)
            Widget.text_right(self.sp, self.W - 6, y, TAG.get(e[1], "?"), self.c_em)
            y = y + self.lh
            i = i + 1
        self.foot([("a", "new"), ("ENT", "open"), ("d", "archive"), ("q", "quit")])

    def archive(self, sel):
        e = self.lib[sel]
        back = e[1] == "archived"
        q = "Archive '{}'?".format(e[3])
        if back:
            q = "Bring '{}' back?".format(e[3])
        if self.ask_yn("ARCHIVE", q, []):
            self.idea = load_idea(e[0])
            self.idea.f["status"] = "archived"
            if back:
                self.idea.f["status"] = "incubating"
            self.save()
            self.msg = ""

    # ---- new idea: one question per screen

    def new_idea(self):
        T = "NEW IDEA"
        name = self.ask_text(T, "What's the idea? Give it a short name.", "", "", 24)
        if name is None or name == "":
            return False
        idea = Idea(self.next_id)
        self.next_id = self.next_id + 1
        self.save_meta()
        idea.f["title"] = name
        self.idea = idea
        steps = [("wish", "What are you trying to make happen?", "I want to ..."),
                 ("picture", "Picture it working. What could you point to that proves it?",
                  "Something you could show someone. Add a number."),
                 ("why", "Why does this matter to you?",
                  "Picture it done first: where you are, how it feels.")]
        for s in steps:
            v = self.ask_text(T, s[1], s[2], "", TEXT_MAX)
            if v is None:
                break
            idea.f[s[0]] = v
        w = self.ask_choice(T, "How far ahead should we look?", WINDOW_NAMES, 3)
        if w is None:
            w = 3
        idea.f["window"] = str(WINDOWS[w])
        c = self.ask_number(T, "How much money can you put toward this right now?",
                            "0 is fine.", 0, 0, 99999999)
        if c is None:
            c = 0
        idea.f["cash"] = str(c)
        self.msg = ""
        while len(idea.stages) < MAX_STAGES:
            q = "Lay it out in stages. First stage?"
            if len(idea.stages) > 0:
                q = "What comes after '{}'?".format(idea.stages[len(idea.stages) - 1][0])
            if not self.add_stage(len(idea.stages), q):
                break
            if len(idea.stages) >= MAX_STAGES:
                break
            more = self.ask_yn(T, "Another stage after this one?",
                               ["{} stage(s) so far.".format(len(idea.stages))])
            if not more:
                break
        self.sel = 0
        self.save()
        return True

    # ---- stages

    def add_stage(self, at, q):
        T = "STAGE"
        name = self.ask_text(T, q, "A short name: Learn, Build, Launch ...", "", 12)
        if name is None or name == "":
            return False
        st = [name, 3, 0, 2, 2]
        if not self.stage_numbers(st):
            return False
        self.idea.stages.insert(at, st)
        self.sel = at
        self.dirty = True
        return True

    def stage_numbers(self, st):
        T = st[0].upper()
        m = self.ask_number(T, "How many months will '{}' take?".format(st[0]),
                            "Calendar months.", st[1], 1, 120)
        if m is None:
            return False
        st[1] = m
        n = self.ask_number(T, "Money each month during '{}'?".format(st[0]),
                            "Spending is negative (-500), income positive.", st[2],
                            -9999999, 9999999)
        if n is None:
            return False
        st[2] = n
        c = self.ask_choice(T, "How sure are you of those numbers?",
                            ["sure", "rough idea", "a guess"], st[3] - 1)
        if c is None:
            return False
        st[3] = c + 1
        d = self.ask_choice(T, "How hard will '{}' be for you?".format(st[0]),
                            ["easy", "medium", "hard"], st[4] - 1)
        if d is None:
            return False
        st[4] = d + 1
        return True

    def edit_stage(self, i):
        st = self.idea.stages[i]
        sel = 0
        while True:
            labels = ["Name     " + st[0], "Months   {}".format(st[1]),
                      "Monthly  " + smoney(st[2]), "Sure?    " + CONF[st[3]],
                      "Hard?    " + DIFF[st[4]]]
            self.paint(self.r_form, ("STAGE {}".format(i + 1), labels, sel,
                                           [("ENT", "edit"), ("1-3", "set"), ("ESC", "done")]))
            k = self.nav(self.key())
            if k == "ESC" or k == "q":
                return
            if k == "DOWN" and sel < 4:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif (sel == 3 or sel == 4) and (k == "1" or k == "2" or k == "3"):
                st[sel] = ord(k) - ord("0")
                self.dirty = True
            elif k == "ENTER":
                v = None
                if sel == 0:
                    v = self.ask_text("STAGE", "Stage name?", "", st[0], 12)
                    if v == "":
                        v = None
                elif sel == 1:
                    v = self.ask_number("STAGE", "Months for '{}'?".format(st[0]), "",
                                        st[1], 1, 120)
                elif sel == 2:
                    v = self.ask_number("STAGE", "Money each month in '{}'?".format(st[0]),
                                        "Spending negative, income positive.", st[2],
                                        -9999999, 9999999)
                elif sel == 3:
                    v = self.ask_choice("STAGE", "How sure are you?",
                                        ["sure", "rough idea", "a guess"], st[3] - 1)
                    if v is not None:
                        v = v + 1
                else:
                    v = self.ask_choice("STAGE", "How hard?", ["easy", "medium", "hard"],
                                        st[4] - 1)
                    if v is not None:
                        v = v + 1
                if v is not None:
                    st[sel] = v
                    self.dirty = True

    def r_form(self, title, labels, sel, hints):
        self.frame(title, "")
        y = self.top + 3
        i = 0
        while i < len(labels):
            self.row(y, labels[i], i == sel)
            y = y + self.lh + 2
            i = i + 1
        Widget.hints(self.sp, hints)

    # ---- the strip (main screen for one idea)

    def refresh(self):
        idea = self.idea
        self.pb = Proj(idea, 0)
        self.pl = Proj(idea, 1)
        self.pw = Proj(idea, 2)
        self.cr = find_cracks(idea, self.pl, self.pw)
        n = 0
        for c in self.cr:
            if is_open(idea, c):
                n = n + 1
        self.n_open = n

    def holds(self):
        self.refresh()
        return self.n_open == 0 and len(self.idea.stages) > 0

    def readonly(self):
        if self.idea.get("status") == "promoted":
            self.msg = "Promoted: Harness owns it now"
            return True
        return False

    def work(self):
        idea = self.idea
        self.sel = 0
        note = idea.get("note")
        if note != "" and idea.num("touched", self.session) < self.session:
            self.show("WHERE YOU LEFT OFF", idea.get("title"),
                      [(note, self.c_em), ("", self.c_text),
                       ("Any key to pick it back up.", self.c_dim)], [("any", "key")])
        while True:
            self.refresh()
            if self.sel >= len(idea.stages):
                self.sel = len(idea.stages) - 1
            if self.sel < 0:
                self.sel = 0
            self.paint(self.r_strip, ())
            self.msg = ""
            k = self.nav(self.key())
            if k == "q" or k == "ESC":
                if self.leave():
                    return
            elif k == "LEFT" and self.sel > 0:
                self.sel = self.sel - 1
            elif k == "RIGHT" and self.sel < len(idea.stages) - 1:
                self.sel = self.sel + 1
            elif k == "p" or k == "ENTER":
                self.play()
            elif k == "c":
                self.crack_list()
            elif k == "$":
                self.money_view()
            elif k == "?":
                self.help()
            elif k == "s":
                if not self.readonly():
                    self.save()
            elif self.readonly():
                pass
            elif k == "e" and len(idea.stages) > 0:
                self.edit_stage(self.sel)
            elif k == "n":
                if len(idea.stages) >= MAX_STAGES:
                    self.msg = "7 stages is the limit"
                else:
                    at = self.sel + 1
                    if len(idea.stages) == 0:
                        at = 0
                    self.add_stage(at, "Name the new stage.")
            elif k == "x" and len(idea.stages) > 0:
                if self.ask_yn("STAGE", "Delete '{}'?".format(idea.stages[self.sel][0]), []):
                    idea.stages.pop(self.sel)
                    self.dirty = True
            elif k == "v":
                self.vision()
            elif k == "a":
                self.assumptions()
            elif k == "o":
                self.premortem()
            elif k == "P":
                self.promote()

    def leave(self):
        if not self.dirty:
            return True
        r = self.ask_yn("LEAVING", "Save your changes?", ["Saving is never automatic."])
        if r is None:
            return False
        if r:
            n = self.ask_text("NOTE", "A note to future you: where are you leaving off?",
                              "ESC skips.", self.idea.get("note"), TEXT_MAX)
            if n is not None:
                self.idea.f["note"] = n
            if not self.save():
                return False
        return True

    def r_strip(self):
        idea = self.idea
        right = "{} !".format(self.n_open)
        if self.n_open == 0 and len(idea.stages) > 0:
            right = "HOLDS"
        if idea.get("status") == "promoted":
            right = "SENT"
        self.frame(Widget.clip(self.sp, idea.get("title"), self.W - 70), right)
        y = self.top + 2
        n = len(idea.stages)
        if n == 0:
            Widget.center_lines(self.sp, [("No stages yet.", self.c_em),
                                          ("n adds one.", self.c_text)])
        else:
            vc = (self.W - 8) // 56
            if vc > n:
                vc = n
            first = self.sel - vc + 1
            if first < 0:
                first = 0
            cw = (self.W - 8) // vc
            i = first
            while i < first + vc:
                self.r_cell(4 + (i - first) * cw, y, cw - 2, i)
                i = i + 1
            if first > 0:
                self.t(0, y + 20, "<", self.c_em)
            if first + vc < n:
                self.t(self.W - 6, y + 20, ">", self.c_em)
        y = y + 4 * 12 + 6
        if n > 0:
            self.r_spark(4, y, self.W - 8, 16)
            y = y + 19
            pl = self.pl
            self.t(6, y, "likely: {} mo, ends {}, low {}".format(pl.months, money(pl.end),
                                                                 money(pl.low)), self.c_text)
            y = y + self.lh
        first_open = None
        for c in self.cr:
            if is_open(idea, c):
                first_open = c
                break
        if first_open is not None:
            self.t(6, y, Widget.clip(self.sp, "! " + first_open[1], self.W - 12), self.c_sel)
        elif n > 0:
            self.t(6, y, "The projection holds.  P promotes.", self.c_em)
        self.foot([("p", "play"), ("c", "cracks"), ("e", "edit"), ("?", "keys")])

    def stage_flag(self, i):
        for c in self.cr:
            if c[3] == i and is_open(self.idea, c):
                return True
        return False

    def r_cell(self, x, y, w, i):
        st = self.idea.stages[i]
        h = 4 * 12 + 2
        sel = i == self.sel
        if sel:
            self.sp.fill_rect(x, y, w, h, self.c_box)
            self.sp.rect(x, y, w, h, self.c_sel)
        else:
            self.sp.rect(x, y, w, h, Widget.theme_border())
        c = self.c_text
        if sel:
            c = self.c_sel
        self.t(x + 3, y + 1, Widget.clip(self.sp, st[0], w - 6), c)
        self.t(x + 3, y + 13, "{}mo {}".format(st[1], DTAG[st[4]]), c)
        self.t(x + 3, y + 25, Widget.clip(self.sp, smoney(st[2]), w - 6), c)
        self.t(x + 3, y + 37, CONF[st[3]], self.c_dim)
        if self.stage_flag(i):
            self.t(x + w - 8, y + 37, "!", self.c_sel)

    def r_spark(self, x, y, w, h):
        # likely-case balance over time; below zero in the selected colour.
        # Only the bands that hold these rows do the work (render runs once per band).
        if self.sp.region_bottom() <= y - 2 or self.sp.region_top() > y + h + 1:
            return
        p = self.pl
        lo = p.low
        if lo > 0:
            lo = 0
        span = p.high - lo
        if span < 1:
            span = 1
        zero = y + h - ((0 - lo) * h) // span
        self.sp.line(x, zero, x + w - 1, zero, self.c_dim)
        px = 0
        while px < w:
            b = p.bal((px * p.months) // (w - 1))
            py = y + h - ((b - lo) * h) // span
            c = self.c_em
            if b < 0:
                c = self.c_sel
            self.sp.pixel(x + px, py, c)
            self.sp.pixel(x + px, py - 1, c)
            px = px + 1

    def help(self):
        self.show("KEYS", "", [
            ("h/l stage   p play   c cracks", self.c_text),
            ("e edit  n new  x delete stage", self.c_text),
            ("v vision   a assumptions", self.c_text),
            ("$ money    o obstacle (premortem)", self.c_text),
            ("P promote  s save   q back", self.c_text)], [("any", "key")])

    # ---- play forward

    def play(self):
        idea = self.idea
        n = len(idea.stages)
        if n == 0:
            self.msg = "Add a stage first (n)"
            return
        i = 0
        while True:
            self.refresh()
            if i > n:
                i = n
            if i < n:
                self.paint(self.r_play, (i,))
            else:
                self.paint(self.r_play_end, ())
            k = self.nav(self.key())
            if k == "q" or k == "ESC":
                return
            if (k == "RIGHT" or k == "ENTER" or k == " ") and i < n:
                i = i + 1
            elif k == "LEFT" and i > 0:
                i = i - 1
            elif (k == "ENTER" or k == "RIGHT") and i == n:
                if self.n_open == 0:
                    self.holds_screen()
                    return
                self.crack_list()
                return
            elif k == "e" and i < n and not self.readonly():
                self.edit_stage(i)
            elif k == "f" and i < n and not self.readonly():
                for c in self.cr:
                    if c[3] == i and is_open(idea, c) and not c[2]:
                        self.face(c)
                        break

    def r_play(self, i):
        st = self.idea.stages[i]
        pl = self.pl
        pw = self.pw
        self.frame("PLAY", "{}/{}".format(i + 1, len(self.idea.stages)))
        y = self.top + 3
        self.t(6, y, "Month {} to {}".format(pl.starts[i] + 1, pl.ends[i]), self.c_dim)
        y = y + self.lh
        Widget.big_text(self.sp, 6, y, Widget.clip(self.sp, st[0].upper(), (self.W - 12) // 2))
        y = y + 22
        self.t(6, y, "{}, {}.  {} a month".format(DIFF[st[4]], CONF[st[3]], smoney(st[2])),
               self.c_text)
        y = y + self.lh
        self.t(6, y, "Cash after: {} likely, {} worst".format(
            money(pl.bal(pl.ends[i])), money(pw.bal(pw.ends[i]))), self.c_text)
        y = y + self.lh + 2
        shown = 0
        for c in self.cr:
            if c[3] == i and shown < 2:
                if is_open(self.idea, c):
                    self.t(6, y, Widget.clip(self.sp, "! " + c[1], self.W - 12), self.c_sel)
                else:
                    self.t(6, y, Widget.clip(self.sp, "faced: " + self.idea.faced[c[0]],
                                             self.W - 12), self.c_em)
                y = y + self.lh
                shown = shown + 1
        self.foot([("l", "next"), ("h", "back"), ("e", "edit"), ("f", "face")])

    def r_play_end(self):
        idea = self.idea
        self.frame("PLAY", "month {}".format(self.pl.months))
        y = self.top + 3
        pic = idea.get("picture")
        if pic == "":
            pic = idea.get("wish")
        self.t(6, y, "Month {}. You're there:".format(self.pl.months), self.c_dim)
        y = self.lines(6, y + self.lh, pic, self.cols, 3, self.c_em) + 4
        if self.n_open == 0:
            self.t(6, y, "Nothing left unanswered.", self.c_text)
            self.t(6, y + self.lh, "ENTER: watch it hold", self.c_sel)
        else:
            self.t(6, y, "But {} crack(s) on the way.".format(self.n_open), self.c_sel)
            self.t(6, y + self.lh, "ENTER: look at them", self.c_text)
        self.foot([("ENT", "go on"), ("h", "back"), ("q", "stop")])

    # ---- cracks

    def crack_list(self):
        sel = 0
        while True:
            self.refresh()
            cr = self.cr
            if len(cr) == 0:
                self.msg = "No cracks."
                return
            if sel >= len(cr):
                sel = len(cr) - 1
            self.paint(self.r_cracks, (sel,))
            self.msg = ""
            k = self.nav(self.key())
            if k == "q" or k == "ESC":
                return
            if k == "DOWN" and sel < len(cr) - 1:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif k == "ENTER" and not self.readonly():
                self.crack_action(cr[sel])

    def r_cracks(self, sel):
        self.frame("CRACKS", "{} open".format(self.n_open))
        rows = self.visible_rows() - 1
        top = self.list_top(sel, len(self.cr), rows)
        y = self.top + 3
        i = top
        while i < len(self.cr) and i < top + rows:
            c = self.cr[i]
            mark = "! "
            if not is_open(self.idea, c):
                mark = "~ "
            self.row(y, mark + c[1], i == sel)
            y = y + self.lh
            i = i + 1
        c = self.cr[sel]
        tail = "Fix it in the plan, or face it."
        if c[2]:
            tail = "This one has to be fixed."
        elif not is_open(self.idea, c):
            tail = "Faced: " + self.idea.faced[c[0]]
        self.t(6, self.bot - self.lh, Widget.clip(self.sp, tail, self.W - 12), self.c_dim)
        self.foot([("ENT", "deal with it"), ("ESC", "back")])

    def crack_action(self, c):
        opts = ["Change the plan"]
        if not c[2]:
            opts.append("Face it: write an If-Then")
            if c[0] in self.idea.faced:
                opts.append("Un-face it")
        r = self.ask_choice("CRACK", c[1], opts, 0)
        if r == 0:
            self.goto_fix(c)
        elif r == 1:
            self.face(c)
        elif r == 2:
            self.idea.faced.pop(c[0])
            self.dirty = True

    def goto_fix(self, c):
        w = c[3]
        if isinstance(w, int):
            self.sel = w
            self.edit_stage(w)
        elif w == "money":
            self.money_view()
        elif w == "vision":
            self.vision()
        elif w == "assume":
            self.assumptions()
        elif w == "premortem":
            self.premortem()
        elif w == "stage":
            self.add_stage(0, "Name the first stage.")

    def face(self, c):
        v = self.ask_text("FACE IT", "Say it happens: " + c[1] + ". What will you do?",
                          "If it happens, I will ...", self.idea.faced.get(c[0], "I will "),
                          TEXT_MAX)
        if v is not None and v != "" and v != "I will":
            self.idea.faced[c[0]] = v
            self.dirty = True

    def premortem(self):
        idea = self.idea
        win = idea.num("window", 36)
        o = self.ask_text("PREMORTEM",
                          "Jump to month {}. It didn't work out. What inside you got in the way?"
                          .format(win), "A habit, a feeling, a pattern. Not bad luck.",
                          idea.get("obstacle"), TEXT_MAX)
        if o is None or o == "":
            return
        idea.f["obstacle"] = o
        self.dirty = True
        start = idea.get("ifthen")
        if start == "":
            start = "When "
        p = self.ask_text("IF-THEN", "When that shows up, what will you do?",
                          "When ___, I will ___.", start, TEXT_MAX)
        if p is not None and p != "" and p != "When":
            idea.f["ifthen"] = p

    # ---- money

    def money_view(self):
        sc = 1
        while True:
            self.refresh()
            self.paint(self.r_money, (sc,))
            k = self.nav(self.key())
            if k == "q" or k == "ESC":
                return
            if k == "s" or k == "RIGHT":
                sc = (sc + 1) % 3
            elif k == "LEFT":
                sc = (sc + 2) % 3
            elif k == "e" and not self.readonly():
                v = self.ask_number("MONEY", "Money you can put toward this now?", "",
                                    self.idea.num("cash", 0), 0, 99999999)
                if v is not None:
                    self.idea.f["cash"] = str(v)
                    self.dirty = True

    def r_money(self, sc):
        self.frame("MONEY", "start " + money(self.idea.num("cash", 0)))
        x = 4
        y = self.top + 2
        widths = [52, 62, 52, 62]
        Widget.table_header(self.sp, x, y, widths, ["case", "lowest", "out", "end"])
        y = y + 14
        ps = [self.pb, self.pl, self.pw]
        i = 0
        while i < 3:
            p = ps[i]
            out = "-"
            if p.out_m > 0:
                out = "M{}".format(p.out_m)
            Widget.table_row(self.sp, x, y, widths,
                             [SCEN[i], money(p.low), out, money(p.end)], i == sc)
            y = y + 14
            i = i + 1
        y = y + 3
        p = ps[sc]
        self.t(6, y, "{}: {} months".format(SCEN[sc], p.months), self.c_dim)
        y = y + self.lh
        vals = []
        lo = p.low
        if lo > 0:
            lo = 0
        hi = 0
        j = 0
        while j < 40:
            v = p.bal((j * p.months) // 39) - lo
            vals.append(v)
            if v > hi:
                hi = v
            j = j + 1
        if hi < 1:
            hi = 1
        h = self.bot - y - 2
        if h > 8:
            Widget.line_chart(self.sp, 4, y, self.W - 8, h, vals, hi)
        self.foot([("s", "case"), ("e", "start $"), ("ESC", "back")])

    # ---- vision

    def vision(self):
        idea = self.idea
        sel = 0
        keys = ["title", "wish", "picture", "why", "window", "cash"]
        names = ["Name", "Wish", "Proof", "Why", "Window", "Start $"]
        qs = ["Short name for the idea?", "What are you trying to make happen?",
              "Picture it working. What proves it? Add a number.",
              "Why does this matter to you?", "", ""]
        while True:
            labels = []
            i = 0
            while i < 6:
                v = idea.get(keys[i])
                if i == 4:
                    v = v + " months"
                elif i == 5:
                    v = money(idea.num("cash", 0))
                labels.append("{:<8}{}".format(names[i], v))
                i = i + 1
            self.paint(self.r_form, ("VISION", labels, sel,
                                           [("ENT", "edit"), ("ESC", "back")]))
            k = self.nav(self.key())
            if k == "q" or k == "ESC":
                return
            if k == "DOWN" and sel < 5:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif k == "ENTER" and not self.readonly():
                if sel == 4:
                    cur = 3
                    j = 0
                    while j < len(WINDOWS):
                        if WINDOWS[j] == idea.num("window", 36):
                            cur = j
                        j = j + 1
                    w = self.ask_choice("VISION", "How far ahead should we look?",
                                        WINDOW_NAMES, cur)
                    if w is not None:
                        idea.f["window"] = str(WINDOWS[w])
                        self.dirty = True
                elif sel == 5:
                    v = self.ask_number("VISION", "Money you can put toward this now?", "",
                                        idea.num("cash", 0), 0, 99999999)
                    if v is not None:
                        idea.f["cash"] = str(v)
                        self.dirty = True
                else:
                    mx = TEXT_MAX
                    if sel == 0:
                        mx = 24
                    v = self.ask_text("VISION", qs[sel], "", idea.get(keys[sel]), mx)
                    if v is not None and (v != "" or sel != 0):
                        idea.f[keys[sel]] = v
                        self.dirty = True

    # ---- assumptions

    def assumptions(self):
        idea = self.idea
        sel = 0
        while True:
            self.paint(self.r_assume, (sel,))
            self.msg = ""
            k = self.nav(self.key())
            n = len(idea.assume)
            if k == "q" or k == "ESC":
                return
            if k == "DOWN" and sel < n - 1:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif self.readonly():
                pass
            elif k == "a" and n >= MAX_ASSUME:
                self.msg = "6 is the limit: check or drop one"
            elif k == "a":
                v = self.ask_text("ASSUMPTION", "What has to be true for this to work?",
                                  "One thing you're counting on.", "", 60)
                if v is not None and v != "":
                    idea.assume.append([0, v])
                    sel = len(idea.assume) - 1
                    self.dirty = True
            elif n == 0:
                pass
            elif k == "ENTER" or k == " ":
                idea.assume[sel][0] = 1 - idea.assume[sel][0]
                self.dirty = True
            elif k == "d":
                if self.ask_yn("ASSUMPTION", "Delete it?", [idea.assume[sel][1]]):
                    idea.assume.pop(sel)
                    if sel > 0:
                        sel = sel - 1
                    self.dirty = True
            elif k == "f" and not idea.assume[sel][0]:
                a = idea.assume[sel][1]
                self.face([akey(a), "Unchecked: " + a, False, "assume"])

    def r_assume(self, sel):
        idea = self.idea
        self.frame("ASSUMPTIONS", "{}".format(len(idea.assume)))
        if len(idea.assume) == 0:
            Widget.center_lines(self.sp, [("What must be true?", self.c_em),
                                          ("a adds one.", self.c_text)])
        rows = self.visible_rows()
        top = self.list_top(sel, len(idea.assume), rows)
        y = self.top + 3
        i = top
        while i < len(idea.assume) and i < top + rows:
            a = idea.assume[i]
            box = "[ ] "
            if a[0]:
                box = "[x] "
            elif akey(a[1]) in idea.faced:
                box = "[~] "
            self.row(y, box + a[1], i == sel)
            y = y + self.lh
            i = i + 1
        self.foot([("a", "add"), ("ENT", "checked"), ("f", "face"), ("d", "del")])

    # ---- the projection holds

    def holds_screen(self):
        idea = self.idea
        pl = self.pl
        frames = 24
        f = 0
        while f <= frames:
            self.paint(self.r_holds_anim, (f, frames))
            sleep_ms(60)
            f = f + 1
        self.show("IT HOLDS", "month {}".format(pl.months), [
            (idea.get("picture"), self.c_em), ("", self.c_text),
            ("Because: " + idea.get("why"), self.c_text), ("", self.c_text),
            ("You faced {} crack(s) to get here.".format(len(idea.faced)), self.c_dim)],
            [("any", "key")])
        if idea.get("fruit") == "":
            self.judge()
        if idea.get("status") != "promoted":
            r = self.ask_yn("IT HOLDS", "Promote it to Harness now?",
                            ["It stays here until you do. P promotes later."])
            if r:
                self.promote()

    def r_holds_anim(self, f, frames):
        idea = self.idea
        pl = self.pl
        self.frame("PROJECTOR", "playing")
        total = pl.months
        x0 = 6
        w = self.W - 12
        y = self.top + 30
        self.sp.rect(x0, y, w, 12, Widget.theme_border())
        filled = (w * f) // frames
        self.sp.fill_rect(x0, y, filled, 12, self.c_em)
        for e in pl.ends:
            ex = x0 + (w * e) // total
            self.sp.line(ex, y - 3, ex, y + 14, self.c_text)
        month = (total * f) // frames
        cur = pl.stage_at(month)
        if month == 0:
            cur = 0
        self.t(x0, y - 18, "Month {}".format(month), self.c_text)
        Widget.text_right(self.sp, self.W - 6, y - 18, idea.stages[cur][0], self.c_em)
        if f >= frames:
            Widget.text_center(self.sp, y + 30, "THE PROJECTION HOLDS", self.c_sel)
        Widget.footer(self.sp, "")

    def judge(self):
        idea = self.idea
        T = "JUDGMENT"
        r = self.ask_choice(T, "How fruitful could this be?",
                            ["barely", "a little", "worthwhile", "a lot", "life-changing"], 2)
        if r is None:
            return
        idea.f["fruit"] = str(r + 1)
        r = self.ask_choice(T, "How will the time feel?", ["quick", "moderate", "dragged out"], 1)
        if r is not None:
            idea.f["feel"] = str(r + 1)
        r = self.ask_choice(T, "How hard, overall?", ["easy", "medium", "hard"], 1)
        if r is not None:
            idea.f["effort"] = str(r + 1)
        v = self.ask_text(T, "Is it worth it? Say why in a line.", "", idea.get("worth"),
                          TEXT_MAX)
        if v is not None:
            idea.f["worth"] = v
        self.dirty = True

    # ---- promote to Harness

    def promote(self):
        idea = self.idea
        if idea.get("status") == "promoted":
            self.msg = "Already promoted"
            return
        if not self.holds():
            self.msg = "Doesn't hold yet: c shows the cracks"
            return
        self.paint(self.r_charter, ())
        k = self.key()
        if k != "ENTER":
            return
        if idea.get("wish") == "" or idea.get("picture") == "":
            self.msg = "Wish and proof first: v"
            return
        T = "FIRST ACTION"
        t = self.ask_text(T, "What's one action under an hour you could take this week?",
                          "A verb and an object.", idea.get("task"), TEXT_MAX)
        if t is None or t == "":
            return
        idea.f["task"] = t
        d = self.ask_text(T, "How will you know it's done?",
                          "Something you could see: a file, a number, a yes.",
                          idea.get("done"), TEXT_MAX)
        if d is None or d == "":
            return
        idea.f["done"] = d
        m = self.ask_number(T, "About how many minutes?", "", idea.num("minutes", 30), 1, 600)
        if m is None:
            return
        idea.f["minutes"] = str(m)
        seeds = self.ask_yn("SEED TASKS", "Bring your stages along as starting tasks?",
                            ["They land in Harness's inbox to plan there."])
        if seeds is None:
            return
        r = self.ask_yn("COMMIT", "This creates a live goal in Harness. Ready to commit?",
                        [idea.get("wish")])
        if not r:
            return
        try:
            path = self.write_goal(seeds)
        except MemoryError:
            self.msg = "Out of memory: not promoted. P again"
            return
        idea.f["status"] = "promoted"
        self.save()
        self.show("COMMITTED", "", [
            (idea.get("wish"), self.c_em), ("", self.c_text),
            ("First: " + t, self.c_text), ("", self.c_text),
            ("Harness picks it up from " + path, self.c_dim)], [("any", "key")])

    def r_charter(self):
        # the four WOOP chunks, two lines each at most, so all four always fit
        idea = self.idea
        self.frame("PROMOTE", "charter")
        y = self.top + 2
        parts = [("Wish ", "wish"), ("Proof", "picture"), ("Snag ", "obstacle"),
                 ("Plan ", "ifthen")]
        for p in parts:
            ln = wrap(idea.get(p[1]), self.cols - 6)
            self.t(4, y, p[0], self.c_em)
            self.t(4 + 6 * self.cw, y, ln[0], self.c_text)
            if len(ln) > 1:
                more = ln[1]
                if len(ln) > 2:
                    more = more + ">"
                self.t(4 + 6 * self.cw, y + 12, more, self.c_text)
                y = y + 12
            y = y + 13
        Widget.hints(self.sp, [("ENT", "commit to this"), ("ESC", "not yet")])

    def write_goal(self, seeds):
        idea = self.idea
        pl = self.pl
        ensure_dir("/data/harness")
        ensure_dir(OUTBOX)
        out = ["HARNESS-GOAL 1", "source: projector", "source_id: {}".format(idea.id),
               "title: " + idea.get("title"),
               "wish: " + idea.get("wish"), "outcome: " + idea.get("picture"),
               "obstacle: " + idea.get("obstacle"), "ifthen: " + idea.get("ifthen"),
               "why: " + idea.get("why"), "window_months: " + idea.get("window"),
               "money_baseline: {}".format(idea.num("cash", 0)),
               "money_projected: {}".format(pl.end)]
        out.append("TASK|next|{}|{}||{}|||".format(idea.get("task"), idea.get("done"),
                                                     idea.get("minutes")))
        if seeds:
            for st in idea.stages:
                out.append("TASK|inbox|{}||||||{} months, {} a month".format(
                    st[0], st[1], smoney(st[2])))
        for a in idea.assume:
            state = "unchecked"
            if a[0]:
                state = "checked"
            out.append("ASSUME|{}|{}".format(state, a[1]))
        for c in self.cr:
            if c[0] in idea.faced:
                out.append("IFTHEN|{}|{}".format(c[1], idea.faced[c[0]]))
        out.append("JUDGE|{}|{}|{}|{}".format(idea.get("fruit"), idea.get("feel"),
                                             idea.get("effort"), idea.get("worth")))
        path = OUTBOX + "/goal-{}.txt".format(idea.id)
        write_lines(path, out)
        return path


App().run()
