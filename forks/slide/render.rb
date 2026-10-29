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
    if more_above? || last < @rows.length
      at = scroll_place
      Widget.scrollbar(@sp, @w - 5, @top + 3, @bot - @top - 6, at[0], last - @scroll, at[1])
    end
    foot(SHOW_KEYS)
  end

  def row_h(row)
    big?(row_kind(row)) ? 28 : @rh
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
    kind = row_kind(row)
    x = 4 + indent(kind)
    if kind == "1"
      if @wide
        Widget.big_text(@sp, x, y + 2, plain(row), @c_em)
        return
      end
      @sp.fill_rect(0, y - 1, @w, @rh, @c_box)
    elsif kind == "c"
      @sp.fill_rect(0, y - 1, @w, @rh, @c_box)
      t(x, y + 1, clip(row[2, row.length - 2], @w - 8), @c_em)
      return
    elsif kind == "-" && first_row?(row)
      t(4, y + 1, "-", @c_em)
    end
    draw_segments(row, x, y + 1, kind)
  end

  # the row's text without its `
  def plain(row)
    s = ""
    a = 2
    i = 2
    while i <= row.length
      if i == row.length || row.getbyte(i) == 96
        s += row[a, i - a] if i > a
        a = i + 1
      end
      i += 1
    end
    s
  end

  # the row's text a piece at a time, `inline code` on a box
  def draw_segments(row, screen_x, screen_y, kind)
    c = @c_text
    c = @c_em if kind == "1" || kind == "2"
    code = inline_at_start?(row)
    a = 2
    i = 2
    while i <= row.length && screen_x < @w
      if i == row.length || row.getbyte(i) == 96
        if i > a
          piece = row[a, i - a]
          piece_w = Widget.text_width(@sp, piece)
          if code
            @sp.fill_rect(screen_x, screen_y - 1, piece_w, @rh - 3, @c_box)
            t(screen_x, screen_y, piece, @c_em)
          else
            t(screen_x, screen_y, piece, c)
          end
          screen_x += piece_w
        end
        code = !code
        a = i + 1
      end
      i += 1
    end
  end
end
