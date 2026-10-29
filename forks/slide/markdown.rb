class Slide
  # One page as rows on screen, each one String: its kind (a byte), its flags (a byte), then
  # its text. Kinds: "1" "2" "3" a heading, "-" a list item, "c" code, "p" a paragraph. Flags,
  # "0" to "3": 1 on the first row of a line (not a row a long line wrapped onto), 2 when the
  # row starts inside `inline code`. One object a row: rows as arrays of arrays of strings took
  # five, and two chunks of them going back up a 10 KB page ran the VM out.
  # Upstream drew each line as one row, cut off at the edge; here a line wraps after a space
  # (code doesn't: it's cut off).
  # text is a chunk of a page (storage.rb); code_block, whether it starts inside ``` lines.
  def layout_page(text, code_block)
    rows = []
    i = 0
    n = text.length
    while i < n
      j = text.index("\n", i) || n
      e = j
      e -= 1 if e > i && text.getbyte(e - 1) == 13
      source_line = text[i, e - i]
      i = j + 1
      if source_line.start_with?("```")
        code_block = !code_block       # upstream: only ```ruby opened a block
      elsif code_block
        rows.push("c1" + source_line)
      else
        layout_line(rows, source_line)
      end
    end
    rows
  end

  def layout_line(rows, source_line)
    kind = "p"
    row_text = source_line
    if source_line.start_with?("###")
      kind = "3"
      row_text = source_line[3, source_line.length - 3].lstrip
    elsif source_line.start_with?("##")
      kind = "2"
      row_text = source_line[2, source_line.length - 2].lstrip
    elsif source_line.start_with?("#")
      kind = "1"
      row_text = source_line[1, source_line.length - 1].lstrip
    elsif source_line.start_with?("- ") || source_line.start_with?("* ") || source_line == "-"
      kind = "-"
      row_text = source_line[1, source_line.length - 1].lstrip
    end
    cuts = wrap(row_text, @w - 12 - indent(kind), big?(kind))
    inline_code = false
    k = 0
    while k < cuts.length
      a = cuts[k]
      b = k + 1 < cuts.length ? cuts[k + 1] : row_text.length
      f = k == 0 ? 1 : 0
      f += 2 if inline_code
      rows.push(kind + FLAGS[f] + (row_text[a, b - a] || ""))
      # a ` turns inline code on and off, and it carries on to the next row
      while a < b
        inline_code = !inline_code if row_text.getbyte(a) == 96
        a += 1
      end
      k += 1
    end
  end

  def row_kind(row)
    row[0, 1]
  end

  def first_row?(row)
    (row.getbyte(1) - 48) & 1 == 1
  end

  def inline_at_start?(row)
    (row.getbyte(1) - 48) & 2 == 2
  end

  # ---- wrapping, by bytes: the firmware's strings are bytes, and what the keyboard's IME
  # types is UTF-8, twice as wide on screen

  # a title is 24 px on TERM512 (Widget.big_text)
  def big?(row_kind)
    @wide && row_kind == "1"
  end

  def indent(row_kind)
    return 12 if row_kind == "-"
    return 4 if row_kind == "2"
    return 8 if row_kind == "3"
    0
  end

  def glyph_w(s, i, big)
    w = s.getbyte(i) < 0x80 ? 6 : 12
    big ? w * 2 : w
  end

  def step(s, i)
    b = s.getbyte(i)
    return 1 if b < 0xc0
    return 2 if b < 0xe0
    return 3 if b < 0xf0
    4
  end

  # the byte offsets where each row of s starts: [0, ...]; a row breaks after its last space
  def wrap(s, width, big)
    out = [0]
    start = 0
    brk = 0
    x = 0
    i = 0
    while i < s.length
      b = s.getbyte(i)
      g = glyph_w(s, i, big)
      if b != 32 && x + g > width && i > start
        cut = brk > start ? brk : i
        out.push(cut)
        start = cut
        brk = 0
        x = 0
        k = cut
        while k < i
          x += glyph_w(s, k, big)
          k += step(s, k)
        end
      end
      brk = i + 1 if b == 32
      x += g
      i += step(s, i)
    end
    out
  end
end
