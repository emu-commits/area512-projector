# Projector overlay "menu": the menu bar (Tab), and Tab > Help. Drawn over the screen it was
# opened from, from that screen's key table (LIB_KEYS etc., docs/UI.md). It hands back the
# key of the item picked and the screen handles it as if it had been pressed: no second code
# path. Every global name here starts with "menu_".

def menu_main(self, spec, fn, args):
    ms = menu_parse(spec)
    m = menu_apps(self, ms)
    i = 0
    while True:
        self.paint(menu_r, (self, fn, args, ms, m, i))
        k = arrow(self.key())
        n = len(ms[m][1])
        if k == "ESC" or k == "\t":
            return None
        if k == "LEFT" or k == "RIGHT":
            m = menu_step(m, len(ms), k)
            i = 0
        elif k == "UP":
            i = (i + n - 1) % n
        elif k == "DOWN":
            i = (i + 1) % n
        else:
            r = menu_pick(self, spec, ms, m, i, k)
            if r != "":
                return r


def menu_apps(self, ms):
    # the Apps menu, first in the bar as on the Psion, when Home has written a registry.
    # The menu opens on the screen's own first menu: commands are what Tab is mostly for.
    its = []
    for p in reg_read():
        its.append((p[0], p[1]))
    if len(its) == 0:
        return 0
    ms.insert(0, ["Apps", its])
    return 1


def menu_step(m, n, k):
    if k == "LEFT":
        return (m + n - 1) % n
    return (m + 1) % n


def menu_pick(self, spec, ms, m, i, k):
    # "" = not an item, keep the menu open; None = done, nothing to do
    if k == "ENTER":
        k = ms[m][1][i][0]
    elif len(k) != 1 or k == "?":
        return ""
    for mm in ms:
        for it in mm[1]:
            if it[0] == k:
                return menu_run(self, spec, k)
    return ""


def menu_run(self, spec, k):
    if k == "?":
        menu_help(self, spec)
        return None
    if k == "ENT":
        return "ENTER"
    if k >= "1" and k <= "9":
        for p in reg_read():
            if p[0] == k and p[2] != self.home:
                return "@" + p[2]
        return None             # this app: nothing to do
    return k


def menu_parse(spec):
    # [[title, [(key, label), ...]], ...]; Help goes last in the last menu
    ms = []
    for part in spec.split(";"):
        p = part.split("|")
        its = []
        j = 1
        while j < len(p):
            its.append(menu_item(p[j]))
            j = j + 1
        ms.append([p[0], its])
    ms[len(ms) - 1][1].append(("?", "help"))
    return ms


def menu_item(it):
    if it[0] >= "1" and it[0] <= "9":
        it = cut(it, 1, len(it))
    s = it.find(" ")
    return (cut(it, 0, s), cut(it, s + 1, len(it)))


def menu_r(self, fn, args, ms, m, i):
    fn(*args)
    hh = Widget.header_height()
    mx = menu_bar(self, ms, m, hh)
    menu_box(self, ms[m][1], mx, hh + 1, i)
    # Widget.hints draws over what's there: clear the screen's own hints first (on TERM512,
    # its three hint lines)
    fh = self.H - self.bot - 1
    self.sp.fill_rect(0, self.H - fh, self.W, fh, self.c_bg)
    m = self.msg
    self.msg = ""
    hs = [("<>", "menus"), ("ESC", "close")]
    if ms[0][0] == "Apps":                      # Tab then the digit: say so, and show them
        hs.insert(0, ("1-" + ms[0][1][-1][0], "switch app"))
        self.wapps = True
    self.foot(hs)
    self.wapps = False
    self.msg = m


def menu_bar(self, ms, m, hh):
    # the menu titles over the header; returns the x of the open one
    self.sp.fill_rect(0, 0, self.W, hh + 1, self.c_bg)
    self.sp.line(0, hh, self.W - 1, hh, Widget.theme_border())
    x = 5
    mx = 2
    j = 0
    while j < len(ms):
        w = Widget.text_width(self.sp, ms[j][0])
        c = self.c_text
        if j == m:
            self.sp.fill_rect(x - 3, 1, w + 6, hh - 1, self.c_box)
            c = self.c_sel
            mx = x - 3
        self.t(x, 3, ms[j][0], c)
        x = x + w + 12
        j = j + 1
    return mx


def menu_box(self, its, x, y, i):
    w = 0
    for it in its:
        n = len(it[1]) + len(menu_kname(it[0])) + 3
        if n > w:
            w = n
    w = w * self.cw + 14
    if x + w > self.W - 2:
        x = self.W - 2 - w
    h = len(its) * self.lh + 4
    self.sp.fill_rect(x, y, w, h, self.c_bg)
    self.sp.rect(x, y, w, h, Widget.theme_border())
    j = 0
    while j < len(its):
        menu_line(self, x, y + 2 + j * self.lh, w, its[j], j == i)
        j = j + 1


def menu_line(self, x, y, w, it, sel):
    c = self.c_text
    if sel:
        self.sp.fill_rect(x + 1, y - 1, w - 2, self.lh, self.c_box)
        c = self.c_sel
    lab = it[1]
    self.t(x + 4, y, lab[0].upper() + cut(lab, 1, len(lab)), c)
    Widget.text_right(self.sp, x + w - 6, y, menu_kname(it[0]), self.c_em)


def menu_kname(k):
    if k == "?":
        return ""
    return k


def menu_help(self, spec):
    # generated from the key table, so it can't drift from the menus and the hint bar
    body = []
    for mm in menu_parse(spec):
        s = mm[0] + ":"
        for it in mm[1]:
            if it[0] != "?":
                s = menu_add(self, body, s, it[0] + " " + it[1])
        body.append((s, self.c_text))
    body.append(("Arrows: ; . , /  ESC back  Tab menu", self.c_dim))
    self.show("KEYS", "", body, [("any", "key")])


def menu_add(self, body, s, pair):
    # a key and its label never split over two lines
    if len(s) + 2 + len(pair) > self.cols:
        body.append((s, self.c_text))
        s = "  "
    return s + "  " + pair
