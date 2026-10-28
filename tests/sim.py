#!/usr/bin/env python3
"""Run the suite's apps in a512sim (AREA512's MicroPython + API mocks) along key scripts.

  tests/sim.py                 every scenario in SCENARIOS, against dist/<app> (./build.sh);
                               scenarios named home* run Home, the rest Projector
  tests/sim.py -v NAME         one scenario, print the last screen + SD files
  tests/sim.py --py            run build/core.py instead (line numbers in errors)
  tests/sim.py --term512       on TERM512: a 240x135 window on a 320x240 display (full_screen)
  tests/sim.py --both          every scenario on the Cardputer and on TERM512

Script syntax: tokens separated by spaces; "T:some text" types the text (spaces
included, use _ for a space inside the token); ENTER ESC BS UP DOWN LEFT RIGHT as is.
"""
import os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTORY = pathlib.Path(os.environ.get("AREA512_FACTORY", pathlib.Path.home() / "area512-factory"))
SIM = FACTORY / "sim/a512sim"
PRELUDES = {"cardputer": FACTORY / "sim/prelude.py", "term512": FACTORY / "sim/prelude_term512.py"}
HEAP_KB = int(os.environ.get("SIM_HEAP_KB", "160"))         # logic checks; memory is measured on the firmware (tests/fw.py, key %).
# Not 128: the sim keeps the key script in the same heap, and at 320x240 the film overlay no
# longer fit in 128 KB (it showed "No memory" and the script went on from the strip).


def expand(script, shots=False):
    out = []
    for tok in script.split():
        if tok.startswith("SHOT:"):
            if shots:
                out.append(tok)            # screenshots are for tests/fw.py
            continue
        if tok.startswith("T:"):
            for ch in tok[2:].replace("_", " "):
                out.append("SPACE" if ch == " " else ch)
        else:
            out.append(tok)
    return " ".join(out)


def expand_keep_shots(script):
    return expand(script, True)


NEW_IDEA = ("a T:Corner_cafe ENTER T:Open_a_small_coffee_shop_in_my_town ENTER "
            "T:200_regulars_a_week_and_I_pay_myself_3k_a_month ENTER "
            "T:I_want_a_place_people_come_back_to ENTER 4 T:5k ENTER T:200 ENTER "
            # stage: name, months, one-time, extra costs a month, income a month, sure, hard
            # (nets a month with the $200 fixed cost: -200, -2000, -1000, +2500)
            "T:Plan ENTER T:3 ENTER ENTER ENTER ENTER 1 1 y "
            "T:Build ENTER T:6 ENTER ENTER T:1800 ENTER ENTER 2 3 y "
            "T:Open ENTER T:6 ENTER ENTER T:800 ENTER ENTER 3 3 y "
            "T:Grow ENTER T:18 ENTER ENTER ENTER T:3500 ENTER 2 2 n ")

SCENARIOS = {
    # memory: hidden % key shows free KB in the footer
    "mem": "% SHOT:m_lib " + NEW_IDEA + "% SHOT:m_strip p l l % SHOT:m_play ESC c % SHOT:m_cracks ESC "
           "$ % SHOT:m_money ESC q",
    # create an idea, look at it, quit without saving more
    "new_idea": NEW_IDEA + "p l l l l ENTER ESC $ s s ESC ? ENTER q n q",
    # whole arc with % probes before each overlay-heavy step (memory margins on firmware)
    "arc_mem": None,
    # whole arc: premortem, face every crack, holds, judge, promote
    "full_arc": NEW_IDEA + "SHOT:strip p SHOT:play1 l l SHOT:play3 l l SHOT:playend ESC c SHOT:cracks ESC "
        "o T:I_lose_nerve_when_money_gets_tight ENTER "
        "T:the_balance_drops_below_1k,_I_will_call_my_mentor_before_deciding ENTER "
        "c ENTER 2 T:cut_hours_and_sell_beans_online ENTER "
        "DOWN ENTER 2 T:pause_and_take_part-time_work ENTER "
        "DOWN ENTER 2 T:hire_a_barista_for_opening_month ENTER "
        "SHOT:faced ESC SHOT:holdstrip $ SHOT:money ESC "
        "p l l l l ENTER SHOT:holds x 3 2 3 T:a_place_I'm_proud_of ENTER SHOT:judged "
        "s SHOT:saved q",
    # reopen after a save in an earlier session: resumption note shown first
    "assumptions_vision": NEW_IDEA +
        "a a T:People_here_will_pay_$5_for_coffee ENTER a T:I_can_get_a_lease ENTER "
        "ENTER f T:test_a_market_stall_first ENTER d y ESC "
        "v DOWN ENTER BS BS BS T:now ENTER DOWN DOWN DOWN DOWN ENTER 1 ESC "
        "h l e DOWN ENTER BS T:9 ENTER ESC n T:Extra ENTER T:2 ENTER ENTER ENTER ENTER 1 1 x y "
        "q y T:pick_up_at_the_lease ENTER q",
    # edge cases: empty library, ESC everywhere, zero stages, long text, archive
    "edges": "j k ENTER d a ESC a T:X ENTER ESC ESC ESC ESC "
             "p c ESC $ ESC P o ESC ? x v ESC a ESC n ESC x q "
             "a T:" + "Very_long_name_that_goes_past_the_cap_" * 2 + " ENTER "
             "T:" + "word_" * 40 + " ENTER ESC ESC ESC ESC "
             "q ENTER q d y d y ENTER q q",
    # memory stress: 7 stages, 100-char answers, 8 assumptions, everything faced, promote
    # memory stress, the largest idea the caps allow: see big_script()
    "big": None,
}


def big_script():
    t80 = "T:" + "abcdefghi_" * 8                       # answers at the 80-char cap
    out = ["a T:Biggest_idea_of_them_all ENTER", t80, "ENTER", t80 + "9", "ENTER", t80,
           "ENTER 5 T:20k ENTER T:300 ENTER"]                        # window 5 years, $20k
    for i in range(1, 8):                                # 7 stages, all hard and rough
        out.append("T:Stage{} ENTER T:9 ENTER T:900 ENTER T:1500 ENTER T:300 ENTER 2 3".format(i))
        out.append("y" if i < 7 else "")
    out.append("SHOT:big_strip % SHOT:big_mem a")
    for i in range(6):                                   # 6 assumptions at the 60-char cap
        out.append("a T:" + "assumption_{}_".format(i) + "x" * 46 + " ENTER")
    out.append("ESC o " + t80 + " ENTER " + t80 + " ENTER")   # premortem + if-then
    # face all 16 cracks (the proof's "9" falls past the 80-char cap: "no number" too)
    out.append("c ENTER 2 " + t80 + " ENTER")
    for i in range(15):
        out.append("DOWN ENTER 2 " + t80 + " ENTER")
    out.append("ESC % SHOT:big_faced s % SHOT:big_saved q ENTER % SHOT:big_reopen")
    out.append("p l l l l l l l ENTER x 3 2 3 " + t80 + " ENTER % SHOT:big_judged s % "
               "SHOT:big_after q q")
    return " ".join(out)


SCENARIOS["big"] = big_script()


# The menu bar (Tab) on every screen with a key table, the 1.0 keys (n new, x delete, m money)
# and the bare ; . , / arrows; "TAB" is the Tab key
SCENARIOS["menu"] = ("TAB SHOT:mn_lib DOWN DOWN DOWN ENTER SHOT:mn_lib_help ENTER TAB ESC "
    + NEW_IDEA.replace("a T:Corner_cafe", "n T:Corner_cafe", 1) +
    "TAB SHOT:mn_idea RIGHT SHOT:mn_plan ENTER c c TAB SHOT:mn_money ESC ESC "
    "TAB LEFT DOWN ENTER T:Extra ENTER T:2 ENTER ENTER ENTER ENTER 1 1 SHOT:mn_added "
    "TAB x y , , / SHOT:mn_arrows TAB TAB m ESC ? SHOT:mn_help ENTER "
    "c . ; ESC a n T:test_it ENTER TAB DOWN DOWN DOWN ENTER y ESC "
    "q n TAB ESC x n q")

# An idea saved by v0.3 (one net figure a month per stage) opens with its money split:
# a cost stage keeps its spending as costs, an earning stage its net as income.
LEGACY = ("PROJECTOR-IDEA 1\ntitle: Old cafe\nstatus: simulating\ntouched: 1\nwindow: 36\n"
          "cash: 5000\nS|Build|6|-2000|2|3\nS|Grow|18|2500|2|2\n")
SEEDS = {"legacy": {"/data": None, "/data/projector": None, "/data/projector/ideas": None,
                    "/data/projector/meta.txt": "session: 1\nnext_id: 2\n",
                    "/data/projector/library.txt": "1|simulating|1|Old cafe",
                    "/data/projector/ideas/1.txt": LEGACY}}
SCENARIOS["legacy"] = "ENTER SHOT:l_strip e SHOT:l_edit ESC l e SHOT:l_edit2 ESC s q q"

# Switching apps (docs/APPS_FORMAT.md): with a registry, Tab 3 saves the idea and its place, then
# hands off (the sim prints @@RUN_NEXT); the next start opens on that stage. An open request
# from another app opens its idea; Esc from the library goes to Home.
APPS = "1|Home|/home/ai/home\n2|Projector|/home/ai/projector\n3|Writer|/home/ai/writer\n"
SEEDS["switch"] = {"/data/area512": None, "/data/area512/apps.txt": APPS}
SCENARIOS["switch"] = NEW_IDEA + "l l v DOWN ENTER BS T:now ENTER ESC TAB 3"
SEEDS["resume"] = dict(SEEDS["legacy"], **{"/data/projector/place.txt": "screen: strip\nsel: 1\nfile: 1\n"})
SCENARIOS["resume"] = "e ESC q q"
SEEDS["open_req"] = dict(SEEDS["legacy"], **{"/data/area512": None, "/data/area512/apps.txt": APPS,
                                            "/data/area512/open.txt": "projector|open|1\n"})
SCENARIOS["open_req"] = "TAB SHOT:apps_menu LEFT ESC TAB 2 q q"

# The film: WAITs let an animation run to its end (in the sim each WAIT is one empty poll; on
# the firmware ~0.25 s), so these reach the freeze frame; the other scenarios press keys
# mid-animation, which skips it.
W = "WAIT " * 16
SCENARIOS["film_accept"] = (NEW_IDEA + "p " + W + "SHOT:f_card0 l " + W + "SHOT:f_freeze % SHOT:f_freeze_mem "
    "a T:my_savings ENTER T:a_place_of_my_own_is_worth_it ENTER SHOT:f_accepted "
    "l " + W + "SHOT:f_open l " + W + "l " + W + "SHOT:f_end ENTER SHOT:f_cracks ESC "
    "c SHOT:f_list ESC q n q")
SCENARIOS["film_edit"] = (NEW_IDEA + "p " + W + "l " + W + "SHOT:fe_freeze e SHOT:fe_edit "
    "DOWN DOWN DOWN ENTER T:300 ENTER SHOT:fe_edited ESC % SHOT:fe_back "
    "l " + W + "SHOT:fe_freeze2 f T:take_contract_work ENTER SHOT:fe_faced q q n q")
# a one-time spend: the film's chart drops at the start of Build, and cash runs out sooner
SCENARIOS["film_once"] = (NEW_IDEA.replace("T:Build ENTER T:6 ENTER ENTER", "T:Build ENTER T:6 ENTER T:3k ENTER")
    + "p " + W + "l " + W + "SHOT:o_freeze l " + W + "SHOT:o_open q $ SHOT:o_money ESC e DOWN DOWN SHOT:o_edit ESC q n q")
# accept the likely cash-out instead of facing it: HOLDS names the cost
SCENARIOS["accept_arc"] = SCENARIOS["full_arc"].replace(
    "c ENTER 2 T:cut_hours_and_sell_beans_online ENTER",
    "c ENTER 3 T:my_savings ENTER T:a_place_of_my_own_is_worth_it ENTER").replace(
    "p l l l l ENTER SHOT:holds", "p l l l l ENTER " + "WAIT " * 12 + "SHOT:holds")
# the largest idea, with free memory measured while the film is loaded
SCENARIOS["big_film"] = SCENARIOS["big"].replace(
    "p l l l l l l l ENTER", "p WAIT WAIT WAIT WAIT % SHOT:bf_play l l l l l l l " + W + "% SHOT:bf_end ENTER")
SCENARIOS["arc_mem"] = SCENARIOS["full_arc"].replace(
    "SHOT:holdstrip $", "SHOT:holdstrip % SHOT:mem_strip $").replace(
    "p l l l l ENTER SHOT:holds", "p l l l l % SHOT:mem_end ENTER SHOT:holds").replace(
    "s SHOT:saved q", "% SHOT:mem_judged s SHOT:saved q")


# The sim's Dir lists nothing: list the sim's card instead (Home scans /home for apps).
# MINIMUM has no slicing, hence the loop.
DIR_MOCK = """
def _sd_init(self, p):
    self._p = p + '/'
    self._l = None
def _sd_read(self):
    if self._l is None:
        self._l = []
        n = len(self._p)
        for k in _sim_fs:
            if k.find(self._p) == 0 and k.find('/', n) < 0:
                s = ''
                i = n
                while i < len(k):
                    s = s + k[i]
                    i = i + 1
                self._l.append(s)
        self._l.sort()
    if len(self._l) == 0:
        return None
    return self._l.pop(0)
Dir.__init__ = _sd_init
Dir.read = _sd_read
"""
# Printed when the run ends, with the stats: the card's /data files. EXPECT checks against
# them and the @@RUN_NEXT line. (Not a file of its own after start.mpy: the sim compiles every
# file first and keeps them where the GC doesn't look, so a later one can be collected.)
DUMP = """
_sim_stats0 = _sim_stats
def _sim_stats():
    _sim_stats0()
    for k in sorted(_sim_fs):
        if k.find('/data/') == 0 and _sim_fs[k] is not None:
            print('@@FS ' + k + ' ' + repr(_sim_fs[k]))
"""
EXPECT = {}


def app_of(name):
    return "home" if name.startswith("home") else "projector"


# Home: a card with Projector, four bundled apps and two games. Slide isn't installed, so
# Agenda is the bundled Scheduler, and Extras lists Bomb, Paint, Space lander, Theme, Files.
def app_dir(path):
    return {path: None, path + "/main.manifest": "main.mrb\n"}


HOME_CARD = {"/home/tool": None, "/home/game": None, "/data": None, "/data/projector": None,
             "/data/projector/recent.txt": "Corner cafe|7\nNight classes|3\n"}
for d in ("/home/ai/projector", "/home/tool/writer", "/home/tool/calc", "/home/tool/scheduler",
          "/home/tool/paint", "/home/tool/theme", "/home/game/bomb", "/home/game/space_lander"):
    HOME_CARD.update(app_dir(d))
REG_WRITTEN = ("@@FS /data/area512/apps.txt '1|Home|/home/ai/home\\n2|Projector|/home/ai/projector\\n"
               "3|Writer|/home/tool/writer\\n4|Calc|/home/tool/calc\\n5|Agenda|/home/tool/scheduler\\n'")
for n in ("home_reg", "home_open", "home_nav", "home_extras", "home_files", "home_new", "home_delete",
          "home_menu", "home_place"):
    SEEDS[n] = dict(HOME_CARD)
# Esc leaves to the filer; the registry is written, and a request no app took is dropped
SEEDS["home_reg"]["/data/area512"] = None
SEEDS["home_reg"]["/data/area512/open.txt"] = "writer|open|x\n"
SCENARIOS["home_reg"] = "SHOT:h_start % SHOT:h_mem ESC"
EXPECT["home_reg"] = [REG_WRITTEN, "!@@FS /data/area512/open.txt", "!@@RUN_NEXT"]
# the second file under Projector's icon: an open request, then Projector
SCENARIOS["home_open"] = "DOWN SHOT:h_file1 DOWN SHOT:h_file2 ENTER"
EXPECT["home_open"] = ["@@RUN_NEXT /home/ai/projector", "@@FS /data/area512/open.txt 'projector|open|3\\n'",
                       "@@FS /data/home/place.txt 'app: projector\\nfile: 1\\n'"]
# icons with the bare arrows, h/l and digits; the app itself (no file) has no request
SCENARIOS["home_nav"] = ("/ / SHOT:h_calc l , h 5 SHOT:h_agenda DOWN UP 9 ; . "
                         "2 / / / / / / / , SHOT:h_left ENTER")      # 7 rights stop at Extras
EXPECT["home_nav"] = ["@@RUN_NEXT /home/tool/scheduler", "!@@FS /data/area512/open.txt"]
# Extras lists the other apps like files: Enter goes into the list, then runs one
SCENARIOS["home_extras"] = "6 SHOT:h_extras ENTER DOWN SHOT:h_paint n x ENTER"
EXPECT["home_extras"] = ["@@RUN_NEXT /home/tool/paint", "@@FS /data/home/place.txt 'app: extras\\nfile: 1\\n'"]
SCENARIOS["home_files"] = "6 ENTER DOWN DOWN DOWN DOWN SHOT:h_files ENTER"
EXPECT["home_files"] = ["!@@RUN_NEXT"]
SCENARIOS["home_new"] = "n"
EXPECT["home_new"] = ["@@RUN_NEXT /home/ai/projector", "@@FS /data/area512/open.txt 'projector|new|\\n'"]
# x asks first: n keeps it, then y hands the delete to Projector
SCENARIOS["home_delete"] = "x DOWN x SHOT:h_delete n x ESC x y"
EXPECT["home_delete"] = ["@@RUN_NEXT /home/ai/projector",
                         "@@FS /data/area512/open.txt 'projector|delete|7\\n'"]
# the menu bar: Apps first (from the registry Home has just written), Help from the key table
SCENARIOS["home_menu"] = ("TAB SHOT:h_menu LEFT SHOT:h_apps RIGHT DOWN DOWN DOWN ENTER SHOT:h_help ENTER "
                          "TAB 1 TAB ESC TAB 3")
EXPECT["home_menu"] = ["@@RUN_NEXT /home/tool/writer"]
# back from an app: on the icon and file you left from, and place.txt is used once
SEEDS["home_place"].update({"/data/home": None, "/data/home/place.txt": "app: projector\nfile: 1\n"})
SCENARIOS["home_place"] = "SHOT:h_back ENTER"
EXPECT["home_place"] = ["@@FS /data/area512/open.txt 'projector|open|3\\n'"]
# nothing installed but Home: Extras alone, with Files
SCENARIOS["home_empty"] = "SHOT:h_empty ENTER ENTER"
EXPECT["home_empty"] = ["@@FS /data/area512/apps.txt '1|Home|/home/ai/home\\n'", "!@@RUN_NEXT"]

# Projector, asked by Home to delete an idea: it archives it and goes back to Home
SEEDS["del_req"] = dict(SEEDS["legacy"], **{"/data/area512": None, "/data/area512/apps.txt": APPS,
                                           "/data/area512/open.txt": "projector|delete|1\n"})
SCENARIOS["del_req"] = ""
EXPECT["del_req"] = ["@@RUN_NEXT /home/ai/home", "@@FS /data/projector/library.txt '1|archived|",
                     "@@FS /data/projector/recent.txt ''", "!@@FS /data/area512/open.txt"]


def run(name, script, target, screen="cardputer"):
    # Like the device: the app's folder on the card, then main.manifest's entries in order.
    work = ROOT / "tests/.work" / name
    work.mkdir(parents=True, exist_ok=True)
    app = app_of(name)
    dist = ROOT / "dist" / app
    seed = ["_sim_fs['/home'] = None", "_sim_fs['/home/ai'] = None"]
    for d in sorted(dist.iterdir()):          # ovl/ and icons/: what the app reads from its folder
        if d.is_dir():
            here = "/home/ai/{}/{}".format(app, d.name)
            seed.append("_sim_fs[{!r}] = None".format(here))
            for f in sorted(d.iterdir()):
                seed.append("_sim_fs[{!r}] = {!r}".format(here + "/" + f.name, f.read_bytes().decode("latin-1")))
    seed.append("_sim_fs[{!r}] = None".format("/home/ai/" + app))
    seed.append("_sim_fs[{!r}] = 'core.mpy\\nstart.mpy\\n'".format("/home/ai/{}/main.manifest".format(app)))
    for path, text in SEEDS.get(name, {}).items():
        seed.append("_sim_fs[{!r}] = {!r}".format(path, text))
    (work / "seed.py").write_text("\n".join(seed) + "\n" + DIR_MOCK + DUMP)
    for f in ("core.mpy", "start.mpy"):
        (work / f).write_bytes((dist / f).read_bytes())
    (work / ".keys").write_text(expand(script))
    files = ["seed.py", "core.mpy", "start.mpy"]
    if target == "py":
        (work / "core.py").write_bytes((ROOT / "build" / app / "core.py").read_bytes())
        (work / "start.py").write_bytes((ROOT / "build" / app / "start.py").read_bytes())
        files = ["seed.py", "core.py", "start.py"]
    heap = HEAP_KB
    if name.startswith("big") and heap < 400:
        heap = 400          # its 3,500-key script is held in the sim's heap, not the app's
    r = subprocess.run([str(SIM), str(PRELUDES[screen]), ".keys", str(heap)] + files,
                       cwd=work, capture_output=True, text=True, timeout=300)
    return r.stdout + r.stderr


def verdict(out, name=""):
    for want in EXPECT.get(name, []):
        if want[0] == "!":
            if want[1:] in out:
                return "UNWANTED " + want[1:].split()[1]
        elif want not in out:
            return "MISSING " + (want + " ").split()[1]
    if "@@COMPILE_ERROR" in out:
        return "COMPILE_ERROR"
    if "@@RUNTIME_ERROR" in out:
        return "RUNTIME_ERROR"
    if "@@EXIT" in out:
        # every key must be used: an early exit means the flow went somewhere unplanned
        m = re.search(r"keys_used=(\d+)/(\d+)", out)
        if m and m.group(1) != m.group(2):
            return "EARLY_EXIT"
        return "ok"
    return "?"


def main():
    args = sys.argv[1:]
    target = "py" if "--py" in args else "mpy"
    verbose = "-v" in args
    screens = ["cardputer"]
    if "--term512" in args:
        screens = ["term512"]
    if "--both" in args:
        screens = ["cardputer", "term512"]
    names = [a for a in args if not a.startswith("-")] or list(SCENARIOS)
    bad = 0
    for screen in screens:
        for n in names:
            out = run(n, SCENARIOS[n], target, screen)
            v = verdict(out, n)
            stats = next((l for l in out.splitlines() if l.startswith("@@STATS")), "")
            label = n if len(screens) == 1 else screen + " " + n
            print("{:30} {:14} {}".format(label, v, stats.replace("@@STATS ", "")))
            if v != "ok" or verbose:
                keep = [l for l in out.splitlines() if not l.startswith(("@@HEAP", "@@FS"))]
                if verbose:
                    keep += [l for l in out.splitlines() if l.startswith("@@FS")]
                print("\n".join(keep[-60:]))
            bad += v != "ok"
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
