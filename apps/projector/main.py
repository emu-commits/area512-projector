# PROJECTOR - play your ideas forward.  AREA512 MicroPython (MINIMUM level:
# no imports, no slicing, no f-strings).  Planning half of the Harness system; the
# hand-off to Harness is designed (docs/PROMOTION_FORMAT.md) but not wired in yet.
# The app never suggests words or numbers; it asks, and it does arithmetic.

APPDIR = "/data/projector"
IDEAS = "/data/projector/ideas"
INDEX = "/data/projector/library.txt"
META = "/data/projector/meta.txt"
RECENT = "/data/projector/recent.txt"     # for Home (docs/APPS_FORMAT.md)

CONF = ["", "sure", "rough", "guess"]
SPREAD = [0, 10, 30, 60]          # % a stage's numbers can be off, by confidence
DIFF = ["", "easy", "medium", "hard"]
DTAG = ["", "easy", "med", "HARD"]
HARD_OVERRUN = 25                 # hard stages run this much % longer in the worst case
WINDOWS = [6, 12, 24, 36, 60]
WINDOW_NAMES = ["6 months", "1 year", "2 years", "3 years", "5 years"]
SCEN = ["best", "likely", "worst"]
TAG = {"incubating": "new", "simulating": "sim", "ready": "HOLDS", "archived": "arch"}
FIELDS = ["title", "status", "touched", "wish", "picture", "why", "window",
          "cash", "obstacle", "ifthen", "note", "fruit", "feel", "effort", "worth",
          "task", "done", "minutes", "runs", "fixed"]
MAX_STAGES = 7
TEXT_MAX = 80
MAX_ASSUME = 6

# One key table per screen (docs/UI.md): menus split by ";", each "Title|item|item", an item
# is "<key> <label>". A digit in front puts it on the hint bar, in that order; the bar always
# ends with Tab menu. The menu bar (overlay "menu") and Tab > Help are drawn from the same
# table, so the three can't disagree.
LIB_KEYS = "Idea|1n new|2ENT open|3x archive"
STRIP_KEYS = ("Idea|1p play|2c cracks|s save|w notes;Plan|5m money|b money sheet|v vision|a assume|o obstacle;"
              "Stage|3e edit|4n new|x delete")
CRACK_KEYS = "Crack|1ENT deal with it"


# ---------------------------------------------------------------- helpers


def akey(text):
    # crack key for an assumption: short, so the text isn't stored twice
    return "a:" + cut(text, 0, 16)


def has_digit(s):
    for ch in s:
        if ch >= "0" and ch <= "9":
            return True
    return False


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


def find_home():
    # the app folder holds the .ovl overlays; Filer can launch it from anywhere
    for d in ["/home/ai/projector", "/home/tool/projector", "/home/projector", "/projector"]:
        if File.exist(d + "/ovl/holds.0"):
            return d
    try:
        top = Dir("/home")
        a = top.read()
        while a is not None:
            sub = Dir("/home/" + a)
            b = sub.read()
            while b is not None:
                d = "/home/" + a + "/" + b
                if File.exist(d + "/ovl/holds.0"):
                    sub.close()
                    top.close()
                    return d
                b = sub.read()
            sub.close()
            a = top.read()
        top.close()
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------- model

class Idea:
    def __init__(self, iid):
        self.id = iid
        self.f = {}
        # [name, months, extra cost a month, conf 1-3, diff 1-3, one-time spend, income a month]
        # money is entered apart and kept apart (user, 2026-10-09); the idea's "fixed" cost
        # a month comes on top of every stage
        self.stages = []
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
                idea.stages.append(read_stage(p))
            elif line[0] == "A" and len(p) >= 3:
                idea.assume.append([toint(p[1], 0), p[2]])
            elif line[0] == "F" and len(p) >= 3:
                idea.faced[p[1]] = p[2]
        else:
            kv = line.split(": ", 1)
            if len(kv) == 2:
                idea.f[kv[0]] = kv[1]
    return idea


def read_stage(p):
    st = [p[1], toint(p[2], 1), toint(p[3], 0), toint(p[4], 2), toint(p[5], 2), 0, 0]
    if len(p) >= 8:
        st[5] = toint(p[6], 0)
        st[6] = toint(p[7], 0)
    elif st[2] > 0:
        # v0.3 and older kept one net figure a month: income if positive
        st[6] = st[2]
        st[2] = 0
    else:
        st[2] = 0 - st[2]
    return st


def stage_net(idea, st):
    return st[6] - st[2] - idea.num("fixed", 0)


def save_idea(idea):
    ensure_dir(IDEAS)
    out = ["PROJECTOR-IDEA 1"]
    for k in FIELDS:
        v = idea.f.get(k, "")
        if v != "":
            out.append(k + ": " + v)
    for s in idea.stages:
        out.append("S|{}|{}|{}|{}|{}|{}|{}".format(s[0], s[1], s[2], s[3], s[4], s[5], s[6]))
    for a in idea.assume:
        out.append("A|{}|{}".format(a[0], a[1]))
    for k in idea.faced:
        out.append("F|{}|{}".format(k, idea.faced[k]))
    write_lines(idea.path(), out)


# ---------------------------------------------------------------- engine

def stage_case(st, sc, fixed):
    # [months, net a month, one-time] for one stage in scenario sc: 0 best, 1 likely,
    # 2 worst. The stage's own numbers move with its confidence (costs up and income down
    # in the worst case, each on its own); the fixed cost doesn't, but runs as long.
    m = st[1]
    s = SPREAD[st[3]]
    if sc == 1:
        return [m, st[6] - st[2] - fixed, st[5]]
    if sc == 2:
        extra = 0
        if st[4] == 3:
            extra = HARD_OVERRUN
        m = (m * (100 + s + extra) + 99) // 100
        s = 0 - s
    else:
        m = (m * (100 - s)) // 100
        if m < 1:
            m = 1
    return [m, pct(st[6], 100 + s) - pct(st[2], 100 - s) - fixed, pct(st[5], 100 - s)]


class Proj:
    # Within a stage the balance moves in a straight line after the one-time spend at its
    # start, so per-stage segments are enough: no per-month list (RAM), and the lowest
    # point and the first month below zero are exact.
    def __init__(self, idea, sc):
        b = idea.num("cash", 0)
        fixed = idea.num("fixed", 0)
        self.start = b
        self.starts = []
        self.ends = []
        self.nets = []
        self.sbal = []
        self.low = b
        self.high = b
        self.low_m = 0
        self.out_m = 0
        self.months = 0
        for st in idea.stages:
            b = self.step(stage_case(st, sc, fixed), b)
        self.end = b

    def step(self, r, b):
        m = self.months
        b = b - r[2]
        self.starts.append(m)
        self.sbal.append(b)
        self.nets.append(r[1])
        self.mark(b, m)
        if self.out_m == 0 and b < 0:
            self.out_m = m + 1
        if self.out_m == 0 and r[1] < 0 and b + r[0] * r[1] < 0:
            self.out_m = m + b // (0 - r[1]) + 1
        b = b + r[0] * r[1]
        self.months = m + r[0]
        self.ends.append(self.months)
        self.mark(b, self.months)
        return b

    def mark(self, b, m):
        if b < self.low:
            self.low = b
            self.low_m = m
        if b > self.high:
            self.high = b

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


def can_accept(key):
    # money cracks can also be accepted as a cost worth paying (overlay "accept")
    return key == "out_base" or key == "out_worst" or key == "endbelow"


def fnote(t):
    if len(t) > 0 and t[0] == "=":
        return "Accepted: " + cut(t, 1, len(t))
    return "Faced: " + t


# ---------------------------------------------------------------- app

class App(UI):
    def __init__(self):
        UI.__init__(self)
        self.lib = []          # [id, status, touched, title]
        self.session = 1
        self.next_id = 1
        self.idea = None
        self.dirty = False
        self.sel = 0
        self.lsel = 0          # the library's selection, for place.txt
        self.wide = False      # TERM512 layouts loaded (overlay "wide", App.run)
        self.pv = None         # wide library: the selected idea's preview
        self.ch = 40           # the film's chart height
        if self.H >= 200:
            self.ch = self.bot - self.top - 64

    # ---- plumbing (the rest is UI's, lib/py/base.py)

    def menu(self, spec, fn, args):
        return self.ov("menu", "menu_main", spec, fn, args)

    def switch(self, path):
        return self.ov("apps", "apps_switch", path)

    def ov(self, name, fn, *args):
        # Run fn from overlay ovl/<name>.*: compile it into the globals, call, then delete
        # exactly the names it added, so its code is resident only while it runs.
        G = globals()
        loaded = []
        if not (fn in G):
            loaded = self.ovl_load(name, fn)
            if loaded is None:
                return None
        try:
            return G[fn](self, *args)
        finally:
            for k in loaded:
                del G[k]
            if len(loaded) > 0:
                collect()

    def ovl_load(self, name, fn):
        # compile ovl/<name>.* into the globals; the names it added, or None if it failed or
        # has no fn. Nothing unloads them but the caller (App.ov), so the TERM512 layouts
        # (overlay "wide") stay loaded for the whole run.
        G = globals()
        if self.home == "":
            self.home = find_home()
        if self.home == "":
            self.msg = "Missing ovl/ folder: reinstall"
            return None
        before = {}
        for k in G:
            before[k] = 1
        spare_free()
        collect()
        ok = False
        i = 0
        n_parts = 0
        try:
            # One file per top-level def (tools/ovl.py), read and compiled one at a
            # time: the compiler's working memory grows with what it compiles at once,
            # and no step needs a big contiguous block (a fragmented heap has none).
            base = self.home + "/ovl/" + name + "."
            while File.exist(base + str(i)):
                exec(SD.read(base + str(i)), G)
                i = i + 1
            n_parts = i
            ok = True
        except MemoryError:
            collect()
            g = 0
            if GC is not None:
                g = GC.mem_free() // 1024
            self.msg = "No memory: {} {}/{} {}KB {}b".format(name, i, n_parts, g, free_kb())
        except Exception as e:
            self.msg = "Overlay {}: {}".format(name, e)
        loaded = []
        for k in G:
            if not (k in before):
                loaded.append(k)
        before = None
        if not ok or not (fn in G):
            for k in loaded:
                del G[k]
            collect()
            spare_take()
            return None
        # take the spare back now, before the overlay runs: a save it makes needs
        # that contiguous block
        collect()
        spare_take()
        return loaded

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
        rec = []
        for e in self.lib:
            if e[1] != "archived":
                rec.append(e)
        rec.sort(key=lambda e: 0 - e[2])
        out = []
        for e in rec:
            if len(out) < 8:
                out.append(e[3] + "|" + str(e[0]))
        out.append("")
        SD.write(RECENT, "\n".join(out))

    def save(self):
        idea = self.idea
        st = idea.get("status")
        if st != "archived":
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
            if self.W >= 300 and self.H >= 200:
                self.wide = self.ovl_load("wide", "wide_strip") is not None
                if self.wide:
                    wide_init(self)
            self.library()
        except Switch:
            pass
        finally:
            self.sp.delete()
            self.sp = None
            Display.fill_screen(self.c_bg)

    def library(self):
        # where you were last time (place.txt), or what another app asked for (open.txt)
        r = self.ov("apps", "apps_start")
        sel = self.lsel
        if r is not None and r[0] == "delete":
            # Home asked first: archive it (Projector's delete), and go back
            self.set_archived(r[1], True)
            self.ov("apps", "apps_home")
            return
        if r is not None and r[0] == "new":
            if self.ov("newidea", "newidea_main"):
                self.work(0)
            self.idea = None
        elif r is not None:
            sel = r[0]
            self.open_idea(sel, r[1])
        while True:
            self.lsel = sel
            if self.wide:
                wide_pv(self, sel)
            k = self.cmd(LIB_KEYS, self.r_library, (sel,))
            if k != "UP" and k != "DOWN":
                self.pv = None          # an idea may change: read it again
            if k == "q" or k == "ESC":
                self.ov("apps", "apps_home")
                return
            if k == "DOWN" and sel < len(self.lib) - 1:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif k == "n" or k == "a":
                if self.ov("newidea", "newidea_main"):
                    sel = 0
                    self.work(0)
                self.idea = None
            elif k == "ENTER" and len(self.lib) > 0:
                self.open_idea(sel, 0)
            elif (k == "x" or k == "d") and len(self.lib) > 0:
                self.archive(sel)

    def open_idea(self, i, at):
        # the strip for library entry i, on stage at
        self.idea = None
        try:
            self.idea = load_idea(self.lib[i][0])
        except MemoryError:
            self.msg = "Out of memory opening it"
        if self.idea is not None:
            self.dirty = False
            self.work(at)
            self.idea = None

    def r_library(self, sel):
        if self.wide:
            wide_library(self, sel)
            return
        self.frame("PROJECTOR", "LIBRARY")
        if len(self.lib) == 0:
            Widget.center_lines(self.sp, [("No ideas yet.", self.c_em),
                                          ("Press n to start one.", self.c_text)])
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
        self.foot(LIB_KEYS)

    def archive(self, sel):
        e = self.lib[sel]
        back = e[1] == "archived"
        q = "Archive '{}'?".format(e[3])
        if back:
            q = "Bring '{}' back?".format(e[3])
        if self.ask_yn("ARCHIVE", q, []):
            self.set_archived(sel, not back)

    def set_archived(self, sel, yes):
        self.idea = load_idea(self.lib[sel][0])
        self.idea.f["status"] = "archived"
        if not yes:
            self.idea.f["status"] = "incubating"
        self.save()
        self.msg = ""
        self.idea = None

    # ---- stages

    def r_form(self, title, labels, sel, hints):
        self.frame(title, "")
        y = self.top + 3
        gap = 2
        if len(labels) > 6:
            gap = 0             # the 7-row stage form only fits close-set
        i = 0
        while i < len(labels):
            self.row(y, labels[i], i == sel)
            y = y + self.lh + gap
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

    def work(self, at):
        idea = self.idea
        self.sel = at
        note = idea.get("note")
        if note != "" and idea.num("touched", self.session) < self.session:
            self.show("WHERE YOU LEFT OFF", idea.get("title"),
                      [(note, self.c_em), ("", self.c_text),
                       ("Any key to pick it back up.", self.c_dim)], [("any", "key")])
        while True:
            spare_take()
            self.refresh()
            if self.sel >= len(idea.stages):
                self.sel = len(idea.stages) - 1
            if self.sel < 0:
                self.sel = 0
            k = self.cmd(STRIP_KEYS, self.r_strip, ())
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
            elif k == "m" or k == "$":
                self.ov("money", "money_main")
            elif k == "?":
                self.ov("menu", "menu_help", STRIP_KEYS)
            elif k == "s":
                self.save()
            elif k == "e" and len(idea.stages) > 0:
                self.ov("edit", "edit_main", self.sel)
            elif k == "n":
                if len(idea.stages) >= MAX_STAGES:
                    self.msg = "7 stages is the limit"
                else:
                    at = self.sel + 1
                    if len(idea.stages) == 0:
                        at = 0
                    self.ov("stage", "stage_add", at, "Name the new stage.")
            elif k == "x" and len(idea.stages) > 0:
                if self.ask_yn("STAGE", "Delete '{}'?".format(idea.stages[self.sel][0]), []):
                    idea.stages.pop(self.sel)
                    self.dirty = True
            elif k == "v":
                self.ov("vision", "vision_main")
            elif k == "a":
                self.ov("assume", "assume_main")
            elif k == "o":
                self.premortem()
            elif k == "w" or k == "b":
                # the idea's notes in Writer, or its money as a sheet in Calc (step 5.2)
                fn = "apps_notes"
                if k == "b":
                    fn = "apps_sheet"
                if self.ov("apps", fn):
                    raise Switch()

    def leave(self):
        if not self.dirty:
            return True
        r = self.ask_yn("LEAVING", "Save your changes?", [])
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
        if self.wide:
            wide_strip(self, y)
            return
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
            self.t(6, y, "The projection holds.", self.c_em)
        self.foot(STRIP_KEYS)

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
        self.t(x + 3, y + 25, Widget.clip(self.sp, smoney(stage_net(self.idea, st)), w - 6), c)
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

    # ---- play forward: the film (overlay "film")

    def play(self):
        # The film hands back what to open next, so the film and that overlay are never
        # in memory together; then it plays on from the same stage.
        i = 0
        first = True
        while True:
            try:
                r = self.ov("film", "film_main", i, first)
            except MemoryError:
                # App.ov has already unloaded the film; back to the strip, work kept
                collect()
                self.msg = "Out of memory in play: s saves"
                return
            first = False
            if r is None:
                return
            if r[0] == "holds":
                self.ov("holds", "holds_main")
                return
            if r[0] == "cracks":
                self.crack_list()
                return
            i = r[1]
            if r[0] == "edit":
                self.sel = i
                self.ov("edit", "edit_main", i)
            else:
                self.ov("accept", "accept_main", r[2])

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
            k = self.cmd(CRACK_KEYS, self.r_cracks, (sel,))
            if k == "q" or k == "ESC":
                return
            if k == "DOWN" and sel < len(cr) - 1:
                sel = sel + 1
            elif k == "UP" and sel > 0:
                sel = sel - 1
            elif k == "ENTER":
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
            tail = fnote(self.idea.faced[c[0]])
        self.t(6, self.bot - self.lh, Widget.clip(self.sp, tail, self.W - 12), self.c_dim)
        self.foot(CRACK_KEYS)

    def crack_action(self, c):
        opts = ["Change the plan"]
        if not c[2]:
            opts.append("Face it: write an If-Then")
            if can_accept(c[0]):
                opts.append("Accept the cost")
            if c[0] in self.idea.faced:
                opts.append("Open it again")
        r = self.ask_choice("CRACK", c[1], opts, 0)
        if r == 0:
            self.goto_fix(c)
        elif r == 1:
            self.face(c)
        elif r is not None and opts[r] == "Accept the cost":
            self.ov("accept", "accept_main", c[0])
        elif r is not None:
            self.idea.faced.pop(c[0])
            self.dirty = True

    def goto_fix(self, c):
        w = c[3]
        if isinstance(w, int):
            self.sel = w
            self.ov("edit", "edit_main", w)
        elif w == "money":
            self.ov("money", "money_main")
        elif w == "vision":
            self.ov("vision", "vision_main")
        elif w == "assume":
            self.ov("assume", "assume_main")
        elif w == "premortem":
            self.premortem()
        elif w == "stage":
            self.ov("stage", "stage_add", 0, "Name the first stage.")

    def face(self, c):
        v = self.idea.faced.get(c[0], "I will ")
        if len(v) > 0 and v[0] == "=":
            v = "I will "
        v = self.ask_text("FACE IT", "Say it happens: " + c[1] + ". What will you do?",
                          "If it happens, I will ...", v, TEXT_MAX)
        if v is not None and v != "" and v != "I will":
            self.idea.faced[c[0]] = v
            self.dirty = True

    def premortem(self):
        self.ov("obstacle", "obstacle_main")

    # ---- vision

    # ---- the projection holds

App().run()
