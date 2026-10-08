# Projector for AREA512 — plan

Status: v0.1 in progress (2026-10-08).
Sources: `Harness_Conceptual_Contract.md` v0.1 (rules), `Projector_Spec_v0.1.md` (intent),
`Harness_Spec_v0.2.md` §10 (promotion), and emu-commits/brain-harness (the web GoalGraph this evolves).

## What it is

A pocket **mental simulator** for an idea. You describe the idea in a few one-line answers, lay it
out as 1–7 stages, and **play it forward**. The app does the arithmetic and points out the
**cracks**: where the money runs out, where the hard stretches pile up, what you are only assuming.
You fix each crack, either by changing the plan or by **facing** it with an If-Then. When nothing
is left unanswered, **the projection holds**: the app replays the idea through to your own picture
of success and your own *why*. Then you can **promote** it to Harness on the SD card.

The spec's five tabs are still there, but they hang off one main screen (the film strip of
stages) instead of being five forms of equal weight.

## Psychology → mechanism

| Mechanism | In Projector |
|---|---|
| Episodic future thinking | **Play**: one screen per stage, "Month 4–12: BUILD", with cash in the likely and worst cases |
| Premortem (prospective hindsight) | "Jump to month 36. It didn't work out. What inside you got in the way?" → the WOOP Obstacle |
| Mental contrasting + If-Then (WOOP) | Every crack can be **faced** with "If it happens, I will…"; the charter's If-Then is required |
| Generation effect / autonomy | The user writes every word and number; the app only asks and calculates. No suggestions |
| Explicit uncertainty | Each stage has a confidence key (sure / rough / guess) that widens the best/worst cases |
| Planning fallacy | Hard stages overrun by a further 25% in the worst case |
| Working memory | One idea in focus; ≤ 4 chunks on the charter screen; one question per screen |
| Resumption | "Note to future you" on leaving; shown first the next time the idea is opened |
| Motivation | The HOLDS screen plays the strip to the finish, then shows your success picture + why |
| Deliberate commitment | Promote restates the charter, asks for a first action with Done-when, then y/n to commit |

## Cracks (deterministic, in severity order)

| Key | Crack | Fix it | Or face it |
|---|---|---|---|
| `out_base` | Cash runs out in the likely case | stage money / start cash | If-Then |
| `out_worst` | Cash runs out if it goes badly | same | If-Then |
| `horizon` | Takes longer than the window you chose | stage months / window | If-Then |
| `hardrun:<stage>` | Two hard stages back to back | difficulty / order | If-Then |
| `wildhard:<stage>` | A hard stage whose numbers are a guess | confidence | If-Then |
| `assume:<text>` | An assumption you haven't checked | mark it checked | If-Then |
| `endbelow` | Ends with less money than it starts | stage money | If-Then |
| `vague` | Success picture has no number in it | rewrite it | If-Then |
| `premortem` | No obstacle named | premortem | — (must fix) |
| `ifthen` | No plan for when the obstacle shows up | write one | — (must fix) |
| `nostage` | No stages | add one | — (must fix) |

**Holds** = at least one stage and every crack either fixed or faced.

## Projection math (integer, monthly)

Per stage: `months`, `net $/month` (negative = cost), `conf` 1–3, `diff` 1–3.
Spread by confidence: sure 10%, rough 30%, guess 60%.
- likely: as entered
- worst: months × (1 + spread [+25% if hard]), rounded up; costs × (1 + spread), income × (1 − spread)
- best: months × (1 − spread) (≥ 1); costs × (1 − spread), income × (1 + spread)

Running balance month by month from the starting cash. Outputs: lowest point and when, first month
below zero, ending balance, total months. That's all: no solver, no Monte Carlo (spec §3.3).

## Platform constraints that shaped this

- Screen 240×135 first (layout reads the sprite size; TERM512 gets more rows/cells).
- `Widget.input` blanks the screen and shows one label line (63-char cap), so the app draws its
  own question screens: question + hint + the whole wrapped answer stay visible while typing.
  Answers are one line, ≤ 100 characters (titles 24). Numbers accept `5k`.
- No clock: "last touched" and resumption use a **session counter** in `meta.txt`.
  ⚠ Harness's "≥ 3 days away" rule will need the same substitute (or a typed date).
- No `json`, no `import`: storage is line-based text (below).
- One `main.mpy`, compiled with area512-factory's `mpyc/a512c`; checked in `a512sim` at 96 KB
  heap and on the official firmware with `emu/fwrun.mjs`.

## Storage (`/Area512_data/data/projector/`)

    meta.txt              session: N / next_id: N
    library.txt           id|status|touched|title     (one line per idea)
    ideas/<id>.txt        one idea (format in PROMOTION_FORMAT.md §Idea file)

Promotion writes `/Area512_data/data/harness/inbox/goal-<id>.txt` (see `PROMOTION_FORMAT.md`).

## Screens and keys

- **Library**: `j/k` move, `Enter` open, `a` new idea, `d` archive, `q` quit.
- **New idea** (one question per screen): name → wish → success picture → why → window →
  starting money → stages (name, months, $/month, sure?, hard?, "another?").
- **Strip** (main): stages as cells, cash line, crack count / HOLDS.
  `h/l` stage, `p` play, `c` cracks, `e` edit stage, `n` new stage, `x` delete stage,
  `v` vision, `a` assumptions, `$` money, `o` obstacle (premortem), `P` promote, `s` save,
  `?` keys, `q` back.
- **Play**: `l/Enter` next, `h` back, `e` edit this stage, `f` face a crack here, `q` stop.
- **Cracks**: `Enter` → change the plan / face it.
- **Money**: best / likely / worst table and the balance line; `s` switches scenario.
- **Promote**: charter (4 chunks) → first action + Done-when + minutes → stages as seed
  tasks? → "Ready to commit?" → writes the goal file, marks the idea promoted (read-only after).

## Build order

1. Engine (projection + cracks) + storage, checked in the sim.
2. Library, new-idea flow, strip, stage editor.
3. Play, cracks + face, premortem, money, vision, assumptions.
4. HOLDS replay, judgment, promote + goal file.
5. Firmware run in the emulator with screenshots; heap check; README.

## Deferred (v0.2+)

Comparison view; scratch memo and calculator helpers (the `5k` number entry covers most rough
math); reordering stages; TERM512-specific layout testing (no 320×240 emulator yet).
