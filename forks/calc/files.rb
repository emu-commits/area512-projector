class Calc
  # A sheet is /data/calc/<name>.txt in upstream's format, one cell a line, "B3<Tab>text",
  # along the rows; then "WIDTH<Tab>B<Tab>14" for a column not 9 wide (upstream skips
  # those lines). The list, recent.txt and Home's requests are lib/ruby/docs.rb.

  def open_doc(name)
    text = read_file(path_of(name))
    if text.nil?
      @msg = "Can't open " + name
      return false
    end
    if text.length > SHEET_MAX
      @msg = name + " is " + (text.length / 1024 + 1).to_s + " KB: too big (" + (SHEET_MAX / 1024).to_s + " KB most)"
      return false
    end
    init_doc
    read_sheet(text)
    text = nil                       # the rows are made: the file's text can go first
    @name = name
    @screen = :doc
    @clip = nil
    touch_recent(name)
    @msg = "Opened " + name + ": " + @count.to_s + " cells" if @msg == ""
    @msg = "Not all of it fits: saving would lose cells" if @full
    true
  end

  # a line at a time from the text, not split into a String for each line first: the
  # lines and the cells at once didn't fit in the VM (measured on the firmware, PLAN_V1 4.3)
  def read_sheet(text)
    @full = false
    i = 0
    n = text.length
    while i < n
      j = text.index("\n", i)
      j = n if j.nil?
      read_line(text[i, j - i]) if j > i
      i = j + 1
    end
    @dirty = false
  end

  def read_line(line)
    p = line.split("\t")
    pos = p.length > 1 ? parse_name(p[0]) : nil
    if pos
      # a tab inside the text (upstream kept it) is a space here
      s = p[1]
      i = 2
      while i < p.length
        s += " " + p[i]
        i += 1
      end
      set_cell(pos[0], pos[1], s.strip)
    elsif p.length == 3 && p[0] == "WIDTH"
      c = p[1].getbyte(0) - 65
      @widths[c] = p[2].to_i if c >= 0 && c < COLS && WIDTHS.include?(p[2].to_i)
    end
  end

  # False (and a message) if the save failed: whatever was about to happen then stops.
  def save_doc
    return true if @name.nil?
    data = ""                        # one String grown in place: no array of lines to join
    r = 0
    while r < ROWS
      if @rows[r]
        p = @rows[r].split("\t")
        c = 0
        while c < p.length
          data << cell_name(c, r) << "\t" << p[c] << "\n" if p[c] != ""
          c += 1
        end
      end
      r += 1
    end
    c = 0
    while c < COLS
      data << "WIDTH\t" << (65 + c).chr << "\t" << @widths[c].to_s << "\n" if @widths[c]
      c += 1
    end
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
      s += "file: " + @name + ".txt\ncell: " + selected_name + "\n"
    end
    SD.write(place_file, s)
  end

  def read_place(f)
    @sel = f["sel"].to_i if f["sel"]
    refresh_docs
    file = f["file"]
    return unless f["screen"] == "doc" && file && file.length > 4
    return unless open_doc(file[0, file.length - 4])
    p = f["cell"] ? parse_name(f["cell"]) : nil
    go(p[0], p[1]) if p
    @msg = ""
  end

  # TERM512's list: what a formula can be
  def guide(x, y, w, h)
    guide_lines(x, y, GUIDE)
  end
end
