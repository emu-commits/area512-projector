# A lifecycle shell for AREA512: feedback on the idea

Status: feedback, 2026-10-26. Nothing here is built. Open questions are at the end.

## The idea, as I understand it

AREA512 has no real graphical launcher: you start apps from the Filer. The obvious fix is a
Psion Series 3 style launcher (an icon bar, then Agenda, Data, Word, Calc, Sheet) and a suite of
PDA apps rebuilt to match. The proposal is to do something else. Projector (*should I do this,
and will it hold?*) and Harness (*doing it, checking it, learning from it*) together already
cover the whole lifecycle of a piece of work. So make **that lifecycle the launcher**, and have
every PDA app open from, and feed back into, one of its phases.

## Verdict

**Yes. It's the strongest idea AREA512 has for a personal shell, and it's worth designing for
from now on.** Three changes would make it work in practice instead of only on paper. They're
below, after the reasons.

### Why it's right

1. **It's what makes AREA512 different.** Every PDA launcher since the Psion is organised by
   *noun*: here are your apps, here are their files. A launcher organised by *verb* (capture,
   shape, commit, do, review) has rarely, if ever, shipped on a pocket device. A Psion clone would
   be nostalgia. This would be a reason to carry the device.
2. **The thinking is already done.** The Harness Conceptual Contract, brain-harness's SPEC
   (session modes, hooks, context assembler, handoff notes) and Projector's PLAN all hold the
   same rules: the user generates and the software asks and computes, one thing in focus, planning
   and doing kept apart, resume from a note. A shell built on the lifecycle is those rules applied
   to the whole device, not just one app.
3. **Working memory is the real constraint, and a shell is where it matters.** A grid of 12 icons
   asks *"what do you want to do?"*, which is the hardest question to answer when you pick up a
   device with a few spare minutes. A lifecycle home can answer *"where were you?"*: the handoff
   note, the one next action, the idea with two open cracks. That's the brain-harness context
   assembler at device scale.
4. **The data already flows one way.** Projector's idea file feeds PROMOTION_FORMAT.md, which
   feeds a Harness goal. Add a capture inbox at the front and a review log at the back and the
   loop is closed: review lessons and dropped ideas come back to Capture.
5. **The Psion lessons still apply, just pointed at a different axis.** What made the Series 3
   good wasn't the icons. It was one hotkey per app from anywhere, the file list under each icon
   (you saw *your stuff*, not programs), and one consistent menu and dialog grammar. All three
   carry over: one key per phase, the items in each phase listed under it, and one grammar
   (Projector's question screens and `j/k/Enter/q`) everywhere.

### What would sink it, and the changes that avoid it

**1. Not everything is a project.** Most PDA use isn't a goal: a phone number, a shopping list,
"what's on Thursday", a quick sum. If every note has to pass through a charter, the device
starts to feel like a coach and people go back to paper.
→ **Two speeds.** The lifecycle is the spine, but **Capture** and a plain **Ledger** (notes,
lists, contacts, dates) never ask for a why, a picture of success or an If-Then. An item enters
the guided path only when *you* choose to promote it ("this note is becoming an idea"). That's
the same rule Projector already follows for Harness (promotion is deliberate). Things that are
never meant to grow (games, Paint, Theme, Terminal) live on a **Shelf** outside the spine.

**2. "Rebuild every PDA app around the lifecycle" is the trap in the proposal.** Writer, Calc
and Scheduler already exist (in PicoRuby), and AREA512 apps can't call each other. Rewriting
them wastes effort, and their versions will keep improving upstream.
→ **Integrate through files, not code.** Each phase *uses* the existing tools for what they're
good at: Calc for the scratch maths Projector deferred, Writer for long-form notes and evidence,
Scheduler for "when and where will you do this?". The shell reads and writes their save files
(read-only at first) instead of replacing them. Build new apps only where there's nothing to
use: Capture, Harness, Review.

**3. Phases must not become walls.** brain-harness gives switching modes deliberate friction, and
that's right for Plan vs Execute. But a shell where you can't jot something down while in Do
will be abandoned.
→ **Capture works from anywhere** (one key, one line, back where you were), the same way
brain-harness's Execute mode allows an inbox add. Only *restructuring* (editing stages, charter,
commitments) is tied to its phase.

## The shape I'd suggest

    CAPTURE ──▶ SHAPE ──▶ COMMIT ──▶ DO ──▶ REVIEW
      ▲        (Projector) (charter)  (Harness)    │
      └──────── lessons, dropped ideas, next ──────┘

    LEDGER: notes · lists · contacts · dates     (never asks why)
    SHELF:  games · paint · theme · terminal · files

| Phase | Question it answers | Its items | Built from |
|---|---|---|---|
| **Capture** | "What's on my mind?" | one-line inbox entries | new, tiny; reachable from every phase |
| **Shape** | "Should I, and will it hold?" | ideas, cracks, HOLDS | **Projector** (as is) + Calc for scratch maths |
| **Commit** | "Am I in?" | charter, first action | Projector's promote step (PROMOTION_FORMAT.md, already designed) |
| **Do** | "What now?" | the one next action, timer, done-when, evidence | **Harness** Execute; Scheduler for when/where; Writer for evidence |
| **Review** | "What did reality say?" | estimates vs actuals, assumptions, lessons | Harness Review (brain-harness §6.4) |

### Home screen (240×135)

Not an icon grid. Agenda was the Psion app people lived in, and the Harness *Today* screen
plays the same part here. The home is a Today card plus a phase strip:

    ┌──────────────────────────────────────┐
    │ AREA512                    S41  ▮▮▮▯ │
    │ Corner cafe · DO                     │
    │ Next: call 3 landlords (45 min)      │
    │ You left off: "rent quotes; ask Ana" │
    │                                      │
    │ Inbox 3 · Cafe: 0 cracks · Review due│
    │ 1 Capture 2 Shape 3 Do 4 Review 5 ⋯  │
    └──────────────────────────────────────┘

- **One key per phase** (`1`–`4`, `5` for Ledger/Shelf). That's the Psion app hotkey, on the
  lifecycle axis.
- Inside a phase you see **your items**, not programs, like the Psion file list under each icon.
- The home suggests nothing new. Everything on it is the user's own words: the next action they
  wrote, the note they left, counts of their own open items. That keeps the contract's rule
  ("it asks, and it calculates").
- On TERM512 (once full screen works, see TERM512.md) the strip becomes a left-hand rail and the
  Today card gets room for the charter line.

### One item, many states

What makes this a shell and not a launcher is that **an item moves; apps don't own it.** One
shared index (line format, like `library.txt`):

    /Area512_data/data/area512/items.txt
    id|kind|phase|touched|title|file
    7|note|ledger|41|Ana's number|ledger/7.txt
    12|idea|shape|40|Corner cafe|projector/ideas/3.txt
    15|goal|do|41|Corner cafe|harness/goals/3.txt

Each app keeps its own detailed file (Projector's idea file doesn't change). The index is what
the home screen and phase lists read, so they never load an app's data to draw a list. Moving
phases (capture → idea, idea → goal) rewrites one index line and writes one new file, the
same arrival pattern PROMOTION_FORMAT.md already uses for the Harness inbox.

## Platform realities that decide the architecture

| Fact (checked in the area512 source) | Consequence |
|---|---|
| ~53 KB Python heap; Projector's resident core alone is ~15.5 KB | The shell can't keep apps resident. One phase loaded at a time, as overlays or as separate apps |
| No API for one app to launch another; the filer is the only launcher; `etc/` default UI is `graphical` or `terminal` only | A launcher written as an app can't start Writer or Calc today |
| No clock exposed to Python (Projector uses a session counter) | "Review due" and "3+ days away" need a substitute: ask "today's date?" once per power-on as the session-start ritual, prefilled from the last answer |
| Bundled apps are PicoRuby, ours are MicroPython | Integration has to be through files. Their save formats become a dependency to pin and test |
| Apps run in a 240×135 window on TERM512 | See TERM512.md |

Two ways to build it:

- **A. One app, phases as overlays.** Projector's overlay loader (`App.ov`) already proves the
  pattern: the shell core (index, question screens, home) stays resident and Shape/Do/Review load
  on entry. Works on today's firmware. Cost: Projector and Harness share one heap budget and
  one release, and the bundled Ruby apps stay a trip through the Filer.
- **B. A suite plus a small upstream change.** Separate apps sharing the index and formats, and
  one firmware addition: when an app exits, the filer runs the path in
  `/Area512_data/etc/next` if it's there, and the default UI accepts `default=app:<path>`. Each
  app then "returns to the shell" by writing `next`, and the shell becomes the boot screen.
  About as small as upstream changes get, and it also lets the shell open Writer, Calc and
  Scheduler directly.

**Recommendation:** design for **B**, start as **A**. Agree the shared index and file formats
first, because they hold under both. Prototype the home screen and Capture as overlays next to
Projector. Propose the `next`-app and full-screen changes upstream together, since both are
"let apps cooperate with the filer". If B lands, split into separate apps without touching
the data.

## Suggested order

1. **Formats.** `items.txt`, the capture line format, and PROMOTION_FORMAT.md extended to cover
   Capture → Shape. Paper only, cheap, decides everything else.
2. **Capture + home** as a thin layer in front of Projector: the index, a one-line inbox,
   "promote to idea" opening Projector's new-idea flow with the line as the wish.
3. **Harness MVP** (Commit + Do): re-enable the promote step (commit 1c3666f has the writer),
   then Today, done-when, a timer and the handoff note. Measure the heap at every step.
4. **Review**: estimates vs actuals, unchecked assumptions from `ASSUME|unchecked`, lessons
   back to Capture.
5. **Ledger and integrations**: read Scheduler's save file for when/where, link to Writer
   documents as evidence.
6. **Upstream**: the `next`-app hook, `default=app:`, and full screen for TERM512.

## Questions for you

1. **Scope of "all PDA apps".** Do you mean the bundled ones (Writer, Calc, Scheduler) brought
   into the flow, or new PDA basics we don't have yet (contacts, lists, a quick notes inbox)?
   I've assumed: use the bundled ones, build only what's missing.
2. **Two speeds.** Are you happy with a Ledger that never asks *why*, or do you want every item,
   even a phone number, to sit somewhere in the lifecycle?
3. **Upstream.** Are you willing to propose firmware changes to engneer-hamachan/area512 (the
   `next`-app hook and full screen)? Option B depends on it. A works without it.
4. **Repos.** Should the shell and Harness live here (making this repo the suite), or in a new
   repo with Projector as a component?
5. **Dates.** Is one "today's date?" question at power-on acceptable, or would you rather keep
   session counters and drop time-based prompts like "review due"?
