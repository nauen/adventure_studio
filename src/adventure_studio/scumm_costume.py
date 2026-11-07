"""Native SCUMM-v6 COST authoring: ScummC .scost plus indexed frame bitmaps.

No runtime animation is simulated here. COUNT is a literal native costume
command; a later script must observe the actor animation counter explicitly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .scumm_assets import _indexed_bmp

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_DIRECTIONS = frozenset(("N", "E", "S", "W"))


@dataclass(frozen=True)
class CostumeFrame:
    id: str
    width: int
    height: int
    pixels: bytes
    offset_x: int = 0
    offset_y: int = 0


@dataclass(frozen=True)
class CostumeDirection:
    direction: str
    commands: tuple[str, ...]  # frame IDs, or native COUNT/SHOW/HIDE/NOP
    loop: bool = True


@dataclass(frozen=True)
class CostumeAnimation:
    name: str
    directions: tuple[CostumeDirection, ...]
    index: int | None = None  # native anim ID; if specified must be divisible by 4


@dataclass(frozen=True)
class CostumeAsset:
    name: str
    palette: tuple[tuple[int, int, int], ...]
    frames: tuple[CostumeFrame, ...]
    animations: tuple[CostumeAnimation, ...]
    palette_first: int = 16
    palette_last: int = 47


def validate_costume(costume: CostumeAsset) -> None:
    if not _IDENTIFIER.fullmatch(costume.name):
        raise ValueError("Invalid native costume name")
    if (type(costume.palette_first) is not int or type(costume.palette_last) is not int
        or not 0 <= costume.palette_first <= costume.palette_last <= 255):
        raise ValueError("Invalid native costume palette range")
    if len(costume.palette) <= costume.palette_last or len(costume.palette) > 256 or any(
        len(rgb) != 3 or any(type(channel) is not int or not 0 <= channel <= 255 for channel in rgb)
        for rgb in costume.palette
    ):
        raise ValueError("Invalid costume BMP palette")
    if not costume.frames or not costume.animations:
        raise ValueError("A native costume requires frames and animations")
    frame_ids = set()
    for frame in costume.frames:
        if not _IDENTIFIER.fullmatch(frame.id) or frame.id in frame_ids:
            raise ValueError("Duplicate or invalid costume frame ID")
        frame_ids.add(frame.id)
        if (type(frame.width) is not int or type(frame.height) is not int
            or not 1 <= frame.width <= 255 or not 1 <= frame.height <= 255
            or len(frame.pixels) != frame.width * frame.height
            or type(frame.offset_x) is not int or type(frame.offset_y) is not int
            or not -32768 <= frame.offset_x <= 32767
            or not -32768 <= frame.offset_y <= 32767):
            raise ValueError("Invalid costume frame dimensions, pixels or origin")
        if any(pixel < costume.palette_first or pixel > costume.palette_last
               for pixel in frame.pixels):
            raise ValueError("Costume frame uses a palette entry outside the native COST range")
    animation_names = set()
    animation_indices = set()
    for anim in costume.animations:
        if not _IDENTIFIER.fullmatch(anim.name) or anim.name in animation_names:
            raise ValueError("Duplicate or invalid native animation name")
        animation_names.add(anim.name)
        if anim.index is not None:
            if (type(anim.index) is not int or not 0 <= anim.index <= 252
                    or anim.index % 4 or anim.index in animation_indices):
                raise ValueError("Explicit COST animation ID must be unique and aligned to four")
            animation_indices.add(anim.index)
        if not anim.directions:
            raise ValueError("Animation requires at least one direction")
        seen_directions = set()
        for direction in anim.directions:
            if direction.direction not in _DIRECTIONS or direction.direction in seen_directions:
                raise ValueError("Duplicate or invalid costume direction")
            seen_directions.add(direction.direction)
            if type(direction.loop) is not bool or not direction.commands:
                raise ValueError("Animation direction requires commands and a Boolean loop")
            if any(cmd not in frame_ids and cmd not in ("COUNT", "SHOW", "HIDE", "NOP")
                   for cmd in direction.commands):
                raise ValueError("Unknown native costume animation command or frame")


def costume_source(costume: CostumeAsset) -> str:
    validate_costume(costume)
    lines = [f"palette([{costume.palette_first}-{costume.palette_last}]);", ""]
    for frame in costume.frames:
        lines.extend((f"picture {frame.id} = {{",
                      f'    path = "{costume.name}_{frame.id}.bmp",',
                      f"    position = {{ {frame.offset_x}, {frame.offset_y} }}",
                      "};", ""))
    lines.extend(("limb body;", ""))
    for anim in costume.animations:
        suffix = f" @ {anim.index}" if anim.index is not None else ""
        lines.append(f"anim {anim.name}{suffix} = {{")
        for direction in anim.directions:
            commands = ", ".join(direction.commands)
            loop_suffix = "" if direction.loop else " !LOOP"
            lines.append(f"    {direction.direction} = {{ body({commands}){loop_suffix} }};")
        lines.extend(("};", ""))
    return "\n".join(lines)


def write_costume_sources(costume: CostumeAsset, destination: Path) -> tuple[Path, tuple[Path, ...]]:
    """Produce deterministic compiler inputs; does not claim a linked game."""
    source = costume_source(costume)
    destination.mkdir(parents=True, exist_ok=True)
    script = destination / f"{costume.name}.scost"
    script.write_text(source, encoding="utf-8")
    images = []
    for frame in costume.frames:
        path = destination / f"{costume.name}_{frame.id}.bmp"
        path.write_bytes(_indexed_bmp(frame.width, frame.height, frame.pixels, costume.palette))
        images.append(path)
    return script, tuple(images)
