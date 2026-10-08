#!/usr/bin/env python3
"""Run Projector in a512sim (AREA512's MicroPython + API mocks) along key scripts.

  tests/sim.py                 every scenario in SCENARIOS, against app/main.mpy
  tests/sim.py -v NAME         one scenario, print the last screen + SD files
  tests/sim.py --py            run main.py instead (line numbers in errors)

Script syntax: tokens separated by spaces; "T:some text" types the text (spaces
included, use _ for a space inside the token); ENTER ESC BS UP DOWN LEFT RIGHT as is.
"""
import os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTORY = pathlib.Path(os.environ.get("AREA512_FACTORY", pathlib.Path.home() / "area512-factory"))
SIM = FACTORY / "sim/a512sim"
PRELUDE = FACTORY / "sim/prelude.py"
HEAP_KB = int(os.environ.get("SIM_HEAP_KB", "128"))         # logic checks; memory is measured on the firmware (tests/fw.py, key %)


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
            "T:I_want_a_place_people_come_back_to ENTER 4 T:5k ENTER "
            "T:Plan ENTER T:3 ENTER T:-200 ENTER 1 1 y "
            "T:Build ENTER T:6 ENTER T:-2k ENTER 2 3 y "
            "T:Open ENTER T:6 ENTER T:-1000 ENTER 3 3 y "
            "T:Grow ENTER T:18 ENTER T:2500 ENTER 2 2 n ")

SCENARIOS = {
    # memory: hidden % key shows free KB in the footer
    "mem": "% SHOT:m_lib " + NEW_IDEA + "% SHOT:m_strip p l l % SHOT:m_play ESC c % SHOT:m_cracks ESC "
           "$ % SHOT:m_money ESC q",
    # create an idea, look at it, quit without saving more
    "new_idea": NEW_IDEA + "p l l l l ENTER ESC $ s s ESC ? ENTER q n q",
    # whole arc: premortem, face every crack, holds, judge, promote
    "full_arc": NEW_IDEA + "SHOT:strip p SHOT:play1 l l SHOT:play3 l l SHOT:playend ESC c SHOT:cracks ESC "
        "o T:I_lose_nerve_when_money_gets_tight ENTER "
        "T:the_balance_drops_below_1k,_I_will_call_my_mentor_before_deciding ENTER "
        "c ENTER 2 T:cut_hours_and_sell_beans_online ENTER "
        "DOWN ENTER 2 T:pause_and_take_part-time_work ENTER "
        "DOWN ENTER 2 T:hire_a_barista_for_opening_month ENTER "
        "DOWN ENTER 2 T:extend_the_window,_it's_fine ENTER "
        "DOWN ENTER 2 T:accept_it ENTER SHOT:faced ESC SHOT:holdstrip $ SHOT:money ESC "
        "p l l l l ENTER SHOT:holds x 3 2 3 T:a_place_I'm_proud_of ENTER y SHOT:charter "
        "ENTER T:Call_3_landlords_about_rent ENTER T:3_quotes_written_down ENTER T:45 ENTER "
        "y SHOT:commit y SHOT:committed x q",
    # reopen after a save in an earlier session: resumption note shown first
    "assumptions_vision": NEW_IDEA +
        "a a T:People_here_will_pay_$5_for_coffee ENTER a T:I_can_get_a_lease ENTER "
        "ENTER f T:test_a_market_stall_first ENTER d y ESC "
        "v DOWN ENTER BS BS BS T:now ENTER DOWN DOWN DOWN DOWN ENTER 1 ESC "
        "h l e DOWN ENTER BS T:9 ENTER ESC n T:Extra ENTER T:2 ENTER T:-1 ENTER 1 1 x y "
        "q y T:pick_up_at_the_lease ENTER q",
    # edge cases: empty library, ESC everywhere, zero stages, long text, archive
    "edges": "j k ENTER d a ESC a T:X ENTER ESC ESC ESC ESC "
             "p c ESC $ ESC P o ESC ? x v ESC a ESC n ESC x q "
             "a T:" + "Very_long_name_that_goes_past_the_cap_" * 2 + " ENTER "
             "T:" + "word_" * 40 + " ENTER ESC ESC ESC ESC "
             "q ENTER q d y d y ENTER q q",
    # memory stress: 7 stages, 100-char answers, 8 assumptions, everything faced, promote
    "big": 'a T:Biggest_idea_of_them_all ENTER T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_9 ENTER T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER 5 T:20k ENTER T:Stage1 ENTER T:9 ENTER T:-1500 ENTER 2 3 y T:Stage2 ENTER T:9 ENTER T:-1500 ENTER 2 3 y T:Stage3 ENTER T:9 ENTER T:-1500 ENTER 2 3 y T:Stage4 ENTER T:9 ENTER T:-1500 ENTER 2 3 y T:Stage5 ENTER T:9 ENTER T:-1500 ENTER 2 3 y T:Stage6 ENTER T:9 ENTER T:-1500 ENTER 2 3 y T:Stage7 ENTER T:9 ENTER T:-1500 ENTER 2 3  SHOT:big_strip % SHOT:big_mem a a T:assumption_number_0_that_is_quite_long_indeed_ok ENTER a T:assumption_number_1_that_is_quite_long_indeed_ok ENTER a T:assumption_number_2_that_is_quite_long_indeed_ok ENTER a T:assumption_number_3_that_is_quite_long_indeed_ok ENTER a T:assumption_number_4_that_is_quite_long_indeed_ok ENTER a T:assumption_number_5_that_is_quite_long_indeed_ok ENTER a T:assumption_number_6_that_is_quite_long_indeed_ok ENTER a T:assumption_number_7_that_is_quite_long_indeed_ok ENTER ESC o T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER BS BS BS BS BS T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER c ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER DOWN ENTER 2 T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER ESC % SHOT:big_faced s % SHOT:big_saved q q ENTER % SHOT:big_reopen P ENTER T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER T:abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_abcdefghi_ ENTER T:50 ENTER y y SHOT:big_committed x % SHOT:big_after q',
}


def run(name, script, target):
    work = ROOT / "tests/.work" / name
    work.mkdir(parents=True, exist_ok=True)
    for f in ("main.mpy", "main.py"):
        (work / f).write_bytes((ROOT / "app" / f).read_bytes())
    (work / ".keys").write_text(expand(script))
    r = subprocess.run([str(SIM), str(PRELUDE), ".keys", str(HEAP_KB), target],
                       cwd=work, capture_output=True, text=True, timeout=120)
    return r.stdout + r.stderr


def verdict(out):
    if "@@COMPILE_ERROR" in out:
        return "COMPILE_ERROR"
    if "@@RUNTIME_ERROR" in out:
        return "RUNTIME_ERROR"
    if "@@EXIT" in out:
        return "ok"
    return "?"


def main():
    args = sys.argv[1:]
    target = "main.py" if "--py" in args else "main.mpy"
    verbose = "-v" in args
    names = [a for a in args if not a.startswith("-")] or list(SCENARIOS)
    bad = 0
    for n in names:
        out = run(n, SCENARIOS[n], target)
        v = verdict(out)
        stats = next((l for l in out.splitlines() if l.startswith("@@STATS")), "")
        print("{:20} {:14} {}".format(n, v, stats.replace("@@STATS ", "")))
        if v != "ok" or verbose:
            keep = [l for l in out.splitlines() if not l.startswith(("@@HEAP",))]
            print("\n".join(keep[-60:]))
        bad += v != "ok"
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
