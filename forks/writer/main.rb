class Writer
  def initialize
    ui_init
    init_doc
    @wrap_w = @w - PAGE_PAD * 2 - SCROLLBAR_W - 3
    docs_init
    @dir = DATA_DIR
    @title = "Writer"
    @kind = "document"
    @old = OLD_FILE
    @docs_keys = FILES_KEYS
    @find = ""
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

Writer.new.run
