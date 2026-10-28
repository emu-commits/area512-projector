# Projector 1.0 and the AREA512 suite: plan

Status: plan, 2026-10-28. Nothing here is built yet, apart from the full-screen opt-in on
`claude/term512-full-screen` (pushed, not yet built or run).

Sources: [PLAN.md](PLAN.md) (Projector today), [TERM512.md](TERM512.md),
[LIFECYCLE_SHELL.md](LIFECYCLE_SHELL.md) (decisions 1–5), [upstream/AREA512_ISSUES.md](upstream/AREA512_ISSUES.md),
and the AREA512 source at upstream `main` fc9f6f9. The bundled apps' current behaviour below was
read from their source in `storage/home/tool/`, not tried on a device.

## What changed upstream

Both firmware requests were merged into AREA512 `main` on 2026-10-28. They aren't in a release yet
(the latest is v2.7, 2026-10-18):

| API | MicroPython | PicoRuby | What it gives us |
|---|---|---|---|
| Full screen (#32) | `Display.screen_width()`, `screen_height()`, `full_screen()` | same, without parentheses | 320×240 on TERM512, opt-in, lasts until the app returns |
| Hand-off (#33) | `Area512.run_next(path)` | `Area512.run_next(path)` | when this app returns, the filer runs `path` as if you'd pressed `R`. Used once. An app that ends with an error doesn't hand off |
| Boot app (#33) | `default=app:<path>` in `/etc/ui` | same | a launcher can be the first screen |

That removes the two blockers in LIFECYCLE_SHELL.md. Issue B shipped as a function, not the
`/Area512_data/etc/next` file it describes, so AREA512_ISSUES.md is out of date (step 0.4).
Issue C (an uptime counter) was never filed and nothing in this plan needs it.

## The goal

One major version, four parts:

1. **Full screen.** Every app uses 320×240 on TERM512 and stays fully usable at 240×135 on a bare
   Cardputer.
2. **App switching.** From any app, two keys reach any other app, and you come back to where you
   were.
3. **One UI grammar, after the Psion Series 3.** The same keys mean the same thing in every app,
   every command sits in a menu with its shortcut beside it, and the screen always shows what you
   can press next.
4. **Usable productivity apps.** Forks of Writer, Calc, Scheduler and Slide (Paint optional) on
   that grammar: arrow keys everywhere, shortcuts on screen, no lost work.

Harness, Capture and the lifecycle index from LIFECYCLE_SHELL.md come after this. The switching
and file conventions here are what they will be built on, so nothing here has to be redone.

## Psion Series 3 principles, translated

The Series 3 screen was 240×80. A Cardputer has more pixels than that (240×135), and TERM512 has
more than a Series 3a (480×160 is wider, but 320×240 has more rows). The Psion's lessons were about
discipline, not screen size:

| Psion Series 3 | Here |
|---|---|
| **Menu key** opens a menu bar; every command is listed, with its hotkey on the right | **`Tab` opens the menu bar** in every app. Every command is in it, with its key beside it. That's where shortcuts are learned |
| **Esc** always backs out one level; Enter always confirms | `Esc` (the `` ` `` key) always backs out or cancels, `Enter` always opens or confirms. `q` stays as an alias for back |
| Application buttons under the screen: one press from anywhere | The menu bar's first menu is **Apps**, numbered: `Tab` `1`…`9` jumps to an app. On TERM512 the app row is always on screen, like the Series 3 silkscreen |
| System screen: an icon per app, **your files listed under it** | **Home** (the boot app) lists each app with its recent files, not just its name |
| Apps stay open; switching back finds you where you were | Apps can't stay open (one heap, ~53 KB). Each app **saves its place** on switch and restores it on start, so it feels the same |
| One dialog style: labelled lines, ←/→ cycles a choice, Enter OK, Esc cancel | One dialog style in every app, in both languages (below) |
| Diamond key, zoom, status window | Not copied. The status line on TERM512 does the job of the status window |

LIFECYCLE_SHELL.md chose not to build "a Psion icon bar plus a rebuilt PDA suite" and organise by
lifecycle phase instead. This plan doesn't reverse that. It takes the Psion's **interaction
grammar** (menus, keys, dialogs, files under apps) for every app now. The lifecycle home replaces
Home's layout later, once Harness and the items index exist (step 5.4).

## The UI grammar

One short document, `docs/UI.md`, written first (step 1.1) and followed by every app. Its content:

### Keys

| Key | Meaning everywhere | Notes |
|---|---|---|
| Arrows | move | `Fn` + `;` `.` `,` `/`. Outside text entry the **bare** `;` `.` `,` `/` also move (the arrows are printed on them, and Calc and Scheduler already do this). `h` `j` `k` `l` stay as aliases |
| `Enter` | open / confirm / next | |
| `Esc` (`` ` ``) | back / cancel / close menu | `q` is an alias, except in text entry |
| `Tab` | menu bar | unused by every bundled app except Theme (preview). Writer drops it today (code 9) |
| `Tab` `1`…`9` | switch app | the Apps menu |
| `?` | help: generated from the menu table, so it can't drift | |
| `n` new, `e` edit, `x` delete, `s` save, `f` find | the same letter for the same verb in every app | Writer, where letters type, uses `Ctrl` + the same letter |
| `%` | memory (hidden), in MicroPython apps | as today |

Not usable, from the firmware source: `Opt`/`Alt` + a letter arrives as Esc followed by the letter,
and `Widget.read_key` returns `ESC` and throws the letter away, so it can't be a Psion-style
command modifier. `Ctrl` + a letter arrives as a control byte (usable), except `Ctrl+H`/`I`/`J`/`M`,
which are Backspace, Tab, Enter and Enter. `Ctrl+C` is avoided, because it may interrupt MicroPython.
An optional upstream request (step 0.5) would make `Opt`+letter readable.

### Shortcuts on a small screen

Three layers, all generated from **one table per screen** (key, label, menu, priority), so the
hint bar, menus and help always agree:

1. **Hint bar** (bottom line, `Widget.hints`). Fits about 4 pairs at 240 px. The last slot is
   always `Tab menu`, so everything else is one key away. The other three are the screen's
   highest-priority commands. Today the strip shows `p c e n`, and `h/l x v a $ o s ? q` are only
   in the help.
2. **Menu bar** (`Tab`). Menus left to right, items with their key right-aligned, ←/→ between
   menus, ↑/↓ between items, `Enter` or the item's own key runs it. The menu returns the key and
   the app handles it as if it had been pressed, so there's no second code path.
3. **TERM512 extras.** Two-line hint bar (8 pairs), the app row, and on wide screens a command
   panel beside the content.

240×135, strip with the menu open:

    ┌ Apps  Idea  Stage  View ───────────────┐
    │ ┌Cafe────┐ ┌──────────────────┐        │
    │ │ Build  │ │ Play forward   p │        │
    │ │ 6 mo   │ │ Cracks         c │        │
    │ └────────┘ │ Edit stage     e │        │
    │            │ New stage      n │        │
    │  $ ▁▂▃▅▆▇  │ Delete stage   x │        │
    │            └──────────────────┘        │
    │ ←→ menu  ↑↓ item  ENT do  ESC close     │
    └────────────────────────────────────────┘

320×240, the same screen with nothing open:

    ┌ PROJECTOR · Corner cafe ─────────────── 2 cracks ┐
    │ ┌Find────┐ ┌Build───┐ ┌Open────┐ ┌Grow────┐      │
    │ │ 3 mo   │ │ 6 mo ! │ │ 4 mo   │ │ 12 mo  │      │
    │ └────────┘ └────────┘ └────────┘ └────────┘      │
    │  cash  ▇▆▅▃▂▁▁▂▃▅▆▇▇                              │
    │  low $-1.2k in month 9 (likely) ─ worst $-4.0k    │
    │ ──────────────────────────────────────────────── │
    │  ! Cash runs out in month 9, likely case          │
    │  ! Two hard stages back to back: Build, Open      │
    │ ──────────────────────────────────────────────── │
    │ p play  c cracks  e edit  n new  x del  $ money   │
    │ v vision  a assume  o obstacle  s save  Tab menu  │
    │ 1 Home  2 Projector  3 Writer  4 Calc  5 Agenda   │
    └──────────────────────────────────────────────────┘

### Dialogs and questions

Projector already draws its own question screens, because `Widget.input` blanks the screen. The
forks do the same and match them: title, the question, the answer with a cursor that ←/→ moves
inside the text, `Enter` OK, `Esc` cancel. Choices cycle with ←/→ (as on the Psion) and also take
`1`…`n`. Calc and Scheduler today read entries through the console (`read_entry` prints the prompt
and echoes), which goes.

### Layout at two sizes

**Design for 240×135, add at 320×240.** Every command works at 240×135. The bigger screen adds
panels (more list rows, a second pane, the app row, two hint lines), never commands. Layouts read
`Display.width()/height()` after the opt-in, as Projector already does.

## App switching

With `run_next`, switching is: save your place → `Area512.run_next(target)` → return. The filer
runs the target straight away. What every app needs:

| Piece | Where | Format |
|---|---|---|
| **App registry** | `/Area512_data/data/area512/apps.txt` | `digit|name|path`, one line per app, e.g. `2|Projector|/home/ai/projector`. Home writes it, finding apps where they're installed. Every app reads it to fill its Apps menu |
| **Place** | each app's own data folder, `place.txt` | screen, selection, open file. Read on start, then deleted (so a crash doesn't trap you on a bad screen) |
| **Open request** | `/Area512_data/data/area512/open.txt` | `app|verb|arg`, e.g. `calc|open|cafe.sheet`. Lets one app open another on a given file. The target reads it and deletes it, like `run_next` itself |
| **Back** | the same registry | `Esc` from an app's top screen goes to Home (if installed), not the filer |

Every format follows the existing conventions (PROMOTION_FORMAT.md): plain lines, `|` fields, no
JSON, files written in 900-byte parts on the MicroPython side.

**Saving on switch.** Projector saves only on `s`, and Writer, Calc and Scheduler only on their save
key: quitting loses work. Switching would make that far more common. Proposal: **switching saves
the open document** (and its place), and plain `Esc`/`q` out of the app asks "Save changes?" when
there are any. That changes a recorded decision ("s save, never automatic"), so it's open question 1.

**Home** is a small MicroPython app, set as `default=app:` in `/etc/ui`. It's the System screen:
one row per app, its two or three most recent files under it, `Enter` opens the app (or the file),
digits jump. On TERM512 it can show more files per app.

## Memory and full screen

- **Measure first.** BandedSprite bands are as wide as the screen, so each band costs a third more
  at 320 px, and the `EXT_DISPLAY` build's heap hasn't been measured. Before any layout work: run
  `claude/term512-full-screen` on a TERM512, press `%` on the biggest idea, and play the film.
  If it's tight, change the `BandedSprite(12)` argument so a band stays the same number of bytes
  (more passes per frame, same memory).
- **The menu is an overlay** in Projector (`ovl/menu`), loaded only while it's open. The hint
  tables are short strings in the core. Same for Home.
- **The Ruby forks** have their own VM heap, which hasn't been measured either. Measure each fork
  at 320×240 before and after the changes.
- **No emulator at 320×240.** a512sim and fwrun are 240×135 only, so TERM512 screenshots need the
  device. Extending fwrun to 320×240 (area512-factory) would let tests cover both sizes. Worth
  doing if TERM512 is the main device (open question 3).

## The productivity apps

Forks live in `forks/` (decision 1), stay PicoRuby, and each gets an `UPSTREAM.md` with the source
commit and what changed. A shared Ruby UI library (menu bar, hint table, dialogs, key reading,
place, registry) lives in `lib/ruby/` and `build.sh` copies it into each fork, the same way
`lib/` works for MicroPython (LIFECYCLE_SHELL.md, repo layout).

What each app does today, and what changes:

### Calc

Today: 26×26 cells. Moves with `h j k l` and the bare `; . , /`. `Fn`+arrow arrives as
`"\e[A"` (Writer relies on this), which Calc doesn't match, so it shows the help line instead of
moving. Edits go through the console. One file, `/data/sheet.txt`. `o` replaces the sheet without
asking, and quitting doesn't save.

1. Arrow keys, including `Fn`+arrow.
2. In-cell editor: ←/→ moves the cursor in the cell text, `Enter` commits and moves down, `Esc`
   cancels.
3. Several sheets through a file list (`Tab` → File → Open), and asking before replacing.
4. Copy and paste a cell, fill down, column width. References adjust on paste.
5. Full screen: more columns and rows, the cell's formula always shown in a line above the grid.
6. Integration: Projector's money table can open as a sheet (step 5.2).

### Scheduler → Agenda

Today: month calendar and a day view. The calendar takes the bare arrow keys, the day view only
`j/k`. `Fn`+arrow shows a help line in both. Events can be added and deleted, not edited. Times are
typed as `HH:MM`. One file, and quitting doesn't save. With no clock, it opens on the last date
used.

1. Arrow keys on both screens. `Enter` on an event edits it.
2. Time as a field: ↑/↓ steps 15 minutes, digits type it.
3. An **Agenda list**: upcoming events from the selected day on, as a scrolling list (the Psion
   Agenda's day/week views, in one list).
4. Full screen: month and the selected day side by side.
5. "Today" stays the last date used until there's a clock (LIFECYCLE_SHELL.md, Time).

### Writer

Today: arrows work. Commands are `Ctrl+S` save, `Ctrl+O` open, `Ctrl+Q` quit, `Ctrl+K`/`Ctrl+J`
page. They're only shown on the help line that `Esc` brings up. One document,
`/data/writer.txt`, and quitting doesn't save.

1. A hint bar with the `Ctrl` keys, and the Tab menu.
2. Several documents through a file list. A word and line count on the status line.
3. Line start and end (`Ctrl+A`/`Ctrl+E`), find (`Ctrl+F`), shown in the menu.
4. Full screen: more lines and columns.
5. Integration: notes for a Projector idea open as a Writer document (step 5.2).

### Slide

Today: `h/l` page, `j/k` scroll, `Esc` quits. Arrows don't work. One deck folder.

1. Arrows, `Enter`/space for the next page, page `3/12` in the header.
2. Pick a deck from a list. A Writer document can be shown as slides (`---` between pages) (step 5.2).
3. Full screen: larger text.

### Paint (optional)

Today: `h j k l y u b n`, no arrows, and **no save**: the picture is gone when you quit.
Arrows, save and open, and the palette with its keys on screen. Only if you use it (open question 2).

### Not forked

Theme and Gallery are system and demo apps. If upstream accepts the small fixes (step 0.6), they'll
get arrows too.

## Order

Each step ends with the tests green (`tests/sim.py`, `tests/fw.py`) and a heap measurement.

**0. Ground truth** (no new features)
- 0.1 Build and test `claude/term512-full-screen` with area512-factory (needs `./build.sh`,
  `tests/sim.py`), then run it on a TERM512 with firmware built from AREA512 `main`. Measure the
  heap with `%`, and check the window close animation after full screen.
- 0.2 Check on the device: `run_next` from MicroPython and from Ruby, and `default=app:`.
- 0.3 Check on the device what `Fn`+arrow sends to Calc and Scheduler (this plan reads it from the
  source).
- 0.4 Update AREA512_ISSUES.md (A and B done, as #32 and #33) and TERM512.md (done upstream).
- 0.5 Optional upstream issue: `Widget.read_key` returns `Opt`+letter as a named key instead of
  dropping the letter.
- 0.6 Optional upstream PRs: `Fn`+arrow in Calc, Scheduler and Slide. A few lines each, and good
  for every AREA512 user, not only this suite. The forks still happen.

**1. Grammar on paper**
- 1.1 `docs/UI.md`: keys, hint table, menu bar, dialogs, two layout sizes. Settle the open
  questions first.
- 1.2 `formats/APPS.md`: registry, place, open request.

**2. Projector 1.0** (MicroPython; the grammar's first user)
- 2.1 Key table per screen; hint bar and help generated from it. `Esc` backs out everywhere.
  One letter per verb (library `a` new → `n`, `a` kept as an alias; `d` archive → `x`).
- 2.2 Menu bar as an overlay.
- 2.3 Bare `; . , /` as arrows outside text entry; ←/→ cursor inside text entry.
- 2.4 320×240 layouts: strip with the money line and cracks on one screen, the library with a
  preview pane, a taller film.
- 2.5 Save-on-switch and place (after open question 1).

**3. Switching and Home**
- 3.1 Repo move to `apps/`, `forks/`, `lib/` (LIFECYCLE_SHELL.md layout), tests green before and after.
- 3.2 `lib/`: menu, hints, dialogs, registry, place, written in MicroPython and in Ruby (`lib/ruby/`).
- 3.3 Home app; `default=app:`; Apps menu in Projector.

**4. Forks**, one at a time, most-used first (open question 2). For each: fork with `UPSTREAM.md`,
then arrows and the grammar, save-on-switch and place, then the app's own list above, then full
screen.

**5. Together**
- 5.1 The app row and two-line hints on TERM512 everywhere.
- 5.2 Open requests between apps: Projector → Calc (money as a sheet), Projector → Writer (notes
  for an idea), Writer → Slide.
- 5.3 Release: one zip with Home, Projector, the forks, and the `/etc/ui` line, plus an install page.
- 5.4 Next major: Capture, Harness and the lifecycle home (LIFECYCLE_SHELL.md order, steps 2, 4–7).

## Open questions

1. **Save on switch?** Proposal: switching saves the open document; `Esc` out asks if there are
   changes. This changes "s save, never automatic".
2. **Which forks, in what order?** Proposal: Agenda (Scheduler), Writer, Calc, Slide. Paint only if
   you use it.
3. **Main device?** If TERM512 is where you'll use the suite most, extending fwrun to 320×240
   earns its cost. If it's the Cardputer, design and test at 240×135 and check TERM512 by hand.
4. **`Tab` for the menu?** The alternative is `Esc` opening the menu on an app's top screen. That's
   one less key to learn, but `Esc` would then mean two things.
5. **Home first or lifecycle first?** This plan puts a Psion System-style Home in front now and the
   lifecycle home later. Doing the lifecycle home now means building Capture and the items index
   in this version.
