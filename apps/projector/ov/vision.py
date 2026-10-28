# Projector overlay "vision": compiled from the SD card when entered, unloaded on exit
# (App.ov). Every global name here starts with "vision_".

def vision_main(self):
    sel = 0
    while True:
        self.paint(self.r_form, ("VISION", vision_labels(self.idea), sel,
                                 [("ENT", "edit"), ("ESC", "back")]))
        k = self.nav(self.key())
        if k == "q" or k == "ESC":
            return
        if k == "DOWN" and sel < 5:
            sel = sel + 1
        elif k == "UP" and sel > 0:
            sel = sel - 1
        elif k == "ENTER":
            vision_edit(self, sel)


def vision_labels(idea):
    names = ["Name", "Wish", "Proof", "Why"]
    keys = ["title", "wish", "picture", "why"]
    out = []
    i = 0
    while i < 4:
        out.append("{:<8}{}".format(names[i], idea.get(keys[i])))
        i = i + 1
    out.append("Window  " + idea.get("window") + " months")
    out.append("Start $ " + money(idea.num("cash", 0)))
    return out


def vision_edit(self, sel):
    if sel == 4:
        vision_window(self)
    elif sel == 5:
        v = self.ask_number("VISION", "Money you can put toward this now?", "",
                            self.idea.num("cash", 0), 0, 99999999)
        if v is not None:
            self.idea.f["cash"] = str(v)
            self.dirty = True
    else:
        vision_text(self, sel)


def vision_window(self):
    cur = 3
    j = 0
    while j < len(WINDOWS):
        if WINDOWS[j] == self.idea.num("window", 36):
            cur = j
        j = j + 1
    w = self.ask_choice("VISION", "How far ahead should we look?", WINDOW_NAMES, cur)
    if w is not None:
        self.idea.f["window"] = str(WINDOWS[w])
        self.dirty = True


def vision_text(self, sel):
    key = ["title", "wish", "picture", "why"][sel]
    q = ["Short name for the idea?", "What are you trying to make happen?",
         "Picture it working. What proves it? Add a number.",
         "Why does this matter to you?"][sel]
    mx = TEXT_MAX
    if sel == 0:
        mx = 24
    v = self.ask_text("VISION", q, "", self.idea.get(key), mx)
    if v is not None and (v != "" or sel != 0):
        self.idea.f[key] = v
        self.dirty = True
