#!/usr/bin/env python3
"""Run a Projector scenario on the REAL AREA512 firmware (area512-factory's emu/fwrun.mjs).

  tests/fw.py NAME [--out DIR]     -> DIR/projector-*.png, DIR/data/... (the card's files after)
  tests/fw.py NAME --term512       on the TERM512 build: shots are the 320x240 lid screen
                                   (firmware: $FW_TERM512, default <factory>/vendor/Area512TFT7789.bin)
  tests/fw.py --keys "SCRIPT" ...  a script of your own instead of a scenario
  --seed big                       start with tests/seeds/big on the card (the largest idea);
                                   a path works too

Uses tests/sim.py's scenarios; SHOT:<name> tokens take screenshots. Each key is followed
by a short idle so the app finishes drawing before the next key arrives.
"""
import os, pathlib, shutil, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sim

def fw_script(script):
    out = []
    for tok in sim.expand_keep_shots(script).split():
        out.append(tok)
        if not tok.startswith("SHOT:"):
            out.append("WAIT")
    return " ".join(out)

def main():
    args = sys.argv[1:]
    out = pathlib.Path(args[args.index("--out") + 1]) if "--out" in args else sim.ROOT / "tests/.fw"
    opts = {}
    for k in ("--out", "--keys", "--seed"):
        if k in args:
            opts[k] = args[args.index(k) + 1]
    name = [a for a in args if not a.startswith("-") and a not in opts.values()]
    script = opts.get("--keys") or sim.SCENARIOS[name[0]]
    app = sim.ROOT / "dist/projector"          # ./build.sh output: main.manifest + core/start.mpy
    shutil.rmtree(out / "data", ignore_errors=True)
    keys = "j ENTER j R " + "WAIT " * 8 + "SHOT:start " + fw_script(script) + \
        " WAIT WAIT WAIT WAIT SHOT:end"
    # the emulator keeps thousands of compiled code blocks alive: past Node's 2 GB default heap
    # on a long scenario
    cmd = ["node", "--max-old-space-size=6144", str(sim.FACTORY / "emu/fwrun.mjs"), str(app), "--out", str(out),
           "--dump", str(out), "--keys", keys]
    if "--term512" in args:
        cmd += ["--fw", os.environ.get("FW_TERM512", str(sim.FACTORY / "vendor/Area512TFT7789.bin"))]
    if "--seed" in opts:
        cmd += ["--seed", str(sim.ROOT / "tests/seeds" / opts["--seed"])]   # a name, or a path
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-2000:])
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()
