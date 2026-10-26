# A lifecycle shell for AREA512

Status: design direction, 2026-10-26. Nothing here is built yet. Round 1 was feedback on the idea.
Round 2 (this version) adds your answers: fork the bundled apps, a lifecycle with no friction, one
repo, no date question.

## The idea

AREA512 has no real graphical launcher: you start apps from the Filer. Instead of a Psion
Series 3 style icon bar plus a rebuilt PDA suite, **make the lifecycle of a piece of work the
shell**. Projector (*should I do this, and will it hold?*) and Harness (*doing it, checking it,
learning from it*) already cover that lifecycle. Every PDA app opens from, and feeds back into,
one of its phases.

## Verdict

**Yes.** Every PDA launcher since the Psion is organised by *noun*: here are your apps, here are
their files. One organised by *verb* (capture, shape, commit, do, review) is new on a pocket
device. It's the Harness contract's rules (the user writes, the software asks and computes; one
thing in focus; resume from a note) applied to the whole device. And it answers the question that
matters when you pick up a device with five spare minutes: not *"what do you want to open?"* but
*"where were you?"*

The Psion lessons still apply, on a different axis: one hotkey per app from anywhere, *your
items* listed under each icon (not programs), and one menu and dialog grammar everywhere.

## Decisions

| # | Decision (2026-10-26) | Consequence |
|---|---|---|
| 1 | The bundled apps are too hard to use: **fork** Writer, Calc and Scheduler for usability and app-to-app integration | Forks live in this repo (`forks/`). They stay PicoRuby, so the suite is mixed-language and integrates through shared files |
| 2 | **No "why" questions** outside Projector's own flow. The lifecycle has to work transparently, with no friction at creation or later | The lifecycle is an *index over items*, inferred from what you do, never a field you fill in (below) |
| 3 | File the upstream asks: **full screen is a dealbreaker** | `docs/upstream/AREA512_ISSUES.md`: A full screen, B app hand-off, C uptime counter |
| 4 | Build on brain-harness; keep **all AREA512 code in this repo** | Folder layout below; brain-harness's engine fixtures become our conformance tests |
| 5 | **Never ask the date** | Harness is designed clock-free; a clock only adds to it (below) |

## A lifecycle you don't notice (decision 2)

The rule: **an item's phase is derived from what you did with it, never asked.** Nothing on a
creation screen mentions phases, and you can always find an item by what it is (a note, a list,
an event) as well as by where it is in the lifecycle.

| What you do | What the shell records | You see |
|---|---|---|
| Type a line anywhere (Capture key, any app) | `note`, phase **capture** | It's in Notes, as you'd expect |
| Tick-box a line, or add it to a list | `task`, still **capture** | It's in Lists |
| Give it a day in the agenda | `task` + day | It's on that day *and* in the Do lane on the day |
| Press `p` (play it forward) on a note | Projector opens with the note as the wish; phase **shape** | The idea, in Projector |
| Projector says HOLDS and you promote it | goal; phase **commit → do** | Its first action in Do |
| Finish a task / reach a stage | progress; may make **review** due | "What did reality say?" when there's something to review |

That keeps the contract's rule ("it asks, and it calculates"):
- **Phases are inferred from actions, never from content.** The shell never reads a note and
  decides "this looks like an idea": that would be a suggestion, and an opaque one.
- **Inference is visible and reversible.** Each item shows its phase as a quiet tag, and one key
  moves it back. Nothing is ever hidden because of its phase.
- **Projector still asks its questions** (picture of success, why, obstacle), but only once you
  choose to play something forward. That's the one deliberate step, and it's the point of
  Projector.

## The shape

    CAPTURE ──▶ SHAPE ──▶ COMMIT ──▶ DO ──▶ REVIEW
      ▲        (Projector) (charter)  (Harness)    │
      └──────── lessons, dropped ideas, next ──────┘

    Notes · Lists · Agenda · Calc · Writer   (every item also reachable by kind)
    Shelf: games · paint · theme · terminal · files

| Phase | Question | Items | App |
|---|---|---|---|
| **Capture** | "What's on my mind?" | lines, list items | new, tiny; one key from every app |
| **Shape** | "Should I, and will it hold?" | ideas, cracks, HOLDS | **Projector** + forked **Calc** for scratch maths |
| **Commit** | "Am I in?" | charter, first action | Projector's promote step (PROMOTION_FORMAT.md) |
| **Do** | "What now?" | the next action, done-when, evidence | **Harness**; forked **Scheduler** as the agenda; forked **Writer** for evidence |
| **Review** | "What did reality say?" | estimates vs actuals, assumptions, lessons | Harness Review (brain-harness §6.4) |

### Home screen (240×135; on TERM512, a left-hand phase rail)

    ┌──────────────────────────────────────┐
    │ AREA512                    #41  ▮▮▮▯ │
    │ Corner cafe · DO                     │
    │ Next: call 3 landlords (45 min)      │
    │ You left off: "rent quotes; ask Ana" │
    │                                      │
    │ Inbox 3 · Cafe: 0 cracks · Review ●  │
    │ 1 Capture 2 Shape 3 Do 4 Review 5 ⋯  │
    └──────────────────────────────────────┘

`#41` is the session number, not a date. Everything on the card is the user's own words or a
count of their own items.

### One item, many states

**An item moves between phases; no app owns it.** One shared index, in the same line format
as `library.txt`:

    /Area512_data/data/area512/items.txt
    id|kind|phase|seq|title|file
    7|note|capture|212|Ana's number|notes/7.txt
    12|idea|shape|230|Corner cafe|projector/ideas/3.txt
    15|goal|do|241|Corner cafe|harness/goals/3.txt

`seq` is a counter that goes up on every change (see Time). Each app keeps its own detailed file.
The home screen and the phase lists read only the index. A phase change rewrites one line, and a
promotion writes one new file into the next app's inbox, as PROMOTION_FORMAT.md already does.

## Time without a clock (decision 5)

**It isn't a dealbreaker for Harness, and you don't need GPS.** Most of what brain-harness uses
dates for works as well, or better, on order, sessions and progress. A clock adds to the design;
it is never required.

**What the device knows today, with no hardware and no questions:**
- *order*: a counter that goes up on every write (`seq`), so "before/after" and "since you last
  did X" are exact;
- *sessions*: Projector's launch counter, shared across the suite;
- *your own numbers*: estimates, actual minutes (Harness's post-task hook asks for them anyway)
  and stage months;
- *progress*: tasks done, stages reached, cracks closed.

**How brain-harness's date rules translate:**

| brain-harness (dates) | AREA512 (no clock) |
|---|---|
| "≥ 3 days away → show the handoff note first" | Show the handoff note first **every** time you enter Do. Free, and never wrong |
| Weekly Review prompt | Review is due when there's something to review: **N tasks done** since the last one, a stage finished, or a crack you faced came true. Event-driven beats weekly |
| Stuck: blocked > 14 days | Blocked across **5 sessions**. The other two stuck rules are already session- and minutes-based |
| Forecast: finish date | **Work left** (hours, low–base–high, from your estimates × your calibration) and **sessions left** at your recent pace. On a calendar: "about 14 weeks at the pace you've kept", never a date |
| Calibration (predicted vs actual) | Unchanged: minutes vs minutes |
| Projector's month timeline | Unchanged. *Where you are on it* moves with progress: finishing a stage's tasks moves you to the next stage, and that's the moment the shell asks "how many months did that stage really take?". One number, at a moment that matters, and it feeds calibration |
| Task timer | Needs an uptime counter (upstream issue C, small). Until then, "how long did it take?" is pre-filled with your estimate |

**Where a clock really matters: the agenda.** A forked Scheduler can't know which day *today*
is. Without a clock it opens on the last day you used, and the Do lane shows *"next on the
agenda"* (the earliest item after the last one you ticked) instead of *"today"*. That's usable,
but it's the one place where the device is noticeably worse without real time.

**Getting real time, from cheapest:**
1. **Pick it up when it passes by.** If the transfer tool that copies files from a computer also
   sent the host's time (upstream issue C, optional part), the ESP32's clock would be right from
   the last sync until the next power-off. No hardware, no question. Would need the firmware.
2. **An RTC unit on the Grove port (recommended if you want dates).** For example an M5Stack
   *Unit RTC* (BM8563, coin cell): a few dollars, set once, right for years. AREA512's **Ruby
   API already has I2C**, so a small Ruby helper could read it and write the time to a file for
   Python apps today. Better: the firmware reads it at boot and exposes `System.time()` (issue
   C). Check the Cardputer ADV's own spec first: if it has an RTC chip on board, this is free.
3. **GPS: not recommended.** It gives the time only after a fix (outdoors, from seconds to
   minutes), costs battery, and needs UART, which AREA512 doesn't expose to Python. Plus a bulky
   module for something an RTC unit does better.

**Recommendation:** build Harness clock-free now (the rules above). Treat the time as optional
data (`time: 0` means unknown) so an RTC unit, if you add one later, makes the agenda show
"today" and the forecast show dates, with no other change.

## Is app launching required? (upstream issue B)

**For this plan, yes, in practice.** Decision 1 makes the suite mixed-language: the forks are
PicoRuby, and Projector, Harness and the shell are MicroPython. A MicroPython overlay can't load
Ruby, and the heap (~53 KB) can't hold two apps at once. Without a hand-off, every switch is
quit → Filer → find the folder → `R`, and the shell can never be the first screen. That's
exactly the friction decision 2 rules out.

What still works **before** issue B lands:
- one MicroPython app holding Capture + home + Projector + Harness as overlays (Projector's
  `App.ov` already proves the pattern);
- the forks reading and writing the shared index, launched from the Filer as now;
- every format and the folder layout, unchanged when B lands, because only launching changes.

What B unlocks: `q` from any app returns to the shell, the shell opens the forks directly, and
`default=app:` makes the shell the boot screen.

Because of that, file **A and B together**. They're separate issues, but both say "let apps
cooperate with the filer".

## Repo layout (decision 4)

Everything for AREA512 stays in this repo. Move Projector the first time shell code arrives, so
`build.sh` and the tests move once:

    apps/
      projector/          today's app/ (main.py, ov/), unchanged inside
      harness/            Commit + Do + Review
      shell/              home, Capture, the items index
    forks/                PicoRuby forks, each with UPSTREAM.md (source commit, what changed)
      writer/  calc/  scheduler/
    lib/                  shared MicroPython: storage in parts, question screens, overlay
                          loader, index. MINIMUM has no import, so build.sh copies lib/ into
                          each app's sources (the same way tools/ovl.py already splits overlays)
    formats/              PROMOTION_FORMAT.md, ITEMS.md, each app's file format: the contract
                          between apps
    tests/                per app + conformance/ (brain-harness fixtures)
    tools/  docs/  docs/upstream/

The repo name could later change to something like `area512-suite`; GitHub redirects the old URL.

**Building on brain-harness without copying its UI:** its `src/core/` engines are pure and
covered by language-agnostic JSON fixtures (`fixtures/calibration`, `finance`, `graph`,
`schedule`). Port the engines Harness needs on the device (next action, calibration, stuck,
progress; the scheduler later, with relative days) to MicroPython, and run the **same fixtures**
against the ports in `tests/conformance/`. The web app and the device then agree by test, not by
hope. Its SPEC (session modes, hooks, context assembler) is the Harness design. Only the parts
that assume a clock change, as listed above.

## Platform realities (checked in the area512 source)

| Fact | Consequence |
|---|---|
| ~53 KB Python heap; Projector's resident core is ~15.5 KB | One phase loaded at a time. Port only the brain-harness engines the device needs |
| No API for one app to launch another; default UI is `graphical` or `terminal` | Issue B |
| On TERM512 every app is held in a 240×135 window | Issue A, see TERM512.md |
| No clock or uptime for Python; Ruby has I2C, Python doesn't | Clock-free design; issue C; RTC unit optional |
| Bundled apps are PicoRuby, ours MicroPython | Integration through `formats/`, pinned and tested |

## Suggested order

1. **File issues A and B** (and C if you want the timer).
2. **Formats**: `formats/ITEMS.md` (the index and `seq`), the capture line, and
   PROMOTION_FORMAT.md extended to cover Capture → Shape. Paper only, and it decides everything
   else.
3. **Repo move** to the layout above, with `lib/` split out of Projector. Tests green before
   and after.
4. **Shell + Capture** in front of Projector: the index, the inbox, `p` to play a note forward.
5. **Harness MVP**: re-enable promote (commit 1c3666f), then Do: next action, done-when,
   handoff note, clock-free rules. brain-harness fixtures ported first. Heap measured at each
   step.
6. **Forks**, most painful first (probably Scheduler, as the agenda): usability, then the index.
7. **Review**, then TERM512 layouts once A lands.

## Still open

- Which bundled app hurts most? That decides the first fork.
- Does your Cardputer ADV have an RTC on board, and would you add a Grove RTC unit if not?
  (Only the agenda really needs one.)
