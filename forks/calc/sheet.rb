class Calc
  # The sheet is kept as one String a row, its cells between tabs: a String for each cell
  # cost too much of the VM's 120 KB, and a Hash or Array that grows reallocates itself 6
  # slots at a time and fragments it (both ran out on the firmware, PLAN_V1 4.3).
  #   @rows[r]  nil, or "Rent<Tab>500<Tab><Tab>=B1*2": the texts typed, A first
  #   @vals[r]  nil, or an Array as long as that row's cells: each one's Float, or nil for
  #             text, empty and #ERR. Made whole by recalc (eval.rb), never grown.
  #   @widths   col => characters, only columns not WIDTH wide
  # A cell is also named by one Integer, k = row * COLS + col (undo, references).

  def init_doc
    @rows = Array.new(ROWS)
    @vals = Array.new(ROWS)
    @count = 0
    @bytes = 0        # the rows' lengths, tabs in: with 4 a cell (name, newline), the file's size
    @widths = {}
    @calc = false     # @vals is out of date
    @dirty = false
    @row = 0
    @col = 0
    @top_r = 0
    @left = 0
    @edit = nil       # the text being typed into the cell, or nil
    @undo = nil       # [[key, text], ...]: the cells before the last change
  end

  def cell_name(c, r)
    (65 + c).chr + (r + 1).to_s
  end

  def selected_name
    cell_name(@col, @row)
  end

  # the text typed in a cell, "" if none: the c-th field of the row
  def cell_at(c, r)
    s = @rows[r]
    return "" if s.nil?
    i = 0
    while c > 0
      j = s.index("\t", i)
      return "" if j.nil?
      i = j + 1
      c -= 1
    end
    j = s.index("\t", i)
    j = s.length if j.nil?
    s[i, j - i]
  end

  # a cell's number, or nil (text, empty, #ERR)
  def value(c, r)
    a = @vals[r]
    a && c < a.length ? a[c] : nil
  end

  # every change to a cell goes through here, so undo can put it back
  def set_cell(c, r, text)
    return if r < 0 || r >= ROWS || c < 0 || c >= COLS
    old = cell_at(c, r)
    return if old == text
    grow = text.length - old.length
    if (text.length > 0 && old == "" && @count >= CELL_MAX) ||
       (grow > 0 && @bytes + @count * 4 + grow > SHEET_MAX)
      @full = true
      return
    end
    @undo_now.push([r * COLS + c, old]) if @undo_now
    put_raw(c, r, text)
    @calc = false
    @dirty = true
  end

  # the row rebuilt with text in column c (no tab in text: typing and reading take them out)
  def put_raw(c, r, text)
    p = @rows[r] ? @rows[r].split("\t") : []
    p.push("") while p.length <= c
    @count += 1 if p[c] == "" && text != ""
    @count -= 1 if p[c] != "" && text == ""
    p[c] = text
    p.pop while p.length > 0 && p[p.length - 1] == ""
    @bytes -= @rows[r].length if @rows[r]
    @rows[r] = p.length > 0 ? p.join("\t") : nil
    @bytes += @rows[r].length if @rows[r]
  end

  # a change of one or more cells, undone with u as one
  def begin_change
    @undo_now = []
    @full = false
  end

  def end_change
    @undo = @undo_now if @undo_now.length > 0
    @undo_now = nil
    @msg = "Full: " + CELL_MAX.to_s + " cells or " + (SHEET_MAX / 1024).to_s + " KB is the most. Start another sheet." if @full
  end

  # u: the cells as they were; u again puts the change back
  def undo
    if @undo.nil?
      @msg = "Nothing to undo"
      return
    end
    was = @undo
    begin_change
    i = was.length - 1
    while i >= 0
      k = was[i][0]
      set_cell(k % COLS, k / COLS, was[i][1])
      i -= 1
    end
    end_change
    k = was[0][0]
    go(k % COLS, k / COLS)
    @msg = "Undone (u again to redo)"
  end

  # "B12" (or "b12", "$B$12") as [col, row], or nil
  def parse_name(s)
    s = s.strip.tr("$", "")
    return nil if s.length < 2
    c = s.getbyte(0)
    c -= 32 if c >= 97 && c <= 122
    return nil if c < 65 || c > 64 + COLS
    i = 1
    while i < s.length
      d = s.getbyte(i)
      return nil if d < 48 || d > 57
      i += 1
    end
    r = s[1, s.length - 1].to_i
    return nil if r < 1 || r > ROWS
    [c - 65, r - 1]
  end

  # ---- columns and moving

  def col_chars(c)
    w = @widths[c]
    w ? w : WIDTH
  end

  def col_px(c)
    col_chars(c) * @cw + 6
  end

  # w: the next width for this column, round from the widest to the narrowest
  def step_width
    w = col_chars(@col)
    i = WIDTHS.index(w)
    n = WIDTHS[i.nil? || i + 1 >= WIDTHS.length ? 0 : i + 1]
    if n == WIDTH
      @widths.delete(@col)
    else
      @widths[@col] = n
    end
    @dirty = true
    adjust_scroll
    @msg = "Column " + (65 + @col).chr + ": " + n.to_s + " wide"
  end

  def move(dc, dr)
    go(@col + dc, @row + dr)
  end

  def go(c, r)
    c = 0 if c < 0
    r = 0 if r < 0
    c = COLS - 1 if c >= COLS
    r = ROWS - 1 if r >= ROWS
    @col = c
    @row = r
    adjust_scroll
  end

  # ]: the bottom right of what's filled in
  def go_end
    mc = 0
    mr = 0
    r = 0
    while r < ROWS
      if @rows[r]
        mr = r
        n = @rows[r].split("\t").length - 1
        mc = n if n > mc
      end
      r += 1
    end
    go(mc, mr)
  end

  def grid_y
    @top + fbar_lines * @lh + 3
  end

  def visible_rows
    n = (@bot - grid_y - ROW_H) / ROW_H
    n < 1 ? 1 : n
  end

  # the selected cell whole on the screen; the columns before it as far as they fit
  def adjust_scroll
    @left = @col if @col < @left
    @top_r = @row if @row < @top_r
    rows = visible_rows
    @top_r = @row - rows + 1 if @row >= @top_r + rows
    while @left < @col && HEAD_W + cols_px(@left, @col) > @w
      @left += 1
    end
  end

  # the width of columns a to b, both in
  def cols_px(a, b)
    x = 0
    while a <= b
      x += col_px(a)
      a += 1
    end
    x
  end
end
