# Projector 1.0 and the AREA512 suite: plan

Status: plan, 2026-10-28, round 3 (all questions answered, below). Nothing here is built yet, apart from the
full-screen opt-in on `claude/term512-full-screen` (pushed, not yet built or run).

## Decisions

| # | Decision (2026-10-28) | Consequence |
|---|---|---|
| 1 | **Switching apps saves automatically** | Replaces Projector's "s save, never automatic". `s` stays for saving without leaving. `Esc` out of an app with unsaved changes asks first |
| 2 | **`Tab` opens the menu bar** in every app | `Tab` then a digit switches app |
| 3 | **No Paint fork**: it's too hard to use with only the keyboard | Forks are Agenda (Scheduler), Writer, Calc and Slide |
| 4 | **Home is Psion-style graphical icon navigation** | A System screen with an icon per app and its files under it (below). LIFECYCLE_SHELL.md's phase-organised home doesn't become the home screen |
| 5 | **Scheduler is the first fork** | Then Writer, Calc, Slide |
| 6 | **TERM512 is the main device** | Layouts are designed at 320×240 first and checked at 240×135. The emulators get a 320×240 mode (step 0.7) so tests cover the main device |

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
    │ p play  c cracks  e edit  n new  x del  $ money  │
    │ v vision  a assume  o obstacle  s save  Tab menu │
    │ 1 Home  2 Projector  3 Writer  4 Calc  5 Agenda  │
    └──────────────────────────────────────────────────┘

### Dialogs and questions

Projector already draws its own question screens, because `Widget.input` blanks the screen. The
forks do the same and match them: title, the question, the answer with a cursor that ←/→ moves
inside the text, `Enter` OK, `Esc` cancel. Choices cycle with ←/→ (as on the Psion) and also take
`1`…`n`. Calc and Scheduler today read entries through the console (`read_entry` prints the prompt
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
Projector's help, app/README.md and PLAN.md change with step 2.5.

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
  at 320 px, and the `EXT_DISPLAY` build's heap hasn't been measured. Before any layout work: run
  `claude/term512-full-screen` on a TERM512, press `%` on the biggest idea, and play the film.
  If it's tight, change the `BandedSprite(12)` argument so a band stays the same number of bytes
  (more passes per frame, same memory).
- **The menu is an overlay** in Projector (`ovl/menu`), loaded only while it's open. The hint
  tables are short strings in the core. Same for Home, which also has the icons to fit.
- **The Ruby forks** have their own VM heap, which hasn't been measured either. Measure each fork
  at 320×240 before and after the changes.
- **No emulator at 320×240.** a512sim and fwrun are 240×135 only, so TERM512 screenshots need the
  device. Since TERM512 is the main device (decision 6), step 0.7 extends a512sim and fwrun
  (area512-factory) to 320×240, so tests and screenshots cover both sizes.

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

### Not forked

- **Paint** (decision 3): drawing with only a keyboard is too hard to make pleasant, and it has no
  save. It stays as it is, under Extras on Home.
- **Theme and Gallery** are system and demo apps, also under Extras. If upstream accepts the small
  fixes (step 0.6), they'll get arrows too.

## Order

Each step ends with the tests green at both sizes (`tests/sim.py`, `tests/fw.py`, once step 0.7 is
done) and a heap measurement on the TERM512.

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
- 0.7 area512-factory: a 320×240 mode for a512sim and for fwrun (firmware built with
  `AREA512_EXT_DISPLAY`), so `tests/sim.py` and `tests/fw.py` can run each scenario at both sizes
  and take TERM512 screenshots. Done before step 2.4, the first 320×240 layout.

**1. Grammar on paper**
- 1.1 `docs/UI.md`: keys, hint table, menu bar, dialogs, two layout sizes, Home.
- 1.2 `formats/APPS.md`: registry, place, recent files, open request.
- 1.3 Draw the icons (Projector, Writer, Calc, Agenda, Slide, Extras) as `.a5d` files.

**2. Projector 1.0** (MicroPython; the grammar's first user)
- 2.1 Key table per screen; hint bar and help generated from it. `Esc` backs out everywhere.
  One letter per verb (library `a` new → `n`, `a` kept as an alias; `d` archive → `x`).
- 2.2 Menu bar as an overlay.
- 2.3 Bare `; . , /` as arrows outside text entry; ←/→ cursor inside text entry.
- 2.4 320×240 layouts: strip with the money line and cracks on one screen, the library with a
  preview pane, a taller film.
- 2.5 Save-on-switch, place and `recent.txt`. Update the help, app/README.md and PLAN.md
  ("never automatic" goes).

**3. Switching and Home**
- 3.1 Repo move to `apps/`, `forks/`, `lib/` (LIFECYCLE_SHELL.md layout), tests green before and after.
- 3.2 `lib/`: menu, hints, dialogs, registry, place, written in MicroPython and in Ruby (`lib/ruby/`).
- 3.3 Home: the icon row and file lists at both sizes, the app scan and registry, Extras, and
  `default=app:`. Measure the heap with the icons loaded.
- 3.4 Apps menu and `Esc` to Home in Projector.

**4. Forks**, one at a time: Agenda (Scheduler), Writer, Calc, Slide (decision 5). For each: fork with `UPSTREAM.md`,
then arrows and the grammar, save-on-switch and place, then the app's own list above, then full
screen.

**5. Together**
- 5.1 The app row and two-line hints on TERM512 everywhere.
- 5.2 Open requests between apps: Projector → Calc (money as a sheet), Projector → Writer (notes
  for an idea), Writer → Slide.
- 5.3 Release: one zip with Home, Projector, the forks, and the `/etc/ui` line, plus an install page.
- 5.4 Next major: Capture, Harness and the items index (LIFECYCLE_SHELL.md order, steps 2, 4–7),
  as icons on Home.

## Open questions

None right now. Step 0 will raise new ones (the heap at 320×240 decides how much each layout can
show).
