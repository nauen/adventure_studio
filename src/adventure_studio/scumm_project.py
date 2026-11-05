"""Versioned, declarative SCUMM project document and deterministic exporter.

No script strings or executable code are accepted from a project document.
The existing room compiler validates names, geometry, palette and references.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .palette_animation import PaletteCycle
from .scumm_assets import CombineRule, RoomAsset, RoomHotspot, UseRule, _validate, write_game_sources
from .targets import RoomGeometry


@dataclass(frozen=True)
class GameDocument:
    id: str
    rooms: tuple[RoomAsset, ...]


def _only(data: object, allowed: set[str], required: set[str]) -> dict:
    if not isinstance(data, dict) or set(data) - allowed or required - set(data):
        raise ValueError(f"Invalid document fields: expected {sorted(allowed)}")
    return data


def _decode_pixels(encoded: object) -> bytes:
    if not isinstance(encoded, str):
        raise ValueError("Pixel data must be base64")
    try:
        return base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("Invalid base64 pixel data") from error


def _encode_pixels(pixels: bytes | None) -> str | None:
    return base64.b64encode(pixels).decode("ascii") if pixels is not None else None


def document_dict(document: GameDocument) -> dict:
    _validate_document(document)
    return {
        "format_version": 1,
        "id": document.id,
        "rooms": [{
            "name": room.name,
            "geometry": {"width": room.geometry.room_width, "height": room.geometry.room_height,
                         "viewport_width": room.geometry.viewport_width,
                         "viewport_height": room.geometry.viewport_height},
            "pixels": _encode_pixels(room.pixels),
            "palette": [list(rgb) for rgb in room.palette],
            "hotspots": [{"id": h.id, "label": h.label, "description": h.description,
                          "x": h.x, "y": h.y, "width": h.width, "height": h.height,
                          "pickup": h.pickup, "sprite_pixels": _encode_pixels(h.sprite_pixels),
                          "open_sprite_pixels": _encode_pixels(h.open_sprite_pixels),
                          "exit_destination": h.exit_destination,
                          **({"talk_lines": list(h.talk_lines)} if h.talk_lines else {})} for h in room.hotspots],
            "use_rules": [{"item_id": r.item_id, "target_id": r.target_id,
                           "response": r.response, "hide_target": r.hide_target,
                           "destination_room": r.destination_room, "open_target": r.open_target,
                           "requires_inventory": list(r.requires_inventory)}
                          for r in room.use_rules],
            "demo_walk_to_x": room.demo_walk_to_x,
            "goal_text": room.goal_text,
            **({"combine_rules": [{"first_id": rule.first_id, "second_id": rule.second_id,
                                    "result_id": rule.result_id, "response": rule.response}
                                   for rule in room.combine_rules]} if room.combine_rules else {}),
            **({"palette_cycles": [{"name": cycle.name, "first": cycle.first,
                                     "last": cycle.last, "period_ticks": cycle.period_ticks,
                                     "reverse": cycle.reverse}
                                    for cycle in room.palette_cycles]} if room.palette_cycles else {}),
            **({"music_id": room.music_id} if room.music_id is not None else {}),
        } for room in document.rooms],
    }


def _validate_document(document: GameDocument) -> None:
    if not isinstance(document.id, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", document.id):
        raise ValueError("Invalid game project identifier")
    if not document.rooms or len(document.rooms) > 64:
        raise ValueError("Project must contain between 1 and 64 rooms")
    room_names = [r.name for r in document.rooms]
    if len(set(room_names)) != len(room_names):
        raise ValueError("Duplicate room name")
    for room in document.rooms:
        _validate(room)
        for destination in (r.destination_room for r in room.use_rules):
            if destination is not None and destination not in room_names:
                raise ValueError(f"Unknown destination room: {destination}")
        for destination in (h.exit_destination for h in room.hotspots):
            if destination is not None and destination not in room_names:
                raise ValueError(f"Unknown exit destination room: {destination}")
    if sum(r.goal_text is not None for r in document.rooms) != 1:
        raise ValueError("Project needs exactly one goal room")


def parse_document(source: str) -> GameDocument:
    """Reject unknown fields and invalid references before exporting anything."""
    try:
        root = json.loads(source)
    except json.JSONDecodeError as error:
        raise ValueError("Invalid project JSON") from error
    data = _only(root, {"format_version", "id", "rooms"}, {"format_version", "id", "rooms"})
    if type(data["format_version"]) is not int or data["format_version"] != 1:
        raise ValueError("Unsupported project format version")
    if not isinstance(data["rooms"], list):
        raise ValueError("Rooms must be a list")
    if len(data["rooms"]) > 64:
        raise ValueError("Too many rooms")
    rooms = []
    for raw in data["rooms"]:
        room = _only(raw, {"name", "geometry", "pixels", "palette", "hotspots", "use_rules", "combine_rules", "palette_cycles", "music_id",
                           "demo_walk_to_x", "goal_text"},
                     {"name", "geometry", "pixels", "palette", "hotspots", "use_rules",
                      "demo_walk_to_x", "goal_text"})
        g = _only(room["geometry"], {"width", "height", "viewport_width", "viewport_height"},
                  {"width", "height", "viewport_width", "viewport_height"})
        if any(type(value) is not int for value in g.values()):
            raise ValueError("Room geometry must use integers")
        if not isinstance(room["hotspots"], list) or not isinstance(room["use_rules"], list):
            raise ValueError("Hotspots and rules must be lists")
        raw_combinations = room.get("combine_rules", [])
        if not isinstance(raw_combinations, list) or len(raw_combinations) > 3:
            raise ValueError("Invalid combine rules")
        combinations = []
        raw_cycles = room.get("palette_cycles", [])
        if not isinstance(raw_cycles, list) or len(raw_cycles) > 16:
            raise ValueError("Invalid palette cycles")
        cycles = []
        for raw_cycle in raw_cycles:
            cycle = _only(raw_cycle, {"name", "first", "last", "period_ticks", "reverse"},
                          {"name", "first", "last", "period_ticks", "reverse"})
            if not isinstance(cycle["name"], str) or type(cycle["reverse"]) is not bool:
                raise ValueError("Invalid palette cycle fields")
            cycles.append(PaletteCycle(**cycle))
        for raw_rule in raw_combinations:
            rule = _only(raw_rule, {"first_id", "second_id", "result_id", "response"},
                         {"first_id", "second_id", "result_id", "response"})
            if any(not isinstance(v, str) for v in rule.values()):
                raise ValueError("Combination fields must be strings")
            combinations.append(CombineRule(**rule))
        hotspots = []
        for item in room["hotspots"]:
            h = _only(item, {"id", "label", "description", "x", "y", "width", "height", "pickup",
                             "sprite_pixels", "open_sprite_pixels", "exit_destination", "talk_lines"},
                      {"id", "label", "description", "x", "y", "width", "height", "pickup",
                       "sprite_pixels", "open_sprite_pixels", "exit_destination"})
            if type(h["pickup"]) is not bool:
                raise ValueError("Pickup must be a Boolean")
            talk_lines = h.get("talk_lines", [])
            if not isinstance(talk_lines, list) or not all(isinstance(x, str) for x in talk_lines):
                raise ValueError("Invalid dialogue lines")
            hotspots.append(RoomHotspot(
                h["id"], h["label"], h["description"], h["x"], h["y"], h["width"], h["height"],
                h["pickup"], _decode_pixels(h["sprite_pixels"]) if h["sprite_pixels"] is not None else None,
                _decode_pixels(h["open_sprite_pixels"]) if h["open_sprite_pixels"] is not None else None,
                h["exit_destination"], tuple(talk_lines),
            ))
        rules = []
        for item in room["use_rules"]:
            r = _only(item, {"item_id", "target_id", "response", "hide_target", "destination_room",
                             "open_target", "requires_inventory"},
                      {"item_id", "target_id", "response", "hide_target", "destination_room",
                       "open_target", "requires_inventory"})
            if type(r["hide_target"]) is not bool or type(r["open_target"]) is not bool:
                raise ValueError("Rule state actions must be Booleans")
            if not isinstance(r["requires_inventory"], list) or len(r["requires_inventory"]) > 16:
                raise ValueError("Invalid inventory requirements")
            if any(not isinstance(item_id, str) for item_id in r["requires_inventory"]):
                raise ValueError("Inventory requirement IDs must be strings")
            rules.append(UseRule(**{**r, "requires_inventory": tuple(r["requires_inventory"])}))
        if not isinstance(room["palette"], list):
            raise ValueError("Palette must be a list")
        rooms.append(RoomAsset(
            room["name"], RoomGeometry(g["width"], g["height"], g["viewport_width"], g["viewport_height"]),
            _decode_pixels(room["pixels"]), tuple(tuple(rgb) for rgb in room["palette"]),
            tuple(hotspots), room["demo_walk_to_x"], tuple(rules), room["goal_text"], tuple(combinations),
            tuple(cycles),
            room.get("music_id"),
        ))
    document = GameDocument(data["id"], tuple(rooms))
    _validate_document(document)
    return document


def canonical_json(document: GameDocument) -> str:
    return json.dumps(document_dict(document), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def export_document(document: GameDocument, directory: Path) -> None:
    """Generate identical files for identical inputs; never interpret code."""
    _validate_document(document)
    write_game_sources(document.rooms, directory)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.scumm_project PROJECT.json OUTPUT_DIRECTORY")
        return 2
    source = Path(sys.argv[1]).read_text(encoding="utf-8")
    document = parse_document(source)
    export_document(document, Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
