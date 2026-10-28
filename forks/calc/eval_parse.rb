class Calc
  # A formula: + - * / and parentheses, numbers, references (B3, $B$3), and SUM AVG
  # (AVERAGE) MIN MAX COUNT over a cell or a range. An empty cell counts as 0; text, a
  # division by zero or another cell's #ERR make this one #ERR.

  def eval_formula(raw)
    @src = raw
    @i = 1
    v = parse_expr
    skip
    raise "extra" if @i < @src.length
    v
  rescue
    nil
  end

  def cur
    return 0 if @i >= @src.length
    @src.getbyte(@i)
  end

  def skip
    @i += 1 while @i < @src.length && (cur == 32 || cur == 9)
  end

  def parse_expr
    v = parse_term
    skip
    while cur == 43 || cur == 45
      op = cur
      @i += 1
      n = parse_term
      v = op == 43 ? v + n : v - n
      skip
    end
    v
  end

  def parse_term
    v = parse_factor
    skip
    while cur == 42 || cur == 47
      op = cur
      @i += 1
      n = parse_factor
      if op == 42
        v *= n
      else
        raise "div" if n == 0
        v /= n
      end
      skip
    end
    v
  end

  def parse_factor
    skip
    sign = 1
    while cur == 43 || cur == 45
      sign = -sign if cur == 45
      @i += 1
      skip
    end
    c = cur
    if c == 40
      @i += 1
      v = parse_expr
      skip
      raise "paren" unless cur == 41
      @i += 1
    elsif c == 36 || (letter?(c) && ref_next?)
      v = ref_value(scan_ref)
    elsif letter?(c)
      v = parse_func
    else
      v = parse_num
    end
    sign < 0 ? -v : v
  end

  # a letter followed by a digit or $: a reference, not a name
  def ref_next?
    n = @i + 1 < @src.length ? @src.getbyte(@i + 1) : 0
    n == 36 || (n >= 48 && n <= 57)
  end

  def parse_num
    v = 0.0
    div = 0.0
    saw = false
    while @i < @src.length
      c = cur
      if c >= 48 && c <= 57
        saw = true
        if div == 0
          v = v * 10 + (c - 48)
        else
          v += (c - 48) / div
          div *= 10
        end
        @i += 1
      elsif c == 46 && div == 0
        div = 10.0
        @i += 1
      else
        break
      end
    end
    raise "num" unless saw
    v
  end

  # B3 or $B$3 at @i, as row * COLS + col
  def scan_ref
    skip
    @i += 1 if cur == 36
    c = cur
    c -= 32 if c >= 97 && c <= 122
    raise "ref" if c < 65 || c > 64 + COLS
    @i += 1
    @i += 1 if cur == 36
    r = 0
    saw = false
    while @i < @src.length && cur >= 48 && cur <= 57
      saw = true
      r = r * 10 + cur - 48
      @i += 1
    end
    raise "ref" if !saw || r < 1 || r > ROWS
    (r - 1) * COLS + c - 65
  end

  def ref_value(k)
    c = k % COLS
    r = k / COLS
    v = value(c, r)
    return v if v
    t = cell_at(c, r)
    return 0.0 if t == ""
    @again = true if t.getbyte(0) == 61
    raise "ref"
  end

  def parse_func
    name = ""
    while @i < @src.length && letter?(cur)
      c = cur
      c -= 32 if c >= 97
      name += c.chr
      @i += 1
    end
    raise "func" unless name == "SUM" || name == "AVG" || name == "AVERAGE" ||
                        name == "MIN" || name == "MAX" || name == "COUNT"
    skip
    raise "func" unless cur == 40
    @i += 1
    a = scan_ref
    b = a
    skip
    if cur == 58
      @i += 1
      b = scan_ref
    end
    skip
    raise "func" unless cur == 41
    @i += 1
    range_func(name, a, b)
  end

  # over the numbers in the range; empty cells and text are left out, an #ERR isn't
  def range_func(name, a, b)
    c1 = a % COLS
    c2 = b % COLS
    r1 = a / COLS
    r2 = b / COLS
    if c1 > c2
      x = c1
      c1 = c2
      c2 = x
    end
    if r1 > r2
      x = r1
      r1 = r2
      r2 = x
    end
    sum = 0.0
    count = 0
    min = nil
    max = nil
    r = r1
    while r <= r2
      c = c1
      while c <= c2
        v = value(c, r)
        if v.nil?
          t = cell_at(c, r)
          if t != "" && t.getbyte(0) == 61
            @again = true
            raise "ref"
          end
        end
        if v
          sum += v
          count += 1
          min = v if min.nil? || v < min
          max = v if max.nil? || v > max
        end
        c += 1
      end
      r += 1
    end
    return count.to_f if name == "COUNT"
    return sum if name == "SUM"
    raise "func" if count == 0
    return sum / count if name == "AVG" || name == "AVERAGE"
    return min if name == "MIN"
    max
  end
end
