#!/usr/bin/env python3
"""Draw Home's app icons as AREA512 dot images: icons/<name>.a5d, 32x32 (the size the device's
own dot editor, Dot.edit, works on, so they can be redrawn there), plus icons/preview.png.

  tools/icons.py [out_dir]          default: apps/home/icons

.a5d (picoruby-area512-dot, dot_image.c): "A5DI", version 1, width, height, colour count,
the palette as RGB565 little-endian, then 4-bit pixels, two to a byte, high nibble first.
Index 0 is transparent. The palette is the editor's default, so editing on the device keeps it.
"""
import pathlib, struct, sys, zlib

PALETTE = [0x0000, 0xFFFF, 0xFAA8, 0xFE66, 0x3FE0, 0x367F, 0xC61F, 0xFB3F,
           0x0000, 0x8410, 0xFC40, 0x0400, 0x0010, 0x8010, 0x8A22, 0xC618]
CLEAR, WHITE, BLACK, GREY, AMBER, LIGHT = 0, 1, 8, 9, 10, 15
N = 32


class Icon:
    def __init__(self):
        self.p = [[CLEAR] * N for _ in range(N)]

    def dot(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.p[y][x] = c

    def fill(self, x, y, w, h, c):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.dot(i, j, c)

    def box(self, x, y, w, h, c):
        self.fill(x, y, w, 1, c)
        self.fill(x, y + h - 1, w, 1, c)
        self.fill(x, y, 1, h, c)
        self.fill(x + w - 1, y, 1, h, c)

    def a5d(self):
        out = bytearray(b"A5DI" + bytes([1, N, N, len(PALETTE)]))
        for c in PALETTE:
            out += struct.pack("<H", c)
        for row in self.p:
            for i in range(0, N, 2):
                out.append((row[i] << 4) | row[i + 1])
        out += bytes(N * N // 8)            # hitbox: none
        return bytes(out)


def projector():
    # a film frame with a play triangle: play your ideas forward
    ic = Icon()
    ic.fill(3, 6, 26, 20, BLACK)
    ic.box(3, 6, 26, 20, AMBER)
    for y in (8, 12, 16, 20, 23):               # sprocket holes
        ic.fill(5, y, 2, 2, GREY)
        ic.fill(25, y, 2, 2, GREY)
    for i in range(10):                         # triangle, pointing right
        ic.fill(12, 11 + i // 2, i + 1, 1, WHITE)
        ic.fill(12, 20 - i // 2, i + 1, 1, WHITE)
    return ic


def writer():
    # a page with a folded corner and lines of text
    ic = Icon()
    ic.fill(7, 3, 18, 26, WHITE)
    ic.box(7, 3, 18, 26, GREY)
    ic.fill(19, 3, 6, 6, CLEAR)
    for i in range(6):                          # the fold
        ic.fill(19, 3 + i, 1, 1, GREY)
        ic.fill(19 + i, 8, 1, 1, GREY)
        ic.fill(19 + i, 3 + i, 1, 1, GREY)
    for k, y in enumerate((11, 14, 17, 20, 23)):
        ic.fill(10, y, 12 if k != 4 else 7, 1, BLACK)
    ic.fill(10, 6, 7, 2, AMBER)                 # a title
    return ic


def calc():
    # a calculator: a display and a 4x4 grid of keys
    ic = Icon()
    ic.fill(6, 2, 20, 28, BLACK)
    ic.box(6, 2, 20, 28, AMBER)
    ic.fill(9, 5, 14, 6, LIGHT)
    ic.fill(17, 7, 4, 2, BLACK)                 # digits on the display
    ic.fill(12, 7, 3, 2, BLACK)
    for r in range(4):
        for c in range(4):
            col = AMBER if c == 3 else WHITE
            ic.fill(9 + c * 4, 13 + r * 4, 3, 3, col)
    return ic


def agenda():
    # a calendar page: rings, a header band, a grid of days, today marked
    ic = Icon()
    ic.fill(4, 6, 24, 23, WHITE)
    ic.box(4, 6, 24, 23, GREY)
    ic.fill(4, 6, 24, 6, AMBER)
    for x in (9, 21):                           # rings
        ic.fill(x, 3, 2, 6, GREY)
    for r in range(4):
        for c in range(5):
            ic.fill(7 + c * 4, 14 + r * 4, 2, 2, GREY)
    ic.fill(14, 17, 4, 4, AMBER)                # today
    return ic


def slide():
    # a screen on a stand, with a bar chart on it
    ic = Icon()
    ic.fill(3, 4, 26, 18, WHITE)
    ic.box(3, 4, 26, 18, GREY)
    ic.fill(2, 3, 28, 2, AMBER)
    for i, h in enumerate((5, 8, 11)):
        ic.fill(8 + i * 6, 19 - h, 4, h, AMBER if i == 2 else GREY)
    ic.fill(15, 22, 2, 6, GREY)                 # stand
    ic.fill(10, 28, 12, 2, GREY)
    return ic


def extras():
    # four tiles: everything else on the card
    ic = Icon()
    for (x, y, c) in ((4, 4, AMBER), (18, 4, WHITE), (4, 18, WHITE), (18, 18, GREY)):
        ic.fill(x, y, 10, 10, c)
        ic.box(x, y, 10, 10, BLACK if c != GREY else GREY)
    return ic


ICONS = {"projector": projector, "writer": writer, "calc": calc, "agenda": agenda,
         "slide": slide, "extras": extras}


def rgb(c):
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31)


def preview(icons, path, scale=3, bg=(0x18, 0x18, 0x18)):
    # every icon side by side on the dark background, scaled up, as a PNG (no PIL needed)
    pad = 8
    w = len(icons) * (N * scale + pad) + pad
    h = N * scale + 2 * pad
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            col = bg
            k, rx = divmod(x - pad, N * scale + pad)
            ry = y - pad
            if 0 <= k < len(icons) and 0 <= rx < N * scale and 0 <= ry < N * scale:
                c = icons[k].p[ry // scale][rx // scale]
                if c != CLEAR:
                    col = rgb(PALETTE[c])
            row += bytes(col)
        rows.append(bytes(row))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))
    pathlib.Path(path).write_bytes(png)


def main():
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "apps/home/icons")
    out.mkdir(parents=True, exist_ok=True)
    drawn = []
    for name, fn in ICONS.items():
        ic = fn()
        (out / (name + ".a5d")).write_bytes(ic.a5d())
        drawn.append(ic)
    preview(drawn, out / "preview.png")
    print("{} icons in {}".format(len(drawn), out))


if __name__ == "__main__":
    main()
