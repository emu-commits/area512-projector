# Writer: a fork of AREA512's Writer

- **Source:** [engneer-hamachan/area512](https://github.com/engneer-hamachan/area512)
  `storage/home/tool/writer/`, at `main` fc9f6f9 (2026-10-28). The first commit of this
  folder is that source, unchanged (`.rb` files, `README.md`, `image.h`, `main.manifest`).
- **Why a fork** ([PLAN_V1.md](../../docs/PLAN_V1.md), decision 8): we never change the bundled
  apps upstream. Every change to Writer is made here.

## What changed

Built by `build.sh` into `dist/writer/` with AREA512's own `picorbc`, with
[`lib/ruby/ui.rb`](../../lib/ruby/ui.rb) (the suite's Ruby UI, `class SuiteApp`) and
[`lib/ruby/docs.rb`](../../lib/ruby/docs.rb) (the list of documents, recent.txt, Home's requests
and switching, cut out of Writer for Calc in step 4.3) first in `main.manifest`. The `.mrb` files aren't kept here.

| Writer | This fork | Why |
|---|---|---|
| `class Writer` | `class Writer < SuiteApp` | the shared key loop, menu bar, dialogs, registry |
| `io.rb`: keys read with `STDIN.getch`, `Fn`+arrow as `\e` and two more bytes read by hand | gone: `Widget.read_key`, which reads the sequence as one key | |
| every command a chord (`Ctrl+S`, `Ctrl+O`, `Ctrl+Q`, `Ctrl+K`/`J`), shown only on the help line Esc brought up | `Tab` then the key, from the menu bar; the `Ctrl` keys still work (`Ctrl+J` can't: the key layer reads it as Enter) | one key at a time (decision 7), PLAN_V1 Writer 1 |
| Esc showed the help line | Esc is back: out of the document to the list, saving first | decision 1 |
| the cursor moved with `Fn`+arrow only | **Move** (`Tab` `m`): the bare `; . , /`, `h`/`l` a word, `j`/`k` a page, `a`/`e` the row's start and end, `[`/`]` the document's; Enter or Esc types again. The footer says TYPE or MOVE; Move's cursor is a block | decision 9, PLAN_V1 Writer 2 |
| one document, `/data/writer.txt`; quitting didn't save | any number in `/data/writer/<name>.txt`, from a list (`n` new, `r` rename, `x` delete into `deleted/`); the old file copied once as "writer"; `Tab` + digit saves and switches | PLAN_V1 Writer 3 |
| a line wider than the screen was cut off at the edge | paragraphs wrap at a space, and up/down go a row as drawn, keeping to the same column; a word carried down is measured again, so a row never runs past the edge | |
| the footer: row:column and the last message | TYPE/MOVE, line:column, the word count | PLAN_V1 Writer 3 |
| — | find (`Tab` `f`, then `g` for the next), from the cursor, round from the top, case not minded; what's found is highlighted. It reads each line where it is: a lowercased copy of a 10 KB paragraph ran the Cardputer build out | PLAN_V1 Writer 3 |
| 240×135 | 320×240 on TERM512: 50 columns and 14 rows, and the list shows the selected document beside it | PLAN_V1 Writer 4 |
| UTF-8 (the keyboard's kana) taken a byte at a time, so a half-typed character could be cut | taken whole, once all its bytes are in; Backspace takes off a whole character | |
| `Ctrl+Space` set a JP/EN message the app never got (the key layer keeps that key) | gone; the README says what Ctrl+Space does to Move's letters | |
| read the whole file and kept typing, whatever its size; past what the VM's 120 KB holds, the device restarts | 10 KB at most, and 16 KB of "room" (the bytes and 40 a line): a bigger file isn't opened, typing stops with "Full"; one copy fewer of the text on opening, two on saving; typing changes the line in place (`[]=`), where a new line built each key made three copies of a long paragraph; the list's preview keeps 16 lines of 64 bytes, not the whole file split; closing a document lets its text go; a paragraph holds 4 KB (one of 10 KB, split and saved, ran the Cardputer build out); a save makes the file at its size and fills it in place, where `join` grew it a line at a time | PLAN_V1 steps 4.2 and 4.3, measured on both builds |
| every key counted the column from the line's start on every band, and wrapped the cursor's paragraph about three times (three reads a byte each): 2.9 s a key at the end of a 10 KB paragraph on TERM512, 5.7 s a page | the column is counted on from where it was; each row is wrapped with one read a byte, and only as far as the screen needs; only the words around a change are counted again. Nothing is kept from key to key but numbers: kept rows were quicker still, but cost the arena the room for a save | PLAN_V1 step 4.3 |
| — | `Tab` `v`: the document as slides in Slide (`slide|show|<file>:<line>`), on the cursor's page; Esc there comes back | PLAN_V1 step 5.2 |
| — | `recent.txt` (for Home), `place.txt` (document, line, column, mode), Home's `open`, `new` (with a name: notes for an idea) and `delete` requests | docs/APPS_FORMAT.md |

`document.rb` keeps Writer's model (one String per line, the panel, the scrollbar, the line
height), now with a byte offset for the column and the wrapping; `edit.rb` keeps its editing,
with the moves added; `render.rb` draws the wrapped rows; `files.rb` (opening, saving, place)
and `actions.rb` (the keys) are new.
