#!/usr/bin/env python3
"""Run Projector in a512sim (AREA512's MicroPython + API mocks) along key scripts.

  tests/sim.py                 every scenario in SCENARIOS, against dist/projector (./build.sh)
  tests/sim.py -v NAME         one scenario, print the last screen + SD files
  tests/sim.py --py            run build/core.py instead (line numbers in errors)

Script syntax: tokens separated by spaces; "T:some text" types the text (spaces
included, use _ for a space inside the token); ENTER ESC BS UP DOWN LEFT RIGHT as is.
"""
import os, pathlib, re, subprocess, sys

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
        "h l e DOWN ENTER BS T:9 ENTER ESC n T:Extra ENTER T:2 ENTER T:-1 ENTER 1 1 x y "
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
           "ENTER 5 T:20k ENTER"]                        # window 5 years, $20k
    for i in range(1, 8):                                # 7 stages, all hard and rough
        out.append("T:Stage{} ENTER T:9 ENTER T:-1500 ENTER 2 3".format(i))
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
SCENARIOS["arc_mem"] = SCENARIOS["full_arc"].replace(
    "SHOT:holdstrip $", "SHOT:holdstrip % SHOT:mem_strip $").replace(
    "p l l l l ENTER SHOT:holds", "p l l l l % SHOT:mem_end ENTER SHOT:holds").replace(
    "s SHOT:saved q", "% SHOT:mem_judged s SHOT:saved q")


def run(name, script, target):
    # Like the device: overlays on the card, then main.manifest's entries in order.
    work = ROOT / "tests/.work" / name
    work.mkdir(parents=True, exist_ok=True)
    dist = ROOT / "dist/projector"
    seed = ["_sim_fs['/home'] = None", "_sim_fs['/home/ai'] = None",
            "_sim_fs['/home/ai/projector'] = None", "_sim_fs['/home/ai/projector/ovl'] = None"]
    for f in sorted((dist / "ovl").iterdir()):
        seed.append("_sim_fs['/home/ai/projector/ovl/{}'] = {!r}".format(f.name, f.read_text()))
    (work / "seed.py").write_text("\n".join(seed) + "\n")
    for f in ("core.mpy", "start.mpy"):
        (work / f).write_bytes((dist / f).read_bytes())
    (work / ".keys").write_text(expand(script))
    files = ["seed.py", "core.mpy", "start.mpy"]
    if target == "py":
        (work / "core.py").write_bytes((ROOT / "build/core.py").read_bytes())
        (work / "start.py").write_bytes((ROOT / "build/start.py").read_bytes())
        files = ["seed.py", "core.py", "start.py"]
    heap = HEAP_KB
    if name == "big" and heap < 400:
        heap = 400          # its 3,500-key script is held in the sim's heap, not the app's
    r = subprocess.run([str(SIM), str(PRELUDE), ".keys", str(heap)] + files,
                       cwd=work, capture_output=True, text=True, timeout=300)
    return r.stdout + r.stderr


def verdict(out):
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
