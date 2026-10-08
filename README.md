# Projector for AREA512

**Play your ideas forward.** A pocket mental simulator for the
[AREA512](https://github.com/engneer-hamachan/area512) OS on the M5Stack Cardputer ADV. You describe an
idea in a few one-line answers, lay it out as stages, and play it forward month by month. The app
does the arithmetic and points out the **cracks**: where the money runs out, where hard stretches
pile up, what you're only assuming. You fix each one, or *face* it with your own If-Then. When
nothing is left unanswered, **the projection holds**: Projector replays the idea through to your
own picture of success and your own reason why. Then you can promote it to Harness, the execution
app, as a committed goal.

It is the planning half of the system that [brain-harness](https://github.com/emu-commits/brain-harness)
(GoalGraph, for the web) began. It is built to the *Harness Conceptual Contract* v0.1. The app never
suggests ideas, words or numbers: it asks, and it calculates.

![the strip, play, cracks and promotion on the real firmware](docs/screens.png)

## Install

Copy `dist/projector/` (from a release, or `./build.sh`) to the card at
`/Area512_data/home/ai/projector/` (any folder works). In Filer, select the folder and press
`R`. Data lives in `/Area512_data/data/projector/`. Promoted goals go to
`/Area512_data/data/harness/inbox/`.

## How it works

- **[docs/PLAN.md](docs/PLAN.md)**: the design. Psychology → mechanism, the crack rules, the
  projection maths, screens and keys, and what was cut and why.
- **[docs/PROMOTION_FORMAT.md](docs/PROMOTION_FORMAT.md)**: the Projector → Harness file format (it closes
  the contract's open question §11), plus Projector's own idea file.
- **[app/README.md](app/README.md)**: the short help that ships on the card.

## Build and test

You need [area512-factory](https://github.com/emu-commits/area512-factory) checked out at
`~/area512-factory` (or set `AREA512_FACTORY`), with its `./setup.sh` run.

    ./build.sh               # app/main.py -> dist/projector/{main.manifest, core.mpy, start.mpy}
    tests/sim.py             # key-script scenarios in a512sim (AREA512's MicroPython + API mocks)
    tests/fw.py full_arc     # the same scenario on the OFFICIAL firmware, headless, with screenshots
                             # and the card's files copied back to tests/.fw/data/

Why it ships as a manifest of two files, not one `main.mpy`: launched as `main.mpy`, the firmware
holds the whole bytecode file in RAM for the entire run, *and* sizes the Python heap after
reading it. That left the app ~6 KB free. Through `main.manifest`, the heap is sized first and each
entry's buffer is freed once it has run, which gives ~19 KB free at the library. The hidden key `%` shows
free memory on any screen (it's measured by allocating 1 KB blocks).

Language level: AREA512's MicroPython is built at MINIMUM. No `import`, slicing, f-strings,
`min`/`max` or `json`. The app also draws its own question screens, because `Widget.input` blanks
the screen down to one label line.

MIT licensed.
