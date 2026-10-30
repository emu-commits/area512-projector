# Projector overlay "wide": the TERM512 layouts (320x240). Loaded once at start when the
# screen is that big (App.run) and never unloaded, so the Cardputer, where memory is short,
# never holds it. Every global name here starts with "wide_". The screens keep their keys
# and key tables: a wide layout shows more, never something different (docs/UI.md).

def wide_strip(self, y):
    # below the stage cells: a taller cash chart, both money lines, and the cracks listed
    if len(self.idea.stages) > 0:
        self.r_spark(4, y, self.W - 8, 40)
        y = wide_money(self, y + 44)
    wide_cracks(self, y)
    self.foot(STRIP_KEYS)


def wide_money(self, y):
    pl = self.pl
    pw = self.pw
    self.t(6, y, "likely: {} mo, ends {}, low {}".format(pl.months, money(pl.end),
                                                         money(pl.low)), self.c_text)
    s = "worst:  {} mo, ends {}, low {}".format(pw.months, money(pw.end), money(pw.low))
    if pw.out_m > 0:
        s = s + ", out M{}".format(pw.out_m)
    self.t(6, y + self.lh, Widget.clip(self.sp, s, self.W - 12), self.c_dim)
    y = y + 2 * self.lh + 2
    Widget.separator(self.sp, y)
    return y + 4


def wide_cracks(self, y):
    # the open cracks first, then the faced ones, as many as fit
    idea = self.idea
    room = (self.bot - y - 2) // self.lh
    n = 0
    for c in self.cr:
        if n < room and is_open(idea, c):
            self.t(6, y + n * self.lh, Widget.clip(self.sp, "! " + c[1], self.W - 12), self.c_sel)
            n = n + 1
    if n == 0 and len(idea.stages) > 0:
        self.t(6, y, "The projection holds.", self.c_em)
        n = 1
    for c in self.cr:
        if n < room and not is_open(idea, c):
            self.t(6, y + n * self.lh, Widget.clip(self.sp, "~ " + c[1], self.W - 12), self.c_dim)
            n = n + 1


def wide_library(self, sel):
    # the list on the left, the selected idea on the right
    self.frame("PROJECTOR", "LIBRARY")
    if len(self.lib) == 0:
        Widget.center_lines(self.sp, [("No ideas yet.", self.c_em),
                                      ("Press n to start one.", self.c_text)])
        self.foot(LIB_KEYS)
        return
    lw = (self.W * 11) // 20
    wide_rows(self, sel, lw)
    Widget.vseparator(self.sp, lw + 2, self.top, self.bot - self.top)
    wide_pane(self, lw + 8, (self.W - lw - 12) // self.cw)
    self.foot(LIB_KEYS)


def wide_rows(self, sel, lw):
    rows = self.visible_rows()
    top = self.list_top(sel, len(self.lib), rows)
    i = top
    while i < len(self.lib) and i < top + rows:
        wide_row(self, self.top + 3 + (i - top) * self.lh, self.lib[i], i == sel, lw)
        i = i + 1


def wide_row(self, y, e, selected, lw):
    # the title clipped short of its status tag
    tag = TAG.get(e[1], "?")
    c = self.c_text
    if selected:
        self.sp.fill_rect(2, y - 1, lw - 4, self.lh, self.c_box)
        c = self.c_sel
    w = lw - 18 - Widget.text_width(self.sp, tag)
    self.t(6, y, Widget.clip(self.sp, e[3], w), c)
    Widget.text_right(self.sp, lw - 4, y, tag, self.c_em)


def wide_pane(self, x, cols):
    pv = self.pv
    if pv is None:
        return
    y = self.lines(x, self.top + 3, pv[1], cols, 4, self.c_em) + 4
    j = 2
    while j < len(pv) and y < self.bot - self.lh:
        c = self.c_text
        if j == 4:
            c = self.c_sel
        if j == 5:
            c = self.c_dim
        y = self.lines(x, y, pv[j], cols, 3, c) + 2
        j = j + 1


def wide_pv(self, sel):
    # read the selected idea once per move: [id, wish, plan, money, cracks, note]
    if len(self.lib) == 0:
        self.pv = None
        return
    iid = self.lib[sel][0]
    if self.pv is not None and self.pv[0] == iid:
        return
    self.pv = None
    try:
        idea = load_idea(iid)
        pl = Proj(idea, 1)
        self.pv = wide_pv2(idea, iid, pl, Proj(idea, 2))
    except MemoryError:
        self.pv = None


def wide_pv2(idea, iid, pl, pw):
    n = 0
    for c in find_cracks(idea, pl, pw):
        if is_open(idea, c):
            n = n + 1
    w = idea.get("wish")
    if w == "":
        w = idea.get("title")
    out = [iid, w, "{} stages, {} months".format(len(idea.stages), pl.months),
           "likely ends {}, low {}".format(money(pl.end), money(pl.low)),
           "{} cracks open".format(n)]
    if n == 0 and len(idea.stages) > 0:
        out[4] = "It holds."
    if idea.get("note") != "":
        out.append("Left off: " + idea.get("note"))
    return out


# ---- the bottom of the screen on TERM512 (step 5.1): two hint lines with every key of the
# screen's table, and the app row, as lib/ruby/ui.rb does for the Ruby apps

def wide_init(self):
    self.bot = self.bot - 28
    self.wfoot = wide_foot
    self.wrow = None
    self.wapps = False         # under the menu bar: two hint lines and the app row


def wide_foot(self, hints):
    if isinstance(hints, str):
        if not (self.hl_spec is hints):
            self.hl = wide_hints(hints)
            self.hl_spec = hints
        hints = self.hl
    y = self.H - 42
    self.sp.line(0, y, self.W - 1, y, Widget.theme_border())
    if self.msg != "":
        self.t(3, y + 2, Widget.clip(self.sp, self.msg, self.W - 6), self.c_em)
    else:
        wide_lines(self, hints, y + 2, 1 if self.wapps else 2)
    if self.wapps:
        wide_apps(self)


def wide_lines(self, hints, y, last):
    x = 3
    ln = 0
    for h in hints:
        w = (len(h[0]) + len(h[1]) + 4) * self.cw
        if x + w > self.W - 3 and x > 3:
            ln = ln + 1
            x = 3
        if ln > last:
            break
        self.t(x, y + ln * self.lh, "[" + h[0] + "]", self.c_em)
        self.t(x + (len(h[0]) + 3) * self.cw, y + ln * self.lh, h[1], self.c_text)
        x = x + w


def wide_hints(spec):
    # every item: the numbered ones in order, then the rest, then [Tab] menu
    out = []
    rest = []
    for it in spec.replace(";", "|").split("|"):
        sp = it.find(" ")
        if sp > 0 and it[0] >= "1" and it[0] <= "9":
            out.append(it)
        elif sp > 0:
            rest.append((cut(it, 0, sp), cut(it, sp + 1, len(it))))
    out.sort()
    for i in range(len(out)):
        sp = out[i].find(" ")
        out[i] = (cut(out[i], 1, sp), cut(out[i], sp + 1, len(out[i])))
    return out + rest + [("Tab", "menu")]


def wide_apps(self):
    # "1 Home  2 Projector ...", this app marked, under the menu bar, where Tab then the
    # digit switches; names cut to 4 letters if all don't fit
    if self.wrow is None:
        wide_appsread(self)
    y = self.H - 14
    self.sp.line(0, y, self.W - 1, y, Widget.theme_border())
    x = 3
    for p in self.wrow:
        name = cut(p[1], 0, self.wcut)
        w = (len(name) + 3) * self.cw
        if x + w - self.cw <= self.W:
            c = self.c_text
            if p[1] == "Projector":
                self.sp.fill_rect(x - 2, y + 1, w - self.cw + 3, 13, self.c_box)
                c = self.c_sel
            self.t(x, y + 1, p[0], self.c_em)
            self.t(x + 2 * self.cw, y + 1, name, c)
        x = x + w


def wide_appsread(self):
    self.wrow = reg_read()
    n = 0
    for p in self.wrow:
        n = n + len(p[1]) + 3
    self.wcut = 9
    if n * self.cw > self.W - 3:
        self.wcut = 4
