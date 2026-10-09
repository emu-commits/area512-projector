# Projector overlay "edit": the stage editor form. Every global name here starts with
# "edit_"; defs stay small (the device compiles one def at a time).

def edit_main(self, i):
    st = self.idea.stages[i]
    sel = 0
    while True:
        self.paint(self.r_form, ("STAGE {}".format(i + 1), edit_labels(st), sel,
                                 [("ENT", "edit")] + edit_hint(sel) + [("ESC", "done")]))
        k = self.nav(self.key())
        if k == "ESC" or k == "q":
            return
        if k == "DOWN" and sel < 4:
            sel = sel + 1
        elif k == "UP" and sel > 0:
            sel = sel - 1
        else:
            edit_key(self, st, sel, k)


def edit_hint(sel):
    if sel >= 3:
        return [("1-3", "set")]
    return []


def edit_labels(st):
    return ["Name     " + st[0], "Months   {}".format(st[1]), "Monthly  " + smoney(st[2]),
            "Sure?    " + CONF[st[3]], "Hard?    " + DIFF[st[4]]]


def edit_key(self, st, sel, k):
    v = None
    if sel >= 3 and (k == "1" or k == "2" or k == "3"):
        v = ord(k) - ord("0")
    elif k == "ENTER" and sel < 3:
        v = edit_value(self, st, sel)
    elif k == "ENTER":
        v = edit_level(self, st, sel)
    if v is not None:
        st[sel] = v
        self.dirty = True


def edit_value(self, st, sel):
    if sel == 0:
        v = self.ask_text("STAGE", "Stage name?", "", st[0], 12)
        if v == "":
            return None
        return v
    if sel == 1:
        return self.ask_number("STAGE", "Months for '{}'?".format(st[0]), "", st[1], 1, 120)
    return self.ask_number("STAGE", "Money each month in '{}'?".format(st[0]),
                           "Spending negative, income positive.", st[2], -9999999, 9999999)


def edit_level(self, st, sel):
    if sel == 3:
        v = self.ask_choice("STAGE", "How sure are you?",
                            ["sure", "rough idea", "a guess"], st[3] - 1)
    else:
        v = self.ask_choice("STAGE", "How hard?", ["easy", "medium", "hard"], st[4] - 1)
    if v is None:
        return None
    return v + 1
