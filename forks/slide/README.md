# Slide

Shows a document as slides. Forked from AREA512's Slide (see UPSTREAM.md in the repository)
onto the suite's keys: the same keys mean the same thing in every app, and Tab shows every
command.

A deck is one of Writer's documents (`/data/writer/<name>.txt`): a line of `---` starts a new
page. Write and change decks in Writer; Slide shows them. The first time Slide starts, it joins
the numbered pages you had in `/home/tool/slide/` (`1.md`, `2.md`, …) into the deck "slides".

## The decks

- `;` `.` (or `k` `j`): up and down the list; Enter shows one
- `e`: edit it in Writer; `n`: a new one, in Writer
- `x`: delete (asks first; it goes to `/data/writer/deleted/`, as from Writer); `r`: rename
- Esc: leave (to Home, if it's installed)

## A deck

- `/` (→) and `,` (←): the next and the previous page, wherever you are on this one
- `.` (↓) and `;` (↑): scroll a row. A document with no `---` is one long page: it scrolls
  to the end
- `[` and `]`: the first and last page
- Enter or Space (a presenter's clicker): on, a screen at a time down a long page, then the
  next page; Backspace: back the same way. Not on the hint bar: the arrows are
- `e`: edit it in Writer; Esc or `o`: back to the list. Shown from Writer (its Tab `v`), Esc
  goes back to Writer, where you were, and `o` to the list
- The header shows the page, as `3/12`
- Tab then a digit: switch app. Coming back shows the same page.

## Markdown

- `#`, `##`, `###`: headings (on TERM512, `#` is large)
- `- ` or `* `: list item
- `` `code` ``: inline code
- Lines between two ```` ``` ```` lines: code. A `---` inside them doesn't start a page.

Long lines wrap at a space. Code doesn't: it's cut off at the edge. A deck is 10 KB at most,
as a Writer document is.
