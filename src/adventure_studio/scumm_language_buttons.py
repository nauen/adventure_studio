"""Opt-in clickable language badges for the SCUMM-v6 room prototype.

The badges are room objects, not a screen-fixed GUI. They are intentionally
experimental and only enabled with an explicit toolchain switch.
"""

from __future__ import annotations

from pathlib import Path

from .localization import LanguageCatalog, validate_catalog


_LETTERS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
}


def button_names(catalog: LanguageCatalog) -> tuple[tuple[str, str, int], ...]:
    validate_catalog(catalog)
    if not (1 <= len(catalog.languages) <= 5):
        raise ValueError("Graphical language selector supports one to five languages")
    return tuple(("Lang" + code.title(), code,
                  int.from_bytes(code.encode("ascii"), "big"))
                 for code in catalog.languages)


def button_sprite(code: str, dark: int, bright: int, selected: bool) -> bytes:
    """Create one 32x16 indexed badge (8-pixel-aligned ScummC sprite)."""
    letters = code.upper()
    if len(letters) != 2 or any(letter not in _LETTERS for letter in letters):
        raise ValueError("Unsupported graphical language code")
    pixels = bytearray([dark] * (32 * 16))
    for y in range(16):
        for x in range(32):
            if x in (0, 31) or y in (0, 15) or (selected and x in (1, 30)):
                pixels[y * 32 + x] = bright
    for index, char in enumerate(letters):
        for y, row in enumerate(_LETTERS[char]):
            for x, active in enumerate(row):
                if active == "1":
                    pixels[(4 + y) * 32 + (7 + index * 11 + x)] = bright
    return bytes(pixels)


def button_room_source(room_name: str, catalog: LanguageCatalog) -> str:
    result = []
    for index, (name, language, code) in enumerate(button_names(catalog)):
        result.extend((
            f"    object {name} {{\n",
            f"        x = {10 + index * 40};\n",
            "        y = 10;\n        w = 32;\n        h = 16;\n",
            f'        name = "{language.upper()}";\n',
            f'        states = {{ {{ 0, 0, "{room_name}{name}.bmp" }}, {{ 0, 0, "{room_name}{name}Active.bmp" }} }};\n',
            "        state = 1;\n",
            "        verb(int vrb, int objA, int objB) {\n",
            "        case WalkTo:\n",
            f"            GameLanguage = {code};\n",
            "            return;\n",
            "        }\n    }\n",
        ))
    return "".join(result)


def button_state_source(catalog: LanguageCatalog, indent: int = 8) -> str:
    padding = " " * indent
    return "".join(
        f"{padding}if (GameLanguage == {code}) setObjectState({name},2);\n"
        f"{padding}else setObjectState({name},1);\n"
        for name, _language, code in button_names(catalog)
    )


def write_button_sprites(room, catalog: LanguageCatalog, directory: Path) -> tuple[Path, ...]:
    """Write each room's indexed badge resources using its existing palette."""
    from .scumm_assets import _indexed_bmp

    if len(room.palette) < 2:
        raise ValueError("Language badges need at least two palette colors")
    values = [sum(color) for color in room.palette]
    dark = min(range(len(values)), key=values.__getitem__)
    bright = max(range(len(values)), key=values.__getitem__)
    if values[dark] == values[bright]:
        raise ValueError("Language badges need contrasting palette colors")
    output = []
    directory.mkdir(parents=True, exist_ok=True)
    for name, language, _code in button_names(catalog):
        for selected, suffix in ((False, ""), (True, "Active")):
            path = directory / f"{room.name}{name}{suffix}.bmp"
            path.write_bytes(_indexed_bmp(32, 16,
                                          button_sprite(language, dark, bright, selected),
                                          room.palette))
            output.append(path)
    return tuple(output)
