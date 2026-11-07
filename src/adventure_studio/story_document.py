"""Strict, versioned story file boundary for the experimental SCUMM exporter.

The author/AI edits semantic story data; only validated values can reach the
deterministic Story -> GameDocument -> SCUMM resources compiler chain.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from .scumm_project import canonical_json, export_document
from .story import (AssetRef, Chapter, Character, Dialogue, DialogueChoice,
                    DialogueNode, Item, Placement, Puzzle, Recipe, Scene,
                    Story, validate_story, verify_story)
from .story_to_scumm import compile_story_to_scumm


_ENTITY_TYPES = {
    "chapters": Chapter, "scenes": Scene, "characters": Character,
    "items": Item, "puzzles": Puzzle,
    "recipes": Recipe,
    "placements": Placement,
    "dialogues": Dialogue, "dialogue_nodes": DialogueNode,
    "dialogue_choices": DialogueChoice, "assets": AssetRef,
}
_STORY_FIELDS = {f.name for f in fields(Story)}


def _object(value: object, expected: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"Invalid {name} fields")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not 0 < len(value) <= 4096:
        raise ValueError(f"Invalid story text: {field}")
    return value


def parse_story_document(raw: str) -> Story:
    if len(raw) > 1_000_000:
        raise ValueError("Story document exceeds size limit")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("Invalid story JSON") from error
    root = _object(envelope, {"format_version", "story"}, "story document")
    version = root["format_version"]
    if type(version) is not int or version not in (1, 2, 3, 4):
        raise ValueError("Unsupported story document version")
    optional_v4 = {"dialogues", "dialogue_nodes", "dialogue_choices", "assets"}
    expected_story_fields = (_STORY_FIELDS if version == 4
                             else _STORY_FIELDS - optional_v4 if version == 3
                             else _STORY_FIELDS - optional_v4 - {"placements"} if version == 2
                             else _STORY_FIELDS - optional_v4 - {"recipes", "placements"})
    story_data = _object(root["story"], expected_story_fields, "story")
    entities: dict[str, tuple] = {}
    for key, entity_type in _ENTITY_TYPES.items():
        entries = story_data[key] if key in story_data else []
        if not isinstance(entries, list) or len(entries) > 128:
            raise ValueError(f"Invalid {key} collection")
        expected = {field.name for field in fields(entity_type)}
        parsed = []
        for entry in entries:
            values = _object(entry, expected, entity_type.__name__)
            for field_name, value in values.items():
                if (entity_type is Puzzle and field_name == "requires"
                        or entity_type is Recipe and field_name == "ingredients"):
                    if not isinstance(value, list) or len(value) > 32:
                        raise ValueError("Invalid item requirements")
                    for item_id in value:
                        _text(item_id, field_name)
                elif ((entity_type is Puzzle and field_name == "opens_scene_id")
                      or (entity_type in (DialogueNode, DialogueChoice) and field_name == "next_node_id")) and value is None:
                    continue
                elif entity_type is Placement and field_name in ("x", "y"):
                    if type(value) is not int or value < 0:
                        raise ValueError("Invalid placement coordinate")
                else:
                    _text(value, field_name)
            if entity_type is Puzzle:
                values = {**values, "requires": tuple(values["requires"])}
            if entity_type is Recipe:
                values = {**values, "ingredients": tuple(values["ingredients"])}
            parsed.append(entity_type(**values))
        entities[key] = tuple(parsed)
    story = Story(
        **entities,
        starting_scene_id=_text(story_data["starting_scene_id"], "starting_scene_id"),
        final_puzzle_id=_text(story_data["final_puzzle_id"], "final_puzzle_id"),
    )
    validate_story(story)
    return story


def canonical_story_json(story: Story) -> str:
    validate_story(story)
    data = asdict(story)
    version = (4 if story.dialogues or story.dialogue_nodes or story.dialogue_choices or story.assets
               else 3 if story.placements else 2 if story.recipes else 1)
    if version == 1:
        del data["recipes"]
    if version < 3:
        del data["placements"]
    if version < 4:
        for field in ("dialogues", "dialogue_nodes", "dialogue_choices", "assets"):
            del data[field]
    return json.dumps({"format_version": version, "story": data},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


@dataclass(frozen=True)
class StoryBuildResult:
    project_json: Path
    resource_directory: Path


def build_story_document(raw: str, directory: Path) -> StoryBuildResult:
    """Validate and compile everything before creating output files."""
    story = parse_story_document(raw)
    project = compile_story_to_scumm(story)
    project_json = canonical_json(project)
    output = directory / "resources"
    export_document(project, output)
    project_path = directory / "project.json"
    project_path.write_text(project_json, encoding="utf-8")
    return StoryBuildResult(project_path, output)


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[2] == "--validate-only":
        story = parse_story_document(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(json.dumps({"playable_path": verify_story(story)}, sort_keys=True))
        return 0
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.story_document STORY.json OUTPUT_DIRECTORY|--validate-only")
        return 2
    result = build_story_document(Path(sys.argv[1]).read_text(encoding="utf-8"), Path(sys.argv[2]))
    print(result.project_json)
    print(result.resource_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
