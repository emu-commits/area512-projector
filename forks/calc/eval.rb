class Calc
  # Values (@vals, sheet.rb): a Float for a number, and for a formula that works out. A
  # cell of text, or a formula that doesn't (#ERR), has none. Everything is a Float:
  # Integer is 32 bits on the device, and 7/2 is 3.5.

  # "12", "-3.5", ".5": a number, all of it (upstream took "12abc" as 12)
  def number?(s)
    i = 0
    n = s.length
    i = 1 if n > 0 && (s.getbyte(0) == 45 || s.getbyte(0) == 43)
    digits = false
    dot = false
    while i < n
      b = s.getbyte(i)
      if b >= 48 && b <= 57
        digits = true
      elsif b == 46 && !dot
        dot = true
      else
        return false
      end
      i += 1
    end
    digits
  end

  def to_num(s)
    @src = s
    @i = 0
    neg = cur == 45
    @i = 1 if neg || cur == 43
    v = parse_num
    neg ? -v : v
  end

  # Numbers first, then the formulas, along the rows. A formula that uses one further on
  # gets its value the pass after (any order, any depth), so passes go on while one did
  # that and something changed; a sheet that reads down needs one. A loop of formulas
  # never gets a value, so it stays #ERR. Nothing is kept that grows with the sheet: each
  # row's values are one Array, made at its length.
  def recalc
    @vals = Array.new(ROWS)
    n = 0
    r = 0
    while r < ROWS
      if @rows[r]
        p = @rows[r].split("\t")
        a = Array.new(p.length)
        c = 0
        while c < p.length
          t = p[c]
          if t.getbyte(0) == 61
            n += 1
          elsif t != "" && number?(t)
            a[c] = to_num(t)
          end
          c += 1
        end
        @vals[r] = a
      end
      r += 1
    end
    pass = 0
    @again = true
    while @again && pass < n && recalc_pass > 0
      pass += 1
    end
    @calc = true
  end

  # the formulas, once each: how many changed. @again: one used a formula with no value yet
  def recalc_pass
    @again = false
    n = 0
    r = 0
    while r < ROWS
      if @rows[r]
        p = @rows[r].split("\t")
        a = @vals[r]
        c = 0
        while c < p.length
          if p[c].getbyte(0) == 61
            x = eval_formula(p[c])
            if x != a[c]
              a[c] = x
              n += 1
            end
          end
          c += 1
        end
      end
      r += 1
    end
    n
  end

  # what the grid shows: [text or Float, :num | :text | :err]
  def shown(c, r)
    t = cell_at(c, r)
    return [t, :text] if t == ""
    recalc unless @calc
    x = value(c, r)
    if t.getbyte(0) == 61
      return x.nil? ? ["#ERR", :err] : [x, :num]
    end
    x.nil? ? [t, :text] : [t, :num]
  end

  # ---- numbers as text, in mruby/c (no round or format) and the same in CRuby

  # v in at most room characters: as many decimals as fit, up to 6, or ### if none do
  def fmt_num(v, room)
    neg = v < 0
    a = neg ? -v : v
    return "###" if a >= 2.0e9
    d = 6
    while d >= 0
      s = fixed(a, d)
      s = "-" + s if neg && s != "0"
      return s if s.length <= room
      d -= 1
    end
    "###"
  end

  # a >= 0 with d decimals, rounded, the zeros at the end left off
  def fixed(a, d)
    m = 1.0
    i = 0
    while i < d
      m *= 10
      i += 1
    end
    a += 0.5 / m
    ip = a.to_i
    f = a - ip
    fs = ""
    i = 0
    while i < d
      f *= 10
      g = f.to_i
      g = 9 if g > 9
      fs += g.to_s
      f -= g
      i += 1
    end
    n = fs.length
    n -= 1 while n > 0 && fs.getbyte(n - 1) == 48
    n > 0 ? ip.to_s + "." + fs[0, n] : ip.to_s
  end

  # ---- copying a formula: its references move with it, but not the $ parts

  # the formula with every reference moved dc columns and dr rows, or nil if one goes off
  # the sheet. Names (SUM) are letters followed by letters, so they're kept as they are.
  def shift_refs(s, dc, dr)
    out = ""
    i = 0
    n = s.length
    while i < n
      j = i
      ac = s.getbyte(j) == 36
      j += 1 if ac
      a = j
      j += 1 while j < n && letter?(s.getbyte(j))
      if j - a == 1
        ar = j < n && s.getbyte(j) == 36
        k = ar ? j + 1 : j
        e = k
        e += 1 while e < n && s.getbyte(e) >= 48 && s.getbyte(e) <= 57
        if e > k
          c = s.getbyte(a)
          c -= 32 if c >= 97
          c -= 65
          r = s[k, e - k].to_i - 1
          c += dc unless ac
          r += dr unless ar
          return nil if c < 0 || c >= COLS || r < 0 || r >= ROWS
          out += (ac ? "$" : "") + (65 + c).chr + (ar ? "$" : "") + (r + 1).to_s
          i = e
          next
        end
      end
      if j > a
        out += s[i, j - i]
        i = j
      else
        out += s[i, 1]
        i += 1
      end
    end
    out
  end

  def letter?(b)
    (b >= 65 && b <= 90) || (b >= 97 && b <= 122)
  end
end
