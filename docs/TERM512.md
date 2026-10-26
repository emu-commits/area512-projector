# Projector on TERM512: full screen

Status: investigated 2026-10-26, against engneer-hamachan/area512 `main`. **It can't be done from
the app alone today.** One small firmware change makes it possible, and with that change detection
is automatic.

## What happens now

TERM512 isn't detected at runtime: it's a **separate firmware build**. The user flashes
`Area512TFT7789.bin` or `Area512TFT9341.bin` (CMake option `AREA512_EXT_DISPLAY`, "Build for the
320x240 display with windows"). On that build:

- The filer draws full screen at 320×240. When it launches an app (`read_filer_action` in
  `picoruby-area512-filer/captft/src/core/ui_lifecycle.c`) it calls `area512_filer_set_gfx_window()`,
  which confines all drawing to a **centred 240×135 window** (`AREA512_WINDOW_WIDTH/HEIGHT` in
  `area512_hal/captft/include/area512_hal.h`).
- `area512_gfx_width()/height()` return the **window** size while a window is set, so
  `Display.width()` is `240` and `Display.height()` is `135`, exactly as on a bare Cardputer.
  Sprite pushes are offset into the window and clipped to it (`area512_gfx.cpp`).
- Python has no way to change or query the window: the `Display` module has only `width`,
  `height`, `fill_screen`, `set_brightness` and `show_header_image`. `Widget`, `IO`, `SD` and
  `Console` don't expose anything about it either.

So an app on TERM512 can't tell that it's on TERM512, and it couldn't escape the window even if
it could tell. That's by design: every app gets the same 240×135 canvas.

## What would make it work (upstream change)

A two-function addition to the MicroPython `Display` module (`area512_micropython_sprite.c`)
and the Ruby `Display` class (`picoruby-area512-sprite`):

    Display.screen_width()   # physical panel width: 320 on TERM512, 240 on a Cardputer
    Display.screen_height()  # 240 / 135
    Display.full_screen()    # area512_gfx_set_window(0, 0, 0, 0); no-op without a window

`full_screen()` is safe: the filer already resets the window to the whole display whenever an
app returns (`area512_filer_setup_ui` calls `area512_gfx_set_window(0, 0, 0, 0)`), so the change
only lasts as long as the app runs. On non-`EXT_DISPLAY` builds the functions return the internal
panel's size and `full_screen()` does nothing.

Detection is then automatic, with no setting:

    try:
        if Display.screen_width() > Display.width():
            Display.full_screen()
    except Exception:
        pass            # older firmware: stay in the window
    self.W = Display.width()
    self.H = Display.height()

Two things would still need checking against the firmware source when that change is made:

- whether `Widget.body_top()/body_bottom()` follow the window or the panel (they should follow
  `area512_gfx_height()`), and
- whether the filer's window-close animation expects the app to have drawn inside the window.

This is a request for the AREA512 repo (engneer-hamachan/area512), not this one. A short issue
there, with the API above, is the next step. Whether to open it is your call.

## Is Projector ready for 320×240?

Mostly. The layout already reads `Display.width()/height()` and the `Widget` body bounds (the
26 uses of `self.W`/`self.H`), and the column count comes from `char_width()`. No sizes are
hard-coded. Before shipping it full screen:

- **Memory.** BandedSprite bands are as wide as the screen, so each band costs a third more at
  320 px. The heap on the `EXT_DISPLAY` build hasn't been measured. It may be smaller, since that
  build also drives the internal display. Measure it with the `%` key before anything else.
- **No emulator.** `a512sim`/`fwrun` are 240×135 only (PLAN.md "Deferred"), so screenshots
  need a real TERM512 for now.
- **Use the room, don't just stretch.** 240×135 → 320×240 is 1.33× wider and 1.78× taller: about
  8 more list rows, a taller play chart, and room for the money table and the strip on one screen.
  The lifecycle shell (docs/LIFECYCLE_SHELL.md) would use the extra width for a phase rail.
