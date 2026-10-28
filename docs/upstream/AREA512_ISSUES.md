# Issues to file on engneer-hamachan/area512

> **Status 2026-10-28: A and B are done.** Both were sent as pull requests instead and merged into
> AREA512 `main` on 2026-10-28, not yet in a release (latest v2.7):
> A as [#32](https://github.com/engneer-hamachan/area512/pull/32) (`Display.screen_width()`,
> `screen_height()`, `full_screen()`), B as [#33](https://github.com/engneer-hamachan/area512/pull/33).
> B shipped as a function, `Area512.run_next(path)`, not the `/Area512_data/etc/next` file below;
> `default=app:<path>` is as proposed. C was never filed, and the v1 plan (../PLAN_V1.md) doesn't
> need it. The text below is kept as it was written.

Three requests, in priority order. **A** blocks us (full screen on TERM512). **B** is what lets
an app suite feel like one device. **C** is small and optional. File them as separate issues:
each one stands alone, and the maintainer can say yes to one without the others. Each section
below is ready to paste: the first line is the title, the rest is the body.

Before filing, re-check the file and function names against the current `main`. They were read on
2026-10-26.

---

## A. Let apps use the whole screen on the external display (TERM512) build

**Title:** Let Python and Ruby apps draw full screen on the external-display (TERM512) build

**Body:**

Hi, and thanks for AREA512 and the TERM512 support. I build apps for it
([Projector](https://github.com/emu-commits/area512-projector), a MicroPython planning app) and
I'd like them to use the whole 320×240 screen when they run on TERM512.

**What happens now**

On the `AREA512_EXT_DISPLAY` build, the filer confines every app it launches to a centred
240×135 window: `read_filer_action()` in
`picoruby-area512-filer/captft/src/core/ui_lifecycle.c` calls `area512_filer_set_gfx_window()`
(`AREA512_WINDOW_WIDTH`/`HEIGHT` in `area512_hal/captft/include/area512_hal.h`). While the window
is set, `area512_gfx_width()`/`height()` return the window size, so `Display.width()` is 240 and
`Display.height()` is 135, exactly as on a bare Cardputer. There's no API to query the panel size
or leave the window, so an app can't tell it's on TERM512 and couldn't use the extra space if it
could.

Keeping 240×135 as the default makes sense: every existing app works unchanged. I'm asking for
a way to opt out.

**Proposal**

Three functions on `Display`, in both MicroPython (`area512_micropython_sprite.c`) and Ruby
(`picoruby-area512-sprite`):

| Function | Returns / does |
|---|---|
| `Display.screen_width()` | the physical panel width (320 on TERM512, 240 on a Cardputer) |
| `Display.screen_height()` | the physical panel height (240 / 135) |
| `Display.full_screen()` | `area512_gfx_set_window(0, 0, 0, 0)`; does nothing if no window is set |

On builds without `AREA512_EXT_DISPLAY`, `screen_width/height` return the display size and
`full_screen()` is a no-op, so apps can call it on any device.

An app then opts in with no setting and no build flag:

```python
if Display.screen_width() > Display.width():
    Display.full_screen()
W = Display.width()      # now 320 x 240
```

**Why I think it's safe**

- The filer already resets the window whenever it takes the screen back:
  `area512_filer_setup_ui()` calls `area512_gfx_set_window(0, 0, 0, 0)`. So the change lasts
  only while the app runs.
- `Widget.body_top()/body_bottom()` already follow `area512_gfx_height()`
  (`picoruby-area512-widget/src/core/metrics.c`), so Widget layouts follow automatically.
- Apps that never call `full_screen()` behave exactly as today.

One thing I'm not sure about: the window close animation
(`filer_window_close_animation.c`) may expect the last frame to be inside the window. If it
does, `full_screen()` could also set a flag that the close animation uses to start from the
whole screen.

I'm happy to send a PR if this direction is acceptable.

---

## B. Let an app hand off to another app when it exits, and boot into an app

**Title:** App hand-off: run a named app when the current one exits, and an optional boot app

**Body:**

I'm building a small suite of apps that share data on the SD card (a planner, a task app, and
improved forks of the bundled tools). They work together through files, but there's no way for
one app to open another. Every switch means quitting to the filer, finding the folder and pressing
`R`. That makes a suite feel like separate programs, and it rules out a launcher written as an app.

Apps can't call each other directly, and with about 53 KB of Python heap they shouldn't. I'm only
asking for a hand-off **between** runs.

**Proposal**

1. **Hand-off file.** After an app run action returns (`ACTION_RUN_DIR`, `ACTION_RUN_PYTHON`,
   `ACTION_RUN_RUBY` in `run_action_task()` in `components/area512/filer_shell.c`), the filer
   checks for `/Area512_data/etc/next`. If the file exists, it reads one line (an app directory
   or file path), **deletes the file**, and runs that path the same way `R` would, without first
   redrawing the filer. If the path doesn't exist, it shows the usual "No main.manifest…"
   message and stays in the filer.
2. **Boot app (optional).** `etc/` default UI already accepts `default=graphical` and
   `default=terminal` (`area512_hal/ui/area512_default_ui.c`). Add `default=app:<path>`: start
   the filer as now, then run that app once at boot. Quitting it lands in the filer as usual.

Deleting the file before running means a crashing app can't cause a loop: after one failure
you're back in the filer. Apps only need `SD.write` to use it, so it works from Python and Ruby
with no new bindings. I'd be glad to send a PR.

---

## C. Elapsed time for Python apps (optional)

**Title:** Expose a millisecond uptime counter to MicroPython apps

**Body:**

MicroPython apps have no way to measure elapsed time: `sleep()`/`sleep_ms()` can wait, but nothing reports
time passing (no `time`/`utime`, and `import` isn't available at MINIMUM). A task timer or a
"you've been working 25 minutes" prompt needs one counter:

```python
System.ticks_ms()    # milliseconds since boot (esp_timer_get_time() / 1000), wraps like ticks_ms
```

It could live on an existing module (next to `sleep_ms()`, say) if a new one isn't wanted.

*Optional, only if you'd want it:* if the firmware ever learns the real time (an I2C RTC unit on
the Grove port, or the file-transfer tool sending the host's time), a `System.time()` that returns
seconds since 1970, or `0` when unknown, would let apps use dates without ever asking the user.
