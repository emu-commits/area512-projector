# The UI grammar

Every app in the suite (Home, Projector, and the forks of Scheduler, Writer, Calc and Slide)
follows this page. It comes from [PLAN_V1.md](PLAN_V1.md), decisions 1, 2, 6, 7 and 9, after the
Psion Series 3: the same keys mean the same thing everywhere, every command is in a menu with its
key beside it, and the screen always shows what you can press next.

Projector 1.0 is the first app built on it. Where this page says "as in Projector", the code is
`app/main.py` (`cmd`, `foot`, `hint_list`, `arrow`) and `app/ov/menu.py`.

## One key at a time

Holding two keys at once is hard on the Cardputer keyboard, so **no command and no movement needs
a chord** (decision 7). The single keys are the letters and digits, `; . , /`, `` ` `` (Esc),
`Tab`, `Enter`, `Backspace` and `Space`. Everything else is a chord: the symbols on the digits
(`$` is `Shift`+`4`), `?` (`Shift`+`/`), and anything with `Fn`, `Ctrl`, `Opt` or `Alt`.

A sequence is fine: `Tab`, then `m`, is two single keys.

`Shift` is only for typing text. A chord may stay as an *alias* for an old key (`$`, `?`), never
as the only way to do something. The one exception is `%`, Projector's hidden memory reading: a
diagnostic, not a command.

## Keys

| Key | Means, in every app | Notes |
|---|---|---|
| `;` `.` `,` `/` | up, down, left, right | The arrows are printed on them. `Fn`+arrow is read too, never needed. `h` `j` `k` `l` also move where letters aren't commands |
| `Enter` | open, confirm, next | |
| `` ` `` (Esc) | back, cancel, close the menu | Always one level. `q` is an alias, except where letters type |
| `Tab` | the menu bar | `Tab` again or Esc closes it |
| `Tab` `1`…`9` | switch app | the Apps menu (step 2.5 / 3.4) |
| `Tab` › Help | every key on this screen | generated from the key table, so it can't drift |
| `n` new, `e` edit, `x` delete, `s` save, `f` find | the same letter for the same verb in every app | where letters type, `Tab` then the letter |

**Where letters type** (Writer's text, a cell being edited, a question's answer), every command
goes through `Tab`. Writer's Move mode is `Tab` › Move; in Move, Esc goes back to typing, and in
typing, Esc goes back out of the document, saving first (decision 9).

## The key table

Each screen has **one key table**. The hint bar, the menu bar and Help are all drawn from it, so
the three always agree. In Projector it's a string, so it costs one object, not one per item:

    STRIP_KEYS = ("Idea|1p play|2c cracks|s save;Plan|5m money|v vision|a assume|o obstacle;"
                  "Stage|3e edit|4n new|x delete")

- Menus are split by `;`. Each is `Title|item|item`.
- An item is `<key> <label>`. The key is what the screen's key loop gets: a letter, a digit, or
  `ENT` for Enter.
- A digit in front puts the item on the hint bar, in that order.
- Help is added at the end of the last menu.

Keep labels to one or two short words: they're shown in the hint bar as well as the menu. Keep a
menu to **six items or fewer**: at 240×135, seven rows fit between the menu bar and the hint bar,
and Help takes one.

A screen with a key table reads its keys through one call that draws the screen, reads a key, and,
if the key is `Tab`, opens the menu bar over the screen. The menu hands back the key of the item
picked, and the screen handles it as if it had been pressed: there is only one code path for each
command. In Projector:

    k = self.cmd(STRIP_KEYS, self.r_strip, ())

and the screen's draw function ends with `self.foot(STRIP_KEYS)`.

**Screens with no key table.** A question, a form whose only action is `Enter`, and the film
(Projector's playback) have nothing to put in a menu, so they show their few keys on the hint bar
and have no `Tab` menu.

## The hint bar

The bottom line (`Widget.hints`, drawn as `[key] label`, not clipped).

- The table's numbered items, in order, **while they fit**. Then `[Tab] menu`, always last, so
  everything else is one key away.
- Esc isn't on it: it always means back.
- A message (saved, an error, the `%` reading) replaces the hints until the next key.

At 240 px a line holds 40 characters, which is three short items and `[Tab] menu`. At 320 px
it's 53, which is four or five. The fit is computed, so the same table works at both sizes.

## The menu bar

`Tab` draws the menu titles over the header and opens the first menu under its title, over the
screen.

| Key | In the menu |
|---|---|
| `,` `/` (←/→) | previous / next menu, wrapping round |
| `;` `.` (↑/↓) | previous / next item, wrapping round |
| `Enter` | run the selected item |
| an item's key | run that item, from any menu |
| `Tab`, Esc | close |

Items are shown as `Label` with the key right-aligned in the emphasis colour, as on the Psion.
`h` `j` `k` `l` don't move in the menu: letters are item keys there.

## Help

`Tab` › Help lists every menu on one screen: `Title:  key label  key label …`, a key never split
from its label, then the arrows, Esc and `Tab`. Any key closes it. `?` opens it directly where it
did before (an alias).

## Questions and dialogs

`Widget.input` blanks the screen to one line, so every app draws its own question screen, as in
Projector (`ask_text`, `ask_number`, `ask_choice`, `ask_yn`):

- The title in the header, the question, an optional hint in the dim colour, then the answer in a
  box.
- The answer is typed at the end. `Backspace` deletes. There is no cursor inside the answer:
  moving one would need `Fn`.
- `Enter` is OK, Esc is cancel.
- A choice lists its options numbered: `1`…`n` picks one, ↑/↓ and `Enter` also work.
- Yes/no is `y` / `n`, Esc cancels.
- A number takes `5k` for 5000, and `Enter` on an empty answer keeps the current value.

## Two sizes

**Design at 320×240, keep everything working at 240×135** (decision 6).

- Opt in to full screen at start, then read the size, as Projector does:

      if Display.screen_width() > Display.width():
          Display.full_screen()
      W = Display.width()

  (`try` around it: firmware before AREA512 `main` fc9f6f9 has no `screen_width`.) Ruby apps
  need `require 'area512-sprite'` for `Display`.
- At 240×135 a screen **drops panels, never commands**: fewer list rows, no second pane, no app
  row, one hint line. Every command stays reachable through the hint bar and `Tab`.
- On TERM512, the extras: a second hint line, the app row (`1 Home  2 Projector …`) like the
  Series 3's silkscreen, and on wide screens a panel beside the content (step 2.4 and 5.1).

Measured on a TERM512 (PLAN_V1 step 0.1): Projector has a 149 KB heap there, and 100 KB of it is
still free with the largest idea after the film. The Cardputer ADV (about 53 KB) is the one that
limits memory.

## Switching and saving

See [APPS_FORMAT.md](APPS_FORMAT.md) for the files. In short:

- `Tab` `1`…`9` (the Apps menu) **saves the open document and your place, then switches**
  (decision 1). If the save fails, the switch stops and says so.
- `s` saves without leaving.
- Esc from an app's top screen goes to Home, if it's installed.
- Leaving with unsaved changes any other way asks "Save changes?".

## Home

Home is a Psion-style System screen (decision 4): a row of app icons, and under the selected icon,
that app's recent files. Icons are 32×32 `.a5d` dot images (`tools/icons.py` draws them into
`home/icons/`), in the dot editor's default palette, so they can be redrawn on the device with
AREA512's own editor. Its layout and keys are in [PLAN_V1.md](PLAN_V1.md), *Home*.

![Home icons](../home/icons/preview.png)
