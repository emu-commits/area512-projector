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
  # Writer's documents stop at 10 KB (forks/writer/const.rb); one copied in by hand may be
  # bigger. Slide holds the text and one page laid out, so a little more is safe.
  DECK_MAX = 12288 unless const_defined?(:DECK_MAX)

  # One key table per screen (docs/UI.md)
  SHOW_KEYS = "Page|1ENT next|2BS back|j down|k up|[ first|] last;Deck|3e edit|o decks" unless const_defined?(:SHOW_KEYS)
  FILES_KEYS = "Deck|1ENT show|2e edit|3n new|x delete|r rename" unless const_defined?(:FILES_KEYS)
end
