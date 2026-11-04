"""Strict JSON boundary for model-proposed story operations (no code execution)."""

from __future__ import annotations

import json
from dataclasses import MISSING, fields

from .story import Chapter, Character, Item, Puzzle, Scene
from .story_changes import DeleteEntity, PutEntity

_TYPES = {"chapter": Chapter, "scene": Scene, "character": Character,
          "item": Item, "puzzle": Puzzle}


def _string(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 4096


def parse_operations(raw: str) -> tuple[PutEntity | DeleteEntity, ...]:
    """Decode a bounded, allowlisted mutation request from an untrusted model."""
    if len(raw) > 200_000:
        raise ValueError("Proposal too large")
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != {"operations"}:
        raise ValueError("Expected operations envelope")
    entries = data["operations"]
    if not isinstance(entries, list) or len(entries) > 100:
        raise ValueError("Too many operations")
    parsed = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") not in _TYPES:
            raise ValueError("Invalid entity kind")
        kind = entry["kind"]
        if entry.get("op") == "delete" and set(entry) == {"op", "kind", "id"}:
            if not _string(entry["id"]):
                raise ValueError("Invalid ID")
            parsed.append(DeleteEntity(kind, entry["id"]))
        elif entry.get("op") == "put" and set(entry) == {"op", "kind", "entity"}:
            cls = _TYPES[kind]
            values = entry["entity"]
            if not isinstance(values, dict):
                raise ValueError("Invalid entity")
            expected = {f.name for f in fields(cls)}
            required = {f.name for f in fields(cls) if f.default is MISSING and f.default_factory is MISSING}
            if not required <= values.keys() or not values.keys() <= expected:
                raise ValueError("Unexpected or missing entity field")
            for name, value in values.items():
                if cls is Puzzle and name == "requires":
                    if not isinstance(value, list) or len(value) > 50 or not all(_string(x) for x in value):
                        raise ValueError("Invalid requirements")
                elif cls is Puzzle and name == "opens_scene_id" and value is None:
                    continue
                elif not _string(value):
                    raise ValueError(f"Invalid text field: {name}")
            if cls is Puzzle:
                values = {**values, "requires": tuple(values["requires"])}
            parsed.append(PutEntity(kind, cls(**values)))
        else:
            raise ValueError("Unknown operation shape")
    return tuple(parsed)
