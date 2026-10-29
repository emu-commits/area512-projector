class Slide
  # One page as rows on screen: [kind, segments, first], where kind is :heading_1, :heading_2,
  # :heading_3, :list, :code or :paragraph, segments are [[:text or :inline_code, text], ...]
  # and first is false on a row a long line wrapped onto. Upstream drew each line as one row,
  # cut off at the edge; here a line wraps after a space (code doesn't: it's cut off).
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
        rows.push([:code, [[:text, source_line]], true])
      else
        layout_line(rows, source_line)
      end
    end
    rows
  end

  def layout_line(rows, source_line)
    row_kind = :paragraph
    row_text = source_line
    if source_line.start_with?("###")
      row_kind = :heading_3
      row_text = source_line[3, source_line.length - 3].lstrip
    elsif source_line.start_with?("##")
      row_kind = :heading_2
      row_text = source_line[2, source_line.length - 2].lstrip
    elsif source_line.start_with?("#")
      row_kind = :heading_1
      row_text = source_line[1, source_line.length - 1].lstrip
    elsif source_line.start_with?("- ") || source_line.start_with?("* ") || source_line == "-"
      row_kind = :list
      row_text = source_line[1, source_line.length - 1].lstrip
    end
    big = big?(row_kind)
    cuts = wrap(row_text, @w - 12 - indent(row_kind), big)
    inline_code = false
    k = 0
    while k < cuts.length
      a = cuts[k]
      b = k + 1 < cuts.length ? cuts[k + 1] : row_text.length
      r = parse_inline_segments(row_text[a, b - a] || "", inline_code)
      inline_code = r[1]
      rows.push([row_kind, r[0], k == 0])
      k += 1
    end
  end

  # [segments, inline code still open at the end]: a ` turns inline code on and off
  def parse_inline_segments(row_text, inline_code)
    segments = []
    segment_kind = inline_code ? :inline_code : :text
    segment_start_index = 0
    character_index = 0

    while character_index < row_text.length
      if row_text.getbyte(character_index) == 96
        segment_text = row_text[segment_start_index, character_index - segment_start_index]
        segments.push([segment_kind, segment_text]) if segment_text.length > 0
        inline_code = !inline_code
        segment_kind = inline_code ? :inline_code : :text
        segment_start_index = character_index + 1
      end
      character_index += 1
    end

    segment_text = row_text[segment_start_index, row_text.length - segment_start_index] || ""
    segments.push([segment_kind, segment_text]) if segment_text.length > 0
    segments.push([:text, ""]) if segments.length == 0
    [segments, inline_code]
  end

  # ---- wrapping, by bytes: the firmware's strings are bytes, and what the keyboard's IME
  # types is UTF-8, twice as wide on screen

  # a title is 24 px on TERM512 (Widget.big_text)
  def big?(row_kind)
    @wide && row_kind == :heading_1
  end

  def indent(row_kind)
    return 12 if row_kind == :list
    return 4 if row_kind == :heading_2
    return 8 if row_kind == :heading_3
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
