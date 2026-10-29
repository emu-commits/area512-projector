class Slide
  def main_loop
    until @quit
      if @screen == :doc
        show_key(cmd(SHOW_KEYS))
      else
        k = cmd(FILES_KEYS)
        if k == "e"
          edit_doc(@docs[@sel]) if @docs[@sel]
        else
          files_key(k)
        end
      end
    end
  end

  # A key on a page, bare or from the menu (which hands back j and k as they are)
  def show_key(k)
    if k.length > 1 && k[0, 1] == "@"
      switch_to(k[1, k.length])
    elsif k == "RIGHT" || k == "ENTER" || k == " "
      next_page
    elsif k == "LEFT" || k == "BS"
      previous_page
    elsif k == "DOWN" || k == "j"
      scroll_down
    elsif k == "UP" || k == "k"
      scroll_up
    elsif k == "["
      go_page(0)
    elsif k == "]"
      go_page(pages - 1)
    elsif k == "e"
      edit_doc(@name)
    elsif (k == "ESC" || k == "q") && @back
      @quit = true if run_next(@back)      # shown from Writer: back to it, where you were
    elsif k == "o" || k == "ESC" || k == "q"
      @back = nil
      close_doc
    end
  end

  def next_page
    if @page >= pages - 1
      @msg = "Last page. o: the decks"
      return
    end
    go_page(@page + 1)
  end

  def previous_page
    go_page(@page - 1) if @page > 0
  end

  def scroll_down
    @scroll += 1 if rows_fit(@scroll) < @rows.length
  end

  def scroll_up
    @scroll -= 1 if @scroll > 0
  end
end
