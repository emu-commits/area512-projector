class Agenda
  # The month. On TERM512 the selected day's events are beside it and what's coming up after
  # it below: the month and the day side by side (PLAN_V1, Agenda 4).
  def render_month
    frame("AGENDA", MONTHS[@month - 1] + " " + @year.to_s)
    cw = @wide ? 26 : 34
    rh = @wide ? 18 : 14
    y0 = @top + (@wide ? 16 : 15)
    col = 0
    while col < 7
      t(col * cw + 4, @top + 2, WDAYS[col], col == 0 ? @c_em : @c_text)     # over the numbers
      col += 1
    end
    first = weekday(@year, @month, 1)
    max = days_in_month(@year, @month)
    day = 1
    while day <= max
      cell = first + day - 1
      x = (cell % 7) * cw
      y = y0 + (cell / 7) * rh
      selected = day == @day
      if selected
        @sp.fill_rect(x + 1, y - 1, cw - 3, rh - 1, @c_box)
        @sp.rect(x + 1, y - 1, cw - 3, rh - 1, @c_sel)
      end
      color = selected ? @c_sel : @c_text
      color = @c_em if col_sunday?(day) && !selected
      t(x + 4, y + (rh - 14) / 2, day.to_s, color)
      @sp.fill_circle(x + cw - 7, y + rh / 2 - 2, 2, @c_em) if event_count(day) > 0
      day += 1
    end
    if @wide
      month_day(7 * cw + 6, @w - 7 * cw - 8)
      month_next(y0 + 6 * rh + 4, 7 * cw)
    end
    foot(MONTH_KEYS, MONTH_NAV)
  end

  def col_sunday?(day)
    weekday(@year, @month, day) == 0
  end

  def month_day(x, w)
    @sp.line(x - 3, @top + 2, x - 3, @bot - 2, @c_border)
    t(x + 3, @top + 3, day_title(date_key), @c_em)
    list = day_events
    if list.empty?
      t(x + 3, @top + 3 + @lh + 4, "Nothing on.", @c_dim)
      return
    end
    y = @top + 3 + @lh + 4
    i = 0
    while i < list.length && y <= @bot - @lh
      event_row(x, y, w, list[i], false)
      y += @lh
      i += 1
    end
  end

  def month_next(y, w)
    t(6, y, "COMING UP", @c_dim)
    y += @lh
    upcoming(next_key(date_key), (@bot - y) / @lh).each do |row|
      ev = event_at(row)
      d = parse_key(row[0])
      t(6, y, d[2].to_s + " " + MONTHS[d[1] - 1], @c_text)
      t(6 + 7 * @cw, y, ev[0], @c_em)
      t(6 + 13 * @cw, y, clip(ev[1], w - 6 - 13 * @cw), @c_text)
      y += @lh
    end
  end
end
