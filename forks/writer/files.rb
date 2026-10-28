class Writer
  # Documents are /data/writer/<name>.txt, plain lines. recent.txt and place.txt sit beside
  # them (docs/APPS_FORMAT.md), so those two names are Writer's own.

  def path_of(name)
    DATA_DIR + "/" + name + ".txt"
  end

  def own_name?(name)
    d = name.downcase
    d == "recent" || d == "place"
  end

  # The names on the card, the recent ones first (recent.txt's order), then A to Z
  def doc_names
    all = []
    begin
      d = Dir.new(DATA_DIR)
      while (f = d.read)
        n = f.length - 4
        all.push(f[0, n]) if n > 0 && f[n, 4] == ".txt" && !own_name?(f[0, n])
      end
      d.close
    rescue
      all = []
      @recent.each { |n| all.push(n) if File.exist?(path_of(n)) }
    end
    out = []
    @recent.each { |n| out.push(n) if all.include?(n) }
    rest = []
    all.each { |n| rest.push(n) unless out.include?(n) }
    rest.sort! { |a, b| a.downcase <=> b.downcase }
    rest.each { |n| out.push(n) }
    out
  end

  def refresh_docs
    @docs = doc_names
    @sel = @docs.length - 1 if @sel >= @docs.length
    @sel = 0 if @sel < 0
  end

  # the document name typed: letters, digits, space - _ ( ) and nothing a card can't name
  def clean_name(s)
    out = ""
    i = 0
    while i < s.length && out.length < NAME_MAX
      b = s.getbyte(i)
      ok = (b >= 48 && b <= 57) || (b >= 65 && b <= 90) || (b >= 97 && b <= 122)
      ok = true if b == 32 || b == 45 || b == 95 || b == 40 || b == 41
      out = out + s[i, 1] if ok
      i += 1
    end
    out.strip
  end

  # the name as it is on the card, if one differs only in case
  def existing(name)
    r = nil
    d = name.downcase
    doc_names.each { |n| r = n if n.downcase == d }
    r
  end

  # nil, or why the name can't be used (it's for a new name, or a rename of "except")
  def name_problem(name, except)
    return "A name needs a letter or a digit" if name == ""
    return "That name is Writer's own" if own_name?(name)
    e = existing(name)
    return "There's a document called " + e if e && e != except
    nil
  end

  # ---- one document

  def open_doc(name)
    text = read_file(path_of(name))
    if text.nil?
      @msg = "Can't open " + name
      return false
    end
    if text.length > DOC_MAX
      @msg = name + " is " + (text.length / 1024 + 1).to_s + " KB: too big (" + (DOC_MAX / 1024).to_s + " KB most)"
      return false
    end
    set_text(text)
    @name = name
    @screen = :doc
    @mode = :type
    @hit = nil
    touch_recent(name)
    true
  end

  # False (and a message) if the save failed: whatever was about to happen then stops.
  def save_doc
    return true if @name.nil?
    @lines.push("")                  # the last newline, without a copy of the whole text
    data = @lines.join("\n")
    @lines.pop
    SD.write(path_of(@name), data)
    @dirty = false
    @msg = "Saved " + @name
    true
  rescue
    @msg = "Save failed: NOT saved"
    false
  end

  # out of the document to the list, saving first
  def close_doc
    return false if @dirty && !save_doc
    @screen = :files
    refresh_docs
    i = @docs.index(@name)
    @sel = i if i
    @name = nil
    true
  end

  # a new document, named now: n, and Home's "new" request (arg: its name, or "" to ask)
  def new_doc(name)
    if name == ""
      s = ask_text("NEW DOCUMENT", "Its name?", "", NAME_MAX)
      return if s.nil?
      name = clean_name(s)
    else
      name = clean_name(name)
    end
    e = existing(name)
    why = e ? nil : name_problem(name, nil)
    if why
      @msg = why
      return
    end
    return if @name && !close_doc
    if e
      open_doc(e)        # one of that name is there already (Home's "new" for notes): open it
      return
    end
    init_doc
    @name = name
    @screen = :doc
    @msg = "New: " + name
    @msg = "Can't write " + name unless save_doc
    touch_recent(name)
  end

  def rename_doc(old)
    s = ask_text("RENAME", "New name for " + old + "?", old, NAME_MAX)
    return if s.nil?
    name = clean_name(s)
    return if name == old
    why = name_problem(name, old)
    if why
      @msg = why
      return
    end
    File.rename(path_of(old), path_of(name))
    @name = name if @name == old
    @recent.each_index { |i| @recent[i] = name if @recent[i] == old }
    write_recent
    refresh_docs
    i = @docs.index(name)
    @sel = i if i
    @msg = "Renamed " + name
  rescue
    @msg = "Rename failed"
  end

  # moved to deleted/, over an older one of the same name
  def delete_doc(name)
    ensure_dir(BIN_DIR)
    bin = BIN_DIR + "/" + name + ".txt"
    File.unlink(bin) if File.exist?(bin)
    File.rename(path_of(name), bin)
    @recent.delete_if { |n| n == name }
    write_recent
    refresh_docs
    @msg = "Deleted " + name + " (kept in deleted/)"
    true
  rescue
    @msg = "Delete failed"
    false
  end

  # ---- recent.txt: for Home, newest first, at most 8 (docs/APPS_FORMAT.md)

  def load_recent
    @recent = []
    text = read_file(RECENT_FILE)
    return unless text
    text.split("\n").each do |l|
      p = l.split("|")
      @recent.push(p[1][0, p[1].length - 4]) if p.length == 2 && p[1].length > 4
    end
  end

  def touch_recent(name)
    @recent.delete_if { |n| n == name }
    @recent.unshift(name)
    @recent.pop while @recent.length > 8
    write_recent
  end

  def write_recent
    data = ""
    @recent.each { |n| data += n + "|" + n + ".txt\n" }
    SD.write(RECENT_FILE, data)
  rescue
  end

  # ---- start-up

  # The folder, and the first time, Writer's one document from before the fork
  def load_data
    ensure_dir("/data")
    first = !Dir.exist?(DATA_DIR)
    ensure_dir(DATA_DIR)
    load_recent
    if first && File.exist?(OLD_FILE)
      text = read_file(OLD_FILE)
      if text
        SD.write(path_of("writer"), text)
        touch_recent("writer")
        @msg = "Your writer.txt is the document \"writer\""
      end
    end
    refresh_docs
  rescue
    @msg = "Can't read " + DATA_DIR
  end

  # where you were, when you switch away
  def write_place
    s = "screen: " + @screen.to_s + "\nsel: " + @sel.to_s + "\n"
    if @name
      s += "file: " + @name + ".txt\nrow: " + @row.to_s + "\ncol: " + @col.to_s + "\nmode: " + @mode.to_s + "\n"
    end
    SD.write(PLACE_FILE, s)
  end

  def read_place(f)
    @sel = f["sel"].to_i if f["sel"]
    refresh_docs
    file = f["file"]
    return unless f["screen"] == "doc" && file && file.length > 4
    return unless open_doc(file[0, file.length - 4])
    @row = f["row"].to_i
    @row = @lines.length - 1 if @row >= @lines.length
    @row = 0 if @row < 0
    @col = f["col"].to_i
    @col = cur_line.length if @col > cur_line.length
    @col = 0 if @col < 0
    @mode = :move if f["mode"] == "move"
  end
end
