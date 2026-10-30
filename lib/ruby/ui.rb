# Shared by the suite's PicoRuby forks (Agenda first): the key loop, hint bar, menu bar,
# Help and question screens of docs/UI.md, and the app registry and switching files of
# docs/APPS_FORMAT.md. The Ruby twin of lib/py/base.py and lib/py/menu.py. build.sh puts it
# first in each fork's main.manifest, so a fork's class is "class Agenda < SuiteApp".
#
# Written for mruby/c (AREA512's PicoRuby VM), the way the bundled apps are: no send or
# procs (a screen is drawn by the app's render_screen, which looks at @screen), and no
# break, next or return inside a block (while loops instead).

class SuiteApp
  REG_FILE = "/data/area512/apps.txt" unless const_defined?(:REG_FILE)
  OPEN_FILE = "/data/area512/open.txt" unless const_defined?(:OPEN_FILE)
  # TERM512: three hint lines under the body; the menu bar's hints and app row take what
  # they need (docs/UI.md, PLAN_V1 5.1)
  FOOT_EXTRA = 28 unless const_defined?(:FOOT_EXTRA)
  FOOT_H = 14 unless const_defined?(:FOOT_H)        # Widget.hints' bar (WIDGET_FOOTER_HEIGHT)
  # what the arrows do on a list, for foot's nav
  NAV_ROWS = ";. select" unless const_defined?(:NAV_ROWS)

  def ui_init
    # TERM512: leave the 240x135 window (firmware after v2.7; older has no screen_width)
    begin
      Display.full_screen if Display.screen_width > Display.width
    rescue
    end
    @w = Display.width
    @h = Display.height
    @wide = @w >= 300 && @h >= 200
    @top = Widget.body_top
    @bot = Widget.body_bottom
    @bot -= FOOT_EXTRA if @wide
    @row_apps = nil  # the app row's [[digit, name, path], ...], read once (SD isn't up yet)
    @cw = Widget.char_width
    @lh = 13
    @c_text = Widget.theme_text
    @c_em = Widget.theme_emphasis
    @c_sel = Widget.theme_selected
    @c_box = Widget.theme_box
    @c_bg = Widget.theme_background
    @c_border = Widget.theme_border
    @c_dim = Widget.dim
    @msg = ""
    @hl_spec = nil
    @hl = []
    @menu = nil      # [menus, open menu, item, its hint lines] while the menu bar is open
  end

  # ---- keys

  def key
    k = ""
    STDIN.raw { k = Widget.read_key }
    k
  end

  # the bare ; . , / have the arrows printed on them: one key, not Fn+key
  def arrow(k)
    return "UP" if k == ";"
    return "DOWN" if k == "."
    return "LEFT" if k == ","
    return "RIGHT" if k == "/"
    k
  end

  def nav(k)
    return "DOWN" if k == "j"
    return "UP" if k == "k"
    return "LEFT" if k == "h"
    return "RIGHT" if k == "l"
    arrow(k)
  end

  # One key on a screen with a key table: Tab opens the menu bar, which hands back the key
  # of the item picked, so the screen has one code path for both. "@<path>" is a switch to
  # another app (the Apps menu): the app saves, then calls switch_to.
  def cmd(spec)
    while true
      paint
      @msg = ""
      k = nav(key)
      if k == "%"
        @msg = mem_text
      elsif k != "\t"
        return k
      else
        k = menu_main(spec)
        return k if k
      end
    end
  end

  # the hidden % key (docs/UI.md): the VM's heap, shared by every Ruby app's objects
  def mem_text
    m = PicoRubyVM.memory_statistics
    "Ruby heap: " + (m[:free] / 1024).to_s + " KB free of " + (m[:total] / 1024).to_s
  rescue
    "Ruby heap: not known here"
  end

  def paint
    while @sp.draw
      render
    end
  end

  def render
    render_screen
    menu_render if @menu
  end

  # ---- drawing helpers

  def frame(title, right)
    @sp.fill(@c_bg)
    Widget.header(@sp, title, right)
  end

  def t(x, y, s, c)
    @sp.text(x, y, s, c)
  end

  def clip(s, w)
    Widget.clip(@sp, s, w)
  end

  def row(x, y, w, s, selected)
    if selected
      @sp.fill_rect(x, y - 1, w, @lh, @c_box)
      t(x + 4, y, clip(s, w - 8), @c_sel)
    else
      t(x + 4, y, clip(s, w - 8), @c_text)
    end
  end

  # nav: on TERM512, what the screen's arrows do ("keys label|keys label", as pairs reads),
  # before the table's items; the Cardputer's one line has no room for it. Cached by spec: a
  # screen's spec always comes with the same nav.
  def foot(spec, nav = nil)
    if @hl_spec != spec
      @hl = @wide ? hint_trim((nav ? pairs(nav) : []) + hint_all(spec), 0) : hint_list(spec)
      @hl_spec = spec
    end
    foot_pairs(@hl, "")
  end

  # "key label|key label" as [[key, label], ...], "_" in a key a space: a list of hints kept
  # as one string, so it costs one object until it's shown
  def pairs(s)
    out = []
    s.split("|").each do |it|
      sp = it.index(" ")
      out.push([it[0, sp].tr("_", " "), it[sp + 1, it.length]])
    end
    out
  end

  # The bottom of the screen: a message, else the hints ([[key, label], ...]); right is a
  # status on the right of the first line ("" for none). On TERM512 three lines of hints
  # (hint_trim them to fit), or the menu bar's (menu_render); on the Cardputer one line, the
  # hints cut to what fits beside right.
  def foot_pairs(hs, right)
    if @wide
      wide_foot(hs, right)
    elsif @msg != ""
      Widget.footer(@sp, @msg)
    else
      Widget.hints(@sp, hs)
      Widget.text_right(@sp, @w - 3, @h - 13, right, @c_em) if right != ""
    end
  end

  def wide_foot(hs, right)
    y = @h - FOOT_H - FOOT_EXTRA
    @sp.line(0, y, @w - 1, y, @c_border)
    rw = right == "" ? 0 : Widget.text_width(@sp, right) + 8
    if @msg != ""
      t(3, y + 2, clip(@msg, @w - 6 - rw), @c_em)
    else
      hint_place(hs, rw, y, 3, true)
    end
    Widget.text_right(@sp, @w - 3, y + 2, right, @c_em) if right != ""
  end

  # "[key] label" pairs from y + 2 down, a key never split from its label, the first line
  # stopping rw short; drawn on the first n lines. Returns the lines they all take.
  def hint_place(hs, rw, y, n, draw)
    @hx = 3
    @hln = 0
    i = 0
    while i < hs.length
      hint_at(hs[i][0], hs[i][1], rw, y, n, draw)
      i += 1
    end
    @hln + 1
  end

  # one of them at line @hln, x @hx, and past it
  def hint_at(k, label, rw, y, n, draw)
    kk = "[" + k + "]"
    w = Widget.text_width(@sp, kk + " " + label) + @cw
    if @hx + w > (@hln == 0 ? @w - 3 - rw : @w - 3) && @hx > 3
      @hln += 1
      @hx = 3
    end
    if draw && @hln < n
      yy = y + 2 + @hln * @lh
      t(@hx, yy, kk, @c_em)
      t(@hx + Widget.text_width(@sp, kk) + @cw, yy, label, @c_text)
    end
    @hx += w
  end

  # hs (the caller's own new list) cut to TERM512's three lines beside a status rw px wide:
  # the last items go first, never the very last ([Tab] menu)
  def hint_trim(hs, rw)
    hs.delete_at(hs.length - 2) while hs.length > 1 && hint_place(hs, rw, 0, 0, false) > 3
    hs
  end

  # the Series 3's application buttons: "1 Home  2 Projector ...", this app marked, shown
  # under the menu bar on TERM512, where Tab then the digit switches. Names are cut to 4
  # letters when all of them don't fit.
  def app_row
    if @row_apps.nil?
      @row_apps = reg_read
      n = 0
      @row_apps.each { |p| n += p[1].length + 3 }
      @row_n = n * @cw > @w - 3 ? 4 : 9
    end
    y = @h - FOOT_H
    @sp.line(0, y, @w - 1, y, @c_border)
    x = 3
    @row_apps.each do |p|
      name = p[1][0, @row_n]
      w = (name.length + 3) * @cw
      if x + w - @cw <= @w
        me = p[2] == @app_dir
        @sp.fill_rect(x - 2, y + 1, w - @cw + 3, 13, @c_box) if me
        t(x, y + 1, p[0], @c_em)
        t(x + 2 * @cw, y + 1, name, me ? @c_sel : @c_text)
      end
      x += w
    end
  end

  # TERM512: every item of the table, the numbered ones first, then "[Tab] menu"
  def hint_all(spec)
    nums = []
    rest = []
    spec.tr(";", "|").split("|").each do |it|
      sp = it.index(" ")
      if sp && sp > 0
        if digit?(it)
          nums.push(it)
        else
          rest.push(it)
        end
      end
    end
    nums.sort!
    out = []
    nums.each { |it| out.push([it[1, it.index(" ") - 1], it[it.index(" ") + 1, it.length]]) }
    rest.each { |it| out.push([it[0, it.index(" ")], it[it.index(" ") + 1, it.length]]) }
    out.push(["Tab", "menu"])
    out
  end

  # the table's numbered items, in order, while they fit beside "[Tab] menu"; Widget.hints
  # draws "[key] label " from 3 px in, unclipped
  def hint_list(spec)
    hint_fit(spec, (@w - 3) / @cw - 10)
  end

  # the same in room characters, for a screen with more on its hint line
  def hint_fit(spec, room)
    found = []
    spec.tr(";", "|").split("|").each do |it|
      found.push(it) if digit?(it)
    end
    found.sort!
    out = []
    i = 0
    while i < found.length
      it = found[i]
      room -= it.length + 2
      break if room < 0
      sp = it.index(" ")
      out.push([it[1, sp - 1], it[sp + 1, it.length]])
      i += 1
    end
    out.push(["Tab", "menu"])
    out
  end

  def digit?(s)
    s.length > 0 && s.getbyte(0) >= 49 && s.getbyte(0) <= 57
  end

  # ---- the menu bar (Tab), drawn over the screen it was opened from

  def menu_main(spec)
    ms = menu_parse(spec)
    m = 0
    apps = []
    reg_read.each { |p| apps.push([p[0], p[1]]) }
    if apps.length > 0
      ms.unshift(["Apps", apps])     # first, as on the Psion; opens on the screen's own
      m = 1
    end
    @menu = [ms, m, 0, 0]
    @menu[3] = menu_hints(ms, 0, 0, false) if @wide
    r = nil
    while true
      paint
      k = arrow(key)
      n = ms[@menu[1]][1].length
      if k == "ESC" || k == "\t"
        break
      elsif k == "LEFT"
        @menu[1] = (@menu[1] + ms.length - 1) % ms.length
        @menu[2] = 0
      elsif k == "RIGHT"
        @menu[1] = (@menu[1] + 1) % ms.length
        @menu[2] = 0
      elsif k == "UP"
        @menu[2] = (@menu[2] + n - 1) % n
      elsif k == "DOWN"
        @menu[2] = (@menu[2] + 1) % n
      else
        k = ms[@menu[1]][1][@menu[2]][0] if k == "ENTER"
        if menu_has(ms, k)
          r = menu_run(spec, k)
          break
        end
      end
    end
    @menu = nil
    r
  end

  def menu_has(ms, k)
    found = false
    ms.each do |mm|
      mm[1].each { |it| found = true if it[0] == k }
    end
    found
  end

  def menu_run(spec, k)
    if k == "?"
      @menu = nil
      help(spec)
      return nil
    end
    return "ENTER" if k == "ENT"
    return k unless k.length == 1 && digit?(k)
    r = nil                          # this app: nothing to do
    reg_read.each do |p|
      r = "@" + p[2] if p[0] == k && p[2] != @app_dir
    end
    r
  end

  # [[title, [[key, label], ...]], ...]; Help goes last in the last menu
  def menu_parse(spec)
    ms = []
    spec.split(";").each do |part|
      p = part.split("|")
      its = []
      i = 1
      while i < p.length
        it = p[i]
        it = it[1, it.length] if digit?(it)
        sp = it.index(" ")
        its.push([it[0, sp], it[sp + 1, it.length]])
        i += 1
      end
      ms.push([p[0], its])
    end
    ms[ms.length - 1][1].push(["?", "help"])
    ms
  end

  def menu_render
    ms = @menu[0]
    hh = Widget.header_height
    @sp.fill_rect(0, 0, @w, hh + 1, @c_bg)
    @sp.line(0, hh, @w - 1, hh, @c_border)
    x = 5
    mx = 2
    j = 0
    while j < ms.length
      tw = Widget.text_width(@sp, ms[j][0])
      c = @c_text
      if j == @menu[1]
        @sp.fill_rect(x - 3, 1, tw + 6, hh - 1, @c_box)
        c = @c_sel
        mx = x - 3
      end
      t(x, 3, ms[j][0], c)
      x += tw + 12
      j += 1
    end
    menu_box(ms[@menu[1]][1], mx, hh + 1)
    m = @msg
    @msg = ""
    if @wide
      # every key that works in the bar, as many lines as they take, then the app row if
      # Home has written one; from at least where the screen's three hint lines start
      apps = ms[0][0] == "Apps"
      y = (apps ? @h - FOOT_H : @h) - @menu[3] * @lh - 3
      y = @h - FOOT_H - FOOT_EXTRA if y > @h - FOOT_H - FOOT_EXTRA
      @sp.fill_rect(0, y, @w, @h - y, @c_bg)
      @sp.line(0, y, @w - 1, y, @c_border)
      menu_hints(ms, y, @menu[3], true)
      app_row if apps
    else
      fh = @h - @bot - 1                         # Widget.hints draws over what's there
      @sp.fill_rect(0, @h - fh, @w, fh, @c_bg)
      hs = [["<>", "menus"], ["ESC", "close"]]
      hs.unshift(["1-" + ms[0][1][ms[0][1].length - 1][0], "switch app"]) if ms[0][0] == "Apps"
      foot_pairs(hs, "")
    end
    @msg = m
  end

  # TERM512: what can be pressed in the menu bar, as hint_place lays it out: every item's own
  # key (not the arrows, which move in it, nor Enter, which runs the one picked), from any
  # menu, then Enter, the app digits, moving and closing. Read from the menus as it goes, no
  # list made: Writer's save, right after, needs the memory in one piece.
  def menu_hints(ms, y, n, draw)
    @hx = 3
    @hln = 0
    ms.each do |mm|
      if mm[0] == "Apps"
        hint_at("1-" + mm[1][mm[1].length - 1][0], "switch app", 0, y, n, draw)
      else
        mm[1].each { |it| hint_at(it[0], it[1], 0, y, n, draw) if it[0].length == 1 && it[0] != "?" }
      end
    end
    hint_at("ENT", "run", 0, y, n, draw)
    hint_at("<>", "menus", 0, y, n, draw)
    hint_at("ESC", "close", 0, y, n, draw)
    @hln + 1
  end

  def menu_box(its, x, y)
    w = 0
    its.each do |it|
      n = it[1].length + (it[0] == "?" ? 0 : it[0].length) + 3
      w = n if n > w
    end
    w = w * @cw + 14
    x = @w - 2 - w if x + w > @w - 2
    h = its.length * @lh + 4
    @sp.fill_rect(x, y, w, h, @c_bg)
    @sp.rect(x, y, w, h, @c_border)
    j = 0
    while j < its.length
      yy = y + 2 + j * @lh
      c = @c_text
      if j == @menu[2]
        @sp.fill_rect(x + 1, yy - 1, w - 2, @lh, @c_box)
        c = @c_sel
      end
      lab = its[j][1]
      t(x + 4, yy, lab[0, 1].upcase + lab[1, lab.length], c)
      Widget.text_right(@sp, x + w - 6, yy, its[j][0], @c_em) if its[j][0] != "?"
      j += 1
    end
  end

  # Tab > Help: every menu on one screen, a key never split from its label
  def help(spec)
    cols = (@w - 12) / @cw
    body = []
    menu_parse(spec).each do |mm|
      s = mm[0] + ":"
      mm[1].each do |it|
        if it[0] != "?"
          pair = it[0] + " " + it[1]
          if s.length + 2 + pair.length > cols
            body.push(s)
            s = " "
          end
          s = s + "  " + pair
        end
      end
      body.push(s)
    end
    body.push("Arrows: ; . , /  ESC back  Tab menu")
    show("KEYS", body)
  end

  # ---- question screens (Widget.input blanks the screen to one line, as in Python)

  def show(title, body)
    @q = [title, body]
    @screen_was = @screen
    @screen = :show
    paint
    @screen = @screen_was
    key
  end

  def render_show
    frame(@q[0], "")
    y = @top + 3
    i = 0
    n = @q[1].length
    while i < n && y <= @bot - @lh
      t(6, y, clip(@q[1][i], @w - 12), i == n - 1 ? @c_dim : @c_text)
      y += @lh
      i += 1
    end
    Widget.hints(@sp, [["any", "key"]])
  end

  # true / false, or nil for Esc
  def ask_yn(title, q)
    @q = [title, q]
    was = @screen
    @screen = :yn
    r = nil
    while true
      paint
      k = key
      if k == "y" || k == "Y"
        r = true
        break
      elsif k == "n" || k == "N"
        r = false
        break
      elsif k == "ESC"
        break
      end
    end
    @screen = was
    r
  end

  def render_yn
    frame(@q[0], "")
    t(6, @top + 6, clip(@q[1], @w - 12), @c_em)
    Widget.hints(@sp, [["y", "yes"], ["n", "no"], ["ESC", "back"]])
  end

  # typed at the end, Backspace deletes, Enter OK, Esc cancel (nil). maxlen is in bytes.
  def ask_text(title, q, initial, maxlen)
    s = initial
    was = @screen
    @screen = :ask
    r = nil
    while true
      @q = [title, q, s + "_", s.length.to_s + "/" + maxlen.to_s]
      paint
      k = key
      if k == "ENTER"
        r = s.tr("|\t", "/ ").strip
        break
      elsif k == "ESC"
        break
      elsif k == "BS"
        s = drop_char(s)
      elsif k.length == 1 && k.getbyte(0) >= 32 && k.getbyte(0) != 127 && s.length < maxlen
        s = s + k        # bytes of 128 and up: UTF-8 from the keyboard's IME, kept as typed
      end
    end
    @screen = was
    r
  end

  # the last character, all of its UTF-8 bytes
  def drop_char(s)
    n = s.length
    return s if n == 0
    n -= 1
    n -= 1 while n > 0 && s.getbyte(n) >= 128 && s.getbyte(n) < 192
    s[0, n]
  end

  def render_ask
    frame(@q[0], @q[3])
    t(6, @top + 4, clip(@q[1], @w - 12), @c_em)
    y = @top + 4 + @lh + 4
    h = @lh * 2 + 6
    @sp.fill_rect(2, y, @w - 4, h, @c_box)
    @sp.rect(2, y, @w - 4, h, @c_border)
    cols = (@w - 16) / @cw
    s = @q[2]
    s = s[s.length - cols * 2, cols * 2] if s.length > cols * 2
    t(8, y + 3, s[0, cols], @c_sel)
    t(8, y + 3 + @lh, s[cols, cols], @c_sel) if s.length > cols
    Widget.hints(@sp, [["ENT", "ok"], ["ESC", "back"]])
  end

  # the screens above, for an app's render_screen: true if it drew one
  def render_ui
    if @screen == :show
      render_show
    elsif @screen == :yn
      render_yn
    elsif @screen == :ask
      render_ask
    else
      return false
    end
    true
  end

  # ---- files shared between the apps (docs/APPS_FORMAT.md)

  def read_file(path)
    return nil unless File.exist?(path)
    SD.read(path)
  rescue
    nil
  end

  def ensure_dir(path)
    Dir.mkdir(path) unless Dir.exist?(path)
  end

  # Home's registry: [[digit, name, path], ...]; none without Home
  def reg_read
    out = []
    text = read_file(REG_FILE)
    return out unless text
    text.split("\n").each do |line|
      p = line.split("|")
      out.push(p) if p.length == 3 && p[0].length == 1 && p[2] != ""
    end
    out
  end

  # an open request for this app ([verb, arg]), read once and deleted; nil if none
  def take_request(name)
    text = read_file(OPEN_FILE)
    return nil unless text
    p = text.strip.split("|")
    return nil if p.length < 2 || p[0] != name   # another app's: leave it for that app
    File.unlink(OPEN_FILE)
    [p[1], p.length > 2 ? p[2] : ""]
  end

  # place.txt as a hash, read once and deleted
  def take_place(path)
    text = read_file(path)
    return nil unless text
    File.unlink(path)
    f = {}
    text.split("\n").each do |line|
      kv = line.split(": ", 2)
      f[kv[0]] = kv[1] if kv.length == 2
    end
    f
  end

  # hand off: the filer runs path once this app returns. False (and a message) if the
  # firmware can't.
  def run_next(path)
    Area512.run_next(path)
    true
  rescue
    @msg = "Can't switch: needs AREA512 after v2.7"
    false
  end

  def home_path
    r = nil
    reg_read.each { |p| r = p[2] if p[1] == "Home" }
    r
  end
end
