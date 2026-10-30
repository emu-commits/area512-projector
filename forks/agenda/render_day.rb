class Agenda
  def render_day
    frame("AGENDA", day_title(date_key) + " " + @year.to_s)
    list = day_events
    if list.empty?
      nothing(@top + 8, "Nothing on this day.")
    else
      rows = (@bot - @top - 6) / @lh
      top = first_row(@cur, rows)
      i = top
      y = @top + 4
      while i < list.length && i < top + rows
        event_row(2, y, @w - 4, list[i], i == @cur)
        y += @lh
        i += 1
      end
    end
    if list.empty?
      foot(DAY_NONE, DAY_NAV0)
    else
      foot(DAY_KEYS, DAY_NAV)
    end
  end
end
