class Writer
  def initialize
    ui_init
    init_doc
    @wrap_w = @w - PAGE_PAD * 2 - SCROLLBAR_W - 3
    @name = nil       # the open document; nil on the list
    @screen = :files
    @sel = 0
    @docs = []
    @recent = []
    @find = ""
    @pv = nil         # TERM512's preview: [name, lines]
    @quit = false
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
