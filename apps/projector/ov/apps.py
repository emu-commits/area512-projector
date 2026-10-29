# Projector overlay "apps": switching between the apps of the suite (docs/APPS_FORMAT.md).
# Every global name here starts with "apps_".

apps_PLACE = "/data/projector/place.txt"
apps_OPEN = "/data/area512/open.txt"


def apps_switch(self, path):
    # save, leave a place.txt, and have the filer run path once this app returns.
    # False (and a message) if any of it fails: a switch never loses work.
    if self.idea is not None and self.dirty:
        if not self.save():
            return False
    try:
        apps_place(self)
        Area512.run_next(path)
    except Exception:
        self.msg = "Can't switch: needs AREA512 after v2.7"
        return False
    return True


def apps_place(self):
    if self.idea is not None:
        SD.write(apps_PLACE, "screen: strip\nsel: {}\nfile: {}\n".format(self.sel, self.idea.id))
    else:
        SD.write(apps_PLACE, "screen: library\nsel: {}\n".format(self.lsel))


def apps_home(self):
    # Esc from the library goes to Home, if it's installed
    for p in reg_read():
        if p[1] == "Home" and p[2] != self.home:
            try:
                Area512.run_next(p[2])
            except Exception:
                pass
            return


def apps_start(self):
    # [library index, stage] to open, ["new"], ["delete", library index], or None. Sets
    # self.lsel. Both files are read once and deleted, so a bad one can't trap you.
    r = apps_request(self)
    if not File.exist(apps_PLACE):
        return r
    f = {}
    for line in read_lines(apps_PLACE):
        kv = line.split(": ", 1)
        if len(kv) == 2:
            f[kv[0]] = kv[1]
    File.unlink(apps_PLACE)
    i = apps_find(self, toint(f.get("file", ""), -1))
    if f.get("screen", "") == "library":
        self.lsel = apps_clamp(self, toint(f.get("sel", ""), 0))
    elif r is None and i >= 0:
        self.lsel = i
        r = [i, toint(f.get("sel", ""), 0)]
    return r


def apps_request(self):
    if not File.exist(apps_OPEN):
        return None
    p = SD.read(apps_OPEN).strip().split("|")
    if len(p) != 3 or p[0] != "projector":
        return None             # another app's request: leave it for that app
    File.unlink(apps_OPEN)
    if p[1] == "new":
        return ["new"]
    i = apps_find(self, toint(p[2], -1))
    if i < 0:
        return None
    self.lsel = i
    if p[1] == "delete":
        return ["delete", i]
    if p[1] == "open":
        return [i, 0]
    return None


def apps_find(self, iid):
    i = 0
    while i < len(self.lib):
        if self.lib[i][0] == iid:
            return i
        i = i + 1
    return -1


def apps_clamp(self, sel):
    if sel >= len(self.lib):
        sel = len(self.lib) - 1
    if sel < 0:
        sel = 0
    return sel


# ---- Projector to Writer and Calc (PLAN_V1 step 5.2): an open request, then a switch

def apps_path(self, app):
    # the app's folder in the registry, or "" (and a message) if it isn't installed
    for p in reg_read():
        if p[1] == app:
            return p[2]
    self.msg = app + " isn't installed"
    return ""


def apps_to(self, path, req):
    # the request for the target, then the switch; the request goes if the switch fails
    SD.write(apps_OPEN, req + "\n")
    if apps_switch(self, path):
        return True
    File.unlink(apps_OPEN)
    return False


def apps_name(self, what):
    # the idea's title as Writer and Calc name a document (letters, digits, space - _ ( ),
    # 24 at most), then " notes" or " money"
    out = ""
    for ch in self.idea.get("title"):
        ok = (ch >= "0" and ch <= "9") or (ch >= "A" and ch <= "Z") or (ch >= "a" and ch <= "z")
        if ok or ch in " -_()":
            out = out + ch
    out = apps_cutw(out.strip(), 23 - len(what))
    if out == "":
        out = "Idea " + str(self.idea.id)
    return out + " " + what


def apps_cutw(s, n):
    # s in at most n characters, at a space if it has to be cut and there is one
    if len(s) <= n:
        return s
    i = n
    while i > 0 and s[i] != " ":
        i = i - 1
    if i == 0:
        i = n
    return cut(s, 0, i).strip()


def apps_notes(self):
    # w: the idea's notes in Writer, one document for each idea, made the first time
    path = apps_path(self, "Writer")
    if path == "":
        return False
    return apps_to(self, path, "writer|new|" + apps_name(self, "notes"))


def apps_sheet(self):
    # b: the plan's money as a sheet in Calc; one already there is replaced only if you say
    path = apps_path(self, "Calc")
    if path == "":
        return False
    name = apps_name(self, "money")
    f = "/data/calc/" + name + ".txt"
    r = True
    if File.exist(f):
        r = self.ask_yn("MONEY SHEET", "Write the plan's money over " + name + "?",
                        ["n opens it as it is."])
        if r is None:
            return False
    if r:
        ensure_dir("/data/calc")
        SD.write(f, apps_cells(self))
    return apps_to(self, path, "calc|open|" + name + ".txt")


def apps_cells(self):
    # cash and fixed costs, then a row a stage (net a month and the stage's total are
    # formulas), then the end: the likely case, as the money screen's numbers are entered
    out = "A1\tCash now\nB1\t{}\nA2\tFixed a month\nB2\t{}\n".format(
        self.idea.num("cash", 0), self.idea.num("fixed", 0))
    hs = ["Stage", "Months", "Start", "Cost/mo", "Income/mo", "Net/mo", "Total"]
    for i in range(7):
        out = out + "{}4\t{}\n".format("ABCDEFG"[i], hs[i])
    r = 5
    for st in self.idea.stages:
        out = out + apps_srow(st, r)
        r = r + 1
    if r > 5:
        out = out + "A{0}\tEnd\nB{0}\t=SUM(B5:B{1})\nG{0}\t=B1+SUM(G5:G{1})\n".format(r + 1, r - 1)
    return out + "WIDTH\tA\t14\n"


def apps_srow(st, r):
    name = st[0].replace("\t", " ")
    return ("A{0}\t{1}\nB{0}\t{2}\nC{0}\t{3}\nD{0}\t{4}\nE{0}\t{5}\n"
            "F{0}\t=E{0}-D{0}-$B$2\nG{0}\t=B{0}*F{0}-C{0}\n").format(r, name, st[1], st[5], st[2], st[6])
