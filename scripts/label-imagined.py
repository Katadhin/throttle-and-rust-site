#!/usr/bin/env python3
"""Burn an "imagined, not archival" label into a generated track image.

    python3 scripts/label-imagined.py <in.jpg> <out.jpg> [--text "..."]

Why this exists, because it will look like belt-and-braces later and it is not:

The Ghost Tracks register cites its sources. Its art must never be mistaken for
one of them. Ephemera art (an object, a blank program) carries no such risk, and
a drawing carries none either, because nobody mistakes a sketch for evidence. A
photorealistic imagining of a real, named, cited track does carry that risk.

The page caption solves this on the page and nowhere else. An `og:image` gets
scraped into a Facebook or X card with the caption stripped off, under a headline
naming the real track. Screenshots and reposts strip it too. The Forgotten
Racetrack social beat links straight at these pages, so this is the normal path
for these images, not an edge case.

So the label goes in the pixels, which are the part that travels. Markup is
advisory. Pixels are not.

Keep the bar. If a future redesign wants it gone, the honest move is to go back
to drawings or ephemera, not to ship unlabeled invented photographs of real
places under their real names.
"""

import sys
from PIL import Image, ImageDraw, ImageFont

DEFAULT_TEXT = "IMAGINED. NOT AN ARCHIVE PHOTOGRAPH."

INK = (28, 31, 38)
CREAM = (243, 237, 223)

# Bar height as a share of image height, with a floor so small images stay legible.
BAR_RATIO = 0.075
BAR_MIN = 34

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def _font(px):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, px)
        except OSError:
            continue
    return ImageFont.load_default()


def _track(draw, xy, text, font, fill, spacing):
    """Draw letterspaced text. PIL has no tracking, so step glyph by glyph."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + spacing
    return x


def _tracked_width(draw, text, font, spacing):
    return sum(draw.textlength(c, font=font) + spacing for c in text) - spacing


def label(src, dst, text=DEFAULT_TEXT):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    bar = max(BAR_MIN, int(h * BAR_RATIO))

    out = Image.new("RGB", (w, h + bar), INK)
    out.paste(im, (0, 0))
    draw = ImageDraw.Draw(out)

    size = max(9, int(bar * 0.36))
    font = _font(size)
    spacing = max(1.0, size * 0.16)

    # Shrink until it fits the width with margins, rather than letting it clip.
    while _tracked_width(draw, text, font, spacing) > w - bar and size > 8:
        size -= 1
        font = _font(size)
        spacing = max(1.0, size * 0.16)

    tw = _tracked_width(draw, text, font, spacing)
    x = (w - tw) / 2
    y = h + (bar - size) / 2 - size * 0.12
    _track(draw, (x, y), text, font, CREAM, spacing)

    out.save(dst, "JPEG", quality=92, optimize=True, progressive=True)
    return out.size


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    text = DEFAULT_TEXT
    if "--text" in args:
        i = args.index("--text")
        text = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) != 2:
        print(__doc__.strip().splitlines()[2])
        sys.exit(1)
    size = label(args[0], args[1], text)
    print("wrote %s at %dx%d with label: %s" % (args[1], size[0], size[1], text))
