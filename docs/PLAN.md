# Projector for AREA512 — plan

Status: v0.1 in progress (2026-10-08).
Sources: `Harness_Conceptual_Contract.md` v0.1 (rules), `Projector_Spec_v0.1.md` (intent),
`Harness_Spec_v0.2.md` §10 (promotion), and emu-commits/brain-harness (the web GoalGraph this evolves).

## What it is

A pocket **mental simulator** for an idea. You describe the idea in a few one-line answers, lay it
out as 1–7 stages, and **play it forward**. The app does the arithmetic and points out the
**cracks**: where the money runs out, where the hard stretches pile up, what you are only assuming.
You fix each crack, either by changing the plan or by **facing** it with an If-Then; a money
crack can also be **accepted** as a cost you choose to pay. When nothing
is left unanswered, **the projection holds**: the app replays the idea through to your own picture
of success and your own *why*.

**Harness hand-off: deferred** (user decision, 2026-10-08). Harness isn't built, and Projector gets
lots of use on its own first, so promotion is not in the UI. Its file format stays designed in
`PROMOTION_FORMAT.md` and the idea data still holds everything the contract's charter needs.

The spec's five tabs are still there, but they hang off one main screen (the film strip of
stages) instead of being five forms of equal weight.

## Psychology → mechanism

| Mechanism | In Projector |
|---|---|
| Episodic future thinking | **Play** is a film: each stage runs month by month on a chart (likely + worst as a ghost line), and an open money or window crack **freezes** it at its month: you meet the crack at a moment, not on a list |
| Premortem (prospective hindsight) | "Jump to month 36. It didn't work out. What inside you got in the way?" → the WOOP Obstacle |
| Mental contrasting + If-Then (WOOP) | Every crack can be **faced** with "If it happens, I will…"; the charter's If-Then is required |
| Values over money | A money crack in the plan as entered isn't a risk that *might* happen, so it can be **accepted**: where the money comes from (cash-out only) and why it's worth it. HOLDS then names the cost next to your picture of success (user, 2026-10-09: "cash isn't everything") |
| Generation effect / autonomy | The user writes every word and number; the app only asks and calculates. No suggestions |
| Explicit uncertainty | Each stage has a confidence key (sure / rough / guess) that widens the best/worst cases |
| Planning fallacy | Hard stages overrun by a further 25% in the worst case |
| Working memory | One idea in focus; ≤ 4 chunks on the charter screen; one question per screen |
| Resumption | "Note to future you" on leaving; shown first the next time the idea is opened |
| Motivation | The HOLDS screen plays the strip to the finish, then shows your success picture + why |
| Deliberate commitment | (deferred with the Harness hand-off) |

## Cracks (deterministic, in severity order)

| Key | Crack | Fix it | Or face / accept it |
|---|---|---|---|
| `out_base` | Cash runs out in the likely case | stage money / start cash | If-Then, or accept |
| `out_worst` | Cash runs out if it goes badly | same | If-Then, or accept |
| `horizon` | Takes longer than the window you chose | stage months / window | If-Then |
| `hardrun:<stage>` | Two hard stages back to back | difficulty / order | If-Then |
| `wildhard:<stage>` | A hard stage whose numbers are a guess | confidence | If-Then |
| `assume:<text>` | An assumption you haven't checked | mark it checked | If-Then |
| `endbelow` | Ends with less money than it starts | stage money | If-Then, or accept |
| `vague` | Success picture has no number in it | rewrite it | If-Then |
| `premortem` | No obstacle named | premortem | — (must fix) |
| `ifthen` | No plan for when the obstacle shows up | write one | — (must fix) |
| `nostage` | No stages | add one | — (must fix) |

**Holds** = at least one stage and every crack fixed, faced or accepted. An accepted crack is stored
as a faced one whose text starts with `=` (`F|out_base|=savings; worth it because ...`).

## Projection math (integer, monthly)

Money is entered **apart and kept apart** (user, 2026-10-09: one net figure a month was too hard to
work out in your head):
- per idea: `fixed` cost a month (rent, phone ...), carried by every stage;
- per stage: `months`, `one-time` spend at its start, extra `costs` a month, `income` a month
  (all ≥ 0), `conf` 1–3, `diff` 1–3. A new stage's costs start at the stage before's (ENTER keeps
  them: the user's own number, carried over).

Spread by the stage's confidence: sure 10%, rough 30%, guess 60%. It moves the stage's own numbers,
each in its bad (worst) or good (best) direction; the fixed cost isn't spread but lasts as long
as the stage does.
- likely: as entered; net a month = income − costs − fixed
- worst: months × (1 + spread [+25% if hard]), rounded up; one-time and costs × (1 + spread),
  income × (1 − spread)
- best: months × (1 − spread) (≥ 1); one-time and costs × (1 − spread), income × (1 + spread)

Why apart matters beyond input: a stage netting +$2.5k from $5k income and $2.5k costs used to
lose 30% of its *net* in the worst case; now its income loses 30% and its costs gain 30%.

Each stage is a drop for its one-time spend, then a straight line, so the projection keeps one
segment per stage (no per-month list). Running balance from the starting cash. Outputs: lowest point and when, first month
below zero, ending balance, total months. That's all: no solver, no Monte Carlo (spec §3.3).

## Platform constraints that shaped this

- Screen 240×135 first (layout reads the sprite size; TERM512 gets more rows/cells).
- `Widget.input` blanks the screen and shows one label line (63-char cap), so the app draws its
  own question screens: question + hint + the whole wrapped answer stay visible while typing.
  Answers are one line, ≤ 100 characters (titles 24). Numbers accept `5k`.
- No clock: "last touched" and resumption use a **session counter** in `meta.txt`.
  ⚠ Harness's "≥ 3 days away" rule will need the same substitute (or a typed date).
- No `json`, no `import`: storage is line-based text (below).
- ~53 KB of Python heap in total, measured on the official firmware. The app ships as main.manifest + core.mpy +
  start.mpy, with source overlays (`ovl/`, one file per def) compiled on entry; see README "Memory". Checked in
  `a512sim` and on the official firmware with `emu/fwrun.mjs`.

## Storage (`/Area512_data/data/projector/`)

    meta.txt              session: N / next_id: N
    library.txt           id|status|touched|title     (one line per idea)
    ideas/<id>.txt        one idea (format in PROMOTION_FORMAT.md §Idea file)


## Screens and keys

- **Library**: `j/k` move, `Enter` open, `a` new idea, `d` archive, `q` quit.
- **New idea** (one question per screen): name → wish → success picture → why → window →
  starting money → fixed costs a month → stages (name, months, one-time, costs a month,
  income a month, sure?, hard?, "another?").
- **Strip** (main): stages as cells, cash line, crack count / HOLDS.
  `h/l` stage, `p` play, `c` cracks, `e` edit stage, `n` new stage, `x` delete stage,
  `v` vision, `a` assumptions, `$` money, `o` obstacle (premortem), `s` save,
  `?` keys, `q` back.
- **Play** (overlay `film`): each stage animates (~23 fps on a real Cardputer; any key skips and
  counts as that key). Freeze frame: `f` face, `a` accept (money cracks), `e` fix, `l` play on.
  Stage card: `l/Enter` next, `h` back, `e` edit, `f` face, `q` stop. The header counts runs
  (`runs` field). The film never loads another overlay itself: it returns what to open
  (edit / accept / holds / cracks) and `App.play` opens it once the film is unloaded, then
  plays on from that stage. With the largest idea there isn't room for both at once.
- **Cracks**: `Enter` → change the plan / face it / accept the cost (money cracks) / open it again.
- **Money**: best / likely / worst table and the balance line; `s` switches scenario,
  `e` starting money, `f` fixed costs a month.
- **Holds**: replay to the finish, your proof and why, then the judgment (fruitful, feel, effort, worth it).

## Build order

1. Engine (projection + cracks) + storage, checked in the sim.
2. Library, new-idea flow, strip, stage editor.
3. Play, cracks + face, premortem, money, vision, assumptions.
4. HOLDS replay and judgment. (Promote + goal file: built, then taken out until Harness exists.)
5. Firmware run in the emulator with screenshots; heap check; README.

## Deferred (v0.2+)

Comparison view; scratch memo and calculator helpers (the `5k` number entry covers most rough
math); reordering stages; TERM512-specific layout testing (no 320×240 emulator yet).
