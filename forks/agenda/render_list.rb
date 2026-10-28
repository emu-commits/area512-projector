class Agenda
  # The agenda: every event from the selected day on, in one list (the Psion Agenda's day
  # and week views in one). A date is shown on its first event only.
  def render_list
    frame("AGENDA", "from " + day_title(date_key))
    if @rows.empty?
      nothing(@top + 8, "Nothing from this day on.")
    else
      rows = (@bot - @top - 6) / @lh
      top = first_row(@cur, rows)
      dx = 10 * @cw
      i = top
      y = @top + 4
      while i < @rows.length && i < top + rows
        row = @rows[i]
        sel = i == @cur
        @sp.fill_rect(2, y - 1, @w - 4, @lh, @c_box) if sel
        t(5, y, day_title(row[0]), @c_text) if i == top || @rows[i - 1][0] != row[0]
        event_row(dx, y, @w - dx - 2, event_at(row), sel)
        y += @lh
        i += 1
      end
    end
    foot(LIST_KEYS)
  end
end
