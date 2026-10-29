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
    elsif k == "ENTER" || k == " "
      more_below? ? screen_down : next_page
    elsif k == "BS"
      more_above? ? screen_up : previous_page
    elsif k == "RIGHT"
      next_page
    elsif k == "LEFT"
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
    fill_down
    @scroll += 1 if more_below?
    fill_down
  end

  def scroll_up
    fill_up
    @scroll -= 1 if @scroll > 0
  end

  # Enter and Space read on: a screen down a long page (a row of it kept), then the next page
  def screen_down
    n = rows_fit(@scroll) - @scroll - 1
    n = 1 if n < 1
    while n > 0 && more_below?
      scroll_down
      n -= 1
    end
  end

  # Backspace: a screen up, then the page before
  def screen_up
    n = rows_fit(@scroll) - @scroll - 1
    n = 1 if n < 1
    while n > 0 && more_above?
      scroll_up
      n -= 1
    end
  end
end
