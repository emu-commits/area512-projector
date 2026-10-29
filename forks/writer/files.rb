class Writer
  # Documents are /data/writer/<name>.txt, plain lines; the list, recent.txt and Home's
  # requests are lib/ruby/docs.rb.

  def open_doc(name)
    text = read_file(path_of(name))
    if text.nil?
      @msg = "Can't open " + name
      return false
    end
    pc = share(text.length, room_of(text))
    if pc > 100
      @msg = name + " is too big: " + pc.to_s + "% of the most"
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
    drop_rows                        # the room for the text; laid out again after
    SD.write(path_of(@name), file_text)
    @dirty = false
    @msg = "Saved " + @name
    true
  rescue
    @msg = "Save failed: NOT saved"
    false
  end

  # The file: every line and its newline, made at its size (@bytes) and filled in place, one
  # piece the whole time. join grew it a line at a time, and each growth past a 10 KB line
  # could hold the old piece and the new one: it ran the TERM512 build out, saving a 10 KB
  # paragraph split in two.
  def file_text
    data = "\n" * @bytes
    at = 0
    @lines.each do |l|
      data[at, l.length] = l if l.length > 0
      at += l.length + 1
    end
    data
  end

  # Tab v: this document in Slide, on the page the cursor is in ("---" lines between pages).
  # Saved first, as any switch; Esc in Slide comes back here (place.txt).
  def show_slides
    sl = nil
    reg_read.each { |p| sl = p[2] if p[1] == "Slide" }
    if sl.nil?
      @msg = "Slide isn't installed"
      return
    end
    return if @dirty && !save_doc
    SD.write(OPEN_FILE, "slide|show|" + @name + ".txt:" + @row.to_s + "\n")
    switch_to(sl)
  rescue
    @msg = "Can't hand over to Slide"
  end

  # where you were, when you switch away
  def write_place
    s = "screen: " + @screen.to_s + "\nsel: " + @sel.to_s + "\n"
    if @name
      s += "file: " + @name + ".txt\nrow: " + @row.to_s + "\ncol: " + @col.to_s + "\nmode: " + @mode.to_s + "\n"
    end
    SD.write(place_file, s)
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
