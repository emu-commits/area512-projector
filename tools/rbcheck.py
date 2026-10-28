#!/usr/bin/env python3
"""Fail on a method call mruby/c (AREA512's PicoRuby VM) has no method for.

  tools/rbcheck.py <file.rb>...

tests/rsim.rb runs the forks under CRuby, which has far more methods than mruby/c: a `map` or
an Array#insert passes there and raises NoMethodError on the device. This reads every
`.name` called in the files and looks for a method of that name anywhere it could come from:
mruby/c's C classes and mrblib, the picoruby and AREA512 gems (AREA512 checkout, $AREA512),
and the files themselves. By name only, not by class, so it catches a method that exists
nowhere (Array#delete passes: Hash has one).
"""
import os, pathlib, re, sys

AREA512 = pathlib.Path(os.environ.get("AREA512", pathlib.Path.home() / "area512"))
PICORUBY = AREA512 / "R2P2-ESP32/components/picoruby-esp32/picoruby"
# on the device, but defined where this doesn't look: STDIN.raw is picoruby-io-console's Ruby
# (Agenda uses it on the firmware)
SYNTAX = {"raw"}


def known():
    names = set(SYNTAX)
    # mruby/c's own classes: C and mrblib, all of it
    core = PICORUBY / "mrbgems/picoruby-mrubyc/lib/mrubyc"
    for f in list(core.glob("src/*.c")) + list(core.glob("mrblib/*.rb")):
        t = f.read_text(errors="ignore")
        names.update(re.findall(r'METHOD\(\s*"([^"]+)"', t))
        names.update(re.findall(r"^\s*def (?:self\.)?([a-z_][a-zA-Z0-9_]*[?!=]?)", t, re.M))
    # the gems' mruby/c bindings (their Ruby is left out: mruby's mrblib, other classes' defs)
    gems = [AREA512 / "components/area512/mrbgems"]
    gems += [d for d in (PICORUBY / "mrbgems").iterdir() if d.is_dir() and d.name != "picoruby-mruby"]
    for root in gems:
        for f in root.rglob("*.c"):
            names.update(re.findall(r'mrbc_define_method\([^"]*"([^"]+)"', f.read_text(errors="ignore"), re.S))
    return names


def calls(text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        code = re.sub(r'"(\\.|[^"\\])*"', '""', line.split(" #")[0])   # strings and comments out
        if code.lstrip().startswith("#"):
            continue
        for m in re.finditer(r"\.([a-z_][a-zA-Z0-9_]*[?!]?)", code):
            out.append((n, m.group(1)))
    return out


def main():
    files = sys.argv[1:]
    if not PICORUBY.is_dir():
        print("rbcheck: no AREA512 checkout at", AREA512, "(set AREA512)")
        return 1
    names = known()
    for f in files:
        names.update(re.findall(r"^\s*def (?:self\.)?([a-z_][a-zA-Z0-9_]*[?!=]?)", pathlib.Path(f).read_text(), re.M))
    bad = 0
    for f in files:
        for n, name in calls(pathlib.Path(f).read_text()):
            if name not in names:
                print("{}:{}: no method {} on the device".format(f, n, name))
                bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
