# Projector overlay "help": compiled from the SD card when entered, unloaded on exit
# (App.ov). Every global name here starts with "help_".

def help_main(self):
    self.show("KEYS", "", [
        ("h/l stage   p play   c cracks", self.c_text),
        ("e edit  n new  x delete stage", self.c_text),
        ("v vision   a assumptions", self.c_text),
        ("$ money    o obstacle (premortem)", self.c_text),
        ("s save     q back", self.c_text)], [("any", "key")])
