# Writer

A word processor: several documents, long lines wrapped to the screen, a word count, and find.
Forked from AREA512's Writer (see UPSTREAM.md in the repository) onto the suite's keys: the
same keys mean the same thing in every app, and Tab shows every command.

Documents are kept in `/data/writer/`, one `<name>.txt` each, plain text. The first time Writer
starts, it copies your old `/data/writer.txt` as the document "writer" (and leaves the old file
as it is).

## The documents

- `;` `.` (or `k` `j`): up and down the list; Enter opens one
- `n`: a new document (it asks for a name); `r`: rename; `x`: delete (asks first)
- Esc: leave (to Home, if it's installed)
- On TERM512, the box beside the list shows the markdown Slide draws: `#` title, `##` heading,
  `###` subheading, `-` list item, `` `x` `` code in a line, ```` ``` ```` a code block, `---`
  the next slide.

A deleted document goes to `/data/writer/deleted/`, so a slip can be undone from the Files app.
Names are letters, digits, spaces, `-` `_` `(` `)`, up to 24 characters.

A document holds up to 10 KB (about 1,700 words), and fewer if its lines are short: each line
costs about 40 bytes more, so a list stops at about 330 lines. Writer shares the device's
120 KB for Ruby apps with its own code, and running out restarts the device. It won't open a
bigger file (it says how big, as a share of the most), and says "Full" when typing reaches it:
start another document. Don't copy a much bigger file into `/data/writer/`.

A paragraph holds up to 4 KB (about 700 words). Typing stops there ("Full: ... Enter starts
another"), Backspace won't join two paragraphs past it, and a file with a longer one isn't
opened (split it on a computer first).

## Typing

Letters type, so Writer's commands are in the menu: **Tab**, then the command's key.

- Enter: a new line. Backspace deletes.
- The hint bar lists the commands: `[Tab] then: [s] save [f] find …` (as many as fit).
- Fn+arrow moves the cursor; up and down go a row as you see it, even inside a long paragraph.
- Esc: back to the list, saving first.
- Tab `s` save, Tab `f` find, Tab `g` find the next one, Tab `o` the list, Tab `n` new,
  Tab `r` rename, Tab `m` **Move**.
- Tab `v`: show the document as slides in Slide (if it's installed), on the page the cursor is
  in. A line of `---` starts a new page. Esc in Slide comes back here.
- The bottom line says TYPE or MOVE, the line and column, and the words.

## Move

Tab `m` switches to Move: the cursor becomes a block, and the bare keys move it.

- `;` `.` `,` `/`: up, down, left, right
- `h` `l`: a word left / right; `k` `j`: a page up / down
- `a` `e`: the start / end of the row (again: of the paragraph)
- `[` `]`: the top / end of the document
- `f` find, `g` find next, `s` save
- Enter or Esc: back to typing

With the Japanese input on (Ctrl+Space), letters become kana before Writer sees them: switch it
off to use Move's letter keys.

## Everywhere

- Tab: the menu bar, with every command and its key; Tab › Help lists them.
  Tab then a digit switches app, saving first (with Home installed).
- The old Ctrl keys still work while typing: Ctrl+S save, Ctrl+O the list, Ctrl+Q leave
  (saving), Ctrl+K page up.
