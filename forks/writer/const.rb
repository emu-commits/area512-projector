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
  # The biggest document, in bytes. It's held twice while it opens and saves, in the VM's
  # 120 KB with the app's own code, and running out restarts the device. On the Cardputer
  # firmware 16 KB opened, took an edit and saved, and 20 KB ran out opening (PLAN_V1 4.2).
  DOC_MAX = 12288 unless const_defined?(:DOC_MAX)
  FIND_MAX = 30 unless const_defined?(:FIND_MAX)

  LINE_H = 14 unless const_defined?(:LINE_H)
  PAGE_PAD = 4 unless const_defined?(:PAGE_PAD)
  SCROLLBAR_W = 3 unless const_defined?(:SCROLLBAR_W)
  GLYPH_W = 6 unless const_defined?(:GLYPH_W)
  WIDE_W = 12 unless const_defined?(:WIDE_W)

  # One key table per screen (docs/UI.md). In the document the letters type, so these are
  # Tab then the key; in Move (Tab m) they work bare, and the digits are Move's hint bar.
  DOC_KEYS = "Edit|1ENT type|m move|2f find|3g find next;Cursor|h word left|l word right|k page up|j page down|a line start|e line end|[ top|] end;File|s save|o documents|n new|r rename" unless const_defined?(:DOC_KEYS)
  FILES_KEYS = "Document|1ENT open|2n new|3x delete|r rename" unless const_defined?(:FILES_KEYS)
end
