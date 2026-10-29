require 'area512-widget'
require 'machine'
require 'io/console'
require 'area512-sprite'
require 'area512-sdfat'

# Writer: AREA512's Writer, forked (UPSTREAM.md) onto the suite's grammar (docs/UI.md).
# SuiteApp is lib/ruby/ui.rb, first in main.manifest, and lib/ruby/docs.rb (the list of
# documents, recent.txt, Home's requests, switching), second.
#
# Constants live under the app class so they never collide with other apps in the shared
# sandbox VM (each run keeps a global const table), guarded for re-runs of this same app.
class Writer < SuiteApp
  DATA_DIR = "/data/writer" unless const_defined?(:DATA_DIR)
  # Writer's one document before the fork: copied once, the first time, as "writer"
  OLD_FILE = "/data/writer.txt" unless const_defined?(:OLD_FILE)
  # The biggest document: DOC_BYTES of text, and DOC_MAX of "room", its bytes and LINE_COST
  # more for each line (a String's own cost in the VM). Opening holds the file twice, each
  # copy in one piece, and saving joins the lines into one, all in the VM's 120 KB with the
  # app's own code; running out restarts the device. Measured on the TERM512 build, which
  # leaves the VM less than the Cardputer's v2.7, opening, editing, saving and closing four
  # times: 10 KB in 160 lines, 330 short lines and 15 KB in 10 paragraphs on the Cardputer
  # took it; 12 KB in 200 lines, 500 short lines and 15 KB in 10 paragraphs on TERM512 ran
  # out (PLAN_V1 4.2). So about 1,700 words of prose, or 330 short lines.
  DOC_BYTES = 10240 unless const_defined?(:DOC_BYTES)
  DOC_MAX = 16384 unless const_defined?(:DOC_MAX)
  LINE_COST = 40 unless const_defined?(:LINE_COST)
  FIND_MAX = 30 unless const_defined?(:FIND_MAX)

  LINE_H = 14 unless const_defined?(:LINE_H)
  PAGE_PAD = 4 unless const_defined?(:PAGE_PAD)
  SCROLLBAR_W = 3 unless const_defined?(:SCROLLBAR_W)
  GLYPH_W = 6 unless const_defined?(:GLYPH_W)
  WIDE_W = 12 unless const_defined?(:WIDE_W)

  # One key table per screen (docs/UI.md). In the document the letters type, so these are
  # Tab then the key; in Move (Tab m) they work bare, and the digits are Move's hint bar.
  DOC_KEYS = "Edit|1ENT type|m move|2f find|3g find next;Cursor|h word left|l word right|k page up|j page down|a line start|e line end|[ top|] end;File|s save|o documents|n new|r rename|v slides" unless const_defined?(:DOC_KEYS)
  FILES_KEYS = "Document|1ENT open|2n new|3x delete|r rename" unless const_defined?(:FILES_KEYS)
end
