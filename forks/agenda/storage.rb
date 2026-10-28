class Agenda
  # The file: "CURSOR\t<date>" (the last date used: there's no clock), then one line per
  # event, "<date>\t<HH:MM>\t<text>", as Scheduler wrote it. False (and a message) if the
  # save failed: a switch then stops, and nothing is lost.
  def save_data
    data = "CURSOR\t" + date_key + "\n"
    @events.keys.sort.each do |key|
      @events[key].each do |event|
        data += key + "\t" + event[0] + "\t" + event[1] + "\n"
      end
    end
    SD.write(SAVE_FILE, data)
    write_recent
    @dirty = false
    @moved = false
    @msg = "Saved"
    true
  rescue
    @msg = "Save failed: NOT saved"
    false
  end

  # For Home (docs/APPS_FORMAT.md): the next 8 events from the last date used,
  # "<title>|<date>#<index in that day>". The time goes last: Home's columns are narrow.
  def write_recent
    data = ""
    upcoming(date_key, 8).each do |row|
      ev = event_at(row)
      d = parse_key(row[0])
      m = MONTHS[d[1] - 1]
      title = d[2].to_s + " " + m[0, 1] + m[1, 2].downcase + " " + ev[1] + " " + ev[0]
      data += title + "|" + row[0] + "#" + row[1].to_s + "\n"
    end
    SD.write(RECENT_FILE, data)
  end

  def load_data
    ensure_dir("/data")
    ensure_dir(DATA_DIR)
    text = read_file(SAVE_FILE)
    old = text.nil?
    text = read_file(OLD_FILE) if old
    return unless text
    text.split("\n").each { |line| load_line(line.chomp) }
    sort_events
    if old
      @msg = "Scheduler's events copied" if save_data
    end
  rescue
    @msg = "Open failed"
  end

  def load_line(line)
    parts = line.split("\t", 3)
    if parts[0] == "CURSOR" && parts.length >= 2
      set_date(parts[1])
    elsif parts.length == 3
      list = @events[parts[0]]
      list = [] unless list.is_a?(Array)
      list.push([parts[1], parts[2]])
      @events[parts[0]] = list
    end
  end

  def set_date(text)
    parts = text.split("-")
    return unless parts.length == 3
    y = parts[0].to_i
    m = parts[1].to_i
    d = parts[2].to_i
    return if y < 1 || m < 1 || m > 12
    return if d < 1 || d > days_in_month(y, m)
    @year, @month, @day = y, m, d
  end

  def sort_events
    @events.each do |_key, list|
      list.sort! { |a, b| a[0] <=> b[0] }
    end
  end

  # where you were, when you switch away (docs/APPS_FORMAT.md)
  def write_place
    SD.write(PLACE_FILE, "screen: " + @screen.to_s + "\nsel: " + @cur.to_s + "\nfile: " + date_key + "\n")
  end

  def read_place(f)
    set_date(f["file"]) if f["file"]
    s = f["screen"]
    @screen = :day if s == "day"
    @screen = :list if s == "list"
    @cur = f["sel"].to_i if f["sel"]
  end
end
