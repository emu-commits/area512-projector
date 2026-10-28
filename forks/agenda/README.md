# Agenda

A month calendar, each day's events, and an agenda list of what's coming up. Forked from
AREA512's Scheduler (see UPSTREAM.md in the repository) onto the suite's keys: the same keys
mean the same thing in every app, and Tab shows every command.

Events are kept in `/data/agenda/agenda.txt`. The first time Agenda starts, it copies
Scheduler's events from `/data/scheduler.txt` (which it leaves as it is).

## Month

- `,` `/` (or `h` `l`): previous / next day; `;` `.` (or `k` `j`): previous / next week.
  Fn+arrow works too.
- `[` `]`: previous / next month
- Enter: the day
- `n`: a new event on the selected day
- `a`: the agenda: every event from the selected day on
- Esc: leave (to Home, if it's installed). It asks first if there are unsaved changes.

## Day

- `,` `/`: previous / next day; `;` `.`: the events
- Enter: edit the event; `n`: a new one; `x`: delete it (asks first)
- `a`: the agenda; Esc or `c`: back to the month

## Agenda

- `;` `.`: the events; Enter: that day, on that event
- `n` new, `x` delete; Esc or `c`: back to the month

## Everywhere

- Tab: the menu bar, with every command and its key; Tab › Help lists them.
  Tab then a digit switches app, saving first (with Home installed).
- `s`: save

## Times

Up and down step 15 minutes. Or type the digits: `9` is 09:00, `930` is 09:30, `1415` is
14:15. Enter OK, Esc cancels.

## No clock

The device has no clock, so "today" is the last date you used: it's saved with the events,
and Agenda opens on it.
