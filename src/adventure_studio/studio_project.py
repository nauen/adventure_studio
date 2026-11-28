"""Versioned authoring document for Story and its native Actor/action layer.

Story remains the source of room content. Native assets and actions are stored
once, without duplicating unchanged generated room bitmaps.
"""

from __future__ import annotations

import json

from .scumm_project import canonical_json, parse_document
from .story_document import canonical_story_json, parse_story_document
from .studio_sequences import compose_story_project, validate_background_width


NATIVE_FIELDS = frozenset(("costumes", "actors", "animation_rules",
                           "animation_input_rules", "animation_triggers",
                           "interaction_sequences", "dialogue_animation_cues"))
ROOM_OVERRIDE_FIELDS = frozenset(("geometry", "pixels", "palette", "authored_background", "palette_cycles",
                                  "hotspots", "use_rules", "zplanes", "walkboxes", "box_routes",
                                  "scale_slots", "scale_curves", "camera_cues", "demo_walk_to_x",
                                  "demo_walk_to_y", "ego_start_x", "ego_start_y"))


def canonical_studio_project(story_raw: str, native_raw: str | None = None) -> str:
    """Store the current validated Story plus native authoring data in one file."""
    story = canonical_story_json(parse_story_document(story_raw))
    project = json.loads(compose_story_project(story, native_raw))
    layer = {name: project[name] for name in sorted(NATIVE_FIELDS) if name in project}
    generated = {r["name"]: r for r in json.loads(compose_story_project(story))["rooms"]}
    overrides = {}
    for room in project["rooms"]:
        original = generated[room["name"]]
        fields = {key: room.get(key) for key in sorted(ROOM_OVERRIDE_FIELDS)
                  if room.get(key) != original.get(key)}
        if fields:
            overrides[room["name"]] = fields
    if overrides:
        layer["room_overrides"] = overrides
    return json.dumps({"format_version": 1, "story": json.loads(story), "native": layer},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def parse_studio_project(raw: str) -> tuple[str, str]:
    """Return the editable Story and native GameDocument; reject stale references."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("Invalid Studio project JSON") from error
    if (not isinstance(data, dict) or set(data) != {"format_version", "story", "native"}
            or type(data["format_version"]) is not int or data["format_version"] != 1):
        raise ValueError("Unsupported Studio project document")
    layer = data["native"]
    if not isinstance(layer, dict) or set(layer) - (NATIVE_FIELDS | {"room_overrides"}):
        raise ValueError("Unknown native Studio authoring field")
    story = canonical_story_json(parse_story_document(json.dumps(data["story"])))
    generated = json.loads(compose_story_project(story))
    overrides = layer.get("room_overrides", {})
    if not isinstance(overrides, dict) or set(overrides) - {r["name"] for r in generated["rooms"]}:
        raise ValueError("Unknown native Studio room override")
    for room in generated["rooms"]:
        fields = overrides.get(room["name"], {})
        if not isinstance(fields, dict) or set(fields) - ROOM_OVERRIDE_FIELDS:
            raise ValueError("Unknown native Studio room authoring field")
        if (set(fields) & {"geometry", "pixels", "palette"}) and fields.get("authored_background") is not True:
            raise ValueError("Room background override needs authored background flag")
        if "geometry" in fields:
            geometry = fields["geometry"]
            if not isinstance(geometry, dict) or {**geometry, "width": room["geometry"]["width"]} != room["geometry"] or "width" not in geometry:
                raise ValueError("Only horizontal room extension is supported")
            validate_background_width(room["geometry"]["width"], geometry["width"])
        for key, value in fields.items():
            if value is None and key != "demo_walk_to_x":
                room.pop(key, None)
            else:
                room[key] = value
    generated.update({key: value for key, value in layer.items() if key in NATIVE_FIELDS})
    native = canonical_json(parse_document(json.dumps(generated)))
    return story, native
