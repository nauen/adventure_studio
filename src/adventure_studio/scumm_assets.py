"""Deterministic 8-bit SCUMM source-asset preparation (not a linked game)."""

from __future__ import annotations

import json
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
    sprite_pixels: bytes | None = None
    open_sprite_pixels: bytes | None = None
    exit_destination: str | None = None


@dataclass(frozen=True)
class UseRule:
    """Use an inventory item on a room hotspot; no arbitrary script payload."""
    item_id: str
    target_id: str
    response: str
    hide_target: bool = False
    destination_room: str | None = None
    open_target: bool = False
    requires_inventory: tuple[str, ...] = ()


@dataclass(frozen=True)
class CombineRule:
    """Consume two owned pickups to create one initially hidden inventory item."""
    first_id: str
    second_id: str
    result_id: str
    response: str


@dataclass(frozen=True)
class RoomAsset:
    name: str
    geometry: RoomGeometry
    pixels: bytes
    palette: tuple[tuple[int, int, int], ...]
    hotspots: tuple[RoomHotspot, ...] = ()
    demo_walk_to_x: int | None = None
    use_rules: tuple[UseRule, ...] = ()
    goal_text: str | None = None
    combine_rules: tuple[CombineRule, ...] = ()


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
    if room.demo_walk_to_x is not None and (
        type(room.demo_walk_to_x) is not int
        or not 0 <= room.demo_walk_to_x < width
    ):
        raise ValueError("Demo walk target outside room bounds")
    if room.goal_text is not None:
        _scumm_string(room.goal_text)
    ids: set[str] = set()
    pickups: set[str] = set()
    for hotspot in room.hotspots:
        if not _IDENTIFIER.fullmatch(hotspot.id) or hotspot.id in ids:
            raise ValueError("Invalid or duplicated hotspot identifier")
        ids.add(hotspot.id)
        if hotspot.pickup:
            pickups.add(hotspot.id)
        _scumm_string(hotspot.label)
        _scumm_string(hotspot.description)
        if any(type(v) is not int for v in (hotspot.x, hotspot.y, hotspot.width, hotspot.height)):
            raise ValueError("Hotspot coordinates must be integers")
        if (hotspot.x < 0 or hotspot.y < 0 or hotspot.width <= 0 or hotspot.height <= 0
                or hotspot.x + hotspot.width > width or hotspot.y + hotspot.height > height):
            raise ValueError("Hotspot outside room bounds")
        if hotspot.sprite_pixels is not None:
            if hotspot.width % 8 or hotspot.height % 8:
                raise ValueError("SCUMM sprite dimensions must be multiples of eight")
            if hotspot.pickup and (hotspot.width > 40 or hotspot.height > 16):
                raise ValueError("Inventory icon sprite exceeds fixed 40x16 GUI slot")
            if len(hotspot.sprite_pixels) != hotspot.width * hotspot.height:
                raise ValueError("Hotspot sprite pixel buffer length mismatch")
            if hotspot.sprite_pixels and max(hotspot.sprite_pixels) >= len(room.palette):
                raise ValueError("Hotspot sprite references missing palette entries")
        if hotspot.open_sprite_pixels is not None:
            if hotspot.sprite_pixels is None or len(hotspot.open_sprite_pixels) != hotspot.width * hotspot.height:
                raise ValueError("Open sprite dimensions do not match closed sprite")
            if max(hotspot.open_sprite_pixels) >= len(room.palette):
                raise ValueError("Open sprite references missing palette entries")
        if hotspot.exit_destination is not None:
            if not _IDENTIFIER.fullmatch(hotspot.exit_destination) or hotspot.exit_destination == room.name:
                raise ValueError("Invalid exit destination room")
    targets: set[str] = set()
    for rule in room.use_rules:
        if rule.item_id not in pickups or rule.target_id not in ids or rule.item_id == rule.target_id:
            raise ValueError("Use rule must connect an inventory pickup to another room hotspot")
        if rule.target_id in targets:
            raise ValueError("Multiple use rules for the same target are not yet supported")
        targets.add(rule.target_id)
        _scumm_string(rule.response)
        if rule.destination_room is not None and (
            not _IDENTIFIER.fullmatch(rule.destination_room) or rule.destination_room == room.name
        ):
            raise ValueError("Invalid destination room in use rule")
        if rule.open_target and rule.hide_target:
            raise ValueError("Use rule cannot hide and open the same target")
        if rule.open_target and next(h for h in room.hotspots if h.id == rule.target_id).open_sprite_pixels is None:
            raise ValueError("Use rule open target needs an open-state sprite")
        if len(set(rule.requires_inventory)) != len(rule.requires_inventory):
            raise ValueError("Duplicate inventory requirements")
        if rule.item_id in rule.requires_inventory or any(item not in pickups for item in rule.requires_inventory):
            raise ValueError("Use rule inventory requirements must reference distinct pickup items")
    results: set[str] = set()
    for rule in room.combine_rules:
        if (len({rule.first_id, rule.second_id, rule.result_id}) != 3
                or any(item not in pickups for item in (rule.first_id, rule.second_id, rule.result_id))):
            raise ValueError("Combination must reference three distinct room inventory objects")
        if rule.result_id in results or rule.second_id in targets:
            raise ValueError("Ambiguous combination result or target")
        results.add(rule.result_id)
        _scumm_string(rule.response)
    if any(rule.first_id in results or rule.second_id in results for rule in room.combine_rules):
        raise ValueError("Chained combinations are not supported by the bounded SCUMM adapter")


def _indexed_bmp(width: int, height: int, pixels: bytes, palette: tuple[tuple[int, int, int], ...]) -> bytes:
    """Encode validated 8-bit indexed pixels in a bottom-up Windows BMP."""
    stride = (width + 3) & ~3
    pixel_data = b"".join(pixels[y * width:(y + 1) * width] + b"\x00" * (stride - width)
                          for y in range(height - 1, -1, -1))
    palette_data = b"".join(bytes((b, g, r, 0)) for r, g, b in palette)
    offset = 14 + 40 + len(palette_data)
    file_size = offset + len(pixel_data)
    header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, offset)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 8, 0, len(pixel_data),
                       2835, 2835, len(palette), 0)
    return header + info + palette_data + pixel_data


def indexed_bmp(room: RoomAsset) -> bytes:
    """Emit an uncompressed bottom-up Windows BMP with 8-bit indexed pixels."""
    _validate(room)
    return _indexed_bmp(room.geometry.room_width, room.geometry.room_height, room.pixels, room.palette)


def scummc_room_source(room: RoomAsset) -> str:
    _validate(room)
    # The external test bootstrap provides verbs, actor and UI. A generated
    # room always owns its own entry script, even when it has no hotspots.
    parts = ["#include <scummVars6.s>\n", '#include "common.sch"\n']
    destinations = ({r.destination_room for r in room.use_rules if r.destination_room}
                    | {h.exit_destination for h in room.hotspots if h.exit_destination})
    for destination in sorted(destinations):
        parts.append(f"room {destination};\n")
    parts.append(f'\nroom {room.name} {{\n    image = "{room.name}.bmp";\n')
    hidden = {rule.result_id for rule in room.combine_rules}
    # ScummC resolves object symbols as it parses each script body. Explicit
    # forward declarations keep the generated helper independent of object
    # layout order (the complete object definitions follow below).
    for item_id in sorted({item for rule in room.combine_rules
                           for item in (rule.first_id, rule.second_id, rule.result_id)}):
        parts.append(f"    object {item_id};\n")
    for index, rule in enumerate(room.combine_rules):
        parts.extend([
            f"    script combine_{index}() {{\n",
            f"        egoSay({_scumm_string(rule.response)});\n",
            f"        setObjectOwner({rule.first_id}, 0);\n",
            f"        setObjectOwner({rule.second_id}, 0);\n",
            f"        pickupObject({rule.result_id}, VAR_ROOM);\n",
            f"        setObjectState({rule.result_id}, 1);\n",
            "    }\n",
        ])
    for hotspot in room.hotspots:
        parts.extend([
            f"    object {hotspot.id} {{\n",
            f"        x = {hotspot.x};\n        y = {hotspot.y};\n",
            f"        w = {hotspot.width};\n        h = {hotspot.height};\n",
            f"        name = {_scumm_string(hotspot.label)};\n",
        ])
        if hotspot.sprite_pixels is not None:
            if hotspot.open_sprite_pixels is None:
                parts.append(f'        states = {{ {{ 0, 0, "{hotspot.id}.bmp" }} }};\n')
            else:
                parts.append(f'        states = {{ {{ 0, 0, "{hotspot.id}.bmp" }}, {{ 0, 0, "{hotspot.id}Open.bmp" }} }};\n')
            parts.append("        state = 0;\n" if hotspot.id in hidden else "        state = 1;\n")
        if hotspot.pickup:
            parts.append("        class = { Pickable };\n")
        parts.extend([
            "        verb(int vrb, int objA, int objB) {\n",
            f"        case LookAt:\n            egoSay({_scumm_string(hotspot.description)});\n            return;\n",
        ])
        if hotspot.exit_destination is not None:
            parts.append("        case WalkTo:\n")
            if hotspot.open_sprite_pixels is not None:
                parts.extend(["            if(getObjectState(objA) == 2) {\n",
                              f"                startRoom({hotspot.exit_destination});\n",
                              "            } else {\n",
                              '                egoSay("The door is locked.");\n',
                              "            }\n"])
            else:
                parts.append(f"            startRoom({hotspot.exit_destination});\n")
            parts.append("            return;\n")
        if hotspot.pickup:
            if (any(rule.item_id == hotspot.id for rule in room.use_rules)
                    or any(rule.first_id == hotspot.id for rule in room.combine_rules)):
                parts.extend(["        case Preposition:\n",
                              '            sntcPrepo[0] = "with";\n',
                              "            return;\n"])
            parts.extend(["        case PickUp:\n", "            pickupObject(objA,VAR_ROOM);\n",
                          "            setObjectState(objA,0);\n",
                          "            return;\n"])
            if hotspot.sprite_pixels is not None:
                parts.extend(["        case Icon:\n",
                              f"            startScript2(vrb,[ResRoom::{hotspot.id}Icon,objA,objB]);\n",
                              "            return;\n"])
        for rule in room.use_rules:
            if rule.target_id == hotspot.id:
                requirements = "".join(
                    f" && getObjectOwner({item}) == VAR_EGO" for item in rule.requires_inventory
                )
                parts.extend([
                    "        case Use:\n",
                    f"            if(objB == {rule.item_id}{requirements}) {{\n",
                    f"                egoSay({_scumm_string(rule.response)});\n",
                ])
                if rule.hide_target:
                    parts.append("                setObjectState(objA,0);\n")
                if rule.open_target:
                    parts.append("                setObjectState(objA,2);\n")
                if rule.destination_room:
                    parts.append(f"                startRoom({rule.destination_room});\n")
                parts.extend(["                return;\n", "            }\n", "            return;\n"])
        for index, rule in enumerate(room.combine_rules):
            if rule.second_id == hotspot.id:
                parts.extend([
                    "        case Use:\n",
                    f"            if(objB == {rule.first_id} && getObjectOwner({rule.first_id}) == VAR_EGO",
                    f" && getObjectOwner({rule.second_id}) == VAR_EGO) {{\n",
                    f"                combine_{index}();\n",
                    "                return;\n",
                    "            }\n            return;\n",
                ])
        parts.append("        }\n    }\n")
    parts.extend([
        "    local script entry() {\n",
        "        setCurrentActor(VAR_EGO);\n",
        f"        putActorAt(VAR_EGO, 60, 100, {room.name});\n",
        "        setActorIgnoreBoxes();\n",
        "        setActorStanding();\n",
        "        cameraFollowActor(VAR_EGO);\n",
        "        ResRoom::showVerbs(1);\n",
        "        ResRoom::showCursor();\n",
    ])
    if room.demo_walk_to_x is not None:
        parts.append(f"        walkActorTo(VAR_EGO, {room.demo_walk_to_x}, 100);\n")
    if room.goal_text is not None:
        parts.append(f"        egoSay({_scumm_string(room.goal_text)});\n")
    parts.append("    }\n")
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
    for hotspot in room.hotspots:
        if hotspot.sprite_pixels is not None:
            (directory / f"{hotspot.id}.bmp").write_bytes(
                _indexed_bmp(hotspot.width, hotspot.height, hotspot.sprite_pixels, room.palette)
            )
            if hotspot.open_sprite_pixels is not None:
                (directory / f"{hotspot.id}Open.bmp").write_bytes(
                    _indexed_bmp(hotspot.width, hotspot.height, hotspot.open_sprite_pixels, room.palette)
                )
            if hotspot.pickup:
                # The inherited SCUMM verb UI allocates 40x16 pixels per item.
                # Use the same source sprite, centered on a GUI-blue backdrop.
                icon_width, icon_height = 40, 16
                x_offset = (icon_width - hotspot.width) // 2
                icon_pixels = bytearray(icon_width * icon_height)
                for y in range(hotspot.height):
                    start = y * icon_width + x_offset
                    icon_pixels[start:start + hotspot.width] = hotspot.sprite_pixels[y * hotspot.width:(y + 1) * hotspot.width]
                (directory / f"Inv_{hotspot.id}.bmp").write_bytes(
                    _indexed_bmp(icon_width, icon_height, bytes(icon_pixels), room.palette)
                )
    return bmp, scc


def write_game_sources(rooms: tuple[RoomAsset, ...], directory: Path) -> tuple[tuple[Path, Path], ...]:
    """Validate all destinations before writing any linked-room source files."""
    if not rooms:
        raise ValueError("A game must contain at least one room")
    names = [room.name for room in rooms]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate room name")
    for room in rooms:
        _validate(room)
        for rule in room.use_rules:
            if rule.destination_room is not None and rule.destination_room not in names:
                raise ValueError(f"Unknown destination room: {rule.destination_room}")
        for hotspot in room.hotspots:
            if hotspot.exit_destination is not None and hotspot.exit_destination not in names:
                raise ValueError(f"Unknown exit destination room: {hotspot.exit_destination}")
    if sum(room.goal_text is not None for room in rooms) != 1:
        raise ValueError("A game needs exactly one goal room")
    pickup_ids = [h.id for room in rooms for h in room.hotspots if h.pickup]
    if len(pickup_ids) != len(set(pickup_ids)):
        raise ValueError("Duplicate global inventory identifier")
    generated = tuple(write_room_sources(room, directory) for room in rooms)
    goal_room = next(room for room in rooms if room.goal_text is not None)
    # Synthetic CI fixture only: the goal room fills its background uniformly,
    # so the known screen probe color demonstrates the actual destination.
    probe_rgb = goal_room.palette[goal_room.pixels[0]]
    # Fixture-only runtime assertions: every additional inventory prerequisite
    # must be acquired before the use rule can open its target. The palette
    # colors identify sprites in screenshots without knowing story item names.
    gates = []
    fixture_combinations = []
    fixture_route = []
    for room in rooms:
        pickups = {hotspot.id: hotspot for hotspot in room.hotspots if hotspot.pickup}
        for rule in room.combine_rules:
            fixture_combinations.append({"room_id": room.name,
                "ingredients": [{"item_id": item_id, "rgb": list(room.palette[pickups[item_id].sprite_pixels[0]])}
                                for item_id in (rule.first_id, rule.second_id)],
                "result": {"item_id": rule.result_id,
                           "rgb": list(room.palette[pickups[rule.result_id].sprite_pixels[0]])}})
        for rule in room.use_rules:
            source = pickups[rule.item_id]
            assert source.sprite_pixels is not None
            destination = next(h.exit_destination for h in room.hotspots if h.id == rule.target_id)
            fixture_route.append({"room_id": room.name, "item_id": rule.item_id,
                                  "rgb": list(room.palette[source.sprite_pixels[0]]),
                                  "next_room_id": destination})
            for item_id in rule.requires_inventory:
                hotspot = pickups[item_id]
                assert hotspot.sprite_pixels is not None
                color_index = hotspot.sprite_pixels[0]
                gates.append({"item_id": item_id, "rgb": list(room.palette[color_index])})
    (directory / "game-goal.json").write_text(
        json.dumps({"condition": "enter_room", "room_id": goal_room.name,
                    "description": goal_room.goal_text,
                    "fixture_probe_rgb": probe_rgb,
                    "fixture_inventory_gates": gates,
                    "fixture_combinations": fixture_combinations,
                    "fixture_route": fixture_route}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (directory / "inventory-ids.txt").write_text(",".join(sorted(pickup_ids)) + "\n", encoding="ascii")
    return generated


def scrolling_fixture() -> RoomAsset:
    """A synthetic two-screen-wide room with distinct left/right regions."""
    width, height = 640, 200
    pixels = bytes(1 if y >= 150 else (2 if x >= 320 else 0)
                   for y in range(height) for x in range(width))
    # An 8-bit golden key silhouette, with orange sky matching its room area.
    key = bytes(3 if (2 <= y <= 4 and 1 <= x <= 5) or (y == 3 and 5 <= x <= 14)
                or (x in (11, 14) and y in (4, 5)) else 2
                for y in range(16) for x in range(16))
    door = bytes(4 if x in (0, 15) or y in (0, 15) else 1
                 for y in range(16) for x in range(16))
    open_door = bytes(5 if x in (0, 15) or y in (0, 15) else 2
                      for y in range(16) for x in range(16))
    return RoomAsset("Harbor", RoomGeometry(width, height, 320, 200), pixels,
                     ((70, 130, 190), (95, 60, 35), (240, 175, 95), (255, 220, 75),
                      (60, 220, 90), (50, 220, 220)),
                     (RoomHotspot("Key", "the key", "A rusty key.", 355, 100, 16, 16, True, key),
                      RoomHotspot("Door", "the door", "A locked door.", 450, 100, 16, 16, False, door,
                                  open_sprite_pixels=open_door, exit_destination="Cellar")),
                     demo_walk_to_x=540,
                     use_rules=(UseRule("Key", "Door", "The door is unlocked.",
                                        open_target=True),))


def destination_fixture() -> RoomAsset:
    """The second room verifies a real engine transition after the puzzle."""
    width, height = 320, 200
    palette = ((70, 130, 190), (95, 60, 35), (240, 175, 95), (255, 220, 75),
               (60, 220, 90), (120, 70, 180))
    stairs = bytes(4 if x in (0, 15) or y in (0, 15) else 1
                   for y in range(16) for x in range(16))
    return RoomAsset("Cellar", RoomGeometry(width, height, 320, 200), bytes([5]) * (width * height), palette,
                     hotspots=(RoomHotspot("Stairs", "stairs to the harbor", "The way back.",
                                           125, 100, 16, 16, sprite_pixels=stairs,
                                           exit_destination="Harbor"),),
                     goal_text="You reached the cellar. Puzzle solved!")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m adventure_studio.scumm_assets OUTPUT_DIRECTORY")
        return 2
    for generated in write_game_sources((scrolling_fixture(), destination_fixture()), Path(sys.argv[1])):
        for path in generated:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
