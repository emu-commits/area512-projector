require 'area512-widget'
require 'machine'
require 'io/console'
require 'area512-sprite'
require 'area512-sdfat'

# Calc: AREA512's Calc, forked (UPSTREAM.md) onto the suite's grammar (docs/UI.md).
# SuiteApp is lib/ruby/ui.rb, first in main.manifest, and lib/ruby/docs.rb (the list of
# sheets, recent.txt, Home's requests, switching), second.
#
# Constants live under the app class so they never collide with other apps in the shared
# sandbox VM (each run keeps a global const table), guarded for re-runs of this same app.
class Calc < SuiteApp
  ROWS = 99 unless const_defined?(:ROWS)
  COLS = 26 unless const_defined?(:COLS)
  ROW_H = 13 unless const_defined?(:ROW_H)
  HEAD_W = 18 unless const_defined?(:HEAD_W)
  # column widths in characters: w steps through them; a new column is the second
  WIDTHS = [5, 9, 14, 20] unless const_defined?(:WIDTHS)
  WIDTH = 9 unless const_defined?(:WIDTH)

  DATA_DIR = "/data/calc" unless const_defined?(:DATA_DIR)
  # Calc's one sheet before the fork: copied once, the first time, as "sheet"
  OLD_FILE = "/data/sheet.txt" unless const_defined?(:OLD_FILE)
  # A cell's text, in bytes; the cells a sheet may hold, and its size as a file. The sheet
  # shares the VM's 120 KB with the app's own code, and running out restarts the device
  # (PLAN_V1 4.2). On the TERM512 firmware (AREA512 main, which leaves less of it than
  # v2.7) 300 formulas in 8 KB opened, took edits and saved, and 399 ran out; on the
  # Cardputer (v2.7) 9 KB of text was fine and 9.7 KB ran out (PLAN_V1 4.3).
  TEXT_MAX = 60 unless const_defined?(:TEXT_MAX)
  CELL_MAX = 250 unless const_defined?(:CELL_MAX)
  SHEET_MAX = 6144 unless const_defined?(:SHEET_MAX)
  FIND_MAX = 30 unless const_defined?(:FIND_MAX)

  # One key table per screen (docs/UI.md). On the grid the letters are commands; a digit,
  # = - + ( or Space starts typing into the cell.
  GRID_KEYS = "Cell|1ENT edit|x clear|u undo|g go to|f find;Copy|2c copy|3v paste|4d fill down|r fill right;Sheet|w width|[ to A1|] to end|s save|o sheets|n new" unless const_defined?(:GRID_KEYS)
  FILES_KEYS = "Sheet|1ENT open|2n new|3x delete|r rename" unless const_defined?(:FILES_KEYS)
end
