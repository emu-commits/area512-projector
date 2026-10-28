class Agenda
  def initialize
    ui_init
    @app_dir = ""
    @year = 2026
    @month = 6
    @day = 21
    @screen = :month
    @events = {}
    @cur = 0             # the selected event: in the day, or in the agenda list
    @rows = []           # the agenda list: [date key, index in that day]
    @dirty = false       # events changed since the last save
    @moved = false       # the date changed: "today" is the last date used
    @last_time = "09:00"
    @quit = false
  end

  def day_events
    list = @events[date_key]
    list.is_a?(Array) ? list : []
  end

  def clamp_cursor(n)
    @cur = n - 1 if @cur >= n
    @cur = 0 if @cur < 0
  end

  # the agenda list: every event from the selected day on, at most 100
  def refresh_rows
    @rows = upcoming(date_key, 100)
    clamp_cursor(@rows.length)
  end

  # [[date key, index], ...] from the date key on, in order
  def upcoming(from, max)
    out = []
    keys = @events.keys.sort
    i = 0
    while i < keys.length && out.length < max
      k = keys[i]
      if (k <=> from) >= 0
        j = 0
        while j < @events[k].length && out.length < max
          out.push([k, j])
          j += 1
        end
      end
      i += 1
    end
    out
  end

  def event_at(row)
    @events[row[0]][row[1]]
  end
end
