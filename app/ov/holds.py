# Projector overlay "holds": the projection-holds replay, your picture and why, and the
# judgment. Every global
# name here starts with "holds_"; defs stay small (the device compiles one def at a time).

def holds_main(self):
    frames = 24
    f = 0
    while f <= frames:
        self.paint(holds_anim, (self, f, frames))
        sleep_ms(60)
        f = f + 1
    holds_picture(self)
    if self.idea.get("fruit") == "":
        holds_judge(self)


def holds_picture(self):
    idea = self.idea
    self.show("IT HOLDS", "month {}".format(self.pl.months), [
        (idea.get("picture"), self.c_em), ("", self.c_text),
        ("Because: " + idea.get("why"), self.c_text), ("", self.c_text),
        ("You faced {} crack(s) to get here.".format(len(idea.faced)), self.c_dim)],
        [("any", "key")])


def holds_anim(self, f, frames):
    pl = self.pl
    self.frame("PROJECTOR", "playing")
    w = self.W - 12
    y = self.top + 30
    self.sp.rect(6, y, w, 12, Widget.theme_border())
    self.sp.fill_rect(6, y, (w * f) // frames, 12, self.c_em)
    for e in pl.ends:
        self.sp.line(6 + (w * e) // pl.months, y - 3, 6 + (w * e) // pl.months, y + 14,
                     self.c_text)
    holds_label(self, (pl.months * f) // frames, y - 18)
    if f >= frames:
        Widget.text_center(self.sp, y + 30, "THE PROJECTION HOLDS", self.c_sel)
    Widget.footer(self.sp, "")


def holds_label(self, month, y):
    cur = 0
    if month > 0:
        cur = self.pl.stage_at(month)
    self.t(6, y, "Month {}".format(month), self.c_text)
    Widget.text_right(self.sp, self.W - 6, y, self.idea.stages[cur][0], self.c_em)


def holds_judge(self):
    if not holds_pick(self, "fruit", "How fruitful could this be?",
                      ["barely", "a little", "worthwhile", "a lot", "life-changing"], 2):
        return
    holds_pick(self, "feel", "How will the time feel?", ["quick", "moderate", "dragged out"], 1)
    holds_pick(self, "effort", "How hard, overall?", ["easy", "medium", "hard"], 1)
    v = self.ask_text("JUDGMENT", "Is it worth it? Say why in a line.", "",
                      self.idea.get("worth"), TEXT_MAX)
    if v is not None:
        self.idea.f["worth"] = v


def holds_pick(self, key, q, opts, cur):
    r = self.ask_choice("JUDGMENT", q, opts, cur)
    if r is None:
        return False
    self.idea.f[key] = str(r + 1)
    self.dirty = True
    return True
