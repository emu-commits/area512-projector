#!/usr/bin/env python3
"""Run a Projector scenario on the REAL AREA512 firmware (area512-factory's emu/fwrun.mjs).

  tests/fw.py NAME [--out DIR]     -> DIR/projector-*.png, DIR/data/... (the card's files after)

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
    name = [a for a in args if not a.startswith("-") and a != str(out)][0]
    app = sim.ROOT / "dist/projector"          # ./build.sh output: main.manifest + core/start.mpy
    shutil.rmtree(out / "data", ignore_errors=True)
    keys = "j ENTER j R " + "WAIT " * 8 + "SHOT:start " + fw_script(sim.SCENARIOS[name]) + \
        " WAIT WAIT WAIT WAIT SHOT:end"
    r = subprocess.run(["node", str(sim.FACTORY / "emu/fwrun.mjs"), str(app), "--out", str(out),
                        "--dump", str(out), "--keys", keys], capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-2000:])
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()
