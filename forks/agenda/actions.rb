class Agenda
  def main_loop
    until @quit
      if @screen == :day
        clamp_cursor(day_events.length)
        day_key(cmd(DAY_KEYS))
      elsif @screen == :list
        refresh_rows
        list_key(cmd(LIST_KEYS))
      else
        month_key(cmd(MONTH_KEYS))
      end
    end
  end

  # keys every screen has; true if k was one of them
  def common_key(k)
    if k[0, 1] == "@"
      switch_to(k[1, k.length])    # Tab, then an app's digit
    elsif k == "s"
      save_data
    elsif k == "n"
      new_event
    else
      return false
    end
    true
  end

  def month_key(k)
    return if common_key(k)
    case k
    when "LEFT" then move_day(-1)
    when "RIGHT" then move_day(1)
    when "UP" then move_day(-7)
    when "DOWN" then move_day(7)
    when "[" then move_month(-1)
    when "]" then move_month(1)
    when "ENTER", " " then @screen = :day
    when "a" then open_list
    when "ESC", "q" then leave
    end
  end

  def day_key(k)
    return if common_key(k)
    case k
    when "LEFT" then move_day(-1)
    when "RIGHT" then move_day(1)
    when "UP" then @cur -= 1
    when "DOWN" then @cur += 1
    when "ENTER" then edit_event(date_key, @cur)
    when "x", "d" then delete_event(date_key, @cur)
    when "a" then open_list
    when "c", "ESC", "q" then @screen = :month
    end
  end

  def list_key(k)
    return if common_key(k)
    row = @rows[@cur]
    case k
    when "UP" then @cur -= 1
    when "DOWN" then @cur += 1
    when "ENTER"
      if row
        set_date(row[0])
        @cur = row[1]
        @moved = true
        @screen = :day
      end
    when "x", "d" then delete_event(row[0], row[1]) if row
    when "c", "ESC", "q" then @screen = :month
    end
  end

  def open_list
    @screen = :list
    @cur = 0
  end

  # ---- events

  def new_event
    ev = ask_event("NEW EVENT", @last_time, "")
    return unless ev
    add_event(date_key, ev)
    @msg = "Added " + ev[0]
  end

  def add_event(key, ev)
    list = @events[key]
    list = [] unless list.is_a?(Array)
    list.push(ev)
    list.sort! { |a, b| a[0] <=> b[0] }
    @events[key] = list
    i = list.length - 1
    while i >= 0
      @cur = i if list[i][0] == ev[0] && list[i][1] == ev[1] && @screen == :day
      i -= 1
    end
    @last_time = ev[0]
    @dirty = true
  end

  def edit_event(key, i)
    list = @events[key]
    return unless list.is_a?(Array) && i < list.length
    ev = ask_event("EDIT EVENT", list[i][0], list[i][1])
    return unless ev
    list.delete_at(i)
    add_event(key, ev)
    @msg = "Changed"
  end

  def delete_event(key, i)
    list = @events[key]
    return unless list.is_a?(Array) && i < list.length
    ev = list[i]
    return unless ask_yn("DELETE", "Delete " + ev[0] + " " + ev[1] + "?")
    remove_event(key, i)
    @msg = "Deleted"
  end

  def remove_event(key, i)
    @events[key].delete_at(i)
    @events.delete(key) if @events[key].length == 0
    @dirty = true
  end

  # ---- leaving and switching (docs/APPS_FORMAT.md)

  # Esc from the month: asks before it loses changes, keeps "today", goes to Home
  def leave
    if @dirty
      r = ask_yn("LEAVING", "Save your changes?")
      return if r.nil?
      return if r && !save_data
    elsif @moved
      save_data
    end
    h = home_path
    run_next(h) if h && h != @app_dir
    @quit = true
  end

  # Tab, then a digit: save, leave a place, hand off. A switch never loses work.
  def switch_to(path)
    return if (@dirty || @moved) && !save_data
    write_place
    @quit = true if run_next(path)
  end

  # Home's request (open.txt), else where you were (place.txt). Both are read once and
  # deleted, so neither is left to act on later.
  def start
    reg_read.each { |p| @app_dir = p[2] if p[1] == "Agenda" }
    req = take_request("agenda")
    place = take_place(PLACE_FILE)
    if req.nil?
      read_place(place) if place
      return
    end
    verb = req[0]
    if verb == "new"
      new_event
    elsif verb == "open" || verb == "delete"
      id = req[1].split("#")
      set_date(id[0]) if id.length == 2
      i = id.length == 2 ? id[1].to_i : 0
      if verb == "open"
        @screen = :day
        @cur = i
      else
        # Home asked first: delete it without asking again, save, and go back
        remove_event(id[0], i) if day_events.length > i
        save_data
        h = home_path
        @quit = true if h && run_next(h)
      end
    end
  end
end
