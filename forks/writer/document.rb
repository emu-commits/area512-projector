class Writer
  # The document: @lines, one String per paragraph, as bytes (the firmware's strings are
  # bytes; what the keyboard's IME types is UTF-8). @col is a byte offset into the line, always
  # on a character's first byte. Every change goes through splice, insert_line and
  # delete_line, which keep the word count.
  def init_doc
    @lines = [""]
    @row = 0
    @col = 0
    @scr = 0          # scrolled to: the first line drawn, and its wrapped row at the top
    @scr_seg = 0
    @goal = nil       # the x that up and down keep to, in pixels
    @words = 0
    @bytes = 1        # the file's size: every line and its newline
    @dirty = false
    @mode = :type
    @hit = nil        # [row, col, length] of what find found, until the next key
    @utf = ""         # a UTF-8 character still arriving, one byte per key
    @cc_row = -1
  end

  # The cursor's column in characters, for the status line: @cc_n at byte @cc_col of line
  # @cc_row, counted on from where it was. Counted from the line's start on every band, it
  # took 1.4 to 2.9 s a key at the end of a 10 KB paragraph on the device (PLAN_V1 4.3).
  # Nothing else is kept from key to key: rows kept and mended a row at a time were quicker,
  # but their code and their pieces left the VM's arena without room for a 10 KB save.

  def line(i)
    s = @lines[i]
    s.is_a?(String) ? s : ""
  end

  def cur_line
    line(@row)
  end

  # s[a, n] that's never nil
  def part(s, a, n)
    p = s[a, n]
    p.is_a?(String) ? p : ""
  end

  # line i's n bytes at pos become text, in place: built anew, a long paragraph was copied
  # three times a key, and 12 KB in one ran the VM out. Only the words around the change are
  # counted again.
  def splice(i, pos, n, text)
    s = @lines[i]
    a = pos
    a -= 1 while a > 0 && !space_at?(s, a - 1)
    b = pos + n
    b += 1 while b < s.length && !space_at?(s, b)
    w = words_in(s, a, b)
    if i == @cc_row && @cc_col >= pos + n
      @cc_n -= chars_in(s, pos, pos + n)
    end
    s[pos, n] = text
    d = text.length - n
    @words += words_in(s, a, b + d) - w
    if i == @cc_row
      if @cc_col >= pos + n
        @cc_n += chars_in(s, pos, pos + text.length)
        @cc_col += d
      elsif @cc_col > pos
        @cc_row = -1
      end
    end
    @bytes += d
    @dirty = true
  end

  # what the document takes against DOC_MAX (const.rb)
  def room
    @bytes + LINE_COST * @lines.length
  end

  # how much of the most a document of these bytes and room is, in percent, rounded up:
  # past 100 is too big
  def share(bytes, rm)
    a = (bytes * 100 + DOC_BYTES - 1) / DOC_BYTES
    b = (rm * 100 + DOC_MAX - 1) / DOC_MAX
    a > b ? a : b
  end

  # the same for a file not opened yet, without splitting it
  def room_of(text)
    n = 0
    i = 0
    while i < text.length
      j = text.index("\n", i)
      break if j.nil?
      n += 1
      i = j + 1
    end
    n += 1 if i < text.length || n == 0      # a last line with no newline, or an empty file
    text.length + LINE_COST * n
  end

  # mruby/c's Array has no insert
  def insert_line(pos, s)
    @lines.push("")
    i = @lines.length - 1
    while i > pos
      @lines[i] = @lines[i - 1]
      i -= 1
    end
    @lines[pos] = s
    @cc_row = -1
    @words += word_count(s)
    @bytes += s.length + 1
    @dirty = true
  end

  def delete_line(i)
    @words -= word_count(line(i))
    @bytes -= line(i).length + 1
    @lines.delete_at(i)
    @cc_row = -1
    @dirty = true
  end

  # The whole file, split. The text and its lines are both held while this runs, and no third
  # copy: a document's size counts twice against the VM's heap, where running out restarts
  # the device (mruby/c can't raise it).
  def set_text(text)
    @cc_row = -1
    @lines = text.split("\n")
    @lines.push("") if @lines.length == 0
    @words = 0
    @bytes = 0
    i = 0
    while i < @lines.length
      l = @lines[i]
      if l.length > 0 && l.getbyte(l.length - 1) == 13
        l = l[0, l.length - 1]      # a CRLF file
        @lines[i] = l
      end
      @words += word_count(l)
      @bytes += l.length + 1
      i += 1
    end
    @row = 0
    @col = 0
    @scr = 0
    @scr_seg = 0
    @goal = nil
    @dirty = false
  end

  def word_count(s)
    words_in(s, 0, s.length)
  end

  # the words starting in bytes a...b of s, a at the start of s or after a space
  def words_in(s, a, b)
    n = 0
    inword = false
    i = a
    while i < b
      c = s.getbyte(i)
      sp = c == 32 || c == 9
      n += 1 if !sp && !inword
      inword = !sp
      i += 1
    end
    n
  end

  # ---- UTF-8, by bytes

  def step(s, i)
    b = s.getbyte(i)
    return 1 unless b.is_a?(Integer)
    return 1 if b < 0xc0
    return 2 if b < 0xe0
    return 3 if b < 0xf0
    4
  end

  def back(s, i)
    i -= 1
    i -= 1 while i > 0 && s.getbyte(i) >= 0x80 && s.getbyte(i) < 0xc0
    i < 0 ? 0 : i
  end

  def glyph_w(s, i)
    s.getbyte(i) < 0x80 ? GLYPH_W : WIDE_W
  end

  def width(s, a, b)
    w = 0
    i = a
    while i < b
      w += glyph_w(s, i)
      i += step(s, i)
    end
    w
  end

  # the characters in bytes a...b of s
  def chars_in(s, a, b)
    n = 0
    i = a
    while i < b
      i += step(s, i)
      n += 1
    end
    n
  end

  # the cursor's column in characters, for the status line: counted from where it was last
  # time, not from the start of the line
  def col_chars
    if @cc_row != @row
      @cc_row = @row
      @cc_col = 0
      @cc_n = 0
    end
    if @col >= @cc_col
      @cc_n += chars_in(cur_line, @cc_col, @col)
    else
      @cc_n -= chars_in(cur_line, @col, @cc_col)
    end
    @cc_col = @col
    @cc_n
  end

  # ---- wrapping: a paragraph is drawn as rows of at most @wrap_w pixels, broken after a
  # space where there is one. Spaces at the end of a row hang past the edge.

  # the byte offsets where each row of s starts: [0, ...]; with max, no more than max + 1 of
  # them (the rest of a long paragraph isn't needed to fill the screen)
  def segs(s, max = 0)
    out = [0]
    a = next_row(s, 0)
    while a
      out.push(a)
      break if max > 0 && out.length > max
      a = next_row(s, a)
    end
    out
  end

  # where the row starting at byte a of s ends, which is where the next one starts; nil if
  # it runs to the end. One read of each byte (glyph_w and step each read it again).
  def next_row(s, a)
    brk = 0           # just after the last space in this row, 0 if none
    x = 0
    i = a
    n = s.length
    while i < n
      b = s.getbyte(i)
      if b < 0x80
        g = GLYPH_W
        st = 1
      else
        g = WIDE_W
        st = b < 0xc0 ? 1 : (b < 0xe0 ? 2 : (b < 0xf0 ? 3 : 4))
      end
      return brk > a ? brk : i if b != 32 && x + g > @wrap_w && i > a
      brk = i + 1 if b == 32
      x += g
      i += st
    end
    nil
  end

  def seg_of(ss, col)
    k = ss.length - 1
    k -= 1 while k > 0 && ss[k] > col
    k
  end

  def seg_end(s, ss, k)
    k + 1 < ss.length ? ss[k + 1] : s.length
  end

  # the byte in row k of s nearest to x pixels in
  def col_at(s, ss, k, x)
    i = ss[k]
    e = seg_end(s, ss, k)
    e = back(s, e) if k + 1 < ss.length     # the end of a row is the next row's start
    w = 0
    while i < e
      g = glyph_w(s, i)
      return i if w + g / 2 >= x
      w += g
      i += step(s, i)
    end
    e
  end

  def visible_rows
    n = (@bot - @top - PAGE_PAD * 2) / LINE_H
    n < 1 ? 1 : n
  end

  # Scroll so the cursor shows, then lay out the rows on screen once (the sprite draws in
  # bands, and render runs once a band): @view is [line, from, to] per row on screen, @cur_y
  # and @cur_x where the cursor is.
  def layout
    rows = visible_rows
    @scr = @lines.length - 1 if @scr >= @lines.length
    @scr = 0 if @scr < 0
    tn = segs(line(@scr)).length
    @scr_seg = tn - 1 if @scr_seg >= tn
    ss = segs(cur_line)
    k = seg_of(ss, @col)
    if @row < @scr || (@row == @scr && k < @scr_seg)
      @scr = @row
      @scr_seg = k
    elsif @row - @scr >= rows || rows_between(@scr, @scr_seg, @row, k, rows) > rows
      scroll_to_bottom(@row, k, rows)
    end
    @view = []
    @cur_y = -1
    r = @scr
    s0 = @scr_seg
    while @view.length < rows && r < @lines.length
      s = line(r)
      ss = segs(s, s0 + rows - @view.length)
      while s0 < ss.length && @view.length < rows
        e = seg_end(s, ss, s0)
        if r == @row && seg_of(ss, @col) == s0
          @cur_y = @view.length
          @cur_x = width(s, ss[s0], @col)
        end
        @view.push([r, ss[s0], e])
        s0 += 1
      end
      r += 1
      s0 = 0
    end
    col_chars                        # counted here once; the status line reads it each band
  end

  # rows on screen from (r0, k0) to (r1, k1), both counted; past max, any number past it
  def rows_between(r0, k0, r1, k1, max)
    n = 0
    r = r0
    k = k0
    while r < r1
      n += segs(line(r), k + max + 1).length - k
      return n if n > max
      k = 0
      r += 1
    end
    n + k1 - k + 1
  end

  # the cursor's row (r, k) on the last row of the screen
  def scroll_to_bottom(r, k, rows)
    left = rows - 1
    while left > 0
      if k >= left
        k -= left
        left = 0
      elsif r > 0
        left -= k + 1
        r -= 1
        k = segs(line(r)).length - 1
      else
        k = 0
        left = 0
      end
    end
    @scr = r
    @scr_seg = k
  end
end
