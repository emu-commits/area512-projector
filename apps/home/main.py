# HOME - the suite's System screen, after the Psion Series 3 (docs/PLAN_V1.md, Home): a row of
# app icons, and under the selected icon that app's files. It finds the apps on the card,
# writes the registry every app reads, and opens an app, or one of its files, with an open
# request and Area512.run_next (docs/APPS_FORMAT.md). Set it as default=app: in /etc/ui to
# make it the first screen. lib/py/base.py and lib/py/menu.py are put in front of this file.

PLACE = "/data/home/place.txt"
OPEN = "/data/area512/open.txt"
# The suite, in Home's order: name, then the folders it may be installed as. A fork wins
# over a bundled app of the same kind (Agenda over Scheduler), and one in /home/ai over
# one anywhere else.
SUITE = [["Projector", "projector"], ["Writer", "writer"], ["Calc", "calc"],
         ["Agenda", "agenda scheduler"], ["Slide", "slide"]]
MAX_FILES = 8
HOME_KEYS = "App|1ENT open|2n new|3x delete"
EXTRA_KEYS = "App|1ENT open"


def app_dirs():
    # every app folder on the card, /home/<group>/<app> with a main.manifest: [[name, path]]
    found = []
    top = None
    try:
        top = Dir("/home")
        a = top.read()
        while a is not None:
            if a[0] != "." and File.directory("/home/" + a):
                sub_dirs(found, "/home/" + a)
            a = top.read()
    except Exception:
        pass
    if top is not None:
        top.close()
    return found


def sub_dirs(found, base):
    sub = Dir(base)
    try:
        b = sub.read()
        while b is not None:
            if b[0] != "." and File.exist(base + "/" + b + "/main.manifest"):
                found.append([b, base + "/" + b])
            b = sub.read()
    finally:
        sub.close()


def pick(found, names):
    # the folder for one suite app: the first name that's installed, /home/ai first
    for n in names.split(" "):
        best = None
        for e in found:
            if e[0] == n and (best is None or e[1].find("/home/ai/") == 0):
                best = e
        if best is not None:
            return best
    return None


def title(folder):
    s = folder.replace("_", " ")
    return s[0].upper() + cut(s, 1, len(s))


class Home(UI):
    def __init__(self):
        UI.__init__(self)
        self.icons = []        # [name, key, path, files, digit]; files are [title, file]
        self.dots = {}         # key -> Dot, or None: a box with the initial
        self.sel = 0
        self.fsel = -1         # -1: the icon itself, else a row of its files
        self.wide = self.W >= 300 and self.H >= 200
        self.slots = 5
        if self.wide:
            self.slots = 6

    def menu(self, spec, fn, args):
        return menu_main(self, spec, fn, args)

    def switch(self, path):
        # the Apps menu (Tab, then a digit): open that app
        self.go(path, "")
        return True

    # ---- finding the apps

    def find(self):
        found = app_dirs()
        for e in found:
            if File.exist(e[1] + "/icons/extras.a5d"):
                self.home = e[1]
                found.remove(e)
                break
        d = 2
        for s in SUITE:
            e = pick(found, s[1])
            if e is not None:
                found.remove(e)
                k = s[0].lower()
                self.icons.append([s[0], k, e[1], self.recent(k), str(d)])
                d = d + 1
        found.sort(key=lambda e: e[0])
        ex = []
        for e in found:
            ex.append([title(e[0]), e[1]])
        ex.append(["Files", ""])          # leave to the filer
        self.icons.append(["Extras", "extras", "", ex, str(d)])

    def recent(self, key):
        # the app's recent.txt: "title|file", newest first (docs/APPS_FORMAT.md)
        out = []
        p = "/data/" + key + "/recent.txt"
        if File.exist(p):
            for line in read_lines(p):
                f = line.split("|")
                if len(f) == 2 and f[1] != "" and len(out) < MAX_FILES:
                    out.append(f)
        return out

    def write_reg(self):
        # the registry, rewritten only when an app was added or moved
        out = []
        if self.home != "":
            out.append("1|Home|" + self.home)
        for ic in self.icons:
            if ic[2] != "":
                out.append(ic[4] + "|" + ic[0] + "|" + ic[2])
        out.append("")
        s = "\n".join(out)
        if not File.exist(REG) or SD.read(REG) != s:
            ensure_dir("/data/area512")
            SD.write(REG, s)

    def load_dots(self):
        for ic in self.icons:
            d = None
            if self.home != "":
                try:
                    d = Dot.load(self.home + "/icons/" + ic[1] + ".a5d")
                except Exception:
                    d = None
            self.dots[ic[1]] = d

    def place(self):
        # where you were when you left Home: the icon (by app) and the file row
        if not File.exist(PLACE):
            return
        f = {}
        for line in read_lines(PLACE):
            kv = line.split(": ", 1)
            if len(kv) == 2:
                f[kv[0]] = kv[1]
        File.unlink(PLACE)
        i = 0
        while i < len(self.icons):
            if self.icons[i][1] == f.get("app", ""):
                self.sel = i
                n = toint(f.get("file", ""), -1)
                if n < len(self.icons[i][3]):
                    self.fsel = n
            i = i + 1

    # ---- the screen

    def run(self):
        Display.fill_screen(self.c_bg)
        self.sp = BandedSprite(12)
        try:
            ensure_dir("/data")
            ensure_dir("/data/home")
            if File.exist(OPEN):
                File.unlink(OPEN)       # back at Home: a request no app took is stale
            self.find()
            self.write_reg()
            self.load_dots()
            self.place()
            self.main()
        except Switch:
            pass
        finally:
            self.sp.delete()
            self.sp = None
            self.dots = None
            Display.fill_screen(self.c_bg)

    def main(self):
        while True:
            ic = self.icons[self.sel]
            keys = HOME_KEYS
            if ic[2] == "":
                keys = EXTRA_KEYS
            k = self.cmd(keys, self.r_home, ())
            n = len(ic[3])
            if k == "ESC" or k == "q":
                return
            if k == "LEFT" and self.sel > 0:
                self.sel = self.sel - 1
                self.fsel = -1
            elif k == "RIGHT" and self.sel < len(self.icons) - 1:
                self.sel = self.sel + 1
                self.fsel = -1
            elif k == "UP" and self.fsel >= 0:
                self.fsel = self.fsel - 1
            elif k == "DOWN" and self.fsel < n - 1:
                self.fsel = self.fsel + 1
            elif len(k) == 1 and k >= "1" and k <= "9":
                self.jump(k)
            elif k == "ENTER":
                self.open(ic)
            elif k == "n" and ic[2] != "":
                self.go(ic[2], ic[1] + "|new|")
            elif k == "x" and ic[2] != "" and self.fsel >= 0:
                self.delete(ic)

    def jump(self, d):
        i = 0
        while i < len(self.icons):
            if self.icons[i][4] == d:
                self.sel = i
                self.fsel = -1
            i = i + 1

    def open(self, ic):
        if ic[2] == "":
            # Extras: its apps are listed like files
            if self.fsel < 0:
                self.fsel = 0
            elif ic[3][self.fsel][1] == "":
                raise Switch()          # Files: back to the filer
            else:
                self.go(ic[3][self.fsel][1], "")
        elif self.fsel < 0:
            self.go(ic[2], "")
        else:
            self.go(ic[2], ic[1] + "|open|" + ic[3][self.fsel][1])

    def delete(self, ic):
        f = ic[3][self.fsel]
        if self.ask_yn("DELETE", "Delete '{}'?".format(f[0]), [ic[0] + " opens to do it, then comes back."]):
            self.go(ic[2], ic[1] + "|delete|" + f[1])

    def go(self, path, req):
        # leave a place, the open request if any, and have the filer run path
        ic = self.icons[self.sel]
        try:
            SD.write(PLACE, "app: {}\nfile: {}\n".format(ic[1], self.fsel))
            if req != "":
                SD.write(OPEN, req + "\n")
            Area512.run_next(path)
        except Exception:
            self.msg = "Can't switch: needs AREA512 after v2.7"
            return
        raise Switch()

    def r_home(self):
        self.frame("AREA512", "")
        # fewer icons than slots: wider slots (names and files clip less), centred
        n = len(self.icons)
        if n > self.slots:
            n = self.slots
        sw = self.W // self.slots
        if n >= 5:
            sw = self.W // n
        x0 = (self.W - n * sw) // 2
        first = self.sel - self.slots + 1
        if first < 0:
            first = 0
        y = self.top + 3
        j = 0
        while j < n and first + j < len(self.icons):
            self.r_icon(x0 + j * sw, y, sw, first + j)
            j = j + 1
        if first > 0:
            self.t(1, y + 12, "<", self.c_em)
        if first + self.slots < len(self.icons):
            self.t(self.W - 7, y + 12, ">", self.c_em)
        if not self.wide:
            self.r_files(4, self.W - 8, self.icons[self.sel], True)
        ic = self.icons[self.sel]
        keys = HOME_KEYS
        if ic[2] == "":
            keys = EXTRA_KEYS
        self.foot(keys)

    def r_icon(self, x, y, sw, i):
        ic = self.icons[i]
        cx = x + sw // 2
        d = self.dots[ic[1]]
        if d is not None:
            d.push(self.sp, cx - 16, y)
        else:
            self.sp.rect(cx - 15, y + 1, 30, 30, self.c_text)
            self.t(cx - 3, y + 12, ic[0][0], self.c_em)
        sel = i == self.sel
        if sel:
            self.sp.rect(cx - 19, y - 3, 38, 38, Widget.theme_border())
        name = ic[0]
        if len(name) * self.cw > sw - 4:
            name = cut(name, 0, (sw - 4) // self.cw)
        nw = len(name) * self.cw
        ny = y + 36
        if sel and self.fsel < 0:
            self.sp.fill_rect(cx - nw // 2 - 3, ny - 1, nw + 6, self.lh, self.c_box)
            self.t(cx - nw // 2, ny, name, self.c_sel)
        elif sel:
            self.t(cx - nw // 2, ny, name, self.c_em)
        else:
            self.t(cx - nw // 2, ny, name, self.c_text)
        if self.wide:
            self.r_files(x + 2, sw - 2, ic, sel)

    def r_files(self, x, w, ic, sel):
        # the app's files under its icon: one list on the Cardputer, a column on TERM512
        y = self.top + 3 + 36 + self.lh + 1
        rows = (self.bot - y - 2) // self.lh
        fs = ic[3]
        if len(fs) == 0 and not self.wide:
            self.t(x + 2, y, "No files yet: n starts one.", self.c_dim)
            return
        top = 0
        if sel:
            top = self.list_top(self.fsel, len(fs), rows)
        i = top
        while i < len(fs) and i < top + rows:
            t = fs[i][0]
            if len(t) * self.cw > w - 6:
                t = cut(t, 0, (w - 6) // self.cw)
            if sel and i == self.fsel:
                self.sp.fill_rect(x, y - 1, w - 2, self.lh, self.c_box)
                self.t(x + 2, y, t, self.c_sel)
            else:
                self.t(x + 2, y, t, self.c_text)
            y = y + self.lh
            i = i + 1


Home().run()
