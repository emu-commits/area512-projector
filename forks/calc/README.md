# Calc

A spreadsheet: several sheets, typing straight into the grid, formulas, copy and fill, and
undo. Forked from AREA512's Calc (see UPSTREAM.md in the repository) onto the suite's keys:
the same keys mean the same thing in every app, and Tab shows every command.

Sheets are kept in `/data/calc/`, one `<name>.txt` each, in the old format (a cell a line:
`B3`, a tab, its text). The first time Calc starts, it copies your old `/data/sheet.txt` as
the sheet "sheet" (and leaves the old file as it is).

## The sheets

- `;` `.` (or `k` `j`): up and down the list; Enter opens one
- `n`: a new sheet (it asks for a name); `r`: rename; `x`: delete (asks first)
- Esc: leave (to Home, if it's installed)
- On TERM512, the box beside the list shows what a formula can be (below)

A deleted sheet goes to `/data/calc/deleted/`, so a slip can be undone from the Files app.

## The grid

Columns A to Z, rows 1 to 99. The line above the grid shows the cell's whole text, and a
formula's value on the right.

- `;` `.` `,` `/` (or `h` `j` `k` `l`, or Fn+arrow): move
- **Typing**: a digit, `=`, `-`, `+` or `(` starts typing into the cell, over what was there.
  Space starts it empty; Enter (or `e`) types on the end of what's there.
  - Enter puts it in and goes down; Fn+arrow puts it in and goes that way
  - Backspace deletes; Esc leaves the cell as it was; Tab puts it in and opens the menu
- `x` (or Backspace): clear the cell
- `u`: undo the last change (again: redo it)
- `c` copy, `v` paste: a formula's references move with it (`=B3*2` copied one right is
  `=C3*2`); a `$` keeps that part where it is (`=B$1`, `=$B$1`)
- `d` fill down, `r` fill right: this cell into the next one, and go there; again and again
  fills a column or a row
- `g` go to a cell (`B12`), `f` find text (again, then Enter: the next one)
- `[` A1, `]` the bottom right of what's filled in
- `w` the column's width: 5, 9, 14, 20 characters, round
- `s` save; `o` or Esc: back to the list, saving first; `n` a new sheet

Letters are commands on the grid: to type a word into a cell, press Enter (or Space) first.

## Formulas

A cell starting with `=` is a formula.

- `+` `-` `*` `/` and parentheses; numbers like `12`, `3.5`, `.5`
- references: `=A1+B2`; an empty cell counts as 0
- `SUM` `AVG` (or `AVERAGE`) `MIN` `MAX` `COUNT` over a cell or a range: `=SUM(B1:B12)`;
  they leave out empty cells and text
- `#ERR`: a formula that can't be worked out: a typing slip, text in a sum (`=A1+1` where A1 is
  a word), a division by zero, a formula that uses itself, or one that uses an `#ERR`
- `7/2` is 3.5; a number shows as many decimals as fit, up to 6, or `###`

## Size

A sheet holds up to 250 cells and 6 KB (about 100 cells of a long note each, or 250 short
ones): Calc shares the device's 120 KB for Ruby apps with its own code, and running out
restarts the device. It won't open a bigger file, and says "Full" when a change would go past
it: start another sheet. A cell holds up to 60 characters.

## Everywhere

- Tab: the menu bar, with every command and its key; Tab › Help lists them.
  Tab then a digit switches app, saving first (with Home installed), and coming back finds
  the same sheet and cell.
