"""Deterministic 8-bit SCUMM source-asset preparation (not a linked game)."""

from __future__ import annotations

import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from .targets import RoomGeometry, validate_geometry

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RoomHotspot:
    id: str
    label: str
    description: str
    x: int
    y: int
    width: int
    height: int
    pickup: bool = False


@dataclass(frozen=True)
class RoomAsset:
    name: str
    geometry: RoomGeometry
    pixels: bytes
    palette: tuple[tuple[int, int, int], ...]
    hotspots: tuple[RoomHotspot, ...] = ()


def _scumm_string(value: str) -> str:
    """Return a deliberately restricted ScummC string literal."""
    if not value or len(value) > 160 or any(ord(c) < 32 or ord(c) > 126 or c in '\\"' for c in value):
        raise ValueError("Unsupported SCUMM text character")
    return f'"{value}"'


def _validate(room: RoomAsset) -> None:
    validate_geometry(room.geometry)
    if not _IDENTIFIER.fullmatch(room.name):
        raise ValueError("Invalid SCUMM room identifier")
    width = room.geometry.room_width
    height = room.geometry.room_height
    if width % 8:
        raise ValueError("Experimental strip exporter requires width divisible by eight")
    if len(room.pixels) != width * height:
        raise ValueError("Pixel buffer length mismatch")
    if not (1 <= len(room.palette) <= 256):
        raise ValueError("Indexed palette must have between 1 and 256 colors")
    if any(len(rgb) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in rgb)
           for rgb in room.palette):
        raise ValueError("Palette contains invalid RGB values")
    if room.pixels and max(room.pixels) >= len(room.palette):
        raise ValueError("Pixels reference missing palette entries")
    ids: set[str] = set()
    for hotspot in room.hotspots:
        if not _IDENTIFIER.fullmatch(hotspot.id) or hotspot.id in ids:
            raise ValueError("Invalid or duplicated hotspot identifier")
        ids.add(hotspot.id)
        _scumm_string(hotspot.label)
        _scumm_string(hotspot.description)
        if any(type(v) is not int for v in (hotspot.x, hotspot.y, hotspot.width, hotspot.height)):
            raise ValueError("Hotspot coordinates must be integers")
        if (hotspot.x < 0 or hotspot.y < 0 or hotspot.width <= 0 or hotspot.height <= 0
                or hotspot.x + hotspot.width > width or hotspot.y + hotspot.height > height):
            raise ValueError("Hotspot outside room bounds")


def indexed_bmp(room: RoomAsset) -> bytes:
    """Emit an uncompressed bottom-up Windows BMP with 8-bit indexed pixels."""
    _validate(room)
    width, height = room.geometry.room_width, room.geometry.room_height
    stride = (width + 3) & ~3
    pixel_data = b"".join(room.pixels[y * width:(y + 1) * width] + b"\x00" * (stride - width)
                          for y in range(height - 1, -1, -1))
    palette_data = b"".join(bytes((b, g, r, 0)) for r, g, b in room.palette)
    offset = 14 + 40 + len(palette_data)
    file_size = offset + len(pixel_data)
    header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, offset)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 8, 0, len(pixel_data),
                       2835, 2835, len(room.palette), 0)
    return header + info + palette_data + pixel_data


def scummc_room_source(room: RoomAsset) -> str:
    _validate(room)
    parts = ["#include <scummVars6.s>\n"]
    if room.hotspots:
        # The existing official example supplies Pickable/LookAt, egoSay and
        # pickupObject. This header must eventually be replaced by our own.
        parts.append('#include "common.sch"\n')
    parts.append(f'\nroom {room.name} {{\n    image = "{room.name}.bmp";\n')
    for hotspot in room.hotspots:
        parts.extend([
            f"    object {hotspot.id} {{\n",
            f"        x = {hotspot.x};\n        y = {hotspot.y};\n",
            f"        w = {hotspot.width};\n        h = {hotspot.height};\n",
            f"        name = {_scumm_string(hotspot.label)};\n",
            "        verb(int vrb, int objA, int objB) {\n",
            f"        case LookAt:\n            egoSay({_scumm_string(hotspot.description)});\n            return;\n",
        ])
        if hotspot.pickup:
            parts.extend(["        case PickUp:\n", "            pickupObject(objA,VAR_ROOM);\n",
                          "            return;\n"])
        parts.append("        }\n    }\n")
    if room.hotspots:
        parts.extend([
            "    local script entry() {\n",
            "        setCurrentActor(VAR_EGO);\n",
            f"        putActorAt(VAR_EGO, 60, 100, {room.name});\n",
            "        setActorIgnoreBoxes();\n",
            "        cameraFollowActor(VAR_EGO);\n",
            "        ResRoom::showVerbs(1);\n",
            "        ResRoom::showCursor();\n",
            "    }\n",
        ])
    parts.append("}\n")
    return "".join(parts)


def write_room_sources(room: RoomAsset, directory: Path) -> tuple[Path, Path]:
    """Write independent ScummC room inputs, never claim a linked game."""
    binary = indexed_bmp(room)
    source = scummc_room_source(room)
    directory.mkdir(parents=True, exist_ok=True)
    bmp = directory / f"{room.name}.bmp"
    scc = directory / f"{room.name}.scc"
    bmp.write_bytes(binary)
    scc.write_text(source, encoding="utf-8")
    return bmp, scc


def scrolling_fixture() -> RoomAsset:
    """A synthetic two-screen-wide room with distinct left/right regions."""
    width, height = 640, 200
    pixels = bytes(1 if y >= 150 else (2 if x >= 320 else 0)
                   for y in range(height) for x in range(width))
    return RoomAsset("Harbor", RoomGeometry(width, height, 320, 200), pixels,
                     ((70, 130, 190), (95, 60, 35), (240, 175, 95)),
                     (RoomHotspot("Key", "the key", "A rusty key.", 355, 100, 16, 12, True),))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m adventure_studio.scumm_assets OUTPUT_DIRECTORY")
        return 2
    for path in write_room_sources(scrolling_fixture(), Path(sys.argv[1])):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
