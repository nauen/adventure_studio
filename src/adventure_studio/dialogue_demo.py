"""Deterministic one-character/linear-dialogue SCUMM test fixture."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from .story import Character, Dialogue, DialogueNode
from .story_document import canonical_story_json, parse_story_document, build_story_document


def dialogue_fixture(raw: str) -> str:
    story = parse_story_document(raw)
    if story.characters or story.dialogues or story.dialogue_nodes or story.dialogue_choices or story.assets:
        raise ValueError("Dialogue fixture requires an unmodified story")
    actor = Character("HarborKeeper", "Hafenwaechter", "Ein alter Waechter steht hier.",
                      story.starting_scene_id)
    greeting = Dialogue("HarborTalk", story.starting_scene_id, "HarborHello")
    nodes = (
        DialogueNode("HarborHello", greeting.id, actor.id, "Was suchst du hier?", "HarborHint"),
        DialogueNode("HarborHint", greeting.id, actor.id, "Der Schluessel liegt am Boden.", None),
    )
    return canonical_story_json(replace(story, characters=(actor,),
                                        dialogues=(greeting,), dialogue_nodes=nodes))


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m adventure_studio.dialogue_demo STORY.json OUTPUT_DIRECTORY")
        return 2
    raw = dialogue_fixture(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    build_story_document(raw, output)
    (output / "story.json").write_text(raw, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
