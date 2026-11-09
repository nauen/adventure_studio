"""Versioned authoring document for Story and its native Actor/action layer.

Story remains the source of room content. Native assets and actions are stored
once, without duplicating generated room bitmaps in the authoring document.
"""

from __future__ import annotations

import json

from .scumm_project import canonical_json, parse_document
from .story_document import canonical_story_json, parse_story_document
from .studio_sequences import compose_story_project


NATIVE_FIELDS = frozenset(("costumes", "actors", "animation_rules",
                           "animation_input_rules", "animation_triggers",
                           "interaction_sequences", "dialogue_animation_cues"))


def canonical_studio_project(story_raw: str, native_raw: str | None = None) -> str:
    """Store the current validated Story plus native authoring data in one file."""
    story = canonical_story_json(parse_story_document(story_raw))
    project = json.loads(compose_story_project(story, native_raw))
    layer = {name: project[name] for name in sorted(NATIVE_FIELDS) if name in project}
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
    if not isinstance(layer, dict) or set(layer) - NATIVE_FIELDS:
        raise ValueError("Unknown native Studio authoring field")
    story = canonical_story_json(parse_story_document(json.dumps(data["story"])))
    # A generated room is never a second, independently mutable authoring copy.
    generated = json.loads(compose_story_project(story))
    generated.update(layer)
    native = canonical_json(parse_document(json.dumps(generated)))
    return story, native
