# Projector overlay "accept": accept a money crack as a cost you choose to pay. Not a risk
# that might happen (that is facing it with an If-Then): the plan as entered costs this, and
# you say it is worth it. Stored as a faced crack whose text starts with "=".
# Every global name here starts with "accept_".

def accept_main(self, key):
    self.refresh()
    c = None
    for x in self.cr:
        if x[0] == key:
            c = x
    if c is None:
        return
    src = ""
    if key != "endbelow":
        src = accept_src(self, c)
        if src is None:
            return
    why = self.ask_text("ACCEPT IT", "Why is it worth it to you anyway?",
                        "In your own words.", "", TEXT_MAX)
    if why is None or why == "":
        return
    self.idea.faced[key] = "=" + src + why
    self.dirty = True


def accept_src(self, c):
    s = self.ask_text("ACCEPT IT", c[1] + ". Where will the money come from?",
                      "Savings, a loan, a job on the side ...", "", 50)
    if s is None or s == "":
        return None
    return s + "; "
