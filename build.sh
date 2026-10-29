#!/bin/sh
# Build the SD-ready apps in dist/<app>/ (copy each folder to the card, e.g. /home/ai/<app>/):
#
#   dist/projector/  core.mpy = lib/py/base.py + apps/projector/main.py (minus its last line)
#                    start.mpy = App().run(), main.manifest = "core.mpy / start.mpy"
#                    ovl/<name>.<n>: overlays from apps/projector/ov/ and lib/py/menu.py, one
#                    file per def (see tools/ovl.py and App.ov)
#   dist/home/       core.mpy = lib/py/base.py + lib/py/menu.py + apps/home/main.py, icons/
#   dist/agenda/     forks/<fork>/*.rb and lib/ruby/*.rb, compiled with AREA512's picorbc;
#   dist/writer/     main.manifest from the fork (ui.mrb first, then docs.mrb for Writer and
#   dist/calc/       Calc and Slide). tools/rbcheck.py first.
#   dist/slide/
#
# Why two files: launched as main.mpy, the firmware holds the whole .mpy in RAM for the entire
# run AND sizes the Python heap after reading it. Through main.manifest the heap is sized first
# and each entry's buffer is freed once it has run, so core.mpy's ~22 KB goes back to the app.
# MINIMUM has no import, so the shared lib/py/ files are put in front of each app's main.py.
set -e
cd "$(dirname "$0")"
A512C="${AREA512_FACTORY:-$HOME/area512-factory}/mpyc/a512c"
# the host picorbc of an AREA512 checkout (its R2P2-ESP32 build), the one that makes the
# bundled apps' .mrb files
PICORBC="${PICORBC:-${AREA512:-$HOME/area512}/R2P2-ESP32/components/picoruby-esp32/picoruby/build/host/bin/picorbc}"
rm -rf dist build && mkdir -p dist build

# py_app <name> <last line of main.py> <lib files...>
py_app() {
    name=$1; run=$2; shift 2
    out=dist/$name; b=build/$name
    mkdir -p "$out" "$b"
    tail -n 1 apps/$name/main.py | grep -qx "$run" || { echo "apps/$name/main.py must end with $run"; exit 1; }
    cat "$@" > "$b/core.py"
    head -n -1 apps/$name/main.py >> "$b/core.py"
    echo "$run" > "$b/start.py"
    (cd "$b" && "$A512C" core.py core.mpy && "$A512C" start.py start.mpy)
    cp "$b/core.mpy" "$b/start.mpy" "$out/"
    printf 'core.mpy\nstart.mpy\n' > "$out/main.manifest"
    cp apps/$name/README.md "$out/" 2>/dev/null || true
}

py_app projector 'App().run()' lib/py/base.py
# overlays: shipped as source (compiled on the device when entered), but every one is
# compiled here too so a syntax the device can't take fails the build
mkdir -p build/projector/ov build/projector/ovl
cp apps/projector/ov/*.py lib/py/menu.py build/projector/ov/
python3 tools/ovl.py build/projector/ov dist/projector/ovl build/projector/ovl
for f in build/projector/ovl/*.py; do "$A512C" "$f" build/projector/ovl/check.mpy || { echo "overlay $f does not compile"; exit 1; }; done

py_app home 'Home().run()' lib/py/base.py lib/py/menu.py
mkdir -p dist/home/icons
cp apps/home/icons/*.a5d dist/home/icons/

# rb_fork <name>: every .rb of the fork and lib/ruby/ to .mrb; each manifest entry must exist
rb_fork() {
    name=$1; out=dist/$name
    mkdir -p "$out"
    # CRuby (tests/rsim.rb) has methods the device lacks: none may be called
    python3 tools/rbcheck.py lib/ruby/*.rb forks/$name/*.rb || { echo "forks/$name calls a method mruby/c lacks"; exit 1; }
    for f in lib/ruby/*.rb forks/$name/*.rb; do
        "$PICORBC" -o "$out/$(basename "$f" .rb).mrb" "$f" || { echo "$f does not compile"; exit 1; }
    done
    cp forks/$name/main.manifest forks/$name/README.md "$out/"
    for e in $(cat forks/$name/main.manifest); do
        [ -f "$out/$e" ] || { echo "forks/$name/main.manifest: no $e"; exit 1; }
    done
}

rb_fork agenda
rb_fork writer
rb_fork calc
rb_fork slide

for d in dist/*; do echo "$d: $(ls "$d" | tr '\n' ' ')"; done
echo "projector overlays: $(ls dist/projector/ovl | wc -l) files"
