HOME - the AREA512 suite's first screen

A row of app icons, and under the selected icon, that
app's files, newest first.

  , / or h/l   app            ; . or j/k   file
  ENT          open the app, or the file picked
  n            a new file in that app
  x            delete the file picked (the app does it,
               after Home asks, then comes back here)
  1-9          jump to an app (its number in Tab > Apps)
  Tab          menu: Apps, App, Help
  Esc          the filer

Extras lists every other app on the card: games, Theme,
Paint. Files, at the end, goes to the filer.

Home finds the apps where they're installed, each time it
starts, and writes /data/area512/apps.txt: the list every
app's Tab > Apps menu reads. Esc from an app's top screen
comes back here, to the icon you left from.

To start on Home, add this line to /etc/ui:
  default=app:/home/ai/home
