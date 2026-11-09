"""Stage a deterministic multilingual SCUMM font bundle after compiler proof."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from .localization import canonical_catalog_json, parse_catalog
from .scumm_font_probe import build_probe


def build_language_package(catalog_source: str, latin_font: Path, cjk_font: Path,
                           char_tool: Path, resource_directory: Path) -> dict:
    """Build in isolation; publish the complete verified package on success.

    The caller must supply a built ScummC CHAR converter, never an untrusted
    compiler command from the project document.
    """
    catalog = parse_catalog(catalog_source)
    canonical = canonical_catalog_json(catalog)
    if not char_tool.is_file():
        raise ValueError("Missing ScummC char executable")
    with tempfile.TemporaryDirectory(prefix="studio-language-") as temp:
        stage = Path(temp)
        catalog_path = stage / "language-catalog.json"
        catalog_path.write_text(canonical, encoding="utf-8")
        report = build_probe(catalog_path, latin_font, cjk_font, char_tool, stage)
        font_bytes = (stage / "multilingual-font.char").read_bytes()
        manifest = {
            "format_version": 1,
            "languages": list(catalog.languages),
            "catalog_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "char_sha256": hashlib.sha256(font_bytes).hexdigest(),
            "charset_slots": report["charset_slots"],
            "glyph_map": report["glyph_map"],
        }
        (stage / "language-package.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8")
        resource_directory.mkdir(parents=True, exist_ok=True)
        for filename in ("language-catalog.json", "multilingual-font.bmp",
                         "multilingual-font.char", "font-probe-report.json",
                         "language-package.json"):
            shutil.copyfile(stage / filename, resource_directory / filename)
    return manifest


def main() -> int:
    if len(sys.argv) != 6:
        print("Usage: python -m adventure_studio.scumm_language_package CATALOG LATIN_FONT CJK_FONT SCUMMC_CHAR RESOURCES")
        return 2
    catalog_path, latin, cjk, converter, resources = map(Path, sys.argv[1:])
    result = build_language_package(catalog_path.read_text(encoding="utf-8"),
                                    latin, cjk, converter, resources)
    print(json.dumps({key: value for key, value in result.items() if key != "glyph_map"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
