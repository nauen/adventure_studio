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
from .story import Chapter, Character, Item, Puzzle, Scene, Story, validate_story
from .story_to_scumm import compile_story_to_scumm


_ENTITY_TYPES = {
    "chapters": Chapter, "scenes": Scene, "characters": Character,
    "items": Item, "puzzles": Puzzle,
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
    if type(root["format_version"]) is not int or root["format_version"] != 1:
        raise ValueError("Unsupported story document version")
    story_data = _object(root["story"], _STORY_FIELDS, "story")
    entities: dict[str, tuple] = {}
    for key, entity_type in _ENTITY_TYPES.items():
        entries = story_data[key]
        if not isinstance(entries, list) or len(entries) > 128:
            raise ValueError(f"Invalid {key} collection")
        expected = {field.name for field in fields(entity_type)}
        parsed = []
        for entry in entries:
            values = _object(entry, expected, entity_type.__name__)
            for field_name, value in values.items():
                if entity_type is Puzzle and field_name == "requires":
                    if not isinstance(value, list) or len(value) > 32:
                        raise ValueError("Invalid puzzle requirements")
                    for item_id in value:
                        _text(item_id, "requires")
                elif entity_type is Puzzle and field_name == "opens_scene_id" and value is None:
                    continue
                else:
                    _text(value, field_name)
            if entity_type is Puzzle:
                values = {**values, "requires": tuple(values["requires"])}
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
    return json.dumps({"format_version": 1, "story": asdict(story)},
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
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.story_document STORY.json OUTPUT_DIRECTORY")
        return 2
    result = build_story_document(Path(sys.argv[1]).read_text(encoding="utf-8"), Path(sys.argv[2]))
    print(result.project_json)
    print(result.resource_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
