# AREA512's API for tests/arena/arena.c: the drawing does nothing (but in bands, as on the
# device), files and keys are HostFS's (C, outside the arena, as the card is). SCREEN is set by
# size_*.rb, loaded first.
def require(name)
  false
end

DISPLAY_S = [SCREEN[0], SCREEN[1], SCREEN[2], SCREEN[3]]

class Display
  def self.width
    DISPLAY_S[0]
  end
  def self.height
    DISPLAY_S[1]
  end
  def self.screen_width
    DISPLAY_S[2]
  end
  def self.screen_height
    DISPLAY_S[3]
  end
  def self.full_screen
    DISPLAY_S[0] = DISPLAY_S[2]
    DISPLAY_S[1] = DISPLAY_S[3]
  end
  def self.fill_screen(c)
    nil
  end
end

class BandedSprite
  def initialize(n)
    @n = (Display.height + n - 1) / n
    @band = 0
  end
  def draw
    if @band >= @n
      @band = 0
      return false
    end
    @band += 1
    true
  end
  def text(x, y, s, c)
  end
  def fill(c)
  end
  def fill_rect(x, y, w, h, c)
  end
  def line(x, y, a, b, c)
  end
  def rect(x, y, w, h, c)
  end
  def delete
  end
end

class Widget
  def self.theme_background
    0
  end
  def self.theme_text
    1
  end
  def self.theme_emphasis
    2
  end
  def self.theme_border
    3
  end
  def self.theme_selected
    4
  end
  def self.theme_box
    5
  end
  def self.dim
    6
  end
  def self.char_width
    6
  end
  def self.header_height
    13
  end
  def self.body_top
    14
  end
  def self.body_bottom
    Display.height - 13
  end
  def self.read_key
    HostFS.key
  end
  def self.text_width(sp, s)
    6 * s.length
  end
  def self.clip(sp, s, w)
    s
  end
  def self.header(sp, title, right = "")
  end
  def self.footer(sp, s)
  end
  def self.hints(sp, hs)
  end
  def self.text_right(sp, x, y, s, c)
  end
  def self.big_text(sp, x, y, s, c = nil)
  end
  def self.panel(sp, x, y, w, h)
  end
  def self.scrollbar(sp, x, y, h, top, visible, total)
  end
end

module SD
  def self.mount
    true
  end
  def self.unmount
  end
  def self.read(p)
    HostFS.read(p)
  end
  def self.write(p, s)
    HostFS.note("save " + p)
    HostFS.write(p, s)
  end
  def self.exist?(p)
    HostFS.kind(p) > 0
  end
  def self.mkdir(p)
    HostFS.mkdir(p)
  end
end

class File
  def self.exist?(p)
    HostFS.kind(p) > 0
  end
  def self.file?(p)
    HostFS.kind(p) == 1
  end
  def self.unlink(p)
    HostFS.unlink(p)
  end
  def self.rename(a, b)
    HostFS.rename(a, b)
  end
end

class Dir
  def self.exist?(p)
    HostFS.kind(p) == 2
  end
  def self.mkdir(p)
    HostFS.mkdir(p)
  end
  def initialize(p)
    @l = HostFS.list(p)
  end
  def read
    @l.shift
  end
  def close
  end
end

module Machine
  def self.board_millis
    0
  end
end

module Area512
  def self.run_next(p)
    HostFS.note("run_next " + p)
    true
  end
end

class HostStdin
  def raw
    yield
  end
end
STDIN = HostStdin.new
