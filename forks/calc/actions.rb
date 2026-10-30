class Calc
  def main_loop
    until @quit
      if @screen != :doc
        files_key(cmd(files_spec))
      elsif @edit
        paint
        @msg = ""
        k = key
        if k == "\t"                 # Tab: the entry goes in, then the menu, as anywhere
          commit_edit(0, 0)
          k = @edit.nil? && !@full ? menu_main(GRID_KEYS) : nil
          grid_key(k) if k
        else
          edit_key(k)
        end
      else
        grid_key(cmd(GRID_KEYS))
      end
    end
  end

  # On the grid the letters are commands. A digit, = - + ( or Space starts typing into
  # the cell, over what's there (Space: an empty start); Enter or e types on the end of it.
  def grid_key(k)
    if k.length > 1 && k[0, 1] == "@"
      switch_to(k[1, k.length])
    elsif k == "UP"
      move(0, -1)
    elsif k == "DOWN"
      move(0, 1)
    elsif k == "LEFT"
      move(-1, 0)
    elsif k == "RIGHT"
      move(1, 0)
    elsif k == "ENTER" || k == "e"
      start_edit(cell_at(@col, @row))
    elsif k == " "
      start_edit("")
    elsif k.length == 1 && starts_entry?(k.getbyte(0))
      start_edit(k)
    elsif k == "x" || k == "BS"
      clear_cell
    elsif k == "u"
      undo
    elsif k == "c"
      copy_cell
    elsif k == "v"
      paste
    elsif k == "d"
      fill(0, 1)
    elsif k == "r"
      fill(1, 0)
    elsif k == "g"
      go_to
    elsif k == "f"
      find
    elsif k == "w"
      step_width
    elsif k == "["
      go(0, 0)
    elsif k == "]"
      go_end
    elsif k == "s"
      save_doc
    elsif k == "o" || k == "ESC" || k == "q"
      close_doc
    elsif k == "n"
      new_doc("")
    end
  end

  # 0-9 = - + (
  def starts_entry?(b)
    (b >= 48 && b <= 57) || b == 61 || b == 45 || b == 43 || b == 40
  end
end
