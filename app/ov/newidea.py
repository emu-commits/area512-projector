# Projector overlay "newidea": compiled from the SD card when entered, unloaded on exit
# (App.ov). Every global name here starts with "newidea_".

# needs: stage
def newidea_main(self):
    T = "NEW IDEA"
    name = self.ask_text(T, "What's the idea? Give it a short name.", "", "", 24)
    if name is None or name == "":
        return False
    idea = Idea(self.next_id)
    self.next_id = self.next_id + 1
    self.save_meta()
    idea.f["title"] = name
    self.idea = idea
    newidea_ask(self, idea, T)
    newidea_money(self, idea, T)
    newidea_stages(self, idea, T)
    self.sel = 0
    self.save()
    return True


def newidea_ask(self, idea, T):
    steps = [("wish", "What are you trying to make happen?", "I want to ..."),
             ("picture", "Picture it working. What could you point to that proves it?",
              "Something you could show someone. Add a number."),
             ("why", "Why does this matter to you?",
              "Picture it done first: where you are, how it feels.")]
    for s in steps:
        v = self.ask_text(T, s[1], s[2], "", TEXT_MAX)
        if v is None:
            return
        idea.f[s[0]] = v


def newidea_money(self, idea, T):
    w = self.ask_choice(T, "How far ahead should we look?", WINDOW_NAMES, 3)
    if w is None:
        w = 3
    idea.f["window"] = str(WINDOWS[w])
    c = self.ask_number(T, "How much money can you put toward this right now?",
                        "0 is fine.", 0, 0, 99999999)
    if c is None:
        c = 0
    idea.f["cash"] = str(c)
    f = self.ask_number(T, "Fixed costs every month, whatever the stage?",
                        "Rent, phone, insurance ... 0 if none.", 0, 0, 9999999)
    if f is not None:
        idea.f["fixed"] = str(f)


def newidea_stages(self, idea, T):
    self.msg = ""
    while len(idea.stages) < MAX_STAGES:
        q = "Lay it out in stages. First stage?"
        if len(idea.stages) > 0:
            q = "What comes after '{}'?".format(idea.stages[len(idea.stages) - 1][0])
        if not stage_add(self, len(idea.stages), q):
            break
        if len(idea.stages) >= MAX_STAGES:
            break
        more = self.ask_yn(T, "Another stage after this one?",
                           ["{} stage(s) so far.".format(len(idea.stages))])
        if not more:
            break
