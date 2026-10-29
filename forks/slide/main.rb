class Slide
  def initialize
    ui_init
    docs_init
    init_doc
    @dir = DECK_DIR
    @title = "Slide"
    @kind = "deck"
    @old = nil
    @docs_keys = FILES_KEYS
    @rh = @wide ? 16 : 14         # a row of text; a title on TERM512 is 24 px (render.rb)
    @back = nil                   # shown from Writer (its Tab v): where Esc goes
  end

  def run
    Display.fill_screen(@c_bg)
    @sp = BandedSprite.new(12)
    begin
      SD.mount
      load_decks
      start
      main_loop
    ensure
      SD.unmount
      @sp.delete if @sp
      Display.fill_screen(@c_bg)
    end
  end
end

Slide.new.run
