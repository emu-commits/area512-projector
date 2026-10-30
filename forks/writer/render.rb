class Writer
  def render_screen
    return if render_ui
    if @screen == :doc
      render_doc
    else
      render_files
    end
  end

  # ---- the document: wrapped rows (laid out by layout), the cursor, the status line

  def render_doc
    frame(@name, @dirty ? "*" : "")
    y = @top
    h = @bot - @top
    Widget.panel(@sp, 0, y, @w, h)
    x = PAGE_PAD
    yy = y + PAGE_PAD
    i = 0
    while i < @view.length
      v = @view[i]
      s = line(v[0])
      t(x, yy, part(s, v[1], v[2] - v[1]), @c_text) if v[2] > v[1]
      draw_hit(x, yy, s, v) if @hit && @hit[0] == v[0]
      draw_cursor(x, yy, s) if i == @cur_y
      yy += LINE_H
      i += 1
    end
    Widget.scrollbar(@sp, @w - PAGE_PAD - SCROLLBAR_W, y + PAGE_PAD, h - PAGE_PAD * 2,
                     @scr, visible_rows, @lines.length)
    doc_foot
  end

  # Type: a bar. Move: a block over the character, so the mode shows where you're looking.
  def draw_cursor(x, y, s)
    cx = x + @cur_x
    mx = x + @wrap_w + 1
    cx = mx if cx > mx
    if @mode == :move
      g = @col < s.length ? glyph_w(s, @col) : GLYPH_W
      @sp.fill_rect(cx, y - 1, g, LINE_H - 1, @c_sel)
      t(cx, y, part(s, @col, step(s, @col)), @c_bg) if @col < s.length
    else
      @sp.line(cx, y - 1, cx, y + LINE_H - 2, @c_sel)
    end
  end

  def draw_hit(x, y, s, v)
    a = @hit[1]
    b = a + @hit[2]
    a = v[1] if a < v[1]
    b = v[2] if b > v[2]
    return if b <= a
    hx = x + width(s, v[1], a)
    @sp.fill_rect(hx, y - 1, width(s, a, b), LINE_H - 1, @c_em)
    t(hx, y, part(s, a, b - a), @c_bg)
  end

  # TYPE or MOVE, line:column and the words, right; the hint bar in what's left
  def doc_foot
    st = (@mode == :move ? "MOVE " : "TYPE ") + (@row + 1).to_s + ":" + (col_chars + 1).to_s +
         " " + @words.to_s + "w"
    if @mode != :move
      foot_pairs(@wide ? TYPE_HINTS : type_fit((@w - 3) / @cw - st.length - 2), st)
    elsif @wide
      if @hl_spec != DOC_KEYS                       # foot's cache: every key, on two lines
        @hl = hint_all(DOC_KEYS)
        @hl_spec = DOC_KEYS
      end
      foot_pairs(@hl, st)
    else
      foot_pairs(hint_fit(DOC_KEYS, (@w - 3) / @cw - st.length - 11), st)
    end
  end

  # the Cardputer's one line: TYPE_HINTS while they fit in room characters
  def type_fit(room)
    out = []
    i = 0
    while i < TYPE_HINTS.length
      room -= TYPE_HINTS[i][0].length + TYPE_HINTS[i][1].length + 4
      break if room < 0
      out.push(TYPE_HINTS[i])
      i += 1
    end
    out
  end

  # TERM512's list: the markdown Slide shows a document in, the marks big, what they make
  # beside them
  def guide(x, y, w, h)
    rh = h / MD_GUIDE.length
    rh = 24 if rh > 24
    MD_GUIDE.each do |g|
      Widget.big_text(@sp, x, y, g[0], @c_em)
      t(x + 44, y + 6, clip(g[1], w - 44), @c_text)
      y += rh
    end
  end
end
