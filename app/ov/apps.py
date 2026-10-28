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
    # [library index, stage] to open, ["new"], or None. Sets self.lsel. Both files are read
    # once and deleted, so a bad one can't trap you.
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
    if p[1] == "open" and i >= 0:
        self.lsel = i
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
