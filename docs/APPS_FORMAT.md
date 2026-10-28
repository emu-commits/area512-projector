# Files shared between the apps

How Home and the apps of the suite find each other, switch, and come back to where you were
([PLAN_V1.md](PLAN_V1.md), *App switching*). Written as files, because only one app runs at a
time: switching is `Area512.run_next(path)` and then the app returns.

Every file follows the conventions of [PROMOTION_FORMAT.md](PROMOTION_FORMAT.md): plain lines,
`|` between fields, no JSON, and `|` and newlines replaced in any text written into a field. A
MicroPython app writes long files in parts of at most 900 bytes (`<path>`, `<path>.1`, …, see
Projector's `write_lines`); these files are all short enough to be one part.

Paths are as the apps see them: `/data/...` is `/Area512_data/data/...` on the card.

## Shared: `/data/area512/`

### `apps.txt`: the registry

One line per app, in Home's order:

    <digit>|<name>|<path>

    1|Home|/home/ai/home
    2|Projector|/home/ai/projector
    3|Writer|/home/ai/writer
    4|Calc|/home/ai/calc
    5|Agenda|/home/ai/agenda
    6|Slide|/home/ai/slide

- `digit` is the key in the Apps menu (`Tab` then the digit). `1` to `9`, each used once. Home
  is `1`, then the suite's apps Home found, in its order, with no gaps. Extras (games, Theme,
  Paint) aren't in the registry: they're one icon on Home.
- `name` is what the menu, the app row and Home show. At most 9 characters.
- `path` is what `run_next` gets: the app's folder (the filer runs its `main.manifest`), or a file.
- **Home writes it**, every time it starts (only when it changed), from where it finds the apps
  installed: every `/home/<group>/<app>/` with a `main.manifest`. A fork in `/home/ai/` wins
  over a bundled app of the same kind, so until the Agenda fork is installed, Agenda is the
  bundled Scheduler (`/home/tool/scheduler`). Every other app only reads it. No file means no
  Apps menu: the app works on its own as before.

### `open.txt`: an open request

One line, written by the app that switches, just before `run_next`:

    <app>|<verb>|<arg>

    calc|open|cafe.sheet
    writer|new|Corner cafe notes

- `app` is the target's name in `apps.txt`, in lower case. A target reads the file at start and
  acts only if `app` is its own name.
- `verb`:
  - `open`: the file named in `arg`, as the target's `recent.txt` names it.
  - `new`: a new document. `arg` is its title, or empty: the app asks, as its own `n` does.
  - `delete`: the file named in `arg`. Home has already asked, so the app doesn't ask again: it
    does what its own `x` does (Projector archives the idea), rewrites `recent.txt`, and hands
    straight back to Home.
- The target deletes the file once read, whatever it says, like `run_next` itself: a request is
  used once. Home deletes any request still there when it starts: one no app took (a bundled
  app, which doesn't read it) is stale by then.

## Per app: in the app's own data folder

Projector's is `/data/projector/`. Each fork has its own (`/data/agenda/`, `/data/writer/`, …).

### `place.txt`: where you were

Written when the app switches away. Read at start, then **deleted**, so a crash on a bad screen
can't trap you there.

    screen: strip
    sel: 2
    file: 7

- `screen`: the app's own name for the screen.
- `sel`: the selected row or item on it.
- `file`: the open document, as the app names it (Projector: the idea's id).
- Other `key: value` lines are the app's own. An app ignores keys it doesn't know.

If the file named in `file` is gone, the app starts on its top screen.

Home's own is `/data/home/place.txt`, written whenever it hands off: `app:` the selected icon,
by name in lower case (`projector`, `extras`), and `file:` the row under it (`-1`: the icon
itself). So Esc from an app lands on the icon and file you left from.

### `recent.txt`: recent files, for Home

The app's documents, newest first, at most 8 lines:

    <title>|<file>

    Corner cafe|7
    Night classes|3

Agenda's are its next 8 events from the last date used, named by date and index in that day:

    3 Nov Dentist 09:00|2026-11-03#0

The app rewrites it whenever it saves. Home reads it to list files under the app's icon, and
opens one by writing `open.txt` (`<app>|open|<file>`) and calling `run_next`. An archived
document isn't listed.

## Order of a switch

1. The app saves the open document. If that fails: stop, say so, stay.
2. It writes `place.txt`, and `open.txt` if it's asking the target for a file.
3. `Area512.run_next(<path from apps.txt>)`, then the app returns from its main loop. The window
   close animation runs, then the filer starts the target straight away.
4. The target reads `open.txt` (if it's for this app) or else its own `place.txt`, and deletes
   whichever it read.
