# Projector overlay "film": play forward. Each stage runs month by month on a chart; an
# open money or window crack FREEZES the film at its month. Every global name here starts
# with "film_". The film never opens another overlay itself (memory: with a big idea there is
# no room for two): it returns [action, stage] and App.play opens it, then plays on from there.
# Measured on a real Cardputer: ~23 frames a second, so no sleep between frames.

film_H = [40]        # the chart's height: App.ch, taller on TERM512


def film_main(self, i, first):
    film_H[0] = self.ch
    if len(self.idea.stages) == 0:
        self.msg = "Add a stage first (n)"
        return None
    k = None
    if first:
        self.idea.f["runs"] = str(self.idea.num("runs", 0) + 1)
        self.dirty = True
        self.refresh()
        k = film_run(self, 0)
    return film_loop(self, i, k)


def film_loop(self, i, k):
    n = len(self.idea.stages)
    while True:
        self.refresh()
        if i >= n:
            r = film_end(self)
            if r != "back":
                return r
            i = n - 1
            k = None
        if k is None:
            self.paint(film_r_stage, (self, i))
            self.msg = ""
            k = self.nav(self.key())
        r = film_act(self, k, i)
        k = None
        if not isinstance(r, int):
            return r
        if r > i and r < n:
            k = film_run(self, r)
        i = r


def film_act(self, k, i):
    if k == "q" or k == "ESC":
        return None
    if k == "RIGHT" or k == "ENTER" or k == " ":
        return i + 1
    if k == "LEFT" and i > 0:
        return i - 1
    if k == "e":
        return ["edit", i]
    c = film_crack(self, i)
    if c is None:
        return i
    if k == "f":
        self.face(c)
    elif k == "a" and can_accept(c[0]):
        return ["accept", i, c[0]]
    return i


def film_crack(self, i):
    # the open crack that freezes stage i, or else its first open crack you can face
    c = film_stopper(self, i)
    if c is not None:
        return c
    for c in self.cr:
        if c[3] == i and is_open(self.idea, c) and not c[2]:
            return c
    return None


def film_stopper(self, i):
    for c in self.cr:
        if c[3] == i and is_open(self.idea, c) and film_month(self, c) > 0:
            return c
    return None


def film_month(self, c):
    if c[0] == "out_base":
        return self.pl.out_m
    if c[0] == "out_worst":
        return self.pw.out_m
    if c[0] == "horizon":
        return self.idea.num("window", 36) + 1
    return 0


def film_run(self, i):
    # animate stage i; a key ends it early and is handed back; a stopper freezes it
    a = self.pl.starts[i]
    b = self.pl.ends[i]
    c = film_stopper(self, i)
    if c is not None:
        b = film_month(self, c)
        if b > self.pl.ends[i]:
            b = self.pl.ends[i]
        if b < a:
            b = a
    k = film_anim(self, i, a, b, c is not None)
    if k is None and c is not None:
        return film_freeze(self, i, b, c)
    return k


def film_anim(self, i, a, b, slow):
    steps = b - a
    if steps > 14:
        steps = 14
    if steps < 6:
        steps = 6
    self.console.raw()
    try:
        f = 0
        while f <= steps:
            self.paint(film_r_run, (self, i, a + ((b - a) * f) // steps))
            k = film_poll(self)
            if k is not None:
                film_drain(self)
                return k
            if slow:
                sleep_ms((f * f * 5) // steps)
            f = f + 1
    finally:
        self.console._restore_termios()
    return None


def film_poll(self):
    # raw bytes: ENTER is 13, ESC alone is 27, an arrow is 27 '[' A/B/C/D
    k = self.console.read_nonblock(1)
    if k is None:
        return None
    if k == "\r" or k == "\n":
        return "ENTER"
    if k != "\x1b":
        return self.nav(k)
    if self.console.read_nonblock(1) != "[":
        return "ESC"
    k = self.console.read_nonblock(1)
    if k == "C":
        return "RIGHT"
    if k == "D":
        return "LEFT"
    return "ESC"


def film_drain(self):
    while self.console.read_nonblock(1) is not None:
        pass


def film_freeze(self, i, m, c):
    k = "%"
    while k == "%":
        self.paint(film_r_freeze, (self, i, m, c))
        self.msg = ""
        k = self.nav(self.key())
    if k == "f":
        self.face(c)
        return None
    return k


def film_chart(self, y, m):
    lo = self.pw.low
    if lo > 0:
        lo = 0
    hi = self.pl.high
    if self.pb.high > hi:
        hi = self.pb.high
    sp = hi - lo
    if sp < 1:
        sp = 1
    z = film_y(0, (y, lo, sp))
    self.sp.line(6, z, self.W - 7, z, self.c_dim)
    film_line(self, self.pw, y, m, lo, sp, self.c_dim, 0)
    film_line(self, self.pl, y, m, lo, sp, self.c_em, 1)


def film_line(self, p, y, m, lo, sp, c, thick):
    tot = self.pl.months
    j = 0
    while j < len(p.starts) and p.starts[j] < m and p.starts[j] < tot:
        b = p.ends[j]
        if b > m:
            b = m
        if b > tot:
            b = tot
        film_seg(self, p, j, b, (y, lo, sp, c, thick))
        j = j + 1


def film_seg(self, p, j, b, g):
    # one stage: a drop for its one-time spend, then a straight line
    w = self.W - 12
    a = p.starts[j]
    x0 = 6 + (a * w) // self.pl.months
    x1 = 6 + (b * w) // self.pl.months
    y0 = film_y(p.bal(a), g)
    y1 = film_y(p.sbal[j], g)
    y2 = film_y(p.sbal[j] + (b - a) * p.nets[j], g)
    self.sp.line(x0, y0, x0, y1, g[3])
    self.sp.line(x0, y1, x1, y2, g[3])
    self.sp.line(x0, y1 + g[4], x1, y2 + g[4], g[3])


def film_y(v, g):
    return g[0] + film_H[0] - ((v - g[1]) * film_H[0]) // g[2]


def film_head(self, i, m):
    st = self.idea.stages[i]
    self.frame("PLAY  run " + self.idea.get("runs"), "MONTH {}".format(m))
    y = self.top + 3
    Widget.big_text(self.sp, 6, y, Widget.clip(self.sp, st[0].upper(), 120))
    Widget.text_right(self.sp, self.W - 6, y + 4, "{}, {}".format(DIFF[st[4]], CONF[st[3]]),
                      self.c_dim)
    film_chart(self, y + 24, m)
    return y + 30 + film_H[0]


def film_r_run(self, i, m):
    y = film_head(self, i, m)
    self.t(6, y, "Cash: {}   worst {}".format(money(self.pl.bal(m)), money(self.pw.bal(m))),
           self.c_text)
    Widget.footer(self.sp, "any key: skip")


def film_r_freeze(self, i, m, c):
    y = film_head(self, i, m)
    h = self.bot - self.top
    self.sp.rect(0, self.top, self.W, h, self.c_sel)
    self.sp.rect(1, self.top + 1, self.W - 2, h - 2, self.c_sel)
    self.t(6, y, Widget.clip(self.sp, "BREAKS: " + c[1], self.W - 12), self.c_sel)
    if can_accept(c[0]):
        self.foot([("f", "face"), ("a", "accept"), ("e", "fix"), ("l", "on")])
    else:
        self.foot([("f", "face"), ("e", "fix"), ("l", "on")])


def film_r_stage(self, i):
    y = film_head(self, i, self.pl.ends[i])
    c = film_crack(self, i)
    s = "Cash after: {}   worst {}".format(money(self.pl.bal(self.pl.ends[i])),
                                          money(self.pw.bal(self.pw.ends[i])))
    col = self.c_text
    if c is not None:
        s = "! " + c[1]
        col = self.c_sel
    self.t(6, y, Widget.clip(self.sp, s, self.W - 12), col)
    self.foot([("l", "next"), ("h", "back"), ("e", "edit"), ("f", "face")])


def film_end(self):
    while True:
        self.paint(film_r_end, (self,))
        self.msg = ""
        k = self.nav(self.key())
        if k == "q" or k == "ESC":
            return None
        if k == "LEFT":
            return "back"
        if k == "ENTER" or k == "RIGHT":
            if self.n_open == 0:
                return ["holds", 0]
            return ["cracks", 0]


def film_r_end(self):
    idea = self.idea
    self.frame("PLAY  run " + idea.get("runs"), "MONTH {}".format(self.pl.months))
    y = self.top + 3
    pic = idea.get("picture")
    if pic == "":
        pic = idea.get("wish")
    self.t(6, y, "Month {}. You're there:".format(self.pl.months), self.c_dim)
    y = self.lines(6, y + self.lh, pic, self.cols, 3, self.c_em) + 4
    film_r_end2(self, y)


def film_r_end2(self, y):
    if self.n_open == 0:
        self.t(6, y, "Nothing left unanswered.", self.c_text)
        self.t(6, y + self.lh, "ENTER: watch it hold", self.c_sel)
    else:
        self.t(6, y, "But {} crack(s) on the way.".format(self.n_open), self.c_sel)
        self.t(6, y + self.lh, "ENTER: look at them", self.c_text)
    self.foot([("ENT", "go on"), ("h", "back"), ("q", "stop")])
