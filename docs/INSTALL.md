# Installing Projector 1.0 and the suite

Projector 1.0 comes with five more apps that share its keys: **Home** (the first screen, an
icon for each app and its files under it), and **Agenda**, **Writer**, **Calc** and **Slide**,
AREA512's Scheduler, Writer, Calc and Slide forked onto the same keys. One zip holds them all:
`projector-v1.0.0.zip`, from the repository's releases.

## What you need

- An M5Stack Cardputer ADV, or a TERM512, running [AREA512](https://github.com/engneer-hamachan/area512).
- For **switching between apps** (`Tab` then a digit, Esc back to Home, Home opening an app on
  a file) and for **starting on Home**: AREA512 newer than v2.7. Both came into AREA512's
  `main` on 2026-10-28 (`Area512.run_next` and `default=app:`) and aren't in a release yet, so
  build the firmware from `main` until one is out.
- For **the whole screen on a TERM512**: the same (AREA512 `main`, its TERM512 build).

On v2.7 every app still runs from the Filer (select its folder, `R`), on its own; asked to
switch, an app says "Can't switch: needs AREA512 after v2.7", and Projector keeps to a 240×135
window on a TERM512.

## Install

1. **Copy the apps.** Unzip at the root of the SD card: the zip's `Area512_data/` merges into
   the card's own, and puts each app in `/Area512_data/home/ai/<app>/` (home, projector,
   agenda, writer, calc, slide). Copy each folder whole: Projector's `ovl/` and Home's `icons/`
   are part of them. Other folders under `/Area512_data/home/` work too: Home finds the apps
   wherever they are, each time it starts.
2. **Start on Home** (optional, needs AREA512 newer than v2.7). The zip's
   `Area512_data/etc/ui.suite` holds one line:

       default=app:/home/ai/home

   If the card has no `/Area512_data/etc/ui`, rename `ui.suite` to `ui`. If it has one, add the
   line to it and delete `ui.suite`: the file's other lines (`default=terminal`, say) are your
   own settings, so don't replace it.
3. **Restart.** With the line, the device starts on Home; without it, open Home (or any app)
   from the Filer.

Home writes `/Area512_data/data/area512/apps.txt` when it starts: the list each app's `Tab`
› Apps menu reads. Start Home once after installing or removing an app.

## Coming from AREA512's own apps, or from Projector 0.4

Nothing is lost, and nothing of yours is changed:

- **Projector** keeps its ideas where 0.4 did (`/data/projector/`), in the same files. Replace
  the old `projector/` folder with the new one, whole.
- **Agenda** copies Scheduler's events (`/data/scheduler.txt`) the first time it starts,
  **Writer** your `/data/writer.txt` as the document "writer", **Calc** your `/data/sheet.txt`
  as the sheet "sheet". The old files stay as they are.
- AREA512's own Scheduler, Writer, Calc and Slide stay installed, and are under **Extras** on
  Home.

## Limits

The Ruby apps share the device's 120 KB for Ruby with their own code, and running out
restarts the device, so they stop before that and say so:

- **Writer**: a document holds 10 KB (about 1,700 words, fewer in short lines), a paragraph
  4 KB (about 700 words). A bigger file isn't opened.
- **Calc**: a sheet holds 250 cells and 6 KB.

Deleted documents and sheets go to `deleted/` in their app's folder under `/data/`, so a slip
can be undone from the Files app.

## Removing

Delete the app's folder from `/Area512_data/home/ai/`, then start Home once so the Apps menu
forgets it. Your files stay in `/Area512_data/data/<app>/`. To stop starting on Home, remove
the `default=app:` line from `/Area512_data/etc/ui`.

## Each app

The keys every app shares are in [UI.md](UI.md); each app's own help is in its README on the
card (Projector's [here](../apps/projector/README.md), Home's [here](../apps/home/README.md),
and the forks' in [forks/](../forks/)).
