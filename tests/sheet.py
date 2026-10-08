# /// script
# dependencies = ["pillow"]
# ///
"""Contact sheet of firmware screenshots: uv run tests/sheet.py DIR name1 name2 ... -> DIR/sheet.png"""
import sys
from PIL import Image
d = sys.argv[1]
names = sys.argv[2:]
ims = [Image.open("{}/projector-{}.png".format(d, n)) for n in names]
w, h = ims[0].size
cols = 3
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (w + 6), rows * (h + 6)), (60, 60, 60))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * (w + 6), (i // cols) * (h + 6)))
sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
sheet.save("{}/sheet.png".format(d))
