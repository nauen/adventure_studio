"""Build ScummC `char -ibmp` input from a verified multilingual glyph plan.

The resulting indexed BMP is not a SCUMM resource until ScummC converts it;
the converter and a real ScummVM screenshot remain separate compatibility gates.
"""

from __future__ import annotations

from pathlib import Path

from .localization import LanguageCatalog, charset_plan


def render_scumm_font_bitmap(catalog: LanguageCatalog, latin_font: Path,
                             cjk_font: Path, output: Path) -> dict[int, str]:
    """Produce an indexed 3-color, bordered BMP for ScummC's `char -ibmp`.

    Explicit cmap inspection prevents the common silent tofu-fallback mistake.
    Every byte position from 0 to the highest used value is represented.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        from fontTools.ttLib import TTFont
    except ImportError as error:
        raise RuntimeError("Font renderer needs Pillow and fonttools") from error

    plan = charset_plan(catalog)
    glyphs = {index: chr(index) for index in range(32, 127)}
    glyphs.update({byte: glyph for glyph, byte in plan.extra_glyphs})
    if len(glyphs) != len(set(glyphs.values())):
        raise ValueError("Glyph mapping is not injective")
    fonts = {}
    coverage = {}
    for label, path in (("latin", latin_font), ("cjk", cjk_font)):
        if not path.is_file():
            raise ValueError(f"Missing {label} font: {path}")
        tt = TTFont(str(path), lazy=True, fontNumber=0)
        try:
            coverage[label] = set().union(*(set(t.cmap) for t in tt["cmap"].tables if t.isUnicode()))
        finally:
            tt.close()
        # The stock SCUMM v6 verb UI has tightly spaced text rows. A 14px
        # bitmap overlaps its neighbours; 9px fits the original text grid.
        fonts[label] = ImageFont.truetype(str(path), 9)
    missing = sorted({glyph for glyph in glyphs.values()
                      if ord(glyph) not in coverage["latin"] | coverage["cjk"]})
    if missing:
        raise ValueError("Font coverage missing: " + ", ".join(f"U+{ord(c):04X}" for c in missing))

    cell_w, cell_h, columns = 14, 15, 16
    # ScummC's char importer scans contiguous palette-last border runs.
    # Leave one background pixel between frames in BOTH directions; otherwise
    # adjacent cells are incorrectly imported as a single giant glyph.
    frame_w, frame_h = cell_w - 1, cell_h - 1
    count = max(glyphs, default=126) + 1
    rows = (count + columns - 1) // columns
    canvas = Image.new("P", (columns * cell_w, rows * cell_h + 2), color=0)
    canvas.putpalette([0, 0, 0, 255, 255, 255, 255, 0, 255])
    draw = ImageDraw.Draw(canvas)
    for code in range(count):
        x, y = (code % columns) * cell_w, (code // columns) * cell_h + 1
        # The imported glyph interior is 11x12 pixels.
        # Top and left guide lines are sufficient: a bottom guide line would
        # be mistaken for a new character by ScummC's row-wise importer.
        draw.line((x, y, x + frame_w - 1, y), fill=2)
        draw.line((x, y, x, y + frame_h - 1), fill=2)
        glyph = glyphs.get(code)
        if glyph is None or glyph == " ":
            continue
        label = "latin" if ord(glyph) in coverage["latin"] else "cjk"
        font = fonts[label]
        box = draw.textbbox((0, 0), glyph, font=font)
        width, height = box[2] - box[0], box[3] - box[1]
        if width > frame_w - 2 or height > frame_h - 2:
            raise ValueError(f"Glyph exceeds SCUMM bitmap cell: U+{ord(glyph):04X}")
        draw.text((x + 1 - box[0], y + 1 - box[1]), glyph, font=font, fill=1)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="BMP")
    return glyphs
