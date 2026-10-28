class Writer
  def main_loop
    until @quit
      if @screen == :doc
        doc_step
      else
        refresh_docs if @docs.nil?
        files_key(cmd(FILES_KEYS))
      end
    end
  end

  # ---- the document: letters type; Tab is the menu; Esc goes back a level

  def doc_step
    layout
    paint
    @msg = ""
    k = key
    @hit = nil
    if k == "\t"
      r = menu_main(DOC_KEYS)
      doc_cmd(r) if r
    elsif @mode == :move
      move_key(k)
    else
      type_key(k)
    end
  end

  def type_key(k)
    if k == "ESC"
      close_doc
    elsif k == "ENTER"
      insert_newline
    elsif k == "BS"
      backspace
    elsif k == "UP" || k == "DOWN" || k == "LEFT" || k == "RIGHT"
      doc_cmd(k)                     # Fn+arrow
    elsif k.length == 1
      b = k.getbyte(0)
      if b >= 32
        type_byte(k)
      elsif b == 19                  # Writer's Ctrl keys still work: ^S ^O ^Q ^K
        save_doc
      elsif b == 15
        close_doc
      elsif b == 17
        leave
      elsif b == 11
        page(-1)
      end
    end
  end

  # In Move the bare keys are commands: Enter or Esc goes back to typing
  def move_key(k)
    k = arrow(k)
    if k == "ENTER" || k == "ESC"
      @mode = :type
    elsif k == "%"
      @msg = mem_text
    elsif !doc_cmd(k)
      @msg = "MOVE: ENT or ESC to type" if k.length == 1
    end
  end

  # A command in the document, from Move's keys or the menu; false if k isn't one
  def doc_cmd(k)
    if k.length > 1 && k[0, 1] == "@"
      switch_to(k[1, k.length])
    elsif k == "ENTER"
      @mode = :type
    elsif k == "m"
      @mode = @mode == :move ? :type : :move
    elsif k == "LEFT"
      move_left
    elsif k == "RIGHT"
      move_right
    elsif k == "UP"
      move_row(-1)
    elsif k == "DOWN"
      move_row(1)
    elsif k == "h"
      word_left
    elsif k == "l"
      word_right
    elsif k == "k"
      page(-1)
    elsif k == "j"
      page(1)
    elsif k == "a"
      row_start
    elsif k == "e"
      row_end
    elsif k == "["
      doc_start
    elsif k == "]"
      doc_end
    elsif k == "f"
      find
    elsif k == "g"
      find_next
    elsif k == "s"
      save_doc
    elsif k == "o"
      close_doc
    elsif k == "n"
      new_doc("")
    elsif k == "r"
      rename_doc(@name)
    else
      return false
    end
    true
  end
end
