# Writer's document under random keys, under CRuby: after every key, the word count, the size
# and the cursor's column, which are kept up a change at a time so a long paragraph stays
# quick (PLAN_V1 4.3), must equal a fresh count; the rows must equal upstream's wrapping (one
# read of each byte now, three then), and a capped wrap the start of the whole one; find must
# equal a search of a lowercased copy.
#
#   ruby tests/wrfuzz.rb [seed] [documents]
#
# Strings are bytes, as on the device. Exits 1 on the first document that goes wrong.
W = File.expand_path("../forks/writer/", __dir__) + "/"
class SuiteApp; end
module Kernel
  def require(name) = false          # const.rb's AREA512 gems: none needed here
end
class Writer < SuiteApp
  attr_accessor :row, :col
  def initialize(wrap, top, bot)
    init_doc
    @wrap_w = wrap
    @top = top
    @bot = bot
  end
end
%w[const document edit].each { |f| eval(File.read(W + f + ".rb"), binding, f + ".rb") }

seed = (ARGV[0] || 1).to_i
docs = (ARGV[1] || 200).to_i
rng = Random.new(seed)
WORDS = %w[a an the lorem ipsum consectetur adipiscing supercalifragilisticexpialidocious x].map(&:b)
KANA = ["あ", "い", "漢"].map(&:b)
LONG = "supercalifragilisticexpialidocious".b

def got(w, v) = w.instance_variable_get(v)
# upstream's wrapping, as forked (document.rb before PLAN_V1 4.3's speed-up), with its one
# fault mended: after carrying a word down it didn't look again, so a row could run past the
# edge (" lcious\u3042a\u3042" at 60 px: "lcious\u3042a\u3042" on one row, 66 px). Now: while,
# not if.
def ref_segs(w, s)
  wrap = w.instance_variable_get(:@wrap_w)
  out = [0]
  start = 0
  brk = 0
  x = 0
  i = 0
  while i < s.length
    b = s.getbyte(i)
    g = w.glyph_w(s, i)
    while b != 32 && x + g > wrap && i > start
      cut = brk > start ? brk : i
      out.push(cut)
      start = cut
      brk = 0
      x = w.width(s, start, i)
    end
    brk = i + 1 if b == 32
    x += g
    i += w.step(s, i)
  end
  out
end

docs.times do |doc|
  # the Cardputer's and TERM512's widths and heights, and narrow ones for more rows
  wr = Writer.new([60, 120, 228, 306][rng.rand(4)], 14, [122, 214][rng.rand(2)])
  text = Array.new(rng.rand(1..6)) do
    Array.new(rng.rand(0..400)) { WORDS.sample(random: rng) + (rng.rand(9) == 0 ? "  " : " ") }.join
  end.join("\n")
  wr.set_text(text.b[0, 9000])
  wr.row = rng.rand(got(wr, :@lines).length)
  wr.col = 0
  300.times do |n|
    op = rng.rand(16)
    case op
    when 0..5 then wr.insert_text([WORDS.sample(random: rng)[0, 1], " ".b, KANA.sample(random: rng)].sample(random: rng))
    when 6 then wr.backspace
    when 7 then wr.insert_newline if rng.rand(4) == 0
    when 8 then wr.move_left
    when 9 then wr.move_right
    when 10 then wr.move_row(rng.rand(2) * 2 - 1)
    when 11 then wr.page(rng.rand(2) * 2 - 1)
    when 12 then rng.rand(2) == 0 ? wr.word_left : wr.word_right
    when 13 then rng.rand(2) == 0 ? wr.row_start : wr.row_end
    when 14 then rng.rand(2) == 0 ? wr.doc_start : wr.doc_end
    when 15 then wr.insert_text(LONG * rng.rand(1..3))
    end
    wr.layout
    lines = got(wr, :@lines)
    bad = []
    l = wr.cur_line
    whole = wr.segs(l)
    bad << "rows" if whole != ref_segs(wr, l)
    cap = rng.rand(1..20)
    bad << "capped rows" if wr.segs(l, cap) != whole[0, cap + 1]
    bad << "@words" if got(wr, :@words) != lines.sum { |l| wr.word_count(l) }
    bad << "@bytes" if got(wr, :@bytes) != lines.sum { |l| l.length + 1 }
    bad << "column" if wr.col_chars != wr.chars_in(wr.cur_line, 0, wr.col)
    if op == 12                      # find: the same as a lowercased copy, without one
      s = lines.sample(random: rng)
      want = (rng.rand(2) == 0 ? WORDS.sample(random: rng) : s[rng.rand(s.length + 1), rng.rand(1..6)].to_s).downcase
      from = rng.rand(s.length + 1)
      want = "a" if want == ""
      mixed = s.dup
      mixed.length.times { |i| mixed.setbyte(i, mixed.getbyte(i) - 32) if rng.rand(3) == 0 && mixed.getbyte(i).between?(97, 122) }
      bad << "find" if wr.find_in(mixed, want, from) != mixed.downcase.index(want, from)
    end
    next if bad.empty?
    puts "seed #{seed}, document #{doc}, key #{n + 1} (op #{op}): #{bad.join(', ')} wrong"
    exit 1
  end
end
puts "seed #{seed}: #{docs} documents, 300 keys each: ok"
