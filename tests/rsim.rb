# Run a PicoRuby fork on the PC, under CRuby, with mocks of AREA512's API: the Ruby twin of
# area512-factory's a512sim, driven by tests/sim.py (scenarios named after the fork).
#
#   ruby tests/rsim.rb <keys file> <seed.json> <cardputer|term512> <file.rb>...
#
# The files run in order, as main.manifest loads them. Output, as a512sim's:
#   @@RUN_NEXT <path>   @@RUNTIME_ERROR <file>   @@STATS ... keys_used=n/m   @@SCREEN <text>
#   @@FS <path> <repr>  @@EXIT ok|keys_exhausted|error
#
# CRuby runs more than mruby/c does, so this checks the logic and the files; whether a method
# exists on the device is checked by tests/fw.py on the firmware.
require "json"

KEYS = File.read(ARGV[0]).split(" ")
SEED = JSON.parse(File.read(ARGV[1]))
SIZE = ARGV[2] == "term512" ? [240, 135, 320, 240] : [240, 135, 240, 135]
SOURCES = ARGV[3..].map { |f| [f, File.read(f)] }    # read before File is mocked

class SimDone < Exception; end

$sim = { pos: 0, frames: 0, cur: [], last: [], fs: {}, pend: [] }
SEED.each { |k, v| $sim[:fs][k] = v.nil? ? nil : v.b }

def sim_txt(s)
  $sim[:cur] << s.to_s if $sim[:cur].length < 40
end

def sim_frame
  $sim[:last] = $sim[:cur] unless $sim[:cur].empty?
  $sim[:cur] = []
  $sim[:frames] += 1
  raise SimDone, "frame_limit" if $sim[:frames] > 40000
end

# A non-ASCII token is UTF-8 from the keyboard's IME: the firmware hands it over a byte a key
def sim_key
  return $sim[:pend].shift unless $sim[:pend].empty?
  while $sim[:pos] < KEYS.length
    t = KEYS[$sim[:pos]]
    $sim[:pos] += 1
    next if t == "WAIT"
    return " " if t == "SPACE"
    return (t[5].ord & 31).chr if t.start_with?("CTRL:")    # CTRL:s is Ctrl+S, byte 19
    return "\t" if t == "TAB"
    unless t.ascii_only?
      $sim[:pend] = t.b.bytes.map { |b| b.chr.b }
      return $sim[:pend].shift
    end
    return t.b
  end
  raise SimDone, "keys_exhausted"
end

module Kernel
  alias_method :sim_require, :require
  def require(name)
    return false if name =~ /\Aarea512|\Amachine\z|\Aio\/console\z/
    sim_require(name)
  end
end

def STDIN.raw
  yield
end

module Display
  @s = SIZE.dup
  def self.width = @s[0]
  def self.height = @s[1]
  def self.screen_width = @s[2]
  def self.screen_height = @s[3]
  def self.full_screen
    @s[0] = @s[2]
    @s[1] = @s[3]
  end
  def self.fill_screen(c) = nil
end

class BandedSprite
  def initialize(n)
    @band = 0
  end

  def draw
    sim_frame
    @band = 1 - @band
    @band == 1
  end

  def text(x, y, s, c)
    raise TypeError, "text: #{s.inspect}" unless s.is_a?(String)
    sim_txt(s)
  end

  %i[fill pixel line rect fill_rect circle fill_circle delete].each { |m| define_method(m) { |*a| nil } }
end

module Widget
  def self.theme_background = 0x000000
  def self.theme_text = 0xCFA45F
  def self.theme_emphasis = 0xF5972D
  def self.theme_border = 0xF5972D
  def self.theme_selected = 0xFFD966
  def self.theme_box = 0x241604
  def self.dim = 0xCFA45F
  def self.char_width = 6
  def self.header_height = 13
  def self.body_top = 14
  def self.body_bottom = Display.height - 13
  def self.read_key = sim_key
  def self.text_width(sp, s) = 6 * s.length
  def self.clip(sp, s, w) = s
  def self.header(sp, title, right = "")
    sim_txt(title)
    sim_txt(right)
  end
  def self.footer(sp, s) = sim_txt(s)
  def self.hints(sp, hs)
    hs.each { |h| raise TypeError, "hints: #{h.inspect}" unless h[0].is_a?(String) && h[1].is_a?(String) }
    sim_txt(hs.map { |h| h[0] + ":" + h[1] }.join(" "))
  end
  def self.text_right(sp, x, y, s, c) = sim_txt(s)
  def self.body_height = body_bottom - body_top
  def self.panel(sp, x, y, w, h) = nil
  def self.scrollbar(sp, x, y, h, top, visible, total) = nil
end

module SD
  def self.mount = true
  def self.unmount = nil
  def self.exist?(p) = $sim[:fs].key?(p)
  def self.read(p)
    v = $sim[:fs][p]
    raise IOError, "no file #{p}" if v.nil?
    v
  end
  def self.write(p, s)
    $sim[:fs][p] = s
    s.length
  end
end

class << File
  def exist?(p) = $sim[:fs].key?(p)
  def unlink(p) = $sim[:fs].delete(p) ? 1 : 0
end

class << File
  def rename(a, b)
    raise IOError, "no file #{a}" unless $sim[:fs].key?(a)
    $sim[:fs][b] = $sim[:fs].delete(a)
    0
  end
end

# Dir.new(path).read: the names in it, then nil (AREA512's Dir, over POSIX readdir)
class Dir
  def self.exist?(p) = $sim[:fs].key?(p) && $sim[:fs][p].nil?
  def self.mkdir(p) = ($sim[:fs][p] = nil)
  def self.new(p)
    raise IOError, "no dir #{p}" unless exist?(p)
    allocate.tap { |d| d.sim_open(p) }
  end
  def sim_open(p)
    pre = p + "/"
    @names = $sim[:fs].keys.select { |k| k.start_with?(pre) && !k[pre.length..].include?("/") }
                       .map { |k| k[pre.length..] }
  end
  def read = @names.shift
  def close = nil
end

module PicoRubyVM
  def self.memory_statistics = { total: 120 * 1024, used: 50 * 1024, free: 70 * 1024, fragmentation: 0 }
end

module Area512
  def self.run_next(p) = puts("@@RUN_NEXT " + p)
end

reason = "ok"
begin
  SOURCES.each do |f, src|
    @sim_file = f
    TOPLEVEL_BINDING.eval(src, f)
  end
rescue SimDone => e
  reason = e.message == "keys_exhausted" ? "keys_exhausted" : "ok"
rescue Exception => e
  puts "@@RUNTIME_ERROR #{@sim_file}"
  puts "#{e.class}: #{e.message}"
  e.backtrace.first(8).each { |l| puts "  " + l }
  reason = "error"
end
sim_frame
puts "@@STATS frames=#{$sim[:frames]} keys_used=#{$sim[:pos]}/#{KEYS.length}"
$sim[:last].each { |t| puts "@@SCREEN " + t }
$sim[:fs].keys.sort.each do |k|
  v = $sim[:fs][k]
  puts "@@FS #{k} #{v.inspect}" if k.start_with?("/data/") && !v.nil?
end
puts "@@EXIT #{reason}"
