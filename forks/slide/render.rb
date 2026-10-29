class Slide
  def render_screen
    return if render_ui
    if @screen == :doc
      render_deck
    else
      render_files
    end
  end

  # ---- a page: the deck's name and the page number above, the rows, the keys below

  def render_deck
    frame(@name, (@page + 1).to_s + "/" + pages.to_s)
    y = @top + 4
    last = rows_fit(@scroll)
    i = @scroll
    while i < last
      draw_row(@rows[i], y)
      y += row_h(@rows[i])
      i += 1
    end
    if @scroll > 0 || last < @rows.length
      Widget.scrollbar(@sp, @w - 5, @top + 3, @bot - @top - 6, @scroll, last - @scroll, @rows.length)
    end
    foot(SHOW_KEYS)
  end

  def row_h(row)
    big?(row[0]) ? 28 : @rh
  end

  # the first row past the screen when it starts at row s
  def rows_fit(s)
    y = @top + 4
    i = s
    while i < @rows.length && y + row_h(@rows[i]) <= @bot
      y += row_h(@rows[i])
      i += 1
    end
    i
  end

  def draw_row(row, y)
    row_kind = row[0]
    x = 4 + indent(row_kind)
    if row_kind == :heading_1
      if @wide
        Widget.big_text(@sp, x, y + 2, plain(row[1]), @c_em)
        return
      end
      @sp.fill_rect(0, y - 1, @w, @rh, @c_box)
    elsif row_kind == :code
      @sp.fill_rect(0, y - 1, @w, @rh, @c_box)
      t(x, y + 1, clip(row[1][0][1], @w - 8), @c_em)
      return
    elsif row_kind == :list && row[2]
      t(4, y + 1, "-", @c_em)
    end
    draw_segments(row[1], x, y + 1, row_kind)
  end

  def plain(segments)
    s = ""
    segments.each { |seg| s += seg[1] }
    s
  end

  def draw_segments(row_segments, screen_x, screen_y, row_kind)
    c = @c_text
    c = @c_em if row_kind == :heading_1 || row_kind == :heading_2
    segment_index = 0
    while segment_index < row_segments.length && screen_x < @w
      segment_kind = row_segments[segment_index][0]
      segment_text = row_segments[segment_index][1]
      segment_width = Widget.text_width(@sp, segment_text)
      if segment_kind == :inline_code
        @sp.fill_rect(screen_x, screen_y - 1, segment_width, @rh - 3, @c_box)
        t(screen_x, screen_y, segment_text, @c_em)
      else
        t(screen_x, screen_y, segment_text, c)
      end
      screen_x += segment_width
      segment_index += 1
    end
  end
end
