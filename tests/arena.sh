#!/bin/bash
# How much of the VM's 120 KB arena a Ruby app has to spare: tests/arena/arena.c runs the
# app's .mrb files on mruby/c on the PC, built with the firmware's settings (AREA512's
# build_config/area512.rb), the way the sandbox runs main.manifest, in arenas from 100 to
# 120 KB, 512 bytes apart. Running out depends on how the arena is cut up, not only on how
# much is used, so one size can pass where a larger one fails: "robust" is the smallest size
# from which every larger one passed. The PC's objects are bigger than the device's, so
# compare apps and versions with this; the device has the last word (tests/fw.py).
#
#   tests/arena.sh <app dir, e.g. dist/writer> <cardputer|term512> <card dir, holds data/> <keys>
#   ARENA=<bytes> tests/arena.sh ...    one run at that size, with free memory at each key
#
# keys are tokens as tests/sim.py's (ENTER ESC TAB BS SPACE UP...; one character each
# otherwise), no T: or WAIT expansion.
set -e
here=$(cd "$(dirname "$0")" && pwd)
mrbc="${AREA512:-$HOME/area512}/R2P2-ESP32/components/picoruby-esp32/picoruby"
work=$here/.work/arena
if [ ! -x $work/arena ] || [ $here/arena/arena.c -nt $work/arena ] || [ $here/arena/mocks.rb -nt $work/mocks.mrb ]; then
    mkdir -p $work/inc
    echo "/* metaprog.c needs nothing from it under mruby/c */" > $work/inc/mrc_common.h
    src=$mrbc/mrbgems/picoruby-mrubyc/lib/mrubyc
    gcc -O1 -w -I$work/inc -I$src/src -I$src/hal/posix -DPICORB_VM_MRUBYC -DPICORB_INT64 -DMRBC_INT64 \
        -DMAX_SYMBOLS_COUNT=2000 -DMRBC_USE_ALLOC_PROF -DMRBC_USE_MATH=1 -DMAX_VM_COUNT=255 \
        -DMAX_REGS_SIZE=255 -DMRBC_USE_FLOAT=2 -DMRBC_TICK_UNIT=10 -DMRBC_TIMESLICE_TICK_COUNT=1 \
        -DMRBC_CONVERT_CRLF=1 -DNDEBUG -D'MRBC_OUT_OF_MEMORY()=arena_oom()' -include stdio.h \
        -o $work/arena $here/arena/arena.c $src/src/*.c $src/hal/posix/hal.c \
        $mrbc/mrbgems/picoruby-metaprog/src/mrubyc/metaprog.c -lm
    echo 'SCREEN = [240, 135, 240, 135]' > $work/size_cardputer.rb
    echo 'SCREEN = [240, 135, 320, 240]' > $work/size_term512.rb
    for f in $work/size_cardputer.rb $work/size_term512.rb $here/arena/mocks.rb; do
        $mrbc/build/host/bin/picorbc --remove-lv -o $work/$(basename $f .rb).mrb $f
    done
fi
app=$1; size=$2; card=$3
echo "$4" > $work/keys
files="$work/size_$size.mrb $work/mocks.mrb"
for e in $(cat $app/main.manifest); do files="$files $app/$e"; done
run() {   # run <bytes> [trace]
    w=$(mktemp -d); cp -r $card/data $w/data
    out=$(ARENA_TRACE=$2 $work/arena $1 $w $work/keys $files 2>&1) || true
    rm -rf $w
    echo "$out"
}
if [ -n "$ARENA" ]; then run $ARENA 1; exit; fi
robust=""; fails=0; top_ok=1
for a in $(seq 122880 -512 102400); do
    if run $a | grep -q "@@DONE"; then
        [ $top_ok = 1 ] && robust=$a
    else
        top_ok=0; fails=$((fails + 1))
    fi
done
if [ -z "$robust" ]; then echo "fails at 120 KB"; run 122880 | tail -3; exit 1; fi
more=""; [ $robust = 102400 ] && more=" or more"
echo "robust from $robust bytes: $((122880 - robust))$more to spare; $fails of 41 sizes failed"
