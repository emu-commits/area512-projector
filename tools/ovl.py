#!/usr/bin/env python3
"""app/ov/<name>.py -> dist/projector/ovl/<name>.<n>, one file per top-level def (the source
the device compiles on entry); the whole minified overlay also goes to build/ovl/<name>.py.

- every top-level def must start with "<name>_" (App.ov deletes what an overlay added, and
  two overlays can be loaded at once, so names must not collide)
- "# needs: other" bundles app/ov/other.py into this overlay (no reload per call)
- full-line comments and blank lines are dropped and indentation becomes 1 space per level:
  less to read from SD and less for the on-device compiler to hold.
"""
import pathlib, re, sys

src_dir, out_dir, full_dir = (pathlib.Path(a) for a in sys.argv[1:4])
out_dir.mkdir(parents=True, exist_ok=True)
MAX_DEF = 520


def check(name, text):
    for m in re.finditer(r"^(def|class) (\w+)|^(\w+)\s*=", text, re.M):
        n = m.group(2) or m.group(3)
        if not n.startswith(name + "_"):
            sys.exit("{}.py: top-level name {!r} must start with {!r}".format(name, n, name + "_"))


def minify(text):
    out = []
    for line in text.split("\n"):
        s = line.rstrip()
        if s.strip() == "" or s.lstrip().startswith("#"):
            continue
        n = len(s) - len(s.lstrip(" "))
        out.append(" " * (n // 4) + s.lstrip(" "))
    return "\n".join(out) + "\n"


for f in sorted(src_dir.glob("*.py")):
    name = f.stem
    text = f.read_text()
    check(name, text)
    parts = [text]
    for dep in re.findall(r"^# needs: (\w+)", text, re.M):
        dt = (src_dir / (dep + ".py")).read_text()
        check(dep, dt)
        parts.append(dt)
    body = minify("\n".join(parts))
    for chunk in body.split("\ndef "):
        if len(chunk) > MAX_DEF:
            sys.exit("{}.ovl: def {} is {} bytes; split it (max {}: the device compiles one def "
                     "at a time and needs ~13x its size)".format(name, chunk.split("(")[0].replace("def ", ""), len(chunk), MAX_DEF))
    # one file per def: the device reads and compiles them one at a time, so no step
    # needs a contiguous block bigger than one def (a fragmented heap has none)
    chunks = body.split("\ndef ")
    i = 0
    for c in chunks:
        if i > 0:
            c = "def " + c
        (out_dir / "{}.{}".format(name, i)).write_text(c.rstrip("\n") + "\n")
        i += 1
    (full_dir / (name + ".py")).write_text(body)          # for the compile check
    print("{:10} {:6} bytes in {} defs".format(name, len(body), len(chunks)))
