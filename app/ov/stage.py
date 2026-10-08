# Projector overlay "stage": compiled from the SD card when entered, unloaded on exit
# (App.ov). Every global name here starts with "stage_".

def stage_add(self, at, q):
    T = "STAGE"
    name = self.ask_text(T, q, "A short name: Learn, Build, Launch ...", "", 12)
    if name is None or name == "":
        return False
    st = [name, 3, 0, 2, 2]
    if not stage_numbers(self, st):
        return False
    self.idea.stages.insert(at, st)
    self.sel = at
    self.dirty = True
    return True


def stage_numbers(self, st):
    T = st[0].upper()
    m = self.ask_number(T, "How many months will '{}' take?".format(st[0]),
                        "Calendar months.", st[1], 1, 120)
    if m is None:
        return False
    st[1] = m
    n = self.ask_number(T, "Money each month during '{}'?".format(st[0]),
                        "Spending is negative (-500), income positive.", st[2],
                        -9999999, 9999999)
    if n is None:
        return False
    st[2] = n
    return stage_levels(self, st, T)


def stage_levels(self, st, T):
    c = self.ask_choice(T, "How sure are you of those numbers?",
                        ["sure", "rough idea", "a guess"], st[3] - 1)
    if c is None:
        return False
    st[3] = c + 1
    d = self.ask_choice(T, "How hard will '{}' be for you?".format(st[0]),
                        ["easy", "medium", "hard"], st[4] - 1)
    if d is None:
        return False
    st[4] = d + 1
    return True
