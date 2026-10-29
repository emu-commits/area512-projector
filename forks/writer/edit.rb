class Writer
  # ---- typing

  # a byte from the keyboard: UTF-8 from the IME comes one byte per key, so a character
  # goes in once all its bytes have
  def type_byte(k)
    b = k.getbyte(0)
    if b < 0x80
      @utf = ""
      insert_text(k)
    elsif b >= 0xc0
      @utf = k
    elsif @utf != ""
      @utf = @utf + k
      if @utf.length >= step(@utf, 0)
        insert_text(@utf)
        @utf = ""
      end
    end
  end

  def insert_text(text)
    return if full(text.length, 0)
    splice(@row, @col, 0, text)
    @col += text.length
    @goal = nil
  end

  def insert_newline
    return if full(1, 1)
    s = cur_line
    rest = part(s, @col, s.length - @col)
    splice(@row, @col, rest.length, "")
    insert_line(@row + 1, rest)
    @row += 1
    @col = 0
    @goal = nil
  end

  # past DOC_BYTES or DOC_MAX the VM could run out (const.rb)
  def full(bytes, lines)
    return false if @bytes + bytes <= DOC_BYTES && room + bytes + LINE_COST * lines <= DOC_MAX
    @msg = "Full: Writer takes no more. Start another."
    true
  end

  def backspace
    s = cur_line
    if @col > 0
      b = back(s, @col)
      splice(@row, b, @col - b, "")
      @col = b
    elsif @row > 0
      plen = line(@row - 1).length
      splice(@row - 1, plen, 0, s)
      delete_line(@row)
      @row -= 1
      @col = plen
    end
    @goal = nil
  end

  # ---- moving: by character, by row on screen, by word, page, row end, document end

  def move_left
    if @col > 0
      @col = back(cur_line, @col)
    elsif @row > 0
      @row -= 1
      @col = cur_line.length
    end
    @goal = nil
  end

  def move_right
    if @col < cur_line.length
      @col += step(cur_line, @col)
    elsif @row < @lines.length - 1
      @row += 1
      @col = 0
    end
    @goal = nil
  end

  # up or down a row as drawn (a long paragraph is several), keeping to the same x
  def move_row(d)
    s = cur_line
    ss = segs(cur_line)
    k = seg_of(ss, @col)
    @goal = width(s, ss[k], @col) if @goal.nil?
    if d < 0
      if k > 0
        k -= 1
      elsif @row > 0
        @row -= 1
        s = cur_line
        ss = segs(cur_line)
        k = ss.length - 1
      else
        @col = 0
        return
      end
    else
      if k < ss.length - 1
        k += 1
      elsif @row < @lines.length - 1
        @row += 1
        s = cur_line
        ss = segs(cur_line)
        k = 0
      else
        @col = s.length
        return
      end
    end
    @col = col_at(s, ss, k, @goal)
  end

  def page(d)
    n = visible_rows - 1
    n = 1 if n < 1
    while n > 0
      move_row(d)
      n -= 1
    end
  end

  def space_at?(s, i)
    b = s.getbyte(i)
    b == 32 || b == 9
  end

  # to the start of the next word, on to the next line at the end of one
  def word_right
    s = cur_line
    if @col >= s.length
      move_right
      return
    end
    i = @col
    i += step(s, i) while i < s.length && !space_at?(s, i)
    i += 1 while i < s.length && space_at?(s, i)
    @col = i
    @goal = nil
  end

  # to the start of this word, or the one before
  def word_left
    if @col == 0
      move_left
      return
    end
    s = cur_line
    i = @col
    i = back(s, i) while i > 0 && space_at?(s, back(s, i))
    i = back(s, i) while i > 0 && !space_at?(s, back(s, i))
    @col = i
    @goal = nil
  end

  # the start of the row on screen; at it already, the start of the paragraph
  def row_start
    ss = segs(cur_line)
    a = ss[seg_of(ss, @col)]
    @col = @col == a ? 0 : a
    @goal = nil
  end

  def row_end
    s = cur_line
    ss = segs(cur_line)
    k = seg_of(ss, @col)
    e = seg_end(s, ss, k)
    e = back(s, e) if k + 1 < ss.length
    @col = @col == e ? s.length : e
    @goal = nil
  end

  def doc_start
    @row = 0
    @col = 0
    @goal = nil
  end

  def doc_end
    @row = @lines.length - 1
    @col = cur_line.length
    @goal = nil
  end

  # ---- find: from the cursor on, then from the top; case doesn't matter

  def find
    s = ask_text("FIND", "Find what?", @find, FIND_MAX)
    return if s.nil? || s == ""
    @find = s
    find_from(@row, @col)
  end

  def find_next
    if @find == ""
      find
    else
      find_from(@row, @col + 1)
    end
  end

  def find_from(r0, c0)
    want = @find.downcase
    n = @lines.length
    i = 0
    found = nil
    while i <= n && found.nil?
      r = (r0 + i) % n
      from = i == 0 ? c0 : 0
      s = line(r)
      if from <= s.length
        c = find_in(s, want, from)
        c = nil if c && i == n && c >= c0      # past where it began: once round is enough
        found = [r, c] if c
      end
      i += 1
    end
    if found
      @msg = "From the top: " + @find if found[0] < r0 || (found[0] == r0 && found[1] < c0)
      @row = found[0]
      @col = found[1]
      @goal = nil
      @hit = [@row, @col, want.length]
    else
      @msg = "Not found: " + @find
    end
  end

  # where want (lowercase) is in s from byte i on, case not minded, or nil. Not in a lowercased
  # copy of s: of a 10 KB paragraph, that copy ran the VM out (the Cardputer build, the second
  # find after a save). index finds each place the first letter is, either case.
  def find_in(s, want, i)
    a = want[0, 1]
    b = a.upcase
    n = want.length
    while i + n <= s.length
      p = s.index(a, i)
      q = a == b ? nil : s.index(b, i)
      p = q if p.nil? || (q && q < p)
      return nil if p.nil? || p + n > s.length
      return p if same_ci?(s, p, want)
      i = p + 1
    end
    nil
  end

  def same_ci?(s, p, want)
    j = 0
    while j < want.length
      c = s.getbyte(p + j)
      c += 32 if c >= 65 && c <= 90
      return false if c != want.getbyte(j)
      j += 1
    end
    true
  end
end
