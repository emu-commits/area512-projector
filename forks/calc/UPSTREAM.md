# Calc: a fork of AREA512's Calc

- **Source:** [engneer-hamachan/area512](https://github.com/engneer-hamachan/area512)
  `storage/home/tool/calc/`, at `main` fc9f6f9 (2026-10-28). The first commit of this
  folder is that source, unchanged (`.rb` files, `README.md`, `image.h`, `main.manifest`).
- **Why a fork** ([PLAN_V1.md](../../docs/PLAN_V1.md), decision 8): we never change the bundled
  apps upstream. Every change to Calc is made here.

## What changed

Built by `build.sh` into `dist/calc/` with AREA512's own `picorbc`, with
[`lib/ruby/ui.rb`](../../lib/ruby/ui.rb) (the suite's Ruby UI, `class SuiteApp`) and
[`lib/ruby/docs.rb`](../../lib/ruby/docs.rb) (the list of documents, shared with Writer) first
in `main.manifest`. The `.mrb` files aren't kept here.

| Calc | This fork | Why |
|---|---|---|
| `class Calc` | `class Calc < SuiteApp` | the shared key loop, menu bar, dialogs, registry |
| `io.rb`: keys read with `STDIN.getch`, so `Fn`+arrow came as three keys and showed the help line three times | gone: `Widget.read_key`, one key | PLAN_V1 Calc 1, step 0.3 |
| `e` or Enter edited through the console (`read_entry`), off the grid; `g` asked the same way | typed on the grid, in the cell, with the whole text in a bar above it: Enter puts it in and goes down, `Fn`+arrow goes that way, Esc leaves the cell as it was, Tab puts it in and opens the menu. A digit, `=` `-` `+` `(` starts typing over the cell, Space empty. `g` asks on a question screen | PLAN_V1 Calc 2, docs/UI.md dialogs |
| commands only on a help line shown after an unknown key | the key table: hint bar, `Tab` menu bar and Help. `c` clear is now `x` (and Backspace), as everywhere; `q` quit is Esc, back to the list | decisions 2 and 7 |
| one sheet, `/data/sheet.txt`; `o` replaced the sheet without asking, and quitting didn't save | any number in `/data/calc/<name>.txt`, the same format, from a list (`n` new, `r` rename, `x` delete into `deleted/`); the old file copied once as "sheet". Opening another sheet, Esc, and `Tab` + digit all save first | PLAN_V1 Calc 3, decision 1 |
| — | `c` copy and `v` paste, the references moving with a formula and `$` keeping them; `d` fill down and `r` fill right, a cell at a time; `u` undo (and redo) of the last change; `w` column width, saved in the file; `f` find; `[` `]` to A1 and the end | PLAN_V1 Calc 4 |
| 3 columns of 26 rows at 240×135 | as many columns as their widths fit, at 240×135 and 320×240 (5 at the normal width, 12 rows); 99 rows; on TERM512 the bar above is two lines and the list shows the sheet's first cells beside it | PLAN_V1 Calc 5 |
| integers: `=7/2` was 3, and past 2³¹ they wrapped on the device; numbers shown by `Float#to_s` (`%g` on the device, all the digits in CRuby) | every value a Float; shown with as many decimals as fit, up to 6, the same on the device and in the tests, `###` if none do | |
| six passes over all 676 cells after each change: a chain of formulas more than six deep stayed `#ERR` | passes over the formulas until nothing changes, and only one when no formula uses one further on; a loop is `#ERR` | |
| an empty cell in a formula, or one of text, was `#ERR`; `SUM` of an empty range was `#ERR`; division by zero was 0; `12abc` read as 12 | an empty cell is 0; text in arithmetic is `#ERR` and is left out of `SUM` and the rest; `SUM` of nothing is 0; division by zero is `#ERR`; a number is all digits | |
| numbers left-aligned like text | numbers right-aligned, `#ERR` in the emphasis colour, the copied cell outlined | |
| a cell's text any length, the sheet any size; past what the VM's 120 KB holds, the device restarts | a cell up to 60 characters; a sheet up to 250 cells and 6 KB, each row kept as one String (a String a cell, and a Hash for the sheet, ran the VM out at 300 cells); a bigger file isn't opened, a change past it says "Full" | PLAN_V1 step 4.3, measured |
| — | `recent.txt` (for Home), `place.txt` (sheet and cell), Home's `open`, `new` (with a name: opens it if it's there) and `delete` requests | docs/APPS_FORMAT.md |

`sheet.rb` is the sheet (rows, undo, moving), `eval.rb` the values and number formatting,
`eval_parse.rb` the formula parser (upstream's, on Floats, with `$`), `edit.rb` typing,
copying and finding, `files.rb` the file format and place, `render.rb` the grid, and
`actions.rb` the keys.
