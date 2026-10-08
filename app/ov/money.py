# Projector overlay "money": compiled from the SD card when entered, unloaded on exit
# (App.ov). Every global name here starts with "money_".

def money_main(self):
    sc = 1
    while True:
        self.refresh()
        self.paint(money_r, (self, sc,))
        k = self.nav(self.key())
        if k == "q" or k == "ESC":
            return
        if k == "s" or k == "RIGHT":
            sc = (sc + 1) % 3
        elif k == "LEFT":
            sc = (sc + 2) % 3
        elif k == "e":
            v = self.ask_number("MONEY", "Money you can put toward this now?", "",
                                self.idea.num("cash", 0), 0, 99999999)
            if v is not None:
                self.idea.f["cash"] = str(v)
                self.dirty = True


def money_r(self, sc):
    self.frame("MONEY", "start " + money(self.idea.num("cash", 0)))
    ps = [self.pb, self.pl, self.pw]
    money_table(self, ps, sc)
    y = self.top + 16 + 14 * 3 + 3
    self.t(6, y, "{}: {} months".format(SCEN[sc], ps[sc].months), self.c_dim)
    money_chart(self, ps[sc], y + self.lh)
    self.foot([("s", "case"), ("e", "start $"), ("ESC", "back")])


def money_table(self, ps, sc):
    widths = [52, 62, 52, 62]
    Widget.table_header(self.sp, 4, self.top + 2, widths, ["case", "lowest", "out", "end"])
    i = 0
    while i < 3:
        Widget.table_row(self.sp, 4, self.top + 16 + 14 * i, widths, money_row(ps[i], i),
                         i == sc)
        i = i + 1


def money_row(p, i):
    out = "-"
    if p.out_m > 0:
        out = "M{}".format(p.out_m)
    return [SCEN[i], money(p.low), out, money(p.end)]


def money_chart(self, p, y):
    lo = p.low
    if lo > 0:
        lo = 0
    vals = []
    hi = 1
    j = 0
    while j < 40:
        v = p.bal((j * p.months) // 39) - lo
        vals.append(v)
        if v > hi:
            hi = v
        j = j + 1
    if self.bot - y - 2 > 8:
        Widget.line_chart(self.sp, 4, y, self.W - 8, self.bot - y - 2, vals, hi)
