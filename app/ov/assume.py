# Projector overlay "assume": the assumptions list. Compiled from the SD card when entered,
# unloaded on exit (App.ov). Every global name here starts with "assume_"; every def stays
# small because the device compiles one def at a time (tools/ovl.py enforces it).

def assume_main(self):
    sel = 0
    while True:
        self.paint(assume_r, (self, sel))
        self.msg = ""
        k = self.nav(self.key())
        n = len(self.idea.assume)
        if k == "q" or k == "ESC":
            return
        if k == "DOWN" and sel < n - 1:
            sel = sel + 1
        elif k == "UP" and sel > 0:
            sel = sel - 1
        else:
            sel = assume_act(self, k, sel, n)


def assume_act(self, k, sel, n):
    if k == "a":
        return assume_add(self, sel, n)
    if n == 0:
        return sel
    a = self.idea.assume[sel]
    if k == "ENTER" or k == " ":
        a[0] = 1 - a[0]
        self.dirty = True
    elif k == "d":
        return assume_del(self, sel)
    elif k == "f" and not a[0]:
        self.face([akey(a[1]), "Unchecked: " + a[1], False, "assume"])
    return sel


def assume_add(self, sel, n):
    if n >= MAX_ASSUME:
        self.msg = "6 is the limit: check or drop one"
        return sel
    v = self.ask_text("ASSUMPTION", "What has to be true for this to work?",
                      "One thing you're counting on.", "", 60)
    if v is None or v == "":
        return sel
    self.idea.assume.append([0, v])
    self.dirty = True
    return len(self.idea.assume) - 1


def assume_del(self, sel):
    if self.ask_yn("ASSUMPTION", "Delete it?", [self.idea.assume[sel][1]]):
        self.idea.assume.pop(sel)
        self.dirty = True
        if sel > 0:
            sel = sel - 1
    return sel


def assume_r(self, sel):
    idea = self.idea
    self.frame("ASSUMPTIONS", "{}".format(len(idea.assume)))
    if len(idea.assume) == 0:
        Widget.center_lines(self.sp, [("What must be true?", self.c_em),
                                      ("a adds one.", self.c_text)])
    assume_rows(self, sel)
    self.foot([("a", "add"), ("ENT", "checked"), ("f", "face"), ("d", "del")])


def assume_rows(self, sel):
    a = self.idea.assume
    rows = self.visible_rows()
    top = self.list_top(sel, len(a), rows)
    i = top
    while i < len(a) and i < top + rows:
        self.row(self.top + 3 + (i - top) * self.lh, assume_line(self.idea, a[i]), i == sel)
        i = i + 1


def assume_line(idea, a):
    if a[0]:
        return "[x] " + a[1]
    if akey(a[1]) in idea.faced:
        return "[~] " + a[1]
    return "[ ] " + a[1]
