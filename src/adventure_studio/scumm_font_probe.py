"""Verify that ScummC can compile every required glyph into a CHAR resource."""

from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

from .localization import charset_plan, parse_catalog
from .scumm_font import render_scumm_font_bitmap


def verify_char_resource(path: Path, needed_codes: set[int]) -> dict:
    data = path.read_bytes()
    if len(data) < 40 or data[:4] != b"CHAR":
        raise ValueError("ScummC did not create a valid CHAR block")
    total = int.from_bytes(data[4:8], "big")
    if total != len(data):
        raise ValueError("Invalid CHAR resource length")
    count = int.from_bytes(data[31:33], "little")
    if not needed_codes or max(needed_codes) >= count:
        raise ValueError("Required glyph index is missing from CHAR")
    for code in sorted(needed_codes):
        position = 33 + 4 * code
        if position + 4 > len(data) or struct.unpack_from("<I", data, position)[0] == 0:
            raise ValueError(f"Missing compiled glyph at SCUMM byte {code}")
    return {"resource_bytes": len(data), "charset_slots": count,
            "required_glyphs": len(needed_codes), "all_slots_present": True}


def build_probe(catalog_path: Path, latin_font: Path, cjk_font: Path,
                scummc_char: Path, output: Path) -> dict:
    catalog = parse_catalog(catalog_path.read_text(encoding="utf-8"))
    plan = charset_plan(catalog)
    output.mkdir(parents=True, exist_ok=True)
    bitmap = output / "multilingual-font.bmp"
    resource = output / "multilingual-font.char"
    glyphs = render_scumm_font_bitmap(catalog, latin_font, cjk_font, bitmap)
    subprocess.run([str(scummc_char), "-ibmp", str(bitmap), "-ochar", str(resource)],
                   check=True, timeout=90)
    report = verify_char_resource(resource, set(glyphs))
    report.update({"languages": list(catalog.languages),
                   "glyph_map": {f"{code:02X}": glyph for code, glyph in sorted(glyphs.items())},
                   "runtime_rendering_verified": False})
    (output / "font-probe-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    if len(sys.argv) != 6:
        print("Usage: python -m adventure_studio.scumm_font_probe CATALOG LATIN_FONT CJK_FONT SCUMMC_CHAR OUTPUT")
        return 2
    report = build_probe(*(Path(value) for value in sys.argv[1:]))
    print(json.dumps({key: value for key, value in report.items() if key != "glyph_map"},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
