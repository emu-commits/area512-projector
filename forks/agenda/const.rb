require 'area512-widget'
require 'machine'
require 'io/console'
require 'area512-sprite'
require 'area512-sdfat'

# Agenda: AREA512's Scheduler, forked (UPSTREAM.md) onto the suite's grammar (docs/UI.md).
# SuiteApp is lib/ruby/ui.rb, first in main.manifest.
class Agenda < SuiteApp
  DATA_DIR = "/data/agenda" unless const_defined?(:DATA_DIR)
  SAVE_FILE = "/data/agenda/agenda.txt" unless const_defined?(:SAVE_FILE)
  # Scheduler's file: read once, when Agenda has none of its own yet
  OLD_FILE = "/data/scheduler.txt" unless const_defined?(:OLD_FILE)
  PLACE_FILE = "/data/agenda/place.txt" unless const_defined?(:PLACE_FILE)
  RECENT_FILE = "/data/agenda/recent.txt" unless const_defined?(:RECENT_FILE)
  TEXT_MAX = 60 unless const_defined?(:TEXT_MAX)

  # One key table per screen (docs/UI.md): menus split by ";", each "Title|item|item", an
  # item "<key> <label>", a digit in front puts it on the hint bar
  MONTH_KEYS = "Day|1ENT day|2n new|3a agenda;Month|[ previous|] next;File|s save" unless const_defined?(:MONTH_KEYS)
  DAY_KEYS = "Event|1ENT edit|2n new|3x delete;Day|a agenda|c calendar;File|s save" unless const_defined?(:DAY_KEYS)
  LIST_KEYS = "Event|1ENT open|2n new|3x delete;View|c calendar;File|s save" unless const_defined?(:LIST_KEYS)

  MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"] unless const_defined?(:MONTHS)
  WDAYS = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"] unless const_defined?(:WDAYS)
end
