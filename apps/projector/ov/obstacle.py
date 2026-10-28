# Projector overlay "obstacle": the premortem (WOOP's Obstacle) and its If-Then plan.
# Every global name here starts with "obstacle_".

def obstacle_main(self):
    idea = self.idea
    o = self.ask_text("PREMORTEM",
                      "Jump to month {}. It didn't work out. What inside you got in the way?"
                      .format(idea.num("window", 36)),
                      "A habit, a feeling, a pattern. Not bad luck.",
                      idea.get("obstacle"), TEXT_MAX)
    if o is None or o == "":
        return
    idea.f["obstacle"] = o
    self.dirty = True
    obstacle_plan(self, idea)


def obstacle_plan(self, idea):
    start = idea.get("ifthen")
    if start == "":
        start = "When "
    p = self.ask_text("IF-THEN", "When that shows up, what will you do?",
                      "When ___, I will ___.", start, TEXT_MAX)
    if p is not None and p != "" and p != "When":
        idea.f["ifthen"] = p
