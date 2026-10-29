# Slide: a fork of AREA512's Slide

- **Source:** [engneer-hamachan/area512](https://github.com/engneer-hamachan/area512)
  `storage/home/tool/slide/`, at `main` fc9f6f9 (2026-10-28). The first commit of this
  folder is that source, unchanged (`.rb` files, `README.md`, `image.h`, `main.manifest`).
- **Why a fork** ([PLAN_V1.md](../../docs/PLAN_V1.md), decision 8): we never change the bundled
  apps upstream. Every change to Slide is made here.

## What changed

Built by `build.sh` into `dist/slide/` with AREA512's own `picorbc`, with
[`lib/ruby/ui.rb`](../../lib/ruby/ui.rb) (the suite's Ruby UI, `class SuiteApp`) and
[`lib/ruby/docs.rb`](../../lib/ruby/docs.rb) (the list of documents, shared with Writer and Calc)
first in `main.manifest`. The `.mrb` files aren't kept here.

| Slide | This fork | Why |
|---|---|---|
| `class SlideShow` | `class Slide < SuiteApp` | the shared key loop, menu bar, dialogs, registry |
| one deck: every `<number>.md` in the app's own folder `/home/tool/slide`, one file a page | any number of decks, from a list: Writer's documents, a line of `---` between pages (not inside a code block, and blank pages skipped). Those pages joined once as the deck "slides". `e` and `n` hand over to Writer (an open request); `x` and `r` act on the document as Writer's list does | PLAN_V1 Slide 2, step 5.2 (a Writer document as slides) |
| `h`/`l` page, `j`/`k` scroll; the arrow keys did nothing | the bare `,` `/` and `Fn`+arrows page, Enter and Space go on, Backspace back; `.` `;` scroll; `[` `]` first and last; `Tab` shows them all | PLAN_V1 Slide 1, decision 7 |
| the header: the file's name, and `3/12` | the deck's name, and `3/12` | PLAN_V1 Slide 1 |
| Esc quit | Esc back to the list, then to Home; `Tab` then a digit switches app, and `place.txt` brings you back to the page | decision 1, docs/APPS_FORMAT.md |
| every page parsed when it started | the text kept (10 KB at most, as Writer's), and of a page only the 1 KB chunks on screen laid out, as you scroll | memory: the Ruby VM's 120 KB. A 10 KB document with no `---` is one page, and laid out whole it restarted the device |
| — | Enter and Space: a screen down a long page, then the next page; Backspace the same way back | reading a long page |
| a line wider than the screen was cut off | wrapped at a space (code still cut off) | |
| only ```` ```ruby ```` opened a code block; any line starting `-` was a list item (`---` too) | any ```` ``` ````; `- ` or `* ` | |
| 240×135 | 320×240 on TERM512: 50 columns, rows of 16 px, a `#` title in 24 px (`Widget.big_text`), and the list shows the selected deck's first page beside it | PLAN_V1 Slide 3 |
| — | Writer's `Tab` `v`: a `show` request (`<file>:<line>`) opens the deck on the page holding that line, and Esc goes back to Writer (`o` to the list) | PLAN_V1 step 5.2 |
| — | `recent.txt` (for Home) and `place.txt` (deck, page) in `/data/slide/`; Home's `open`, `new` (to Writer) and `delete` requests | docs/APPS_FORMAT.md |

`storage.rb` keeps the deck (its pages, place, the hand-over to Writer), `markdown.rb` lays out
a page with upstream's Markdown, wrapped, `render.rb` draws it, and `actions.rb` has the keys.
