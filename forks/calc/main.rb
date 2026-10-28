class Calc
  def initialize
    ui_init
    docs_init
    init_doc
    @dir = DATA_DIR
    @title = "Calc"
    @kind = "sheet"
    @old = OLD_FILE
    @docs_keys = FILES_KEYS
    @find = ""
    @clip = nil       # [text, col, row]: the cell c copied
  end

  def run
    Display.fill_screen(@c_bg)
    @sp = BandedSprite.new(12)
    begin
      SD.mount
      load_data
      start
      main_loop
    ensure
      SD.unmount
      @sp.delete if @sp
      Display.fill_screen(@c_bg)
    end
  end
end

Calc.new.run
