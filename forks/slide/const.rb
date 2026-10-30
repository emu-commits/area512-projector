require 'area512-widget'
require 'machine'
require 'io/console'
require 'area512-sprite'
require 'area512-sdfat'

# Slide: AREA512's Slide, forked (UPSTREAM.md) onto the suite's grammar (docs/UI.md).
# SuiteApp is lib/ruby/ui.rb, first in main.manifest, and lib/ruby/docs.rb (the list of
# documents, recent.txt, Home's requests, switching), second.
#
# A deck is one of Writer's documents: its pages are split by a line of "---". Slide reads
# them from Writer's folder and never writes there but to delete or rename one, as Writer's
# own list does; its recent.txt and place.txt are in its own folder.
#
# Constants live under the app class so they never collide with other apps in the shared
# sandbox VM (each run keeps a global const table), guarded for re-runs of this same app.
class Slide < SuiteApp
  DECK_DIR = "/data/writer" unless const_defined?(:DECK_DIR)
  DATA_DIR = "/data/slide" unless const_defined?(:DATA_DIR)
  # Slide's pages before the fork: <number>.md in its own folder, joined once as "slides"
  OLD_DIR = "/home/tool/slide" unless const_defined?(:OLD_DIR)
  # Writer's documents stop at 10 KB (forks/writer/const.rb), and so do decks: one copied in
  # by hand may be bigger. Slide holds the text and the rows of a chunk or two; on the
  # Cardputer build a 12 KB page with no "---" ran out paging down, and 10 KB went to the end.
  DECK_MAX = 10240 unless const_defined?(:DECK_MAX)
  # a page is laid out this many bytes of whole lines at a time (storage.rb)
  CHUNK = 1024 unless const_defined?(:CHUNK)
  # a row's flags byte (markdown.rb): 1 its line's first row, 2 inside `inline code`
  FLAGS = ["0", "1", "2", "3"] unless const_defined?(:FLAGS)

  # One key table per screen (docs/UI.md)
  # The arrows turn and scroll (Enter, Space and Backspace read on, unlisted: a clicker's keys)
  SHOW_KEYS = "Page|1RIGHT next|2LEFT back|3DOWN scroll|4UP scroll up|[ first|] last;Deck|e edit|o decks" unless const_defined?(:SHOW_KEYS)
  FILES_KEYS = "Deck|1ENT show|2e edit|3n new|x delete|r rename" unless const_defined?(:FILES_KEYS)
  # TERM512's list: how a deck works; "!" picks a line out (docs.rb guide_lines)
  GUIDE = ["A deck is a Writer document.", "A line holding only", "!---", "starts the next slide.", "",
           "e edits the deck in Writer.", "In Writer, Tab v shows it.", "",
           "Slide draws the markdown:", "!# title  ## heading", "!- list  `code`  ``` block",
           "The arrows turn and scroll."] unless const_defined?(:GUIDE)
end
