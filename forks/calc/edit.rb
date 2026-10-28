class Calc
  # Typing into a cell, on the grid (upstream read it through the console): typed at the
  # end, Backspace deletes, Enter puts it in and goes down, Fn+arrow puts it in and goes
  # that way, Esc leaves the cell as it was. The whole text is in the bar above the grid.

  def start_edit(text)
    @edit = text
    @msg = ""
  end

  def edit_key(k)
    if k == "ENTER"
      commit_edit(0, 1)
    elsif k == "ESC"
      @edit = nil
    elsif k == "UP"
      commit_edit(0, -1)
    elsif k == "DOWN"
      commit_edit(0, 1)
    elsif k == "LEFT"
      commit_edit(-1, 0)
    elsif k == "RIGHT"
      commit_edit(1, 0)
    elsif k == "BS"
      @edit = drop_char(@edit)
    elsif k.length == 1 && k.getbyte(0) >= 32 && k.getbyte(0) != 127
      if @edit.length < TEXT_MAX
        @edit += k     # bytes of 128 and up: UTF-8 from the keyboard's IME, kept as typed
      else
        @msg = "A cell holds " + TEXT_MAX.to_s + " characters"
      end
    end
  end

  def commit_edit(dc, dr)
    s = @edit.tr("\t", " ").strip
    @edit = nil
    if s != cell_at(@col, @row)
      begin_change
      set_cell(@col, @row, s)
      end_change
      return if @full
    end
    move(dc, dr)
  end

  # ---- copy, paste, fill, clear

  def copy_cell
    @clip = [cell_at(@col, @row), @col, @row]
    @msg = "Copied " + selected_name + ": v pastes"
  end

  def paste
    if @clip.nil?
      @msg = "Nothing copied: c copies a cell"
      return
    end
    put(@clip[0], @col - @clip[1], @row - @clip[2], @col, @row)
  end

  # d: this cell into the one below, and go there (again and again fills a column)
  def fill(dc, dr)
    c = @col + dc
    r = @row + dr
    if c >= COLS || r >= ROWS
      @msg = "That's the edge of the sheet"
      return
    end
    put(cell_at(@col, @row), dc, dr, c, r)
    move(dc, dr) unless @full || @bad
  end

  # text copied dc, dr away to (c, r): a formula's references move with it
  def put(text, dc, dr, c, r)
    @bad = false
    if text.length > 0 && text.getbyte(0) == 61
      text = shift_refs(text, dc, dr)
      if text.nil?
        @bad = true
        @msg = "Its references would go off the sheet"
        return
      end
    end
    begin_change
    set_cell(c, r, text)
    end_change
  end

  def clear_cell
    return if cell_at(@col, @row) == ""
    begin_change
    set_cell(@col, @row, "")
    end_change
    @msg = selected_name + " cleared: u undoes"
  end

  # ---- go to, find

  def go_to
    s = ask_text("GO TO", "Which cell? (A1 to " + cell_name(COLS - 1, ROWS - 1) + ")", "", 4)
    return if s.nil? || s == ""
    p = parse_name(s)
    if p
      go(p[0], p[1])
    else
      @msg = "No cell " + s
    end
  end

  # f: the next cell after this one, along the rows, whose text has it (case not minded)
  def find
    s = ask_text("FIND", "Find which text?", @find, FIND_MAX)
    return if s.nil? || s == ""
    @find = s
    want = s.downcase
    start = @row * COLS + @col
    hit = nil
    r = 0
    while r < ROWS
      if @rows[r] && @rows[r].downcase.include?(want)
        p = @rows[r].split("\t")
        c = 0
        while c < p.length
          k = r * COLS + c
          if p[c].downcase.include?(want)
            d = (k - start - 1 + ROWS * COLS) % (ROWS * COLS)
            hit = [d, k] if hit.nil? || d < hit[0]
          end
          c += 1
        end
      end
      r += 1
    end
    if hit
      go(hit[1] % COLS, hit[1] / COLS)
      @msg = "Found in " + selected_name + ": f, Enter for the next"
    else
      @msg = "No cell has " + s
    end
  end
end
