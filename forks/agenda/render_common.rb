class Agenda
  def render_screen
    return if render_ui
    if @screen == :time
      render_time
    elsif @screen == :day
      render_day
    elsif @screen == :list
      render_list
    else
      render_month
    end
  end

  # "09:00  Dentist", the time in the emphasis colour
  def event_row(x, y, w, ev, selected)
    @sp.fill_rect(x, y - 1, w, @lh, @c_box) if selected
    t(x + 3, y, ev[0], @c_em)
    t(x + 3 + 6 * @cw, y, clip(ev[1], w - 6 - 6 * @cw), selected ? @c_sel : @c_text)
  end

  def first_row(sel, rows)
    top = sel - rows + 1
    top < 0 ? 0 : top
  end

  def nothing(y, what)
    t(8, y, what, @c_text)
    t(8, y + @lh, "n adds an event.", @c_em)
  end

  def event_count(day)
    list = @events[format_date(@year, @month, day)]
    list.is_a?(Array) ? list.length : 0
  end
end
