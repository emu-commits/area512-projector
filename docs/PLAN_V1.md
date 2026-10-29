# Projector 1.0 and the AREA512 suite: plan

Status: plan, 2026-10-28, round 3 (all questions answered, below). Steps 0 to 4 are built
(Agenda, Writer, Calc and Slide); each step's status is under *Order*, in italics.

## Decisions

| # | Decision (2026-10-28) | Consequence |
|---|---|---|
| 1 | **Switching apps saves automatically** | Replaces Projector's "s save, never automatic". `s` stays for saving without leaving. `Esc` out of an app with unsaved changes asks first |
| 2 | **`Tab` opens the menu bar** in every app | `Tab` then a digit switches app |
| 3 | **No Paint fork**: it's too hard to use with only the keyboard | Forks are Agenda (Scheduler), Writer, Calc and Slide |
| 4 | **Home is Psion-style graphical icon navigation** | A System screen with an icon per app and its files under it (below). LIFECYCLE_SHELL.md's phase-organised home doesn't become the home screen |
| 5 | **Scheduler is the first fork** | Then Writer, Calc, Slide |
| 6 | **TERM512 is the main device** | Layouts are designed at 320×240 first and checked at 240×135. The emulators get a 320×240 mode (step 0.7) so tests cover the main device |
| 7 | **One key at a time.** Holding two keys at once is hard on the Cardputer keyboard, so no command or movement needs a chord | Bare `; . , /` move; `Fn`+arrow still works but is never needed. Commands are one key, or a sequence like `Tab` then `s`. Shifted keys (`$` `?`) become plain letters or menu items. `Shift` is only for typing. No `Opt`/`Ctrl` commands (step 0.5 dropped) |
| 8 | **Never change the stock apps upstream: fork them** into this repo for full control | Steps 0.5 and 0.6 dropped. Every fix to Calc, Scheduler, Writer or Slide (the `Fn`+arrow bug included) is made in our fork |
| 9 | **Writer's Move mode is `Tab` › Move**; `Esc` keeps one meaning, back | In Move, `Esc` goes back to typing |

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
4. **Usable productivity apps.** Forks of Writer, Calc, Scheduler and Slide on that grammar:
   arrow keys everywhere, shortcuts on screen, no lost work.

Home ties them together: a Psion-style screen of app icons, the first thing you see when the
device starts.

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
| System screen: an icon per app, **your files listed under it** | **Home** (the boot app): a row of app icons, ←/→ between apps, ↑/↓ through the selected app's files, `Enter` opens (below) |
| Apps stay open; switching back finds you where you were | Apps can't stay open (one heap, ~53 KB). Each app **saves its place** on switch and restores it on start, so it feels the same |
| One dialog style: labelled lines, ←/→ cycles a choice, Enter OK, Esc cancel | One dialog style in every app, in both languages (below) |
| Diamond key, zoom, status window | Not copied. The status line on TERM512 does the job of the status window |

LIFECYCLE_SHELL.md proposed organising the home screen by lifecycle phase instead of a Psion icon
bar. Decision 4 reverses that for the home screen: Home is Psion-style icons. The rest of that
design (phases inferred from what you do, the shared items index, Capture, Harness) is unaffected
and comes in the next major version. When it does, it lives inside the icon Home, for example as
Harness's own icon and its files, not as a different home screen.

## The UI grammar

One short document, `docs/UI.md`, written first (step 1.1) and followed by every app. Its content:

### Keys

| Key | Meaning everywhere | Notes |
|---|---|---|
| Arrows | move | the **bare** `;` `.` `,` `/` (the arrows are printed on them; Calc and Scheduler already do this), and `h` `j` `k` `l`. `Fn`+arrow is read too, never required (decision 7). Where letters type, see Writer's Move mode |
| `Enter` | open / confirm / next | |
| `Esc` (`` ` ``) | back / cancel / close menu | `q` is an alias, except in text entry |
| `Tab` | menu bar | unused by every bundled app except Theme (preview). Writer drops it today (code 9) |
| `Tab` `1`…`9` | switch app | the Apps menu |
| `Tab` › Help | help: generated from the menu table, so it can't drift | `?` is `Shift`+`/`, a chord, so it's only an alias |
| `n` new, `e` edit, `x` delete, `s` save, `f` find | the same letter for the same verb in every app | Where letters type (Writer, a cell being edited), it's `Tab` then the letter |
| `%` | memory (hidden), in MicroPython apps | a chord, but a diagnostic, not a command |

**One key at a time** (decision 7). The single keys are the letters and digits, `; . , /`, `` ` ``
(Esc), `Tab`, `Enter` and `Backspace`. Anything else is a chord: every symbol on a digit (`$` is
`Shift`+`4`), `?` (`Shift`+`/`), and anything with `Fn`, `Ctrl`, `Opt` or `Alt`. So Projector's `$`
money becomes `m`, and its `?` help moves to the menu. Sequences (`Tab`, then `1`) are fine: each
key is pressed alone. (From the firmware source, `Opt`/`Alt`+letter couldn't even be read: AREA512
turns it into Esc and drops the letter.)

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
    │ ←→ menu  ↑↓ item  ENT do  ESC close    │
    └────────────────────────────────────────┘

320×240, the same screen with nothing open:

    ┌ PROJECTOR · Corner cafe ─────────────── 2 cracks ┐
    │ ┌Find────┐ ┌Build───┐ ┌Open────┐ ┌Grow────┐      │
    │ │ 3 mo   │ │ 6 mo ! │ │ 4 mo   │ │ 12 mo  │      │
    │ └────────┘ └────────┘ └────────┘ └────────┘      │
    │  cash  ▇▆▅▃▂▁▁▂▃▅▆▇▇                             │
    │  low $-1.2k in month 9 (likely) ─ worst $-4.0k   │
    │ ──────────────────────────────────────────────── │
    │  ! Cash runs out in month 9, likely case         │
    │  ! Two hard stages back to back: Build, Open     │
    │ ──────────────────────────────────────────────── │
    │ p play  c cracks  e edit  n new  x del  m money  │
    │ v vision  a assume  o obstacle  s save  Tab menu │
    │ 1 Home  2 Projector  3 Writer  4 Calc  5 Agenda  │
    └──────────────────────────────────────────────────┘

### Dialogs and questions

Projector already draws its own question screens, because `Widget.input` blanks the screen. The
forks do the same and match them: title, the question, the answer (typed at the end, `Backspace`
deletes, as in Projector today: moving a cursor inside a typed answer would need `Fn`), `Enter` OK,
`Esc` cancel. Choices cycle with the bare ← → (as on the Psion) and also take `1`…`n`. Calc and Scheduler today read entries through the console (`read_entry` prints the prompt
and echoes), which goes.

### Layout at two sizes

**Design at 320×240, keep everything working at 240×135** (decision 6). Each screen is designed for
TERM512 first. At 240×135 it drops panels (fewer list rows, no second pane, no app row, one hint
line), never commands: everything stays reachable through the hint bar and the `Tab` menu. Layouts read
`Display.width()/height()` after the opt-in, as Projector already does.

## App switching

With `run_next`, switching is: save your place → `Area512.run_next(target)` → return. The filer
runs the target straight away. What every app needs:

| Piece | Where | Format |
|---|---|---|
| **App registry** | `/Area512_data/data/area512/apps.txt` | `digit|name|path`, one line per app, e.g. `2|Projector|/home/ai/projector`. Home writes it, finding apps where they're installed. Every app reads it to fill its Apps menu |
| **Place** | each app's own data folder, `place.txt` | screen, selection, open file. Read on start, then deleted (so a crash doesn't trap you on a bad screen) |
| **Open request** | `/Area512_data/data/area512/open.txt` | `app|verb|arg`, e.g. `calc|open|cafe.sheet`. Lets one app open another on a given file. The target reads it and deletes it, like `run_next` itself |
| **Recent files** | each app's own data folder, `recent.txt` | `title|file`, newest first, at most 8 lines. The app rewrites it when it saves. Home reads it to list files under the app's icon |
| **Back** | the same registry | `Esc` from an app's top screen goes to Home (if installed), not the filer |

Every format follows the existing conventions (PROMOTION_FORMAT.md): plain lines, `|` fields, no
JSON, files written in 900-byte parts on the MicroPython side.

**Saving on switch** (decision 1). Today Projector saves only on `s`, and Writer, Calc and
Scheduler only on their save key, so quitting loses work. From 1.0, switching app (from the Apps
menu, or `Esc` back to Home) saves the open document and its place first, then hands off. `s`
still saves without leaving. Leaving with unsaved changes any other way asks "Save changes?". If
the save fails (out of memory or no card), the switch stops and says so: a switch never loses work.
Projector's help, apps/projector/README.md and PLAN.md changed with step 2.5.

## Home

A small MicroPython app, set as `default=app:` in `/etc/ui`, so it's the first screen at boot. It
copies the Series 3 System screen (decision 4): **a row of app icons, and under the selected icon,
that app's files**.

240×135 (five icons a row; more scroll sideways, with ‹ › at the edges):

    ┌ AREA512 ───────────────────────── ▮▮▮▯ ┐
    │  ┌──┐   ┌──┐   ┌──┐   ┌──┐   ┌──┐      │
    │  │▞▚│   │≡ │   │▦ │   │▤ │   │▭ │   ›  │
    │  └──┘   └──┘   └──┘   └──┘   └──┘      │
    │ [Projct] Writer  Calc  Agenda  Slide   │
    │ ▸ Corner cafe                          │
    │   Night classes                        │
    │   Allotment                            │
    │ ←→ app  ↑↓ file  ENT open  Tab menu    │
    └────────────────────────────────────────┘

320×240 (six icons a row, and every icon's files in its own column, as on the Series 3):

    ┌ AREA512 ─────────────────────────────────── ▮▮▮▯ ┐
    │  ┌──┐    ┌──┐    ┌──┐    ┌──┐    ┌──┐    ┌──┐    │
    │  │▞▚│    │≡ │    │▦ │    │▤ │    │▭ │    │▣ │    │
    │  └──┘    └──┘    └──┘    └──┘    └──┘    └──┘    │
    │ [Projct] Writer  Calc    Agenda  Slide   Extras  │
    │ ▸Cafe    notes   budget  Nov     talk    Bomb    │
    │  Classes letter  cafe$   Dec     cafe    Lander  │
    │  Allotm. list    hours           demo    Theme   │
    │                                          Files   │
    │ ←→ app  ↑↓ file  ENT open  n new  x delete       │
    │ Tab menu  1-6 jump  Esc filer                    │
    └──────────────────────────────────────────────────┘

- **Keys.** ←/→ (and `h`/`l`) move between icons. ↑/↓ move through the selected app's files.
  `Enter` opens the app, on the highlighted file if there is one (an open request, then
  `run_next`). `1`…`9` select an icon. `n` starts a new file in the selected app, `x` deletes the
  highlighted file after asking. `Esc` leaves to the filer.
- **Icons** are 32×32 `.a5d` dot images in Home's `icons/` folder, drawn with `Dot.load` and
  `Dot.push`, in theme colours. They can be redrawn on the device with AREA512's own dot editor
  (`Dot.edit`). An app with no icon gets a box with its initial. Only the visible icons are
  loaded, and their memory is measured in step 3.3.
- **Which apps.** The suite's apps first, in a fixed order. **Extras** is the last icon: every other
  app Home finds under `/Area512_data/home` (folders with a `main.manifest`: the games, Theme,
  Gallery), listed like files, plus **Files**, which leaves to the filer. Home writes the registry
  (`apps.txt`) from the same scan.
- **Place.** Home remembers the selected icon and file, so `Esc` back from an app lands on the icon
  you left from.

## Memory and full screen

- **Measure first.** BandedSprite bands are as wide as the screen, so each band costs a third more
  at 320 px. Measured on a TERM512 (step 0.1): 149 KB heap, 100 KB free at worst with the
  biggest idea, so no change to `BandedSprite(12)` is needed. The Cardputer ADV (~53 KB) is
  still the tight one: everything must keep fitting there.
- **The menu is an overlay** in Projector (`ovl/menu`), loaded only while it's open. The hint
  tables are short strings in the core. Same for Home, which also has the icons to fit.
- **The Ruby forks** have their own VM heap, which hasn't been measured either. Measure each fork
  at 320×240 before and after the changes.
- **No emulator at 320×240.** a512sim and fwrun are 240×135 only, so TERM512 screenshots need the
  device. Since TERM512 is the main device (decision 6), step 0.7 extends a512sim and fwrun
  (area512-factory) to 320×240, so tests and screenshots cover both sizes.

## The productivity apps

Forks live in `forks/` (decisions 1 and 8: we fork, and never change the stock apps upstream), stay PicoRuby, and each gets an `UPSTREAM.md` with the source
commit and what changed. A shared Ruby UI library (menu bar, hint table, dialogs, key reading,
place, registry) lives in `lib/ruby/` and `build.sh` copies it into each fork, the same way
`lib/` works for MicroPython (LIFECYCLE_SHELL.md, repo layout).

What each app does today, and what changes:

### Calc

Today: 26×26 cells. Moves with `h j k l` and the bare `; . , /`. `Fn`+arrow arrives as three
keys (`\e` `[` `A`, step 0.3), none of which Calc knows, so it shows the help line instead of
moving. Edits go through the console. One file, `/data/sheet.txt`. `o` replaces the sheet without
asking, and quitting doesn't save.

1. Bare arrow keys as now, and `Fn`+arrow read as one key instead of three.
2. In-cell editor on the grid, not the console: the dialog rule (type at the end, `Backspace`),
   `Enter` commits and moves down, `Esc` cancels. The cell's whole text shows above the grid.
3. Several sheets through a file list (`Tab` → File → Open), and asking before replacing.
4. Copy and paste a cell, fill down, column width. References adjust on paste.
5. Full screen: more columns and rows, the cell's formula always shown in a line above the grid.
6. Integration: Projector's money table can open as a sheet (step 5.2).

### Scheduler → Agenda

Today: month calendar and a day view. The calendar takes the bare arrow keys, the day view only
`j/k`. `Fn`+arrow jumps back a month (its `[` is "previous month"; step 0.3). Events can be added and deleted, not edited. Times are
typed as `HH:MM`. One file, and quitting doesn't save. With no clock, it opens on the last date
used.

1. Fix the `Fn`+arrow bug (read the three bytes as one key). Bare arrow keys on both screens.
   `Enter` on an event edits it.
2. Time as a field: ↑/↓ steps 15 minutes, digits type it.
3. An **Agenda list**: upcoming events from the selected day on, as a scrolling list (the Psion
   Agenda's day/week views, in one list).
4. Full screen: month and the selected day side by side.
5. "Today" stays the last date used until there's a clock (LIFECYCLE_SHELL.md, Time).

### Writer

Today: the cursor moves with `Fn`+arrow only, and every command is a chord: `Ctrl+S` save,
`Ctrl+O` open, `Ctrl+Q` quit, `Ctrl+K`/`Ctrl+J` page. They're only shown on the help line that `Esc`
brings up. One document, `/data/writer.txt`, and quitting doesn't save.

1. Commands in the Tab menu: `Tab` then `s` saves, `Tab` then `o` opens, and so on. The `Ctrl`
   keys keep working, but nothing needs them.
2. **Move mode** (decision 9): `Tab` › Move (`Tab`, then `m`) switches from Type to Move. In Move,
   the bare `; . , /` move the cursor, `h`/`l` a word, `j`/`k` a page, `a`/`e` to line start and
   end. `Esc` goes back to typing, one level back as everywhere, and `Enter` does too. In Type,
   `Esc` means back as in every app: out of the document, saving first (decision 1). The status
   line always says TYPE or MOVE.
3. Several documents through a file list. A word and line count on the status line. Find in the
   menu.
4. Full screen: more lines and columns.
5. Integration: notes for a Projector idea open as a Writer document (step 5.2).

### Slide

Today: `h/l` page, `j/k` scroll, `Esc` quits. Arrows don't work. One deck folder.

1. Arrows, `Enter`/space for the next page, page `3/12` in the header.
2. Pick a deck from a list. A Writer document can be shown as slides (`---` between pages) (step 5.2).
3. Full screen: larger text.

### Not forked

- **Paint** (decision 3): drawing with only a keyboard is too hard to make pleasant, and it has no
  save. It stays as it is, under Extras on Home.
- **Theme and Gallery** are system and demo apps, also under Extras, as they are. If one ever needs
  changing, it's forked like the others (decision 8).

## Order

Each step ends with the tests green at both sizes (`tests/sim.py`, `tests/fw.py`, once step 0.7 is
done) and a heap measurement on the TERM512.

**0. Ground truth** (no new features). Status 2026-10-28 in *italics*.
- 0.1 Build and test `claude/term512-full-screen` with area512-factory, then run it on a TERM512
  with firmware built from AREA512 `main`. Measure the heap with `%`, and check the window close
  animation after full screen.
  *Built, and all 13 scenarios pass in the sim at both sizes (`tests/sim.py --both`). One finding:
  at 320×240 the film overlay didn't load in the sim's 128 KB heap ("No memory"), and `full_arc`
  passed anyway because its keys happened to work from the strip. The sim heap is now 160 KB.
  The sim keeps its key script in the app's heap, so this says the margin is thin, not what the
  device has.*
  *Device run 2026-10-28, TERM512: Projector's heap is **149 KB** (vs ~53 KB on the Cardputer
  ADV). With the biggest idea, after playing the film and an update: 100 KB free, 99 KB of it
  in 1 KB blocks. Opened straight from boot via `default=app:`: 104 KB free (115). The sim's
  "No memory" was the sim, not the device. Memory isn't the limit at 320×240, and the
  `BandedSprite(12)` argument can stay. The probe (a small app) sees 128 KB, 125 KB free with
  the full-screen sprite. The Filer redraws cleanly after the close animation (emulator, TERM512 build: "Returned: projector").*
- 0.2 Check on the device: `run_next` from MicroPython and from Ruby, and `default=app:`.
  *Python → Projector works, and `default=app:` boots into the app. The Ruby probe failed with
  "uninitialized constant Display": it lacked `require 'area512-sprite'` (a probe bug; Ruby
  apps must require it for `Display`). With that fixed: Python → Ruby → Python works, and the
  Ruby probe draws at 320×240 too. Done.*
- 0.3 What `Fn`+arrow sends to Calc and Scheduler.
  *Answered from the source: Ruby's `STDIN.getch` returns one byte, so `Fn`+arrow arrives as three
  keys, `\e` `[` `A`. Writer reads the two bytes after `\e` itself. Calc shows its help line three
  times. In Scheduler it's a bug: `[` is "previous month", so **every `Fn`+arrow on the calendar
  jumps back a month**, and in the day view `\e` goes back to the calendar first. Worth one look on
  the device.*
- 0.4 Update AREA512_ISSUES.md and TERM512.md. *Done.*
- 0.5 ~~Upstream issue: `Opt`+letter as a key.~~ *Dropped: no chords (decision 7).*
- 0.6 ~~Upstream PRs: `Fn`+arrow in Calc, Scheduler and Slide.~~ *Dropped: we fix them in our forks
  (decision 8).*
- 0.7 area512-factory: a 320×240 mode for a512sim and for fwrun (firmware built with
  `AREA512_EXT_DISPLAY`), so `tests/sim.py` and `tests/fw.py` can run each scenario at both sizes
  and take TERM512 screenshots. Done before step 2.4, the first 320×240 layout.
  *Done. a512sim: factory branch `claude/term512-sim` (it also pins AREA512 fc9f6f9 for the new
  API; `tests/sim.py --both`). fwrun: emucard-adv draws the TERM512 lid screen, so
  `tests/fw.py --term512` boots our TERM512 build and every shot is 320×240; `--seed` puts
  data on the card first (`tests/seeds/big` is the largest idea). A long run needs Node's heap
  raised to 6 GB (fw.py does it): the emulator keeps thousands of compiled blocks alive.*

**1. Grammar on paper**
- 1.1 `docs/UI.md`: keys, hint table, menu bar, dialogs, two layout sizes, Home. *Done, written
  with Projector's menu (2.1–2.3) so it describes code that runs.*
- 1.2 `docs/APPS_FORMAT.md` (beside PROMOTION_FORMAT.md): registry, place, recent files, open
  request. *Done.*
- 1.3 Draw the icons (Projector, Writer, Calc, Agenda, Slide, Extras) as `.a5d` files. *Done:
  `tools/icons.py` writes `apps/home/icons/*.a5d` and a preview. A `.a5d` holds its own palette, so
  icons can't follow the theme colours; they use the dot editor's default palette, so they can
  be redrawn on the device.*

**2. Projector 1.0** (MicroPython; the grammar's first user)
- 2.1 Key table per screen; hint bar and help generated from it. `Esc` backs out everywhere.
  One letter per verb (library `a` new → `n`, `a` kept as an alias; `d` archive → `x`).
  *Done for the library, strip, cracks, assumptions (`n` new, `x` delete) and money (`c` case,
  `s` now saves). The hint bar fits as many items as the width allows (3 at 240 px, 4–5 at
  320). Questions, the one-action forms (edit, vision) and the film keep a plain hint bar.*
- 2.2 Menu bar as an overlay. *Done: `ovl/menu`, 3 KB, loaded only while open. Help is in it.
  `ovl/help` is gone.*
- 2.3 Bare `; . , /` as arrows outside text entry. No chords left (decision 7): `$` money → `m`,
  `?` help → `Tab` › Help (`$` and `?` kept as aliases). *Done. New sim scenario `menu` drives
  every menu, the new keys and the bare arrows; all 14 scenarios pass at both sizes. The
  menu's memory on the Cardputer (the strip, or assumptions, with the menu open) still needs
  a `%` reading on a device.*
- 2.4 320×240 layouts: strip with the money line and cracks on one screen, the library with a
  preview pane, a taller film. *Done, checked on the TERM512 firmware in the emulator. The
  layouts are in `ovl/wide`, loaded once at start only when the screen is 320×240, so the
  Cardputer never holds them. Strip: a 40 px cash chart, the likely and worst lines, then the
  open cracks and the faced ones. Library: the list, and the selected idea's wish, size,
  money and cracks beside it. Film: the chart is 140 px tall (40 on the Cardputer). Heap
  with the largest idea after the film: 92 KB free of 149.*
- 2.5 Save-on-switch, place and `recent.txt`. Update the help, apps/projector/README.md and PLAN.md
  ("never automatic" goes). *Done, with 3.4's Apps menu and Esc to Home (overlay `apps`).
  With a registry, `Tab` shows an Apps menu first in the bar (it opens on the screen's own
  menu), and `Tab` then a digit saves, writes `place.txt`, and calls `run_next`. On start,
  `open.txt` (for Projector) or `place.txt` reopens the idea on its stage. Every save rewrites
  `recent.txt`. Esc from the library goes to Home if the registry has one. Sim scenarios
  `switch`, `resume`, `open_req`; all 17 pass at both sizes. On the TERM512 firmware in the
  emulator: `Tab` `3` saved, wrote `place.txt` and `recent.txt`, and handed off (the filer said
  "Cannot run writer": not installed); running Projector again reopened the idea on Stage 3
  and deleted `place.txt`.*

**3. Switching and Home**
- 3.1 Repo move to `apps/`, `forks/`, `lib/` (LIFECYCLE_SHELL.md layout), tests green before and after.
  *Done: `apps/projector/` (was `app/`), `apps/home/` (was `home/`), `lib/py/`. `build.sh` builds
  every app into `dist/<app>/`; `tests/sim.py` runs `home*` scenarios against Home.*
- 3.2 `lib/`: menu, hints, dialogs, registry, place, written in MicroPython and in Ruby (`lib/ruby/`).
  *MicroPython half done: `lib/py/base.py` (class `UI`: screen setup, key loop with the menu
  hook, hint bar, yes/no and message screens; helpers, files in parts, the registry) and
  `lib/py/menu.py` (menu bar and Help), cut out of Projector unchanged and put in front of each
  app's `main.py` by `build.sh`. Projector's 17 scenarios pass at both sizes before and after.
  One fix on the way: the hint bar's fit ignored its 3 px margin, so a line that filled the
  width exactly lost its last word. The Ruby half comes with the first fork (step 4).*
- 3.3 Home: the icon row and file lists at both sizes, the app scan and registry, Extras, and
  `default=app:`. Measure the heap with the icons loaded.
  *Done. `apps/home/main.py`, about 11 KB of source. It scans `/home/*/*` for a `main.manifest`,
  places the suite in order (a fork in `/home/ai` over a bundled app: Agenda is the bundled
  Scheduler until the fork is installed), puts the rest under Extras with Files last, and
  rewrites `apps.txt` when it changed. Files come from each app's `recent.txt`. `Enter`, `n` and
  `x` hand off through `open.txt` (`open`, `new`, and a new verb, `delete`: Home asks, the app
  does what its own `x` does and hands back). `place.txt` brings you back to the icon and file
  you left from. On TERM512 each icon has its files in its own column, with wider slots when
  there are fewer than six icons. 11 sim scenarios (`home_*`, and `del_req` for Projector's
  side) check the registry, requests, place and hand-offs at both sizes.
  On the TERM512 firmware in the emulator: Home → Projector on the idea picked → Esc, Esc →
  back on Home on the same icon and file. Heap with the icons loaded: **111 KB free of 149**
  (118 in 1 KB blocks); Projector after the hand-off: 91 KB. The Cardputer firmware in the
  emulator (v2.7) draws Home and writes the registry, but has no `run_next`, so a switch
  shows "Can't switch: needs AREA512 after v2.7". `default=app:/home/ai/home` is documented
  in Home's README; booting into an app that way was checked in step 0.2.*
- 3.4 Apps menu and `Esc` to Home in Projector. *Done with 2.5.*

**4. Forks**, one at a time: Agenda (Scheduler), Writer, Calc, Slide (decision 5). For each: fork with `UPSTREAM.md`,
then arrows and the grammar, save-on-switch and place, then the app's own list above, then full
screen.
- 4.1 Agenda. *Done: `forks/agenda/` (Scheduler at upstream fc9f6f9, then every change listed in
  its UPSTREAM.md), on `lib/ruby/ui.rb`, the Ruby half of step 3.2 (`class SuiteApp`: key loop,
  hint bar, menu bar, Help, question screens, registry, open requests, place). All five items
  of the list above: `Fn`+arrow read as one key (`Widget.read_key`), bare arrows on every
  screen, Enter edits an event; the time field (↑/↓ 15 minutes, digits type it); the agenda
  list (`a`); 320×240 with the selected day beside the month and what's coming up below;
  "today" is still the last date used. Its data moved to `/data/agenda/agenda.txt`, the same
  format, with Scheduler's file copied the first time. Esc asks before losing changes; `Tab`
  then a digit saves and switches; `recent.txt` lists the next 8 events for Home.
  `build.sh` compiles it with AREA512's own `picorbc` (which rebuilds the bundled `.mrb` files
  byte for byte). Ruby has no a512sim, so `tests/rsim.rb` runs the fork under CRuby with mocks
  of the API, in the same output format: 13 `agenda_*` scenarios at both sizes. CRuby runs
  more than mruby/c does, so the firmware has the last word: on both firmware builds in the
  emulator the fork runs, draws every screen, adds an event with the time field, and
  `Fn`+up moves a week, not a month. With Home, Projector and Agenda installed together on the
  TERM512 firmware: Home lists Agenda's next events under its icon (the bundled Scheduler
  moves to Extras) → Enter opens Agenda on the event → Help, edit the time → `Tab` `1` saves
  and goes back to Home on the same row → `x`, `y` on Home: Agenda deletes it and hands back.
  That run found one bug, fixed: a request left Agenda's own `place.txt` behind. The Ruby
  VM's heap: see 4.2.*
- 4.2 Writer. *Done: `forks/writer/` (Writer at upstream fc9f6f9, then every change listed in
  its UPSTREAM.md). All five items of the list above but 5 (step 5.2): the commands on `Tab`
  with the `Ctrl` keys kept (`Ctrl+J` can't be: the key layer reads it as Enter); Move
  (`Tab` `m`, a block cursor, TYPE/MOVE on the status line); a list of documents in
  `/data/writer/` (`n` `r` `x`, deleted ones kept in `deleted/`), find (`Tab` `f`, `g`), and
  a word count; 320×240 with 50 columns, 14 rows and a preview beside the list. Not in the
  list but needed: paragraphs wrap at a space (upstream cut a long line off at the edge), and
  up/down go a row as drawn. Home's `new` with a name opens that document if it's there, ready
  for Projector's notes. `tools/rbcheck.py` (run by `build.sh`) fails the build on a call to a
  method mruby/c doesn't have, which CRuby in `tests/rsim.rb` can't catch. 17 `writer_*`
  scenarios at both sizes. On the firmware: the list, typing, wrapping, Move, find and save
  on the Cardputer build; the preview and find's highlight on TERM512; and Home → Writer on
  its document → type → `Tab` `1` → Home → `x` `y` (Writer deletes it into `deleted/` and
  hands back).
  **Memory**: the Ruby apps share one 120 KB arena (`AREA512_ARENA_BYTE_SIZE`) for code and
  objects, and mruby/c can't raise running out: it **restarts the device**. Writer's code is
  33 KB of bytecode (upstream's 9 KB). A 24 KB document restarted the Cardputer build; with
  one copy less on opening and two less on saving, 16 KB opened, took an edit and saved, and
  20 KB still ran out while opening. So Writer stops at **12 KB** (about 2,000 words): it
  won't open a bigger file (it says how big) or type past it. A file needs reading to know its
  size (AREA512's `File` has no size), so one much bigger copied in by hand could still run
  out while it's read. The `%` key reads the heap in the Ruby apps too, but the sandbox VM has
  no `PicoRubyVM` on either firmware, so it says "not known" there: the filer's ARN figure is
  the measure (60% used after a Writer session with small documents).*
- 4.3 Calc. *Done: `forks/calc/` (Calc at upstream fc9f6f9, then every change listed in its
  UPSTREAM.md). Items 1 to 5 of the list above (6 is step 5.2): `Fn`+arrow read as one key;
  typing on the grid, with the cell's whole text in a bar above it (a digit, `=` `-` `+` `(`
  starts an entry over the cell, Enter types on the end of it; Enter puts it in and goes
  down, `Fn`+arrow goes that way, Esc cancels); a list of sheets in `/data/calc/` (`n` `r` `x`,
  deleted ones kept in `deleted/`), every way out saving first, so nothing replaces a sheet
  unasked; copy and paste with references that move (`$` keeps them), fill down and right,
  column widths saved in the file, and, not in the list, undo/redo of the last change, find,
  go to, 99 rows instead of 26; 320×240 with 5 columns and 12 rows and a two-line bar. Also
  fixed: `=7/2` was 3 (integers, 32 bits on the device), chains of formulas more than six
  deep stayed `#ERR`, and an empty cell in a formula was `#ERR`. Writer's list of documents,
  recent.txt, Home's requests and switching moved to `lib/ruby/docs.rb`, shared by both
  (Writer's 19 scenarios pass unchanged). 17 `calc_*` scenarios at both sizes, 154 in all.
  On the firmware: the copy, fill, `$` and undo scenario gives the same file on both builds,
  and with Home on the TERM512 build: Home → Calc on its sheet → type → `Tab` `1` saves and
  goes Home → `x` `y` (Calc moves the sheet to `deleted/` and hands back).
  **Memory**: the TERM512 build (AREA512 `main`) leaves the Ruby apps less of the 120 KB arena
  than the Cardputer's v2.7: 399 formulas in 8 KB opened on the Cardputer and ran out on
  TERM512. What it cost, in order of finding: a String for every cell (300 one-digit
  numbers ran out); one Hash for the sheet, which mruby/c grows 6 slots at a time, each a
  copy (it fragments the arena); a Hash per row (two headers a row cost more than they
  saved). So a row is one String, its cells between tabs, with one Array of values made at
  its length; the grid is laid out once a frame into two flat Arrays; and the file's text
  is let go before the first frame. Reading a file needs it whole (AREA512's `File#read`
  and `SD.read` read all of it). With that, on both builds, 250 formulas in 6 KB and 6 KB of
  60-character text open, take copy, paste, fill, undo, find and a width, and save. So a
  sheet stops at **250 cells and 6 KB**, and a change past either says "Full".
  **Writer, re-checked on the TERM512 build**: a 12 KB document (its limit, measured on the
  Cardputer's v2.7) runs the VM out while opening and restarts the device. *Fixed after
  step 4.3:* three causes, all fixed. On TERM512 only, the list's preview kept the whole
  document split into lines, a second copy while it opened (now 16 lines of 64 bytes). Closing
  a document kept its lines while the list read the file again (`close_doc` now lets them
  go). And each key built a new line from three copies of the old one (now `[]=` in place:
  one 12 KB paragraph ran out on the first key). Measured again on the TERM512 build, two
  emulators at a time, opening, editing, saving and closing four times: what ran out was
  12 KB in 200 lines, 12 KB in 300, 500 short lines, and 15 KB in 10 paragraphs. Lines count:
  each String costs about 40 bytes more. So Writer now stops at **10 KB, and 16 KB of
  "room"** (the bytes, and 40 a line): about 1,700 words of prose, or 330 short lines.
  At the limit, 10 KB in 160 lines, 330 short lines, 250 lines of 24 bytes and 10 KB in 7
  paragraphs all took that four times on both builds. A file that's too big says how big,
  as a share of the most. One long paragraph near 10 KB is slow to type in (it's laid out
  again on each key); not fixed. 21 `writer_*` scenarios, 158 in all at both sizes.*
  *Fixed after step 5.2 (2026-10-29). A key at the end of a 10 KB paragraph took 2.9 s on the
  TERM512 build and 2.3 s on the Cardputer's, a page 5.7 s (a timer on the status line, in the
  emulator): the column was counted from the paragraph's start on every band, the paragraph
  was wrapped about three times a key, three reads a byte. Now the column is counted on from
  where it was, rows are wrapped with one read a byte and only as far as the screen needs,
  and only the words around a change are counted again: about a tenth of the work. Rows kept
  and mended from key to key were quicker still (58 ms), but cost more of the VM's arena
  than they saved, and the device can't say how its arena is cut up, so `tests/arena.sh` was
  written to: it runs a fork on mruby/c built for the PC with the firmware's settings and
  says how much it has to spare. It also found the rest. A 10 KB paragraph, split, saved,
  joined and searched, ran the old Writer out too: find lowercased a copy of each line (now
  it reads them where they are), a save grew the file a line at a time (now it's made at its
  size), and the paragraph itself is held twice or more, in one piece, by each of those. So
  a paragraph holds 4 KB (typing stops, a join past it is refused, a longer file isn't
  opened), and `build.sh` drops local variables' names from the bytecode (`--remove-lv`,
  2.2 KB of Writer's), which Agenda, Calc, Slide and Home were checked with on both builds.
  On both builds, a 10 KB document with a 4 KB paragraph took that four times. Upstream's
  wrapping could run a row past the edge (a word carried down wasn't measured again); fixed.
  `tests/wrfuzz.rb` checks the column, words, size, rows and find under random keys. 26
  `writer_*` scenarios, 242 in all.*

- 4.4 Slide. *Done: `forks/slide/` (Slide at upstream fc9f6f9, then every change listed in its
  UPSTREAM.md). A deck is one of Writer's documents, a line of `---` between pages, so decks
  are written on the device and step 5.2's "a Writer document as slides" is how Slide works
  (Writer's own menu item for it is still 5.2). Upstream's numbered pages are joined once as
  the deck "slides". All three items of the list above: the bare arrows, Enter and Space for
  the next page, `3/12` in the header; a list of decks (Writer's documents; `e` and `n` hand
  over to Writer, `x` and `r` as Writer's list); 320×240 with 50 columns and a 24 px `#` title
  (`Widget.big_text`; the screen buffer has one font, and only that call changes it). Long
  lines wrap; one page is laid out at a time, from the text. Its recent.txt and place.txt are
  in `/data/slide/`. On the way: every app with documents now drops a recent.txt entry whose
  file is gone, since two apps can delete the same document. 18 `slide_*` scenarios at both
  sizes, 194 in all. On the firmware, both builds: the one-time join, the list (and the
  preview on TERM512), every page of a four-page deck with a wrapped list and a code block
  holding `---`, the menu, and `e` without Writer installed.*

**5. Together**
- 5.1 The app row and two-line hints on TERM512 everywhere.
  *Done (docs/UI.md, Two sizes): on TERM512 every screen with a key table shows all of it on
  two hint lines, with a message or Writer's status on the first, and the app row under them
  (`1 Home  2 Projector  3 Writer  4 Calc  5 Agenda  6 Slide`, this app marked). Ruby: in
  `lib/ruby/ui.rb` (`foot`, `foot_pairs`), so Agenda, Writer, Calc and Slide have it, and the
  menu bar keeps the app row. Projector: in `ovl/wide`, so the Cardputer holds none of it;
  `lib/py/base.py` only has the hook. On the TERM512 firmware with the suite: Writer (Type and
  Move), Calc and its menu, Agenda, Slide and Projector (library, strip, menu). Projector's
  heap with the largest idea on the strip: 87 KB free of 149. Size-specific checks in
  `tests/sim.py` (`EXPECT_SIZE`): `foot_lib`, `writer_foot`, `slide_foot`; 206 in all.*
- 5.2 Open requests between apps: Projector → Calc (money as a sheet), Projector → Writer (notes
  for an idea), Writer → Slide.
  *Writer → Slide done: Writer's `Tab` `v` saves and asks Slide to `show` the document
  (`<file>:<line>`), which opens on the cursor's page; Esc there goes back to Writer, which
  reopens where it was. On the TERM512 firmware with the suite installed: Home → Writer → type
  `---` and a second page → `Tab` `v` → Slide on page 2 → `,` → Esc → Writer on the same
  character → `Tab` `1` → Home lists the document under Slide's icon. 4 more scenarios.*
  *Projector → Writer and → Calc done: on the strip, `w` asks Writer for the idea's notes
  (`writer|new|<title> notes`: Writer makes it the first time, then opens it), and `b` writes
  the plan's money into `/data/calc/<title> money.txt` and asks Calc to open it: cash and
  fixed costs, a row a stage (months, start, cost and income a month, then net a month and
  the stage's total as formulas), and the end, `=B1+SUM(...)`, the likely case. A sheet
  already there is replaced only if you say (`n` opens it as it is). The code is in the
  `apps` overlay, loaded only for the switch. On the TERM512 firmware with the suite: Home →
  Projector on the largest idea → `b` → Calc on the sheet, whose end (−80,800) is Projector's
  likely end → `Tab` `2` → `w` → Writer on the notes → `Tab` `1` → Home lists both. The sim's
  heap went from 160 to 168 KB: `arc_mem` at 320×240 ran out in the sim only (it holds its
  mocks and the key script there); on both firmware builds the same arc has 88 KB free of 149
  and 109 of 157. 7 more scenarios, 222 in all.*
- 5.3 Release: one zip with Home, Projector, the forks, and the `/etc/ui` line, plus an install page.
- 5.4 Next major: Capture, Harness and the items index (LIFECYCLE_SHELL.md order, steps 2, 4–7),
  as icons on Home.

## Open questions

None. The heap at 320×240 (step 0.1) came back at 149 KB, so layouts are limited by screen
space, not memory.
