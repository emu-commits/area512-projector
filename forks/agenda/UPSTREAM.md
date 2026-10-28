# Agenda: a fork of AREA512's Scheduler

- **Source:** [engneer-hamachan/area512](https://github.com/engneer-hamachan/area512)
  `storage/home/tool/scheduler/`, at `main` fc9f6f9 (2026-10-28). The first commit of this
  folder is that source, unchanged (`.rb` files, `README.md`, `image.h`, `main.manifest`).
- **Why a fork** ([PLAN_V1.md](../../docs/PLAN_V1.md), decision 8): we never change the bundled
  apps upstream. Every change to Scheduler is made here.

## What changed

Built by `build.sh` into `dist/agenda/` with AREA512's own `picorbc`, with
[`lib/ruby/ui.rb`](../../lib/ruby/ui.rb) (the suite's Ruby UI, `class SuiteApp`) first in
`main.manifest`. The `.mrb` files aren't kept here.

| Scheduler | Agenda | Why |
|---|---|---|
| `class Scheduler` | `class Agenda < SuiteApp` | the shared key loop, menu bar, dialogs, registry |
| keys read with `STDIN.getch`: `Fn`+arrow arrives as `\e` `[` `A`, and `[` is "previous month", so every `Fn`+arrow on the calendar jumped back a month | `Widget.read_key`, which reads the sequence as one key | the bug (PLAN_V1 step 0.3) |
| the day view moved with `j`/`k` only | bare `;` `.` `,` `/` on every screen, `h j k l` too | one key at a time (decision 7) |
| `a` add, `d` delete (no question), `c` calendar, `q` quit | `n` new, `x` delete (asks; `d` kept), Esc back (`c`, `q` kept), Enter edits | the same letter for the same verb in every app |
| events couldn't be edited | Enter on an event edits its time and text | |
| time typed as `HH:MM` through the console | a time field: ↑/↓ steps 15 minutes, digits type it (`930`, `1415`) | PLAN_V1, Agenda 2 |
| the prompt went through the console (`read_entry`) | drawn question screens, as in every app | docs/UI.md, Questions |
| — | the agenda list (`a`): every event from the selected day on | PLAN_V1, Agenda 3 |
| 240×135 | 320×240 on TERM512: the month, the selected day beside it, what's coming up below | PLAN_V1, Agenda 4 |
| a help line in the footer | the hint bar and the `Tab` menu bar, from one key table per screen | docs/UI.md |
| one file, `/data/scheduler.txt`; quitting didn't save | `/data/agenda/agenda.txt` (Scheduler's file copied once, the same format); Esc asks "Save your changes?"; `Tab` + digit saves and switches | decision 1 |
| — | `recent.txt` (the next 8 events, for Home), `place.txt`, Home's `open`, `new` and `delete` requests | docs/APPS_FORMAT.md |
| `input.rb`: console entry and UTF-8 helpers | `input.rb`: the time field and the event dialog; text entry in `lib/ruby/ui.rb` | |
| `render_calendar.rb`, `render_day.rb` | the same, at both sizes, and `render_list.rb` | |

Unchanged: the date maths (`date_math.rb`, with three helpers added), the file format, and
"today is the last date used" (there's no clock).

Text entry keeps Scheduler's UTF-8: what the keyboard layer's IME types goes in as it
comes, and Backspace takes off a whole character.
