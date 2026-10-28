class Agenda
  # Time as a field (PLAN_V1, Agenda 2): up and down step 15 minutes, digits type it
  # ("9" is 09:00, "930" 09:30, "1415" 14:15), Backspace deletes a digit. Enter OK, Esc nil.
  def ask_time(title, initial)
    mins = to_mins(initial)
    typed = ""
    was = @screen
    @screen = :time
    r = nil
    while true
      @q = [title, typed, mins]
      paint
      @msg = ""
      k = arrow(key)
      if k == "ENTER"
        m = typed == "" ? mins : typed_mins(typed)
        if m
          r = fmt_time(m)
          break
        end
        @msg = "Not a time: 00:00 to 23:59"
        typed = ""
      elsif k == "ESC"
        break
      elsif k == "UP" || k == "DOWN"
        m = typed_mins(typed)
        mins = m if m
        typed = ""
        mins = k == "UP" ? (mins / 15 + 1) * 15 : ((mins + 14) / 15 - 1) * 15
        mins = (mins + 1440) % 1440
      elsif k == "BS"
        typed = typed[0, typed.length - 1] if typed.length > 0
      elsif k.length == 1 && k.getbyte(0) >= 48 && k.getbyte(0) <= 57 && typed.length < 4
        typed = typed + k
      end
    end
    @screen = was
    r
  end

  def to_mins(hhmm)
    p = hhmm.split(":")
    return 540 if p.length != 2
    p[0].to_i * 60 + p[1].to_i
  end

  def fmt_time(m)
    h = m / 60
    mm = m % 60
    (h < 10 ? "0" : "") + h.to_s + ":" + (mm < 10 ? "0" : "") + mm.to_s
  end

  # what's been typed so far, in minutes, or nil if it isn't a time
  def typed_mins(s)
    return nil if s == ""
    h = s.to_i
    m = 0
    if s.length == 3
      h = s[0, 1].to_i
      m = s[1, 2].to_i
    elsif s.length == 4
      h = s[0, 2].to_i
      m = s[2, 2].to_i
    end
    return nil if h > 23 || m > 59
    h * 60 + m
  end

  def render_time
    frame(@q[0], "")
    t(6, @top + 4, "What time?", @c_em)
    y = @top + 4 + @lh + 4
    h = @lh + 8
    @sp.fill_rect(2, y, @w - 4, h, @c_box)
    @sp.rect(2, y, @w - 4, h, @c_border)
    # what's typed, read as a time as it goes: "9" 09:00, "93" --:--, "930" 09:30
    m = @q[1] == "" ? @q[2] : typed_mins(@q[1])
    t(8, y + 4, m ? fmt_time(m) : "--:--", @c_sel)
    t(60, y + 4, "typed " + @q[1], @c_dim) if @q[1] != ""
    t(6, y + h + 6, clip("Up/down: 15 min. Or type 930, 1415.", @w - 12), @c_dim)
    if @msg != ""
      Widget.footer(@sp, @msg)
    else
      Widget.hints(@sp, [[";.", "15 min"], ["0-9", "type"], ["ENT", "ok"]])
    end
  end

  # time, then text; nil if either is cancelled
  def ask_event(title, time, text)
    time = ask_time(title, time)
    return nil unless time
    text = ask_text(title, "At " + time + ": what?", text, TEXT_MAX)
    return nil if text.nil? || text == ""
    [time, text]
  end
end
