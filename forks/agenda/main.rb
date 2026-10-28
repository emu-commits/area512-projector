class Agenda
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

Agenda.new.run
