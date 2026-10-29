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
    if @msg != ""
      Widget.footer(@sp, @msg)
      return
    end
    st = (@mode == :move ? "MOVE " : "TYPE ") + (@row + 1).to_s + ":" +
         (chars(cur_line, @col) + 1).to_s + " " + @words.to_s + "w"
    if @mode == :move
      Widget.hints(@sp, hint_fit(DOC_KEYS, (@w - 3) / @cw - st.length - 11))
    else
      Widget.hints(@sp, [["Tab", "menu"]])
    end
    Widget.text_right(@sp, @w - 3, @h - 13, st, @c_em)
  end

  # TERM512's list: the selected document's first lines, only as many as show, and only
  # their first 64 bytes. Not the whole text split: the list keeps them, and a second copy of
  # the document while it opens ran the VM out at 12 KB on the TERM512 build. And a long
  # paragraph whole made Widget.clip, which drops a character at a time, slow every band.
  def doc_preview(name)
    text = read_file(path_of(name))
    return [] if text.nil?
    return ["(too big to open)"] if share(text.length, room_of(text)) > 100
    out = []
    i = 0
    while out.length < 16 && i < text.length
      j = text.index("\n", i) || text.length
      n = j - i
      if n > 64
        n = 64
        n -= 1 while n > 0 && text.getbyte(i + n) >= 0x80 && text.getbyte(i + n) < 0xc0
      end
      out.push(text[i, n])
      i = j + 1
    end
    out
  end
end
