# Shared by the forks that keep documents in a folder (Writer, Calc): the list of documents,
# new, rename and delete, recent.txt for Home, the start-up requests and place, leaving and
# switching (docs/APPS_FORMAT.md). Cut out of Writer unchanged but for the names below. In
# main.manifest after ui.mrb, for the forks that use it.
#
# The app sets, in initialize, after ui_init:
#   @dir   its data folder ("/data/writer"); a document is <@dir>/<name>.txt
#   @title its name in apps.txt ("Writer"); @kind what a document is called ("document")
#   @old   its one file from before the fork, copied once as a document, or nil
# and has: init_doc, open_doc(name) (true if opened), save_doc (false if it failed),
# write_place, read_place(f), doc_preview(name) (lines, for TERM512's list), and @dirty,
# and sets @docs_keys, the list's key table: "<Title>|1ENT open|2n new|3x delete|r rename",
# and @docs_none, the same with nothing in the list: "<Title>|1n new". The list's screen
# reads its keys with cmd(files_spec).

class SuiteApp
  # the card's long names stop at 32 bytes, with ".txt"
  NAME_MAX = 24 unless const_defined?(:NAME_MAX)

  def docs_init
    @name = nil       # the open document; nil on the list
    @screen = :files
    @sel = 0
    @docs = []
    @recent = []
    @pv = nil         # TERM512's preview: [name, lines]
    @quit = false
  end

  def path_of(name)
    @dir + "/" + name + ".txt"
  end

  def place_file
    @dir + "/place.txt"
  end

  def recent_file
    @dir + "/recent.txt"
  end

  # recent.txt and place.txt sit beside the documents, so those two names are the app's own
  def own_name?(name)
    d = name.downcase
    d == "recent" || d == "place"
  end

  # The names on the card, the recent ones first (recent.txt's order), then A to Z
  def doc_names
    all = []
    begin
      d = Dir.new(@dir)
      while (f = d.read)
        n = f.length - 4
        all.push(f[0, n]) if n > 0 && f[n, 4] == ".txt" && !own_name?(f[0, n])
      end
      d.close
    rescue
      all = []
      @recent.each { |n| all.push(n) if File.exist?(path_of(n)) }
    end
    out = []
    @recent.each { |n| out.push(n) if all.include?(n) }
    rest = []
    all.each { |n| rest.push(n) unless out.include?(n) }
    rest.sort! { |a, b| a.downcase <=> b.downcase }
    rest.each { |n| out.push(n) }
    out
  end

  def refresh_docs
    @docs = doc_names
    @sel = @docs.length - 1 if @sel >= @docs.length
    @sel = 0 if @sel < 0
  end

  # the name typed: letters, digits, space - _ ( ) and nothing a card can't name
  def clean_name(s)
    out = ""
    i = 0
    while i < s.length && out.length < NAME_MAX
      b = s.getbyte(i)
      ok = (b >= 48 && b <= 57) || (b >= 65 && b <= 90) || (b >= 97 && b <= 122)
      ok = true if b == 32 || b == 45 || b == 95 || b == 40 || b == 41
      out = out + s[i, 1] if ok
      i += 1
    end
    out.strip
  end

  # the name as it is on the card, if one differs only in case
  def existing(name)
    r = nil
    d = name.downcase
    doc_names.each { |n| r = n if n.downcase == d }
    r
  end

  # nil, or why the name can't be used (it's for a new name, or a rename of "except")
  def name_problem(name, except)
    return "A name needs a letter or a digit" if name == ""
    return "That name is " + @title + "'s own" if own_name?(name)
    e = existing(name)
    return "There's a " + @kind + " called " + e if e && e != except
    nil
  end

  # ---- the list

  # the list's key table: with nothing in it, only n (the rest would do nothing)
  def files_spec
    @docs && @docs.length == 0 ? @docs_none : @docs_keys
  end

  def files_key(k)
    name = @docs[@sel]
    if k.length > 1 && k[0, 1] == "@"
      switch_to(k[1, k.length])
    elsif k == "UP"
      @sel -= 1 if @sel > 0
    elsif k == "DOWN"
      @sel += 1 if @sel < @docs.length - 1
    elsif k == "ENTER" || k == "RIGHT"
      open_doc(name) if name
    elsif k == "n"
      new_doc("")
    elsif k == "x" || k == "d"
      if name && ask_yn("DELETE", "Delete " + name + "?")
        delete_doc(name)
      end
    elsif k == "r"
      rename_doc(name) if name
    elsif k == "ESC" || k == "q"
      leave
    end
  end

  def render_files
    n = @docs.length
    frame(@title.upcase, n == 1 ? "1 " + @kind : n.to_s + " " + @kind + "s")
    lw = @wide ? 132 : @w
    y = @top + 3
    if n == 0
      t(8, y, "No " + @kind + "s yet.", @c_text)
      t(8, y + @lh, "n starts one.", @c_em)
    else
      rows = (@bot - y - 2) / @lh
      first = @sel - rows + 1
      first = 0 if first < 0
      i = first
      while i < n && i < first + rows
        row(2, y, lw - 4, @docs[i], i == @sel)
        y += @lh
        i += 1
      end
      preview if @wide
    end
    foot(files_spec, n > 0 ? NAV_ROWS : nil)
  end

  # TERM512: the selected document's first lines beside the list
  def preview
    name = @docs[@sel]
    @pv = [name, doc_preview(name)] if @pv.nil? || @pv[0] != name
    x = 138
    y = @top + 2
    h = @bot - y - 2
    @sp.rect(x, y, @w - x - 2, h, @c_border)
    cols = (@w - x - 10) / @cw
    yy = y + 4
    i = 0
    while i < @pv[1].length && yy <= y + h - @lh
      t(x + 5, yy, clip(@pv[1][i], cols * @cw), @c_dim)
      yy += @lh
      i += 1
    end
  end

  # ---- one document

  # out of the document to the list, saving first
  def close_doc
    return false if @dirty && !save_doc
    @screen = :files
    @pv = nil         # it may have changed
    refresh_docs
    i = @docs.index(@name)
    @sel = i if i
    @name = nil
    init_doc          # let the text go: the list's preview reads the file again
    true
  end

  # a new document, named now: n, and Home's "new" request (arg: its name, or "" to ask)
  def new_doc(name)
    if name == ""
      s = ask_text("NEW " + @kind.upcase, "Its name?", "", NAME_MAX)
      return if s.nil?
      name = clean_name(s)
    else
      name = clean_name(name)
    end
    e = existing(name)
    why = e ? nil : name_problem(name, nil)
    if why
      @msg = why
      return
    end
    return if @name && !close_doc
    if e
      open_doc(e)        # one of that name is there already (Home's "new" for notes): open it
      return
    end
    init_doc
    @name = name
    @screen = :doc
    @msg = "New: " + name
    @msg = "Can't write " + name unless save_doc
    touch_recent(name)
  end

  def rename_doc(old)
    s = ask_text("RENAME", "New name for " + old + "?", old, NAME_MAX)
    return if s.nil?
    name = clean_name(s)
    return if name == old
    why = name_problem(name, old)
    if why
      @msg = why
      return
    end
    File.rename(path_of(old), path_of(name))
    @name = name if @name == old
    @recent.each_index { |i| @recent[i] = name if @recent[i] == old }
    write_recent
    refresh_docs
    i = @docs.index(name)
    @sel = i if i
    @msg = "Renamed " + name
  rescue
    @msg = "Rename failed"
  end

  # moved to deleted/, over an older one of the same name (a delete from Home is one key away)
  def delete_doc(name)
    bin_dir = @dir + "/deleted"
    ensure_dir(bin_dir)
    bin = bin_dir + "/" + name + ".txt"
    File.unlink(bin) if File.exist?(bin)
    File.rename(path_of(name), bin)
    @recent.delete_if { |n| n == name }
    write_recent
    refresh_docs
    @msg = "Deleted " + name + " (kept in deleted/)"
    true
  rescue
    @msg = "Delete failed"
    false
  end

  # ---- recent.txt: for Home, newest first, at most 8 (docs/APPS_FORMAT.md)

  # without the ones gone from the card (Slide shows Writer's documents, and either app can
  # delete one), rewritten if any were, so Home doesn't list them
  def load_recent
    @recent = []
    text = read_file(recent_file)
    return unless text
    gone = false
    text.split("\n").each do |l|
      p = l.split("|")
      if p.length == 2 && p[1].length > 4
        n = p[1][0, p[1].length - 4]
        if File.exist?(path_of(n))
          @recent.push(n)
        else
          gone = true
        end
      end
    end
    write_recent if gone
  end

  def touch_recent(name)
    @recent.delete_if { |n| n == name }
    @recent.unshift(name)
    @recent.pop while @recent.length > 8
    write_recent
  end

  def write_recent
    data = ""
    @recent.each { |n| data += n + "|" + n + ".txt\n" }
    SD.write(recent_file, data)
  rescue
  end

  # ---- start-up

  # The folder, and the first time, the app's one file from before the fork, as the document
  # of that file's name
  def load_data
    ensure_dir("/data")
    first = !Dir.exist?(@dir)
    ensure_dir(@dir)
    load_recent
    if first && @old && File.exist?(@old)
      text = read_file(@old)
      if text
        p = @old.split("/")
        base = p[p.length - 1]
        name = base[0, base.length - 4]
        SD.write(path_of(name), text)
        touch_recent(name)
        @msg = "Your " + base + " is the " + @kind + " \"" + name + "\""
      end
    end
    refresh_docs
  rescue
    @msg = "Can't read " + @dir
  end

  # Home's request (open.txt), else where you were (place.txt). Both are read once and
  # deleted, so neither is left to act on later.
  def start
    reg_read.each { |p| @app_dir = p[2] if p[1] == @title }
    req = take_request(@title.downcase)
    place = take_place(place_file)
    if req.nil?
      read_place(place) if place
      return
    end
    verb = req[0]
    arg = req[1]
    name = arg.length > 4 && arg[arg.length - 4, 4] == ".txt" ? arg[0, arg.length - 4] : arg
    if verb == "new"
      new_doc(arg)
    elsif verb == "open"
      @sel = @docs.index(name) || 0
      open_doc(name)
    elsif verb == "delete"
      # Home asked first: delete it without asking again, and go back
      delete_doc(name) if @docs.include?(name)
      h = home_path
      @quit = true if h && run_next(h)
    else
      request(verb, arg)
    end
  end

  # a verb of the app's own (Slide's "show", from Writer); none by default
  def request(verb, arg)
  end

  # ---- leaving and switching (docs/APPS_FORMAT.md)

  # Esc from the list: saves first, goes to Home
  def leave
    return if @dirty && !save_doc
    h = home_path
    run_next(h) if h && h != @app_dir
    @quit = true
  end

  # Tab, then a digit: save, leave a place, hand off. A switch never loses work.
  def switch_to(path)
    return if @dirty && !save_doc
    write_place
    @quit = true if run_next(path)
  end
end
