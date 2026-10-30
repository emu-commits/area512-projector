class Calc
  def render_screen
    return if render_ui
    if @screen == :doc
      render_sheet
    else
      render_files
    end
  end

  # one line of the bar above the grid at 240x135, two at 320x240
  def fbar_lines
    @wide ? 2 : 1
  end

  def render_sheet
    frame(@name, @dirty ? "*" : "")
    render_bar
    render_grid
    if @edit
      foot_pairs(@wide ? EDIT_WIDE : EDIT_HINTS, "")
    else
      foot(GRID_KEYS, GRID_NAV)
    end
  end

  # The cell's name, then its whole text (or what's being typed, ending in _), and a
  # formula's value on the right when there's room
  def render_bar
    y = @top + 2
    name = selected_name
    t(4, y, name, @c_em)
    x = 4 + (name.length + 1) * @cw
    cols = (@w - x - 4) / @cw
    s = @edit ? @edit + "_" : cell_at(@col, @row)
    right = ""
    if @edit.nil? && s.length > 0 && s.getbyte(0) == 61
      v = shown(@col, @row)
      right = v[1] == :err ? "#ERR" : "= " + fmt_num(v[0], 14)
    end
    n = fbar_lines
    room = cols * n
    room -= right.length + 2 if right != ""
    if s.length > room
      s = @edit ? s[s.length - room, room] : s[0, room - 1] + "~"
    end
    i = 0
    while i < n && i * cols < s.length
      t(x, y + i * @lh, s[i * cols, cols], @edit ? @c_sel : @c_text)
      i += 1
    end
    Widget.text_right(@sp, @w - 4, y + (n - 1) * @lh, right, @c_em) if right != ""
    yy = grid_y - 2
    @sp.line(0, yy, @w - 1, yy, @c_border)
  end

  # The grid is worked out once a frame (layout_grid), then drawn band by band: cutting
  # each row's String into cells and formatting each number, once for every band, was
  # slow enough on the firmware that keys were lost.
  def paint
    layout_grid if @screen == :doc
    while @sp.draw
      render
    end
  end

  # @gcols: [col, x, px wide] of the columns on screen. @gtext and @gkind, a cell a slot,
  # row after row of them: the text as drawn, and 0 text, 1 number, 2 #ERR. Two flat
  # Arrays made at their size, and the last frame's let go first: with a sheet at its
  # limit, an Array per cell ran the VM out (PLAN_V1 4.3).
  def layout_grid
    recalc unless @calc
    @gtext = nil
    @gkind = nil
    @gcols = []
    x = HEAD_W
    c = @left
    while c < COLS && x < @w
      w = col_px(c)
      @gcols.push([c, x, w])
      x += w
      c += 1
    end
    nc = @gcols.length
    nr = visible_rows
    nr = ROWS - @top_r if @top_r + nr > ROWS
    @gtext = Array.new(nr * nc)
    @gkind = Array.new(nr * nc)
    i = 0
    while i < nr
      r = @top_r + i
      p = @rows[r] ? @rows[r].split("\t") : nil
      j = 0
      while j < nc
        c = @gcols[j][0]
        cell_text(i * nc + j, c, r, p && c < p.length ? p[c] : "", (@gcols[j][2] - 6) / @cw) if p
        j += 1
      end
      i += 1
    end
  end

  def cell_text(n, c, r, t, room)
    return if t == ""
    v = value(c, r)
    if t.getbyte(0) == 61
      @gtext[n] = v.nil? ? "#ERR" : fmt_num(v, room)
      @gkind[n] = v.nil? ? 2 : 1
    elsif v.nil?
      @gtext[n] = t.length > room ? t[0, room] : t
      @gkind[n] = 0
    else
      @gtext[n] = t.length > room ? fmt_num(v, room) : t
      @gkind[n] = 1
    end
  end

  def render_grid
    y0 = grid_y
    j = 0
    while j < @gcols.length
      g = @gcols[j]
      @sp.fill_rect(g[1], y0, g[2], ROW_H, @c_box) if g[0] == @col
      @sp.rect(g[1], y0, g[2], ROW_H, @c_border)
      t(g[1] + 3, y0 + 1, (65 + g[0]).chr, g[0] == @col ? @c_sel : @c_text)
      j += 1
    end
    y = y0 + ROW_H
    nc = @gcols.length
    i = 0
    while i * nc < @gtext.length
      r = @top_r + i
      @sp.fill_rect(0, y, HEAD_W, ROW_H, @c_box) if r == @row
      t(2, y + 1, (r + 1).to_s, r == @row ? @c_sel : @c_dim)
      j = 0
      while j < @gcols.length
        draw_cell(@gcols[j], r, y, i * nc + j)
        j += 1
      end
      y += ROW_H
      i += 1
    end
  end

  # text left, numbers right, #ERR in the emphasis colour; the copied cell is outlined
  def draw_cell(g, r, y, n)
    c = g[0]
    x = g[1]
    w = g[2]
    sel = c == @col && r == @row
    @sp.fill_rect(x, y, w, ROW_H, @c_box) if sel
    @sp.rect(x, y, w, ROW_H, sel ? @c_sel : @c_border)
    @sp.rect(x + 1, y + 1, w - 2, ROW_H - 2, @c_em) if @clip && @clip[1] == c && @clip[2] == r
    if sel && @edit
      room = (w - 6) / @cw
      s = @edit + "_"
      s = s[s.length - room, room] if s.length > room
      t(x + 3, y + 1, s, @c_sel)
      return
    end
    s = @gtext[n]
    return if s.nil?
    col = sel ? @c_sel : @c_text
    if @gkind[n] == 0
      t(x + 3, y + 1, s, col)
    else
      col = @c_em if @gkind[n] == 2
      Widget.text_right(@sp, x + w - 3, y + 1, s, col)
    end
  end
end
