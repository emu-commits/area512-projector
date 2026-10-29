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
CTRL:s is Ctrl+S (the PicoRuby forks only, under tests/rsim.rb).
"""
import json, os, pathlib, re, subprocess, sys

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


FORKS = ("agenda", "writer", "calc", "slide")   # PicoRuby: run by tests/rsim.rb under CRuby


def app_of(name):
    for a in ("home",) + FORKS:
        if name.startswith(a):
            return a
    return "projector"


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


# Agenda (forks/agenda, PicoRuby): run by tests/rsim.rb. Its @@FS lines are Ruby's inspect.
def rfs(path, text):
    q = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
    return "@@FS " + path + ' "' + q + '"'


AG_DATA = {"/data": None, "/data/agenda": None}
AG_FILE = ("CURSOR\t2026-11-02\n2026-11-03\t09:00\tDentist\n2026-11-03\t13:00\tLunch with Sam\n"
           "2026-11-10\t18:30\tChoir\n")
AG_SEED = dict(AG_DATA, **{"/data/agenda/agenda.txt": AG_FILE})
AG_APPS = "1|Home|/home/ai/home\n2|Projector|/home/ai/projector\n5|Agenda|/home/ai/agenda\n"
AG_REG = dict(AG_SEED, **{"/data/area512": None, "/data/area512/apps.txt": AG_APPS})
# Scheduler's file is copied once, saved as Agenda's, with recent.txt for Home
SEEDS["agenda_import"] = {"/data": None, "/data/scheduler.txt": AG_FILE}
SCENARIOS["agenda_import"] = "SHOT:a_month ESC"
EXPECT["agenda_import"] = [rfs("/data/agenda/agenda.txt", AG_FILE), rfs(
    "/data/agenda/recent.txt", "3 Nov Dentist 09:00|2026-11-03#0\n3 Nov Lunch with Sam 13:00|2026-11-03#1\n"
    "10 Nov Choir 18:30|2026-11-10#0\n"), "!@@RUN_NEXT"]
# n: the time field (down twice is 08:30), then the text; in the day, typed digits
SCENARIOS["agenda_add"] = ("n DOWN DOWN SHOT:a_time ENTER T:Dentist ENTER ENTER n 1 4 SHOT:a_typed 1 5 ENTER "
                           "T:Lunch ENTER SHOT:a_day ESC ESC SHOT:a_leave y")
EXPECT["agenda_add"] = [rfs("/data/agenda/agenda.txt", "CURSOR\t2026-06-21\n2026-06-21\t08:30\tDentist\n"
                                                       "2026-06-21\t14:15\tLunch\n")]
# Enter edits (13:00 up twice is 13:30), x asks then deletes, s saves
SEEDS["agenda_edit"] = AG_SEED
SCENARIOS["agenda_edit"] = ("/ ENTER DOWN ENTER UP UP ENTER BS BS BS T:Jo ENTER SHOT:a_edited "
                            "UP x n x y ESC s ESC")
EXPECT["agenda_edit"] = [rfs("/data/agenda/agenda.txt", "CURSOR\t2026-11-03\n2026-11-03\t13:30\tLunch with Jo\n"
                                                        "2026-11-10\t18:30\tChoir\n")]
# the agenda list from the selected day; Enter opens that day on the event
SEEDS["agenda_list"] = AG_SEED
SCENARIOS["agenda_list"] = "a SHOT:a_list DOWN DOWN ENTER SHOT:a_list_day c ] [ , / ; . ESC"
EXPECT["agenda_list"] = ['"CURSOR\\t2026-11-10\\n']
# Fn+arrow comes as one key (Widget.read_key): it moves the day, never the month
SEEDS["agenda_fn"] = AG_SEED
SCENARIOS["agenda_fn"] = "UP DOWN LEFT RIGHT RIGHT ESC"         # a day on: 3 Nov, still November
EXPECT["agenda_fn"] = ['"CURSOR\\t2026-11-03\\n']
# Tab, then a digit: saves, leaves a place, hands off
SEEDS["agenda_switch"] = AG_REG
SCENARIOS["agenda_switch"] = "/ n ENTER T:Gym ENTER TAB SHOT:a_menu 2"
EXPECT["agenda_switch"] = ["@@RUN_NEXT /home/ai/projector",
                           rfs("/data/agenda/place.txt", "screen: month\nsel: 0\nfile: 2026-11-03\n"),
                           "2026-11-03\\t09:00\\tGym\\n"]
# the menu bar: Apps first, its own digit does nothing; Help; Esc from the month goes Home
SEEDS["agenda_menu"] = AG_REG
SCENARIOS["agenda_menu"] = ("TAB LEFT SHOT:a_apps RIGHT RIGHT DOWN ENTER TAB a TAB ? SHOT:a_help ENTER "
                            "TAB 5 c TAB RIGHT RIGHT ENTER ESC")       # Apps, Day, Month, File: File > save
EXPECT["agenda_menu"] = ["@@RUN_NEXT /home/ai/home", '"CURSOR\\t2026-12-02\\n']
# Home's requests: open on an event, new, delete (no question, then back to Home)
SEEDS["agenda_open"] = dict(AG_REG, **{"/data/area512/open.txt": "agenda|open|2026-11-03#1\n"})
SCENARIOS["agenda_open"] = "SHOT:a_opened ENTER ENTER ENTER x y ESC ESC y"
EXPECT["agenda_open"] = [rfs("/data/agenda/agenda.txt", "CURSOR\t2026-11-03\n2026-11-03\t09:00\tDentist\n"
                                                        "2026-11-10\t18:30\tChoir\n"), "!/data/area512/open.txt"]
SEEDS["agenda_new_req"] = dict(AG_REG, **{"/data/area512/open.txt": "agenda|new|\n"})
SCENARIOS["agenda_new_req"] = "ENTER T:Call_mum ENTER ESC y"
EXPECT["agenda_new_req"] = ["2026-11-02\\t09:00\\tCall mum\\n"]
SEEDS["agenda_del_req"] = dict(AG_REG, **{"/data/area512/open.txt": "agenda|delete|2026-11-03#0\n",
                                         "/data/agenda/place.txt": "screen: day\nsel: 1\nfile: 2026-11-03\n"})
SCENARIOS["agenda_del_req"] = ""
EXPECT["agenda_del_req"] = ["@@RUN_NEXT /home/ai/home", "!Dentist", "!/data/area512/open.txt",
                            "!/data/agenda/place.txt"]     # a request uses up the place too
# back from another app: place.txt puts you on the list, on the event you left
SEEDS["agenda_place"] = dict(AG_SEED, **{"/data/agenda/place.txt": "screen: list\nsel: 1\nfile: 2026-11-03\n"})
SCENARIOS["agenda_place"] = "ENTER x y ESC ESC y"
EXPECT["agenda_place"] = ["!Lunch", "!/data/agenda/place.txt", "Choir"]
# the time field: 25 and 93 aren't times; 0 is midnight; down from midnight is 23:45
SCENARIOS["agenda_time"] = ("n 2 5 ENTER SHOT:a_bad 9 3 ENTER 9 3 0 ENTER T:x ENTER n 0 ENTER T:Midnight ENTER "
                            "n DOWN ENTER T:Late ENTER n ESC n ENTER ESC ESC y")
EXPECT["agenda_time"] = [rfs("/data/agenda/agenda.txt", "CURSOR\t2026-06-21\n2026-06-21\t00:00\tMidnight\n"
                                                        "2026-06-21\t09:30\tx\n2026-06-21\t23:45\tLate\n")]
# nothing on the card: every screen says so; leaving without a change writes nothing
SCENARIOS["agenda_empty"] = "SHOT:a_empty ENTER SHOT:a_empty_day a SHOT:a_empty_list ESC ESC"
EXPECT["agenda_empty"] = ["!/data/agenda/agenda.txt", "!@@RUN_NEXT"]


# Writer (forks/writer, PicoRuby): documents in /data/writer, Type and Move, find
WR_NOTES = "The quick brown fox\njumps over the lazy dog\n"
WR_SEED = {"/data": None, "/data/writer": None, "/data/writer/notes.txt": WR_NOTES,
           "/data/writer/Shopping.txt": "Milk\nBread\n", "/data/writer/recent.txt": "notes|notes.txt\n"}
WR_APPS = "1|Home|/home/ai/home\n2|Projector|/home/ai/projector\n3|Writer|/home/ai/writer\n"
WR_REG = dict(WR_SEED, **{"/data/area512": None, "/data/area512/apps.txt": WR_APPS})
# the one document from before the fork becomes "writer", and the old file stays
SEEDS["writer_import"] = {"/data": None, "/data/writer.txt": "Hello\nWorld\n"}
SCENARIOS["writer_import"] = "SHOT:w_files ENTER SHOT:w_doc ESC ESC"
EXPECT["writer_import"] = [rfs("/data/writer/writer.txt", "Hello\nWorld\n"),
                           rfs("/data/writer/recent.txt", "writer|writer.txt\n"), rfs("/data/writer.txt", "Hello\nWorld\n")]
# n names it, then typing; Esc saves and goes to the list, Esc again leaves
SCENARIOS["writer_type"] = "SHOT:w_empty n T:Draft ENTER T:Hello_world ENTER T:Second_line SHOT:w_typed ESC SHOT:w_list ESC"
EXPECT["writer_type"] = [rfs("/data/writer/Draft.txt", "Hello world\nSecond line\n"),
                         rfs("/data/writer/recent.txt", "Draft|Draft.txt\n")]
# Move (Tab m): the bare arrows, l a word, [ the top, e the row's end; Enter types again
SEEDS["writer_move"] = WR_SEED
SCENARIOS["writer_move"] = ("ENTER TAB SHOT:w_menu m SHOT:w_move . l l ENTER T:X TAB m [ e x SHOT:w_movekey ENTER T:! "
                            "TAB m , , h ESC T:< ESC ESC")
EXPECT["writer_move"] = [rfs("/data/writer/notes.txt", "The quick brown <fox!\njumps over Xthe lazy dog\n")]
# a paragraph wider than the screen wraps; down stays in it, on the next row
WR_LONG = "Lorem ipsum " * 12 + "end\nSecond para\n"
SEEDS["writer_wrap"] = {"/data": None, "/data/writer": None, "/data/writer/long.txt": WR_LONG}
SCENARIOS["writer_wrap"] = "ENTER SHOT:w_wrap DOWN T:X DOWN DOWN DOWN DOWN DOWN DOWN T:Y TAB m a e e ENTER T:Z ESC ESC"
EXPECT["writer_wrap"] = ["XLorem", "\\nSecond paraYZ\\n"]
# find (Tab f) from the cursor, Tab g again (round from the top), case doesn't matter;
# Tab then Writer's own digit does nothing
SEEDS["writer_find"] = WR_REG
SCENARIOS["writer_find"] = "ENTER TAB f T:LAZY ENTER SHOT:w_found T:very_ TAB g TAB 3 T:Q ESC ESC"
EXPECT["writer_find"] = [rfs("/data/writer/notes.txt", "The quick brown fox\njumps over the very Qlazy dog\n")]
# the list: new, rename, delete (into deleted/), Enter opens; names a card can't take
SEEDS["writer_files"] = WR_SEED
SCENARIOS["writer_files"] = ("SHOT:w_list2 n T:recent ENTER n T:a/b?c ENTER ESC DOWN DOWN SHOT:w_three r BS BS BS BS BS BS BS BS "
                             "T:Groceries ENTER r T:x ENTER UP x n x y SHOT:w_deleted n T:GROCERIESX ENTER T:Tea ENTER ESC ESC")
EXPECT["writer_files"] = [rfs("/data/writer/abc.txt", "\n"), rfs("/data/writer/Groceriesx.txt", "Tea\nMilk\nBread\n"),
                          rfs("/data/writer/deleted/notes.txt", WR_NOTES), "!/data/writer/notes.txt ",
                          "!/data/writer/recent.txt.", "!Shopping.txt", "!GROCERIESX"]
# Tab then a digit: saved, the place written, then Projector
SEEDS["writer_switch"] = WR_REG
SCENARIOS["writer_switch"] = "ENTER DOWN T:Hi TAB SHOT:w_apps 2"
EXPECT["writer_switch"] = ["@@RUN_NEXT /home/ai/projector", rfs("/data/writer/notes.txt", "The quick brown fox\nHijumps over the lazy dog\n"),
                           rfs("/data/writer/place.txt", "screen: doc\nsel: 0\nfile: notes.txt\nrow: 1\ncol: 2\nmode: type\n")]
# back from a switch: the same document, line, column and mode, and place.txt used up
SEEDS["writer_place"] = dict(WR_SEED, **{"/data/writer/place.txt": "screen: doc\nsel: 0\nfile: notes.txt\nrow: 1\ncol: 6\nmode: move\n"})
SCENARIOS["writer_place"] = "SHOT:w_back ENTER T:Z ESC ESC"
EXPECT["writer_place"] = ["jumps Zover", "!/data/writer/place.txt"]
# Home's requests: open, new (named), delete
SEEDS["writer_open"] = dict(WR_REG, **{"/data/area512/open.txt": "writer|open|Shopping.txt\n"})
SCENARIOS["writer_open"] = "T:Eggs ENTER ESC ESC"
EXPECT["writer_open"] = [rfs("/data/writer/Shopping.txt", "Eggs\nMilk\nBread\n"), "@@RUN_NEXT /home/ai/home",
                         rfs("/data/writer/recent.txt", "Shopping|Shopping.txt\nnotes|notes.txt\n")]
SEEDS["writer_new_req"] = dict(WR_REG, **{"/data/area512/open.txt": "writer|new|Corner cafe notes\n"})
SCENARIOS["writer_new_req"] = "T:Hi ESC ESC"
EXPECT["writer_new_req"] = [rfs("/data/writer/Corner cafe notes.txt", "Hi\n"), "!/data/area512/open.txt"]
SEEDS["writer_del_req"] = dict(WR_REG, **{"/data/area512/open.txt": "writer|delete|notes.txt\n"})
SCENARIOS["writer_del_req"] = ""
EXPECT["writer_del_req"] = ["@@RUN_NEXT /home/ai/home", rfs("/data/writer/deleted/notes.txt", WR_NOTES),
                            rfs("/data/writer/recent.txt", ""), "!/data/area512/open.txt"]
# Writer's Ctrl keys still work: ^S save, ^K page up, ^O the list, ^Q leave
SEEDS["writer_ctrl"] = WR_SEED
SCENARIOS["writer_ctrl"] = "ENTER T:A CTRL:s CTRL:k T:B CTRL:o ENTER CTRL:q"
EXPECT["writer_ctrl"] = [rfs("/data/writer/notes.txt", "BAThe quick brown fox\njumps over the lazy dog\n")]
# UTF-8 from the IME, a byte a key: kept whole, and Backspace takes a whole character
SCENARIOS["writer_utf8"] = "n T:jp ENTER T:あい BS T:x LEFT LEFT T:< ESC ESC"
EXPECT["writer_utf8"] = [rfs("/data/writer/jp.txt", "<\\xE3\\x81\\x82x\n").replace("\\\\x", "\\x")]
# Tab > Help in Move, and the Apps menu
SEEDS["writer_menu"] = WR_REG
SCENARIOS["writer_menu"] = "ENTER TAB m TAB ? SHOT:w_help ENTER TAB LEFT LEFT RIGHT ENTER"
EXPECT["writer_menu"] = ["@@RUN_NEXT /home/ai/home"]
# a long document: the end, the top, pages
SEEDS["writer_long"] = {"/data": None, "/data/writer": None,
                        "/data/writer/big.txt": "".join("Line %d of the big one\n" % i for i in range(1, 201))}
SCENARIOS["writer_long"] = "ENTER TAB m ] SHOT:w_end k k [ j j ENTER T:@ ESC ESC"
EXPECT["writer_long"] = ["big one\\n@Line ", "!@Line 1 "]     # two pages down: 7 rows a page, 14 on TERM512
# the hidden % in Move: the Ruby heap (rsim's numbers; tests/fw.py shows the real ones)
SEEDS["writer_mem"] = WR_SEED
SCENARIOS["writer_mem"] = "ENTER TAB m % SHOT:w_mem"
EXPECT["writer_mem"] = ["@@SCREEN Ruby heap: 70 KB free of 120"]
# past 10 KB, or 16 KB of room (bytes, and 40 a line): a file that big isn't opened, and
# typing stops at the limit; short lines count, one String each
SEEDS["writer_full"] = {"/data": None, "/data/writer": None, "/data/writer/huge.txt": "x" * 17000 + "\n",
                        "/data/writer/edge.txt": "y" * 10230 + "\n", "/data/writer/lines.txt": "b\n" * 400}
SCENARIOS["writer_full"] = "ENTER TAB m ] ENTER T:abcdefghij SHOT:w_full"
EXPECT["writer_full"] = ["@@SCREEN Full: Writer takes no more. Start another."]
SEEDS["writer_edge"] = SEEDS["writer_full"]
SCENARIOS["writer_edge"] = "ENTER TAB m ] ENTER T:abcdefghij ESC"
EXPECT["writer_edge"] = [rfs("/data/writer/edge.txt", "y" * 10230 + "abcdefghi\n")]
SEEDS["writer_huge"] = SEEDS["writer_full"]
SCENARIOS["writer_huge"] = "DOWN ENTER SHOT:w_huge"
EXPECT["writer_huge"] = ["@@SCREEN huge is too big: 167% of the most"]
SEEDS["writer_lines"] = SEEDS["writer_full"]
SCENARIOS["writer_lines"] = "DOWN DOWN ENTER SHOT:w_lines"
EXPECT["writer_lines"] = ["@@SCREEN lines is too big: 103% of the most"]
# nothing on the card: every key on the empty list is harmless
SCENARIOS["writer_empty"] = "SHOT:w_none ENTER x r DOWN UP ESC"
EXPECT["writer_empty"] = ["!/data/writer/recent.txt \"", "!@@RUN_NEXT"]



# Calc (forks/calc, PicoRuby): sheets in /data/calc, typing on the grid, formulas, copy and fill
CA_SHEET = "A1\tRent\nB1\t500\nA2\tFood\nB2\t320.5\nA3\tTotal\nB3\t=SUM(B1:B2)\n"
CA_SEED = {"/data": None, "/data/calc": None, "/data/calc/budget.txt": CA_SHEET,
           "/data/calc/recent.txt": "budget|budget.txt\n"}
CA_APPS = "1|Home|/home/ai/home\n2|Projector|/home/ai/projector\n4|Calc|/home/ai/calc\n"
CA_REG = dict(CA_SEED, **{"/data/area512": None, "/data/area512/apps.txt": CA_APPS})
# the one sheet from before the fork becomes "sheet", and the old file stays
SEEDS["calc_import"] = {"/data": None, "/data/sheet.txt": "A1\t1\nA2\t=A1*2\n"}
SCENARIOS["calc_import"] = "SHOT:c_files ENTER SHOT:c_grid"
EXPECT["calc_import"] = [rfs("/data/calc/sheet.txt", "A1\t1\nA2\t=A1*2\n"), rfs("/data/sheet.txt", "A1\t1\nA2\t=A1*2\n"),
                         rfs("/data/calc/recent.txt", "sheet|sheet.txt\n"), "@@SCREEN 2"]
# typing on the grid: digits and = start an entry, Enter goes down, Fn+right across
SCENARIOS["calc_type"] = ("n T:Cash ENTER 1 2 ENTER 3 . 5 ENTER = T:A1/A2 ENTER SHOT:c_typed UP UP UP RIGHT "
                          "SPACE T:Twelve RIGHT T:=a1*$A$2 ENTER DOWN DOWN s")
EXPECT["calc_type"] = [rfs("/data/calc/Cash.txt", "A1\t12\nB1\tTwelve\nC1\t=a1*$A$2\nA2\t3.5\nA3\t=A1/A2\n"),
                       "3.428571"]
# a formula's value: chains in any order, an empty cell is 0, text and loops are #ERR
SEEDS["calc_eval"] = {"/data": None, "/data/calc": None, "/data/calc/e.txt":
    "A1\t=A2+1\nA2\t=A3*2\nA3\t4\nB1\t=B4+1\nB2\t=AVG(A1:A3)\nB3\t=A1/0\nC1\t=C2\nC2\t=C1\nC3\t=COUNT(A1:B1)\n"
    "D1\tword\nD2\t=D1+1\nD3\t=7/2\n"}
SCENARIOS["calc_eval"] = "ENTER SHOT:c_eval"
EXPECT["calc_eval"] = ["@@SCREEN 9\n@@SCREEN 1\n@@SCREEN #ERR\n@@SCREEN word\n@@SCREEN 2\n@@SCREEN 8\n@@SCREEN 7\n"
                       "@@SCREEN #ERR\n@@SCREEN #ERR\n@@SCREEN 3\n@@SCREEN 4\n@@SCREEN #ERR\n@@SCREEN 2\n@@SCREEN 3.5\n"]
# copy and paste moves the references; $ stays; d fills down, r right; u undoes
SEEDS["calc_copy"] = CA_SEED
SCENARIOS["calc_copy"] = ("ENTER . . / / = T:B3*2 ENTER UP c / v d d u SHOT:c_copy ; ; ; ; = T:B$1+1 ENTER UP r s")
EXPECT["calc_copy"] = [rfs("/data/calc/budget.txt", "A1\tRent\nB1\t500\nD1\t=B$1+1\nE1\t=C$1+1\nA2\tFood\nB2\t320.5\n"
                                                    "A3\tTotal\nB3\t=SUM(B1:B2)\nC3\t=B3*2\nD3\t=C3*2\nD4\t=C4*2\n")]
# off the sheet: a paste whose reference would go before A
SEEDS["calc_edge"] = CA_SEED
SCENARIOS["calc_edge"] = "ENTER . . / c ; ; v SHOT:c_off x u ] SHOT:c_end [ g T:z99 ENTER d SHOT:c_z99"
EXPECT["calc_edge"] = ["@@SCREEN That's the edge of the sheet", "@@SCREEN Z99", rfs("/data/calc/budget.txt", CA_SHEET)]
# Esc cancels typing; BS deletes; x clears; w widens, saved as WIDTH lines
SEEDS["calc_edit"] = CA_SEED
SCENARIOS["calc_edit"] = "ENTER / ENTER BS BS BS T:1 ESC ENTER BS T:9 ENTER x SHOT:c_cleared ; w w SHOT:c_wide s ESC ESC"
EXPECT["calc_edit"] = [rfs("/data/calc/budget.txt", "A1\tRent\nB1\t509\nA2\tFood\nA3\tTotal\nB3\t=SUM(B1:B2)\nWIDTH\tB\t20\n")]
# find: text in a cell, round from the top, case not minded
SEEDS["calc_find"] = CA_SEED
SCENARIOS["calc_find"] = "ENTER f T:FOO ENTER SHOT:c_found f ENTER SPACE T:x ENTER ESC ESC"
EXPECT["calc_find"] = ['A1\\tRent\\nB1\\t500\\nA2\\tx\\n']
# Tab, then a digit: saves, leaves a place, hands off; back on the same cell
SEEDS["calc_switch"] = CA_REG
SCENARIOS["calc_switch"] = "ENTER . / 7 TAB SHOT:c_apps 2"
EXPECT["calc_switch"] = ["@@RUN_NEXT /home/ai/projector", "B2\\t7\\n",
                         rfs("/data/calc/place.txt", "screen: doc\nsel: 0\nfile: budget.txt\ncell: B2\n")]
SEEDS["calc_place"] = dict(CA_SEED, **{"/data/calc/place.txt": "screen: doc\nsel: 0\nfile: budget.txt\ncell: B2\n"})
SCENARIOS["calc_place"] = "SHOT:c_back 1 ENTER ESC ESC"
EXPECT["calc_place"] = ["B2\\t1\\n", "!/data/calc/place.txt"]
# Home's requests: open, new (with a name), delete into deleted/
SEEDS["calc_open"] = dict(CA_REG, **{"/data/area512/open.txt": "calc|open|budget.txt\n"})
SCENARIOS["calc_open"] = "4 ENTER ESC ESC"
EXPECT["calc_open"] = ["A1\\t4\\n", "@@RUN_NEXT /home/ai/home", "!/data/area512/open.txt"]
SEEDS["calc_new_req"] = dict(CA_REG, **{"/data/area512/open.txt": "calc|new|Cafe money\n"})
SCENARIOS["calc_new_req"] = "5 ENTER ESC ESC"
EXPECT["calc_new_req"] = [rfs("/data/calc/Cafe money.txt", "A1\t5\n")]
SEEDS["calc_del_req"] = dict(CA_REG, **{"/data/area512/open.txt": "calc|delete|budget.txt\n"})
SCENARIOS["calc_del_req"] = ""
EXPECT["calc_del_req"] = ["@@RUN_NEXT /home/ai/home", rfs("/data/calc/deleted/budget.txt", CA_SHEET),
                          rfs("/data/calc/recent.txt", "")]
# the menu bar and Help; a menu item runs as its key
SEEDS["calc_menu"] = CA_REG
SCENARIOS["calc_menu"] = "ENTER TAB SHOT:c_menu RIGHT SHOT:c_menu2 DOWN ENTER TAB ? SHOT:c_help ENTER TAB LEFT LEFT RIGHT ENTER"
EXPECT["calc_menu"] = ["@@RUN_NEXT /home/ai/home"]
# a big sheet stops at CELL_MAX
SEEDS["calc_full"] = {"/data": None, "/data/calc": None, "/data/calc/big.txt":
    "".join("%s%d\t%d\n" % (chr(65 + i % 5), i // 5 + 1, i) for i in range(249))}
SCENARIOS["calc_full"] = "ENTER ] / 1 ENTER 2 ENTER SHOT:c_full"
EXPECT["calc_full"] = ["@@SCREEN Full: 250 cells or 6 KB is the most. Start another sheet."]
# 8 KB: a bigger file isn't opened, and typing stops at the limit
# rows 1-48 of A and B, 59 bytes each: about 6,100 of the 6,144 (texts, tabs and 4 a cell)
SEEDS["calc_bytes"] = {"/data": None, "/data/calc": None,
    "/data/calc/huge.txt": "".join("A%d\t%s\n" % (i, "x" * 90) for i in range(1, 99)),
    "/data/calc/edge.txt": "".join("A%d\t%s\nB%d\t%s\n" % (i, "y" * 59, i, "z" * 59) for i in range(1, 49))}
SCENARIOS["calc_bytes"] = "ENTER SHOT:c_edge / / ENTER T:abcdefghijklmnopqrstuvwxyz ENTER ENTER T:abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefgh ENTER SHOT:c_bfull"
EXPECT["calc_bytes"] = ["@@SCREEN Full: 250 cells or 6 KB is the most. Start another sheet.", "@@SCREEN C2"]
SEEDS["calc_huge"] = SEEDS["calc_bytes"]
SCENARIOS["calc_huge"] = "DOWN ENTER SHOT:c_huge"
EXPECT["calc_huge"] = ["@@SCREEN huge is 10 KB: too big (6 KB most)"]
# nothing on the card: every key on the empty list is harmless
SCENARIOS["calc_empty"] = "SHOT:c_none ENTER x r DOWN UP ESC"
EXPECT["calc_empty"] = ["!@@RUN_NEXT"]

# Slide (forks/slide, PicoRuby): Writer's documents shown as decks, pages split by "---"
SL_TALK = ("# Corner cafe\nA plan in `three` stages\n---\n## Money\n- Rent 900 a month\n"
           "- Wages for two, and a very long line that has to wrap on both screens, the small one and the big one too\n"
           "---\n```\ncode line\n---\nstill code\n```\n---\n\n---\n### End\nThanks\n")
SL_APPS = "1|Home|/home/ai/home\n2|Projector|/home/ai/projector\n3|Writer|/home/ai/writer\n4|Slide|/home/ai/slide\n"
SL_SEED = {"/data": None, "/data/writer": None, "/data/writer/talk.txt": SL_TALK,
           "/data/writer/notes.txt": "Just notes\n", "/data/area512": None, "/data/area512/apps.txt": SL_APPS,
           "/data/slide": None, "/data/slide/recent.txt": "talk|talk.txt\n"}
# four pages (the blank one is skipped), Enter, Space and the bare / for the next; the last says so
SEEDS["slide_show"] = SL_SEED
SCENARIOS["slide_show"] = "SHOT:s_list ENTER SHOT:s_p1 ENTER SHOT:s_p2 SPACE SHOT:s_p3 / SHOT:s_p4 ENTER"
EXPECT["slide_show"] = ["@@SCREEN 4/4", "@@SCREEN Thanks", "@@SCREEN Last page. o: the decks"]
# a "---" inside a code block isn't a page break; back with BS and the bare ,
SEEDS["slide_code"] = SL_SEED
SCENARIOS["slide_code"] = "ENTER ] BS , / SHOT:s_code"
EXPECT["slide_code"] = ["@@SCREEN 3/4", "@@SCREEN code line\n@@SCREEN ---\n@@SCREEN still code"]
# a long line wraps after a space; the list's dash only on its first row
SEEDS["slide_wrap"] = SL_SEED
SCENARIOS["slide_wrap"] = "ENTER ENTER SHOT:s_wrap"
EXPECT["slide_wrap"] = ["@@SCREEN 2/4", "@@SCREEN Wages for two, and a very ", "!both screens, the small one and the big one too\n@@SCREEN -",
                        "!@@SCREEN Wages for two, and a very long line that has to wrap on both screens, the small one and the big one too"]
# the title of a page is one row; inline code is its own piece
SEEDS["slide_title"] = SL_SEED
SCENARIOS["slide_title"] = "ENTER SHOT:s_title"
EXPECT["slide_title"] = ["@@SCREEN Corner cafe\n", "@@SCREEN A plan in \n@@SCREEN three\n@@SCREEN  stages"]
# a page longer than the screen scrolls with j and the bare .
SEEDS["slide_scroll"] = dict(SL_SEED, **{"/data/writer/long.txt": "".join("Row %d\n" % i for i in range(1, 31)),
                                        "/data/slide/recent.txt": "long|long.txt\n"})
SCENARIOS["slide_scroll"] = "ENTER j . . k SHOT:s_scroll"
EXPECT["slide_scroll"] = ["@@SCREEN Row 3\n", "!@@SCREEN Row 2\n", "@@SCREEN 1/1"]
# Tab then a digit: to Writer, and the deck and page are kept for coming back
SEEDS["slide_switch"] = SL_SEED
SCENARIOS["slide_switch"] = "ENTER ENTER TAB SHOT:s_apps 3"
EXPECT["slide_switch"] = ["@@RUN_NEXT /home/ai/writer",
                          rfs("/data/slide/place.txt", "screen: doc\nsel: 0\nfile: talk.txt\npage: 1\n")]
SEEDS["slide_place"] = dict(SL_SEED, **{"/data/slide/place.txt": "screen: doc\nsel: 0\nfile: talk.txt\npage: 2\n"})
SCENARIOS["slide_place"] = "SHOT:s_back"
EXPECT["slide_place"] = ["@@SCREEN 3/4", "!/data/slide/place.txt"]
# e and n hand over to Writer: the deck to edit, or a new document
SEEDS["slide_edit"] = SL_SEED
SCENARIOS["slide_edit"] = "ENTER e"
EXPECT["slide_edit"] = ["@@RUN_NEXT /home/ai/writer", rfs("/data/area512/open.txt", "writer|open|talk.txt\n")]
SEEDS["slide_new"] = SL_SEED
SCENARIOS["slide_new"] = "n"
EXPECT["slide_new"] = ["@@RUN_NEXT /home/ai/writer", rfs("/data/area512/open.txt", "writer|new|\n")]
# without Writer there's nowhere to write a deck
SEEDS["slide_nowriter"] = dict(SL_SEED, **{"/data/area512/apps.txt": "1|Home|/home/ai/home\n4|Slide|/home/ai/slide\n"})
SCENARIOS["slide_nowriter"] = "e SHOT:s_nowriter"
EXPECT["slide_nowriter"] = ["@@SCREEN Decks are written in Writer: not here", "!@@RUN_NEXT"]
# Home's requests: open a deck; delete one (into Writer's deleted/, as Writer does) and go back
SEEDS["slide_open"] = dict(SL_SEED, **{"/data/area512/open.txt": "slide|open|notes.txt\n"})
SCENARIOS["slide_open"] = "SHOT:s_open"
EXPECT["slide_open"] = ["@@SCREEN notes\n@@SCREEN 1/1", rfs("/data/slide/recent.txt", "notes|notes.txt\ntalk|talk.txt\n"),
                        "!/data/area512/open.txt"]
SEEDS["slide_del_req"] = dict(SL_SEED, **{"/data/area512/open.txt": "slide|delete|talk.txt\n"})
SCENARIOS["slide_del_req"] = ""
EXPECT["slide_del_req"] = ["@@RUN_NEXT /home/ai/home", rfs("/data/writer/deleted/talk.txt", SL_TALK),
                           rfs("/data/slide/recent.txt", ""), "!/data/writer/talk.txt "]
# the first time: Slide's numbered pages, in number order, become the deck "slides"
SEEDS["slide_import"] = {"/data": None, "/home": None, "/home/tool": None, "/home/tool/slide": None,
                         "/home/tool/slide/2.md": "# Two\n", "/home/tool/slide/10.md": "# Ten",
                         "/home/tool/slide/1.md": "# One\n", "/home/tool/slide/notes.md": "not a page\n"}
SCENARIOS["slide_import"] = "SHOT:s_import ENTER ] SHOT:s_ten"
EXPECT["slide_import"] = [rfs("/data/writer/slides.txt", "# One\n---\n# Two\n---\n# Ten\n"),
                          rfs("/data/slide/recent.txt", "slides|slides.txt\n"), "@@SCREEN 3/3", "@@SCREEN Ten"]
# a deck gone from the card leaves recent.txt (Home lists it)
SEEDS["slide_prune"] = dict(SL_SEED, **{"/data/slide/recent.txt": "gone|gone.txt\ntalk|talk.txt\n"})
SCENARIOS["slide_prune"] = "SHOT:s_prune"
EXPECT["slide_prune"] = [rfs("/data/slide/recent.txt", "talk|talk.txt\n")]
# the menu bar: Page's last (]) and Deck's "o decks" back to the list
SEEDS["slide_menu"] = SL_SEED
SCENARIOS["slide_menu"] = "ENTER TAB SHOT:s_menu UP ENTER SHOT:s_last TAB RIGHT SHOT:s_menu2 DOWN ENTER SHOT:s_list"
EXPECT["slide_menu"] = ["@@SCREEN SLIDE\n@@SCREEN 2 decks", "!@@RUN_NEXT"]
SEEDS["slide_menu_last"] = SL_SEED
SCENARIOS["slide_menu_last"] = "ENTER TAB UP ENTER"
EXPECT["slide_menu_last"] = ["@@SCREEN 4/4"]
SEEDS["slide_huge"] = dict(SL_SEED, **{"/data/writer/huge.txt": "x" * 13000 + "\n",
                                      "/data/slide/recent.txt": "huge|huge.txt\n"})
SCENARIOS["slide_huge"] = "ENTER SHOT:s_huge"
EXPECT["slide_huge"] = ["@@SCREEN huge is 13 KB: too big (12 KB most)"]
# nothing on the card: every key on the empty list is harmless
SCENARIOS["slide_empty"] = "SHOT:s_none ENTER e x r DOWN UP ESC"
EXPECT["slide_empty"] = ["!@@RUN_NEXT"]


# Writer's Tab v: the document in Slide, on the cursor's line; Esc there comes back to Writer
SEEDS["writer_slides"] = dict(WR_SEED, **{"/data/area512": None, "/data/area512/apps.txt": SL_APPS})
SCENARIOS["writer_slides"] = "ENTER DOWN T:Hi TAB SHOT:w_slides v"
EXPECT["writer_slides"] = ["@@RUN_NEXT /home/ai/slide", rfs("/data/area512/open.txt", "slide|show|notes.txt:1\n"),
                           rfs("/data/writer/notes.txt", "The quick brown fox\nHijumps over the lazy dog\n"),
                           rfs("/data/writer/place.txt", "screen: doc\nsel: 0\nfile: notes.txt\nrow: 1\ncol: 2\nmode: type\n")]
SEEDS["writer_noslide"] = WR_REG
SCENARIOS["writer_noslide"] = "ENTER TAB v SHOT:w_noslide"
EXPECT["writer_noslide"] = ["@@SCREEN Slide isn't installed", "!@@RUN_NEXT"]
SEEDS["slide_from_writer"] = dict(SL_SEED, **{"/data/area512/open.txt": "slide|show|talk.txt:8\n"})
SCENARIOS["slide_from_writer"] = "SHOT:s_fromw ESC"
EXPECT["slide_from_writer"] = ["@@SCREEN 3/4", "@@RUN_NEXT /home/ai/writer", "!/data/area512/open.txt"]
SEEDS["slide_from_writer_o"] = SEEDS["slide_from_writer"]
SCENARIOS["slide_from_writer_o"] = "o SHOT:s_fromw_o"
EXPECT["slide_from_writer_o"] = ["@@SCREEN SLIDE", "!@@RUN_NEXT"]


def run_fork(name, app, script, screen):
    # the fork's sources, in main.manifest's order, from forks/<app>/ and lib/ruby/
    work = ROOT / "tests/.work" / name
    work.mkdir(parents=True, exist_ok=True)
    (work / ".keys").write_text(expand(script))
    (work / "seed.json").write_text(json.dumps(SEEDS.get(name, {})))
    files = []
    for e in (ROOT / "forks" / app / "main.manifest").read_text().split():
        rb = e.replace(".mrb", ".rb")
        src = ROOT / "forks" / app / rb
        files.append(str(src if src.exists() else ROOT / "lib/ruby" / rb))
    r = subprocess.run(["ruby", str(ROOT / "tests/rsim.rb"), str(work / ".keys"), str(work / "seed.json"),
                        screen] + files, capture_output=True, text=True, timeout=300)
    return r.stdout + r.stderr


def run(name, script, target, screen="cardputer"):
    if app_of(name) in FORKS:
        return run_fork(name, app_of(name), script, screen)
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
                return "UNWANTED " + want[1:].replace("@@FS ", "")[:40]
        elif want not in out:
            return "MISSING " + want.replace("@@FS ", "")[:40]
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
