#!/bin/sh
# Build the SD-ready app in dist/projector/:
#   core.mpy   every definition (app/main.py minus its last line)
#   start.mpy  App().run()
#   main.manifest  "core.mpy / start.mpy"
#   ovl/<name>.<n> overlays from app/ov/, one file per def (see tools/ovl.py and App.ov)
# Why two files: launched as main.mpy, the firmware holds the whole .mpy in RAM for the entire
# run AND sizes the Python heap after reading it. Through main.manifest the heap is sized first
# and each entry's buffer is freed once it has run, so core.mpy's ~22 KB goes back to the app.
set -e
cd "$(dirname "$0")"
A512C="${AREA512_FACTORY:-$HOME/area512-factory}/mpyc/a512c"
OUT=dist/projector
rm -rf "$OUT" build && mkdir -p "$OUT" build
tail -n 1 app/main.py | grep -qx 'App().run()' || { echo "app/main.py must end with App().run()"; exit 1; }
head -n -1 app/main.py > build/core.py
echo 'App().run()' > build/start.py
(cd build && "$A512C" core.py core.mpy && "$A512C" start.py start.mpy)
cp build/core.mpy build/start.mpy "$OUT/"
printf 'core.mpy\nstart.mpy\n' > "$OUT/main.manifest"
cp app/README.md "$OUT/" 2>/dev/null || true
# overlays: shipped as source (compiled on the device when entered), but every one is
# compiled here too so a syntax the device can't take fails the build
mkdir -p build/ovl
python3 tools/ovl.py app/ov "$OUT/ovl" build/ovl
for f in build/ovl/*.py; do "$A512C" "$f" build/ovl/check.mpy || { echo "overlay $f does not compile"; exit 1; }; done
ls -l "$OUT"; ls "$OUT/ovl" | wc -l
