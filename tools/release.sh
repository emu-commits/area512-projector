#!/bin/sh
# The suite as one zip, laid out as the card is, to unzip at the card's root (docs/INSTALL.md):
#
#   tools/release.sh 1.0.0   -> release/projector-v1.0.0.zip
#
#   Area512_data/home/ai/<app>/   Home, Projector, Agenda, Writer, Calc, Slide (./build.sh)
#   Area512_data/etc/ui.suite     the line that starts on Home: renamed to ui, or added to it
#   INSTALL.md                    docs/INSTALL.md
set -e
cd "$(dirname "$0")/.."
ver=${1:?usage: tools/release.sh <version>}
./build.sh
name=projector-v$ver
stage=build/release/$name
rm -rf build/release && mkdir -p "$stage/Area512_data/home/ai" "$stage/Area512_data/etc" release
for app in home projector agenda writer calc slide; do
    cp -r dist/$app "$stage/Area512_data/home/ai/$app"
done
echo "default=app:/home/ai/home" > "$stage/Area512_data/etc/ui.suite"
cp docs/INSTALL.md "$stage/INSTALL.md"
rm -f release/$name.zip
(cd "$stage" && zip -qr -X "../../../release/$name.zip" Area512_data INSTALL.md)
echo "release/$name.zip: $(unzip -l release/$name.zip | tail -1)"
