class Writer
  # Documents are /data/writer/<name>.txt, plain lines; the list, recent.txt and Home's
  # requests are lib/ruby/docs.rb.

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
