class Slide
  # The decks are Writer's documents (lib/ruby/docs.rb lists @dir); what's Slide's own is in
  # its own folder, so Writer's recent.txt and place.txt are left alone.
  def place_file
    DATA_DIR + "/place.txt"
  end

  def recent_file
    DATA_DIR + "/recent.txt"
  end

  # The folders, and the first time, Slide's numbered pages from before the fork as one deck
  def load_decks
    ensure_dir("/data")
    ensure_dir(@dir)
    first = !Dir.exist?(DATA_DIR)
    ensure_dir(DATA_DIR)
    load_recent
    import_old if first
    refresh_docs
  rescue
    @msg = "Can't read " + @dir
  end

  # <number>.md in Slide's folder, in number order, joined by "---" as the deck "slides"
  def import_old
    return if File.exist?(path_of("slides"))
    nums = []
    d = Dir.new(OLD_DIR)
    while (f = d.read)
      n = f.length - 3
      nums.push(f[0, n].to_i) if n > 0 && f[n, 3] == ".md" && f[0, n].to_i.to_s == f[0, n]
    end
    d.close
    return if nums.length == 0
    nums.sort!
    data = ""
    nums.each do |n|
      text = read_file(OLD_DIR + "/" + n.to_s + ".md")
      if text
        data += "---\n" if data != ""
        data += text
        data += "\n" if text.length > 0 && text[text.length - 1, 1] != "\n"
      end
    end
    SD.write(path_of("slides"), data)
    touch_recent("slides")
    @msg = "Your pages are the deck \"slides\""
  rescue
  end

  # ---- one deck: its text, where its pages start and end, and one page laid out

  def init_doc
    @text = nil
    @starts = [0]
    @ends = [0]
    @page = 0
    @cs = [0, 0]          # the page's chunks: where each starts, then where the last ends
    @cf = [false]         # each chunk starts inside a ``` block
    @rows = []            # the rows of chunks @c to @d - 1, @counts of them for each
    @counts = []
    @c = 0
    @d = 0
    @scroll = 0
    @dirty = false        # Slide never changes a deck
  end

  def open_doc(name)
    text = read_file(path_of(name))
    if text.nil?
      @msg = "Can't open " + name
      return false
    end
    if text.length > DECK_MAX
      @msg = name + " is " + (text.length / 1024 + 1).to_s + " KB: too big (" + (DECK_MAX / 1024).to_s + " KB most)"
      return false
    end
    init_doc
    @text = text
    split_pages
    @name = name
    @screen = :doc
    go_page(0)
    touch_recent(name)
    true
  end

  def save_doc
    true
  end

  # A line of "---" (CRLF too) ends a page, except inside ``` fences; blank pages are skipped
  def split_pages
    @starts = []
    @ends = []
    t = @text
    n = t.length
    s = 0
    i = 0
    fence = false
    while i < n
      j = t.index("\n", i) || n
      e = j
      e -= 1 if e > i && t.getbyte(e - 1) == 13
      if e - i >= 3 && t.getbyte(i) == 96 && t.getbyte(i + 1) == 96 && t.getbyte(i + 2) == 96
        fence = !fence
      elsif !fence && e - i == 3 && t.getbyte(i) == 45 && t.getbyte(i + 1) == 45 && t.getbyte(i + 2) == 45
        add_page(s, i)
        s = j + 1
      end
      i = j + 1
    end
    add_page(s, n)
    if @starts.length == 0
      @starts.push(0)
      @ends.push(0)
    end
  end

  def add_page(a, b)
    i = a
    while i < b
      if @text.getbyte(i) > 32
        @starts.push(a)
        @ends.push(b)
        return
      end
      i += 1
    end
  end

  def pages
    @starts.length
  end

  # the top of page k
  def go_page(k)
    k = pages - 1 if k >= pages
    k = 0 if k < 0
    @page = k
    split_chunks
    view(0, 0)
  end

  # ---- a page laid out a chunk at a time. A page with no "---" can be the whole of a 10 KB
  # document, and its rows all at once are past the VM's 120 KB (it restarted the device). So a
  # page is cut into chunks of CHUNK bytes of whole lines, and only the chunks the screen shows
  # are laid out: rows below are added as you scroll down, and a chunk scrolled past goes.

  def split_chunks
    @cs = [@starts[@page]]
    @cf = [false]
    t = @text
    n = @ends[@page]
    i = @cs[0]
    fence = false
    while i < n
      j = t.index("\n", i) || n
      fence = !fence if j - i >= 3 && t.getbyte(i) == 96 && t.getbyte(i + 1) == 96 && t.getbyte(i + 2) == 96
      i = j + 1
      if i < n && i - @cs[@cs.length - 1] >= CHUNK
        @cs.push(i)
        @cf.push(fence)
      end
    end
    @cs.push(n)
  end

  def chunk_rows(c)
    layout_page(@text[@cs[c], @cs[c + 1] - @cs[c]] || "", @cf[c])
  end

  # chunk c at the top, then down s rows (or as far as the page goes)
  def view(c, s)
    c = @cs.length - 2 if c > @cs.length - 2
    c = 0 if c < 0
    @rows = []           # the old rows go before the new ones are made
    @counts = []
    @c = c
    @d = c
    @scroll = 0
    fill_down
    while s > 0 && more_below?
      scroll_down
      s -= 1
    end
  end

  # rows enough to fill the screen from @scroll, and none from a chunk above it
  def fill_down
    while @d < @cs.length - 1 && rows_fit(@scroll) >= @rows.length
      r = chunk_rows(@d)
      @rows = @rows + r
      @counts.push(r.length)
      @d += 1
    end
    while @d - @c > 1 && @counts[0] <= @scroll
      n = @counts[0]
      @rows = @rows[n, @rows.length - n]
      @counts = @counts[1, @counts.length - 1]
      @scroll -= n
      @c += 1
    end
  end

  # the chunk above, when the screen is at the top of the rows on hand
  def fill_up
    return unless @scroll == 0 && @c > 0
    @c -= 1
    r = chunk_rows(@c)
    @rows = r + @rows
    @counts = [r.length] + @counts
    @scroll = r.length
    while @d - @c > 1 && @rows.length - @counts[@counts.length - 1] > rows_fit(@scroll)
      n = @counts[@counts.length - 1]
      @rows = @rows[0, @rows.length - n]
      @counts = @counts[0, @counts.length - 1]
      @d -= 1
    end
  end

  def more_below?
    rows_fit(@scroll) < @rows.length
  end

  def more_above?
    @scroll > 0 || @c > 0
  end

  # where the screen is in the page, in rows: [first row shown, rows in all]. Rows not laid
  # out are guessed from the bytes, at the rate of the chunks that are
  def scroll_place
    bytes = @cs[@d] - @cs[@c]
    return [@scroll, @rows.length] if bytes <= 0
    total = (@cs[@cs.length - 1] - @cs[0]) * @rows.length / bytes
    pos = (@cs[@c] - @cs[0]) * @rows.length / bytes + @scroll
    total = pos + @rows.length - @scroll if total < pos + @rows.length - @scroll
    [pos, total]
  end

  # ---- where you were, when you switch away

  def write_place
    s = "screen: " + @screen.to_s + "\nsel: " + @sel.to_s + "\n"
    s += "file: " + @name + ".txt\npage: " + @page.to_s + "\nchunk: " + @c.to_s + "\nscroll: " + @scroll.to_s + "\n" if @name
    SD.write(place_file, s)
  end

  def read_place(f)
    @sel = f["sel"].to_i if f["sel"]
    refresh_docs
    file = f["file"]
    return unless f["screen"] == "doc" && file && file.length > 4
    return unless open_doc(file[0, file.length - 4])
    go_page(f["page"].to_i) if f["page"]
    view(f["chunk"].to_i, f["scroll"].to_i) if f["chunk"]
  end

  # TERM512's list: the deck's first page, its first lines, 64 bytes of each
  def doc_preview(name)
    text = read_file(path_of(name))
    return [] if text.nil?
    return ["(too big to open)"] if text.length > DECK_MAX
    out = []
    i = 0
    while out.length < 16 && i < text.length
      j = text.index("\n", i) || text.length
      n = j - i
      break if n == 3 && text[i, 3] == "---"
      if n > 64
        n = 64
        n -= 1 while n > 0 && text.getbyte(i + n) >= 0x80 && text.getbyte(i + n) < 0xc0
      end
      out.push(text[i, n])
      i = j + 1
    end
    out
  end

  # Writer's Tab v: "<file>:<line>", the deck on the page holding that line; Esc goes back
  def request(verb, arg)
    return unless verb == "show"
    c = arg.length - 1
    c -= 1 while c > 0 && arg[c, 1] != ":"
    line = c > 0 ? arg[c + 1, arg.length].to_i : 0
    file = c > 0 ? arg[0, c] : arg
    name = file.length > 4 && file[file.length - 4, 4] == ".txt" ? file[0, file.length - 4] : file
    @sel = @docs.index(name) || 0
    return unless open_doc(name)
    reg_read.each { |p| @back = p[2] if p[1] == "Writer" }
    off = offset_of_line(line)
    k = 0
    k += 1 while k + 1 < pages && @starts[k + 1] <= off
    go_page(k)
    return if off <= @cs[0]
    # the cursor's line at the top of the screen: its chunk, and the rows above it in that
    c = 0
    c += 1 while c + 2 < @cs.length && @cs[c + 1] <= off
    view(c, layout_page(@text[@cs[c], off - @cs[c]] || "", @cf[c]).length)
  end

  # where line n (from 0) starts
  def offset_of_line(n)
    off = 0
    while n > 0
      j = @text.index("\n", off)
      break if j.nil?
      off = j + 1
      n -= 1
    end
    off
  end

  # ---- writing a deck is Writer's: n and e hand over to it (docs/APPS_FORMAT.md)

  # n, and Home's "new" request: Writer makes the document (and asks its name if none)
  def new_doc(name)
    to_writer("new", name)
  end

  def edit_doc(name)
    to_writer("open", name + ".txt")
  end

  def to_writer(verb, arg)
    w = nil
    reg_read.each { |p| w = p[2] if p[1] == "Writer" }
    if w.nil?
      @msg = "Decks are written in Writer: not here"
      return
    end
    SD.write(OPEN_FILE, "writer|" + verb + "|" + arg + "\n")
    write_place
    @quit = true if run_next(w)
  rescue
    @msg = "Can't hand over to Writer"
  end
end
